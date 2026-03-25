#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes da Fase 3 - Speech Scribe Pro V3
Testes para: StructuredLogger, BatchProcessor, CLI, PerformanceMonitor
"""

import pytest
import time
import threading
from pathlib import Path


class TestStructuredLogger:
    """Testes para StructuredLogger"""
    
    @pytest.fixture
    def logger(self, tmp_path):
        """Fixture de logger"""
        from speech_scribe.utils.structured_logger import StructuredLogger, LogLevel
        return StructuredLogger(
            name="test_logger",
            log_dir=tmp_path,
            level=LogLevel.DEBUG,
            json_output=True,
            console_output=False
        )
    
    def test_basic_logging(self, logger):
        """Testa logging básico"""
        logger.info("Test message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        
        metrics = logger.get_metrics()
        assert metrics['total_logs'] == 3
    
    def test_context_logging(self, logger):
        """Testa logging com contexto"""
        logger.set_context(operation="test", model="small")
        logger.info("Message with context")
        
        # Verificar que contexto foi definido
        assert logger._get_context()['operation'] == "test"
    
    def test_context_manager(self, logger):
        """Testa context manager"""
        with logger.context(file="audio.mp3"):
            context = logger._get_context()
            assert context['file'] == "audio.mp3"
        
        # Contexto deve ser restaurado
        assert 'file' not in logger._get_context()
    
    def test_timer(self, logger):
        """Testa timer de operações"""
        with logger.timer("test_operation"):
            time.sleep(0.01)
        
        metrics = logger.get_metrics()
        assert 'test_operation' in metrics['operations']
        assert metrics['operations']['test_operation']['count'] == 1
    
    def test_error_counting(self, logger):
        """Testa contagem de erros"""
        logger.error("Test error", exc_info=False)
        logger.warning("Test warning")
        
        metrics = logger.get_metrics()
        assert metrics['errors'] == 1
        assert metrics['warnings'] == 1


class TestBatchProcessor:
    """Testes para BatchProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Fixture de processor"""
        from speech_scribe.core.batch_processor import BatchProcessor
        return BatchProcessor(max_workers=2)
    
    def test_add_file(self, processor, tmp_path):
        """Testa adição de arquivo"""
        test_file = tmp_path / "test.mp3"
        test_file.touch()
        
        task = processor.add_file(str(test_file))
        
        assert task.file_path == str(test_file)
        assert task.file_name == "test.mp3"
    
    def test_add_multiple_files(self, processor, tmp_path):
        """Testa adição de múltiplos arquivos"""
        files = []
        for i in range(3):
            f = tmp_path / f"test{i}.mp3"
            f.touch()
            files.append(str(f))
        
        tasks = processor.add_files(files)
        
        assert len(tasks) == 3
    
    def test_priority_ordering(self, processor, tmp_path):
        """Testa ordenação por prioridade"""
        from speech_scribe.core.batch_processor import TaskPriority
        
        low = tmp_path / "low.mp3"
        high = tmp_path / "high.mp3"
        low.touch()
        high.touch()
        
        processor.add_file(str(low), priority=TaskPriority.LOW)
        processor.add_file(str(high), priority=TaskPriority.HIGH)
        
        # High deve estar primeiro na fila
        assert processor._queue[0].priority == TaskPriority.HIGH
    
    def test_progress(self, processor, tmp_path):
        """Testa progresso"""
        for i in range(5):
            f = tmp_path / f"test{i}.mp3"
            f.touch()
            processor.add_file(str(f))
        
        progress = processor.get_progress()
        
        assert progress.total == 5
        assert progress.pending == 5
    
    def test_clear(self, processor, tmp_path):
        """Testa limpeza"""
        f = tmp_path / "test.mp3"
        f.touch()
        processor.add_file(str(f))
        
        processor.clear()
        
        assert len(processor._tasks) == 0


class TestCLI:
    """Testes para CLI"""
    
    def test_parser_creation(self):
        """Testa criação do parser"""
        from speech_scribe.cli import create_parser
        
        parser = create_parser()
        
        assert parser is not None
    
    def test_transcribe_args(self):
        """Testa parsing de argumentos de transcrição"""
        from speech_scribe.cli import create_parser
        
        parser = create_parser()
        args = parser.parse_args(['transcribe', 'audio.mp3', '-m', 'large-v3', '-l', 'pt'])
        
        assert args.command == 'transcribe'
        assert args.model == 'large-v3'
        assert args.language == 'pt'
    
    def test_analyze_args(self):
        """Testa parsing de argumentos de análise"""
        from speech_scribe.cli import create_parser
        
        parser = create_parser()
        args = parser.parse_args(['analyze', 'text.txt', '--sentiment', '--keywords'])
        
        assert args.command == 'analyze'
        assert args.sentiment is True
        assert args.keywords is True
    
    def test_status_args(self):
        """Testa parsing de argumentos de status"""
        from speech_scribe.cli import create_parser
        
        parser = create_parser()
        args = parser.parse_args(['status', '--all'])
        
        assert args.command == 'status'
        assert args.all is True


class TestPerformanceMonitor:
    """Testes para PerformanceMonitor"""
    
    @pytest.fixture
    def monitor(self):
        """Fixture de monitor"""
        from speech_scribe.utils.performance import PerformanceMonitor
        return PerformanceMonitor(enable_gpu=False)
    
    def test_collect_metrics(self, monitor):
        """Testa coleta de métricas"""
        metrics = monitor.collect_system_metrics()
        
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_used_mb > 0
    
    def test_profile_operation(self, monitor):
        """Testa profiling de operação"""
        with monitor.profile("test_op"):
            time.sleep(0.01)
        
        stats = monitor.get_operation_stats("test_op")
        
        assert stats['count'] == 1
        assert stats['success_rate'] == 100
    
    def test_profile_error(self, monitor):
        """Testa profiling com erro"""
        try:
            with monitor.profile("error_op"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        stats = monitor.get_operation_stats("error_op")
        
        assert stats['count'] == 1
        assert stats['success_rate'] == 0
    
    def test_thresholds(self, monitor):
        """Testa definição de thresholds"""
        monitor.set_threshold('cpu_percent', 80)
        
        assert monitor._thresholds['cpu_percent'] == 80
    
    def test_alert_callback(self, monitor):
        """Testa callback de alerta"""
        alerts_received = []
        
        def on_alert(alert_type, data):
            alerts_received.append(alert_type)
        
        monitor.add_alert_callback(on_alert)
        
        # Verificar que callback foi adicionado
        assert len(monitor._alert_callbacks) == 1
        
        # Testar que alertas são enviados corretamente
        # Simular uma métrica que excede threshold
        monitor.set_threshold('memory_percent', 0)  # Threshold impossível
        monitor.collect_system_metrics()
        
        # Deve ter recebido alerta de memória (sempre > 0%)
        assert 'high_memory' in alerts_received or len(alerts_received) > 0
    
    def test_summary(self, monitor):
        """Testa resumo"""
        # Coletar algumas métricas
        for _ in range(3):
            monitor.collect_system_metrics()
        
        with monitor.profile("test"):
            pass
        
        summary = monitor.get_summary()
        
        assert 'system' in summary
        assert 'operations' in summary
    
    def test_reset(self, monitor):
        """Testa reset"""
        monitor.collect_system_metrics()
        with monitor.profile("test"):
            pass
        
        monitor.reset()
        
        assert len(monitor._operations) == 0
        assert len(monitor._system_metrics) == 0
