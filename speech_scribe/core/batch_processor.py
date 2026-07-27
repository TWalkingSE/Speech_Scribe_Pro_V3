#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📦 Processador em Batch Otimizado - Speech Scribe Pro V3
Processamento paralelo de múltiplos arquivos com fila e progresso
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from speech_scribe.utils.logger import logger


class TaskStatus(Enum):
    """Status de uma tarefa"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Prioridade de tarefa"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class BatchTask:
    """Tarefa individual do batch"""
    id: str
    file_path: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Duração em segundos"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def file_name(self) -> str:
        """Nome do arquivo"""
        return Path(self.file_path).name

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'priority': self.priority.name,
            'status': self.status.value,
            'progress': self.progress,
            'duration': self.duration,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class BatchProgress:
    """Progresso geral do batch"""
    total: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    processing: int = 0

    @property
    def pending(self) -> int:
        return self.total - self.completed - self.failed - self.cancelled - self.processing

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100

    @property
    def success_rate(self) -> float:
        finished = self.completed + self.failed
        if finished == 0:
            return 0.0
        return (self.completed / finished) * 100


class BatchProcessor:
    """
    Processador de batch com suporte a:
    - Processamento paralelo
    - Fila com prioridade
    - Callbacks de progresso
    - Cancelamento
    - Retry automático
    """

    def __init__(self,
                 max_workers: int = 2,
                 on_task_start: Optional[Callable[[BatchTask], None]] = None,
                 on_task_complete: Optional[Callable[[BatchTask], None]] = None,
                 on_task_error: Optional[Callable[[BatchTask, Exception], None]] = None,
                 on_progress: Optional[Callable[[BatchProgress], None]] = None):
        """
        Inicializa o processador.
        
        Args:
            max_workers: Número máximo de workers paralelos
            on_task_start: Callback quando tarefa inicia
            on_task_complete: Callback quando tarefa completa
            on_task_error: Callback quando tarefa falha
            on_progress: Callback de progresso geral
        """
        self.max_workers = max_workers
        self._tasks: Dict[str, BatchTask] = {}
        self._queue: List[BatchTask] = []
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._running = False

        # Callbacks
        self.on_task_start = on_task_start
        self.on_task_complete = on_task_complete
        self.on_task_error = on_task_error
        self.on_progress = on_progress

        # Função de processamento (deve ser definida)
        self._process_func: Optional[Callable] = None

        logger.info(f"BatchProcessor inicializado com {max_workers} workers")

    def set_processor(self, func: Callable[[str, Dict[str, Any]], Dict[str, Any]]):
        """
        Define a função de processamento.
        
        Args:
            func: Função que recebe (file_path, metadata) e retorna resultado
        """
        self._process_func = func

    def add_file(self, file_path: str, priority: TaskPriority = TaskPriority.NORMAL,
                 metadata: Optional[Dict[str, Any]] = None) -> BatchTask:
        """
        Adiciona arquivo à fila.
        
        Args:
            file_path: Caminho do arquivo
            priority: Prioridade da tarefa
            metadata: Metadados adicionais
            
        Returns:
            Tarefa criada
        """
        task_id = f"task_{len(self._tasks)}_{int(time.time() * 1000)}"

        task = BatchTask(
            id=task_id,
            file_path=file_path,
            priority=priority,
            status=TaskStatus.QUEUED,
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[task_id] = task
            self._queue.append(task)
            # Ordenar por prioridade (maior primeiro)
            self._queue.sort(key=lambda t: t.priority.value, reverse=True)

        logger.info(f"Tarefa adicionada: {task.file_name} (prioridade: {priority.name})")
        self._notify_progress()

        return task

    def add_files(self, file_paths: List[str], priority: TaskPriority = TaskPriority.NORMAL,
                  metadata: Optional[Dict[str, Any]] = None) -> List[BatchTask]:
        """Adiciona múltiplos arquivos"""
        return [self.add_file(fp, priority, metadata) for fp in file_paths]

    def get_task(self, task_id: str) -> Optional[BatchTask]:
        """Obtém tarefa por ID"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[BatchTask]:
        """Obtém todas as tarefas"""
        return list(self._tasks.values())

    def get_progress(self) -> BatchProgress:
        """Obtém progresso atual"""
        progress = BatchProgress(total=len(self._tasks))

        for task in self._tasks.values():
            if task.status == TaskStatus.COMPLETED:
                progress.completed += 1
            elif task.status == TaskStatus.FAILED:
                progress.failed += 1
            elif task.status == TaskStatus.CANCELLED:
                progress.cancelled += 1
            elif task.status == TaskStatus.PROCESSING:
                progress.processing += 1

        return progress

    def _notify_progress(self):
        """Notifica callback de progresso"""
        if self.on_progress:
            try:
                self.on_progress(self.get_progress())
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")

    def _process_task(self, task: BatchTask) -> BatchTask:
        """Processa uma tarefa individual"""
        if self._cancel_event.is_set():
            task.status = TaskStatus.CANCELLED
            return task

        try:
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()
            task.progress = 0.0

            # Notificar início
            if self.on_task_start:
                self.on_task_start(task)
            self._notify_progress()

            # Processar
            if self._process_func is None:
                raise ValueError("Função de processamento não definida. Use set_processor()")

            result = self._process_func(task.file_path, task.metadata)

            # Sucesso
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.progress = 100.0
            task.result = result

            logger.info(f"✅ Concluído: {task.file_name} ({task.duration:.1f}s)")

            if self.on_task_complete:
                self.on_task_complete(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.error = str(e)

            logger.error(f"❌ Falha: {task.file_name} - {e}")

            if self.on_task_error:
                self.on_task_error(task, e)

        self._notify_progress()
        return task

    def start(self):
        """Inicia processamento do batch"""
        if self._running:
            logger.warning("Processamento já em andamento")
            return

        if not self._queue:
            logger.warning("Fila vazia")
            return

        if self._process_func is None:
            raise ValueError("Função de processamento não definida")

        self._running = True
        self._cancel_event.clear()

        logger.info(f"🚀 Iniciando batch: {len(self._queue)} arquivos")

        # Processar com ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        try:
            # Submeter todas as tarefas
            futures = {
                self._executor.submit(self._process_task, task): task
                for task in self._queue
            }

            # Aguardar conclusão
            for future in as_completed(futures):
                if self._cancel_event.is_set():
                    break

                task = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Erro inesperado em {task.file_name}: {e}")

        finally:
            self._executor.shutdown(wait=False)
            self._running = False

            progress = self.get_progress()
            logger.info(f"📊 Batch finalizado: {progress.completed}/{progress.total} sucesso, "
                       f"{progress.failed} falhas")

    def start_async(self) -> threading.Thread:
        """Inicia processamento em thread separada"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def cancel(self):
        """Cancela processamento"""
        logger.info("⛔ Cancelando batch...")
        self._cancel_event.set()

        # Marcar tarefas pendentes como canceladas
        with self._lock:
            for task in self._queue:
                if task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                    task.status = TaskStatus.CANCELLED

        if self._executor:
            self._executor.shutdown(wait=False)

    def clear(self):
        """Limpa todas as tarefas"""
        with self._lock:
            self._tasks.clear()
            self._queue.clear()
        logger.info("Fila limpa")

    def retry_failed(self):
        """Reprocessa tarefas que falharam"""
        with self._lock:
            for task in self._tasks.values():
                if task.status == TaskStatus.FAILED:
                    task.status = TaskStatus.QUEUED
                    task.error = None
                    task.result = None
                    task.progress = 0.0
                    if task not in self._queue:
                        self._queue.append(task)

        logger.info("Tarefas falhadas re-enfileiradas")

    def get_results(self) -> List[Dict[str, Any]]:
        """Obtém resultados de todas as tarefas completadas"""
        return [
            {
                'task': task.to_dict(),
                'result': task.result
            }
            for task in self._tasks.values()
            if task.status == TaskStatus.COMPLETED and task.result
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo do processamento"""
        progress = self.get_progress()

        completed_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.COMPLETED]
        total_duration = sum(t.duration or 0 for t in completed_tasks)

        return {
            'progress': {
                'total': progress.total,
                'completed': progress.completed,
                'failed': progress.failed,
                'cancelled': progress.cancelled,
                'success_rate': progress.success_rate
            },
            'timing': {
                'total_duration_s': total_duration,
                'avg_duration_s': total_duration / len(completed_tasks) if completed_tasks else 0
            },
            'tasks': [t.to_dict() for t in self._tasks.values()]
        }


class TranscriptionBatchProcessor(BatchProcessor):
    """
    Processador de batch especializado para transcrições.
    """

    def __init__(self, engine, model: str = "small", language: str = "auto", **kwargs):
        """
        Inicializa processador de transcrições.
        
        Args:
            engine: IntelligentTranscriptionEngine
            model: Modelo a usar
            language: Idioma
        """
        super().__init__(**kwargs)
        self.engine = engine
        self.model = model
        self.language = language

        # Definir função de processamento
        self.set_processor(self._transcribe_file)

    def _transcribe_file(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Transcreve um arquivo"""

        # Usar modelo e idioma do metadata se fornecidos
        model = metadata.get('model', self.model)
        language = metadata.get('language', self.language)

        # Executar transcrição
        result = asyncio.run(self.engine.transcribe_async(file_path, model, language))

        return result

    def add_audio_files(self, file_paths: List[str], model: Optional[str] = None,
                        language: Optional[str] = None) -> List[BatchTask]:
        """
        Adiciona arquivos de áudio com configurações específicas.
        
        Args:
            file_paths: Lista de caminhos de arquivos
            model: Modelo (opcional, usa padrão se não fornecido)
            language: Idioma (opcional)
        """
        metadata = {}
        if model:
            metadata['model'] = model
        if language:
            metadata['language'] = language

        return self.add_files(file_paths, metadata=metadata)


__all__ = [
    'TaskStatus',
    'TaskPriority',
    'BatchTask',
    'BatchProgress',
    'BatchProcessor',
    'TranscriptionBatchProcessor',
]
