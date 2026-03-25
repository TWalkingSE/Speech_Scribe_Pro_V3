#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📋 Sistema de Logging Estruturado - Speech Scribe Pro V3
Logging avançado com suporte a JSON, contexto e métricas
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
import threading
import time


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Contexto para logs estruturados"""
    operation: str = ""
    component: str = ""
    file_path: str = ""
    model: str = ""
    device: str = ""
    user_id: str = ""
    session_id: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {k: v for k, v in asdict(self).items() if v}
        if 'extra' in result and not result['extra']:
            del result['extra']
        return result


@dataclass
class LogEntry:
    """Entrada de log estruturada"""
    timestamp: str
    level: str
    message: str
    logger_name: str
    context: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    error: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            context=getattr(record, 'context', {}),
            duration_ms=getattr(record, 'duration_ms', None),
            metrics=getattr(record, 'metrics', None)
        )
        
        # Adicionar informações de erro se houver exceção
        if record.exc_info:
            entry.error = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        return entry.to_json()


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para terminal"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        # Timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Level com cor
        level = record.levelname
        if self.use_colors and level in self.COLORS:
            level = f"{self.COLORS[level]}{level:8}{self.RESET}"
        else:
            level = f"{level:8}"
        
        # Mensagem
        message = record.getMessage()
        
        # Contexto
        context = getattr(record, 'context', {})
        context_str = ""
        if context:
            ctx_parts = [f"{k}={v}" for k, v in context.items() if v]
            if ctx_parts:
                context_str = f" [{', '.join(ctx_parts)}]"
        
        # Duração
        duration = getattr(record, 'duration_ms', None)
        duration_str = f" ({duration:.1f}ms)" if duration else ""
        
        # Métricas
        metrics = getattr(record, 'metrics', None)
        metrics_str = ""
        if metrics:
            metrics_str = f" | {json.dumps(metrics)}"
        
        return f"{timestamp} | {level} | {message}{context_str}{duration_str}{metrics_str}"


class StructuredLogger:
    """
    Logger estruturado com suporte a contexto, métricas e múltiplos outputs.
    
    Features:
    - Logs em JSON para arquivos
    - Logs coloridos para terminal
    - Contexto thread-local
    - Métricas de operações
    - Timers automáticos
    """
    
    _instances: Dict[str, 'StructuredLogger'] = {}
    _context = threading.local()
    
    def __init__(self, name: str, log_dir: Optional[Path] = None, 
                 level: LogLevel = LogLevel.INFO,
                 json_output: bool = True,
                 console_output: bool = True):
        """
        Inicializa o logger.
        
        Args:
            name: Nome do logger
            log_dir: Diretório para arquivos de log
            level: Nível mínimo de log
            json_output: Habilitar saída JSON para arquivo
            console_output: Habilitar saída colorida no console
        """
        self.name = name
        self.log_dir = log_dir or Path.home() / ".speech_scribe_v3" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar logger Python
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value))
        self._logger.handlers.clear()
        
        # Handler para console
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter(use_colors=True))
            self._logger.addHandler(console_handler)
        
        # Handler para arquivo JSON
        if json_output:
            json_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
            file_handler = logging.FileHandler(json_file, encoding='utf-8')
            file_handler.setFormatter(JSONFormatter())
            self._logger.addHandler(file_handler)
        
        # Métricas internas
        self._metrics = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'operations': {}
        }
    
    @classmethod
    def get_logger(cls, name: str = "speech_scribe", **kwargs) -> 'StructuredLogger':
        """Obtém ou cria logger singleton"""
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]
    
    def _get_context(self) -> Dict[str, Any]:
        """Obtém contexto thread-local"""
        if not hasattr(self._context, 'data'):
            self._context.data = {}
        return self._context.data
    
    def set_context(self, **kwargs):
        """Define contexto para logs subsequentes"""
        ctx = self._get_context()
        ctx.update(kwargs)
    
    def clear_context(self):
        """Limpa contexto"""
        self._context.data = {}
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager para contexto temporário"""
        old_ctx = self._get_context().copy()
        self.set_context(**kwargs)
        try:
            yield
        finally:
            self._context.data = old_ctx
    
    def _log(self, level: int, message: str, context: Optional[Dict] = None,
             duration_ms: Optional[float] = None, metrics: Optional[Dict] = None,
             exc_info: bool = False):
        """Log interno com contexto"""
        # Merge contexto
        full_context = {**self._get_context(), **(context or {})}
        
        # Criar record extra
        extra = {
            'context': full_context,
            'duration_ms': duration_ms,
            'metrics': metrics
        }
        
        # Log
        self._logger.log(level, message, extra=extra, exc_info=exc_info)
        
        # Atualizar métricas
        self._metrics['total_logs'] += 1
        if level >= logging.ERROR:
            self._metrics['errors'] += 1
        elif level >= logging.WARNING:
            self._metrics['warnings'] += 1
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log informativo"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log de erro"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log crítico"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    @contextmanager
    def timer(self, operation: str, context: Optional[Dict] = None):
        """
        Context manager para medir tempo de operação.
        
        Usage:
            with logger.timer("transcription"):
                result = transcribe(file)
        """
        start = time.perf_counter()
        self.info(f"Iniciando: {operation}", context=context)
        
        try:
            yield
            duration_ms = (time.perf_counter() - start) * 1000
            self.info(f"Concluído: {operation}", duration_ms=duration_ms, context=context)
            
            # Atualizar métricas de operação
            if operation not in self._metrics['operations']:
                self._metrics['operations'][operation] = {'count': 0, 'total_ms': 0, 'errors': 0}
            self._metrics['operations'][operation]['count'] += 1
            self._metrics['operations'][operation]['total_ms'] += duration_ms
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            self.error(f"Erro em: {operation}", duration_ms=duration_ms, context=context)
            
            if operation in self._metrics['operations']:
                self._metrics['operations'][operation]['errors'] += 1
            raise
    
    def log_operation(self, operation: str, success: bool, duration_ms: float,
                      context: Optional[Dict] = None, metrics: Optional[Dict] = None):
        """
        Log de operação completa.
        
        Args:
            operation: Nome da operação
            success: Se foi bem sucedida
            duration_ms: Duração em milissegundos
            context: Contexto adicional
            metrics: Métricas da operação
        """
        level = logging.INFO if success else logging.ERROR
        status = "✅" if success else "❌"
        message = f"{status} {operation}"
        
        self._log(level, message, context=context, duration_ms=duration_ms, metrics=metrics)
    
    def log_transcription(self, file_path: str, model: str, language: str,
                          duration_s: float, success: bool, 
                          audio_duration_s: Optional[float] = None,
                          text_length: Optional[int] = None):
        """Log especializado para transcrições"""
        metrics = {
            'audio_duration_s': audio_duration_s,
            'text_length': text_length,
            'speed_factor': audio_duration_s / duration_s if audio_duration_s and duration_s else None
        }
        
        self.log_operation(
            "transcription",
            success=success,
            duration_ms=duration_s * 1000,
            context={'file': Path(file_path).name, 'model': model, 'language': language},
            metrics={k: v for k, v in metrics.items() if v is not None}
        )
    
    def log_analysis(self, analysis_type: str, text_length: int,
                     duration_s: float, success: bool, model: Optional[str] = None):
        """Log especializado para análises"""
        self.log_operation(
            f"analysis.{analysis_type}",
            success=success,
            duration_ms=duration_s * 1000,
            context={'type': analysis_type, 'model': model},
            metrics={'text_length': text_length}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do logger"""
        return {
            **self._metrics,
            'operations_summary': {
                op: {
                    'count': data['count'],
                    'avg_ms': data['total_ms'] / data['count'] if data['count'] > 0 else 0,
                    'error_rate': data['errors'] / data['count'] if data['count'] > 0 else 0
                }
                for op, data in self._metrics['operations'].items()
            }
        }


# Logger global
_default_logger: Optional[StructuredLogger] = None


def get_structured_logger(name: str = "speech_scribe") -> StructuredLogger:
    """Obtém logger estruturado global"""
    global _default_logger
    if _default_logger is None:
        _default_logger = StructuredLogger.get_logger(name)
    return _default_logger


__all__ = [
    'LogLevel',
    'LogContext',
    'LogEntry',
    'StructuredLogger',
    'get_structured_logger',
]
