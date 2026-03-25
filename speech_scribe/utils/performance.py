#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📈 Monitoramento de Performance - Speech Scribe Pro V3
Métricas, profiling e monitoramento de recursos em tempo real
"""

import time
import threading
import psutil
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from contextlib import contextmanager
import statistics

from speech_scribe.utils.logger import logger


@dataclass
class OperationMetric:
    """Métrica de uma operação"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_start_mb: float = 0
    memory_end_mb: float = 0
    memory_delta_mb: float = 0
    gpu_memory_start_mb: float = 0
    gpu_memory_end_mb: float = 0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """Marca operação como completa"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error
        
        # Memória atual
        process = psutil.Process()
        self.memory_end_mb = process.memory_info().rss / (1024 ** 2)
        self.memory_delta_mb = self.memory_end_mb - self.memory_start_mb
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'duration_ms': self.duration_ms,
            'memory_delta_mb': self.memory_delta_mb,
            'success': self.success,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    gpu_utilization: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'gpu_memory_used_mb': self.gpu_memory_used_mb,
            'gpu_memory_total_mb': self.gpu_memory_total_mb,
            'gpu_utilization': self.gpu_utilization
        }


class PerformanceMonitor:
    """
    Monitor de performance com coleta de métricas.
    
    Features:
    - Métricas de CPU, memória e GPU
    - Profiling de operações
    - Histórico de métricas
    - Alertas de recursos
    """
    
    def __init__(self, 
                 history_size: int = 1000,
                 sample_interval: float = 1.0,
                 enable_gpu: bool = True):
        """
        Inicializa o monitor.
        
        Args:
            history_size: Tamanho máximo do histórico
            sample_interval: Intervalo de coleta em segundos
            enable_gpu: Habilitar monitoramento de GPU
        """
        self.history_size = history_size
        self.sample_interval = sample_interval
        self.enable_gpu = enable_gpu
        
        # Históricos
        self._operations: deque = deque(maxlen=history_size)
        self._system_metrics: deque = deque(maxlen=history_size)
        
        # Estatísticas por operação
        self._operation_stats: Dict[str, Dict[str, List[float]]] = {}
        
        # Monitoramento em background
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Alertas
        self._alert_callbacks: List[Callable[[str, Dict], None]] = []
        self._thresholds = {
            'cpu_percent': 90,
            'memory_percent': 85,
            'gpu_memory_percent': 90
        }
        
        # Verificar GPU
        self._gpu_available = False
        if enable_gpu:
            try:
                import torch
                self._gpu_available = torch.cuda.is_available()
            except Exception:
                pass
        
        logger.info(f"PerformanceMonitor inicializado (GPU: {self._gpu_available})")
    
    def _get_gpu_metrics(self) -> Dict[str, Optional[float]]:
        """Obtém métricas de GPU"""
        if not self._gpu_available:
            return {'memory_used_mb': None, 'memory_total_mb': None, 'utilization': None}
        
        try:
            import torch
            memory_used = torch.cuda.memory_allocated() / (1024 ** 2)
            memory_total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
            
            # Utilização via nvidia-smi se disponível
            utilization = None
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=1
                )
                if result.returncode == 0:
                    utilization = float(result.stdout.strip())
            except Exception:
                pass
            
            return {
                'memory_used_mb': memory_used,
                'memory_total_mb': memory_total,
                'utilization': utilization
            }
        except Exception:
            return {'memory_used_mb': None, 'memory_total_mb': None, 'utilization': None}
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Coleta métricas atuais do sistema"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        gpu = self._get_gpu_metrics()
        
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 ** 2),
            memory_available_mb=memory.available / (1024 ** 2),
            disk_usage_percent=disk.percent,
            gpu_memory_used_mb=gpu['memory_used_mb'],
            gpu_memory_total_mb=gpu['memory_total_mb'],
            gpu_utilization=gpu['utilization']
        )
        
        with self._lock:
            self._system_metrics.append(metrics)
        
        # Verificar alertas
        self._check_alerts(metrics)
        
        return metrics
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Verifica se métricas excedem thresholds"""
        alerts = []
        
        if metrics.cpu_percent > self._thresholds['cpu_percent']:
            alerts.append(('high_cpu', {'value': metrics.cpu_percent, 'threshold': self._thresholds['cpu_percent']}))
        
        if metrics.memory_percent > self._thresholds['memory_percent']:
            alerts.append(('high_memory', {'value': metrics.memory_percent, 'threshold': self._thresholds['memory_percent']}))
        
        if metrics.gpu_memory_used_mb and metrics.gpu_memory_total_mb:
            gpu_percent = (metrics.gpu_memory_used_mb / metrics.gpu_memory_total_mb) * 100
            if gpu_percent > self._thresholds['gpu_memory_percent']:
                alerts.append(('high_gpu_memory', {'value': gpu_percent, 'threshold': self._thresholds['gpu_memory_percent']}))
        
        # Notificar callbacks
        for alert_type, data in alerts:
            for callback in self._alert_callbacks:
                try:
                    callback(alert_type, data)
                except Exception as e:
                    logger.error(f"Erro em callback de alerta: {e}")
    
    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """Adiciona callback para alertas"""
        self._alert_callbacks.append(callback)
    
    def set_threshold(self, metric: str, value: float):
        """Define threshold para alerta"""
        self._thresholds[metric] = value
    
    @contextmanager
    def profile(self, operation_name: str, **metadata):
        """
        Context manager para profiling de operação.
        
        Usage:
            with monitor.profile("transcription", file="audio.mp3"):
                result = transcribe(file)
        """
        process = psutil.Process()
        
        metric = OperationMetric(
            name=operation_name,
            start_time=time.time(),
            memory_start_mb=process.memory_info().rss / (1024 ** 2),
            metadata=metadata
        )
        
        if self._gpu_available:
            try:
                import torch
                metric.gpu_memory_start_mb = torch.cuda.memory_allocated() / (1024 ** 2)
            except Exception:
                pass
        
        try:
            yield metric
            metric.complete(success=True)
        except Exception as e:
            metric.complete(success=False, error=str(e))
            raise
        finally:
            if self._gpu_available:
                try:
                    import torch
                    metric.gpu_memory_end_mb = torch.cuda.memory_allocated() / (1024 ** 2)
                except Exception:
                    pass
            
            self._record_operation(metric)
    
    def _record_operation(self, metric: OperationMetric):
        """Registra métrica de operação"""
        with self._lock:
            self._operations.append(metric)
            
            # Atualizar estatísticas
            if metric.name not in self._operation_stats:
                self._operation_stats[metric.name] = {
                    'durations': [],
                    'memory_deltas': [],
                    'success_count': 0,
                    'error_count': 0
                }
            
            stats = self._operation_stats[metric.name]
            if metric.duration_ms:
                stats['durations'].append(metric.duration_ms)
            stats['memory_deltas'].append(metric.memory_delta_mb)
            
            if metric.success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            # Limitar tamanho das listas
            for key in ['durations', 'memory_deltas']:
                if len(stats[key]) > self.history_size:
                    stats[key] = stats[key][-self.history_size:]
    
    def start_monitoring(self):
        """Inicia monitoramento em background"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Monitoramento de performance iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento em background"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("Monitoramento de performance parado")
    
    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self._monitoring:
            try:
                self.collect_system_metrics()
            except Exception as e:
                logger.error(f"Erro na coleta de métricas: {e}")
            
            time.sleep(self.sample_interval)
    
    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém estatísticas de operações.
        
        Args:
            operation_name: Nome da operação (ou None para todas)
        """
        with self._lock:
            if operation_name:
                stats = self._operation_stats.get(operation_name, {})
                return self._calculate_stats(operation_name, stats)
            
            return {
                name: self._calculate_stats(name, stats)
                for name, stats in self._operation_stats.items()
            }
    
    def _calculate_stats(self, name: str, stats: Dict) -> Dict[str, Any]:
        """Calcula estatísticas de uma operação"""
        durations = stats.get('durations', [])
        memory_deltas = stats.get('memory_deltas', [])
        total = stats.get('success_count', 0) + stats.get('error_count', 0)
        
        result = {
            'name': name,
            'count': total,
            'success_rate': (stats.get('success_count', 0) / total * 100) if total > 0 else 0
        }
        
        if durations:
            result['duration_ms'] = {
                'min': min(durations),
                'max': max(durations),
                'mean': statistics.mean(durations),
                'median': statistics.median(durations),
                'stdev': statistics.stdev(durations) if len(durations) > 1 else 0
            }
        
        if memory_deltas:
            result['memory_delta_mb'] = {
                'min': min(memory_deltas),
                'max': max(memory_deltas),
                'mean': statistics.mean(memory_deltas)
            }
        
        return result
    
    def get_system_metrics_history(self, last_n: Optional[int] = None) -> List[Dict]:
        """Obtém histórico de métricas do sistema"""
        with self._lock:
            metrics = list(self._system_metrics)
            if last_n:
                metrics = metrics[-last_n:]
            return [m.to_dict() for m in metrics]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Obtém métricas atuais formatadas"""
        metrics = self.collect_system_metrics()
        
        return {
            'system': metrics.to_dict(),
            'operations': self.get_operation_stats(),
            'alerts': {
                'thresholds': self._thresholds,
                'current_status': {
                    'cpu_ok': metrics.cpu_percent <= self._thresholds['cpu_percent'],
                    'memory_ok': metrics.memory_percent <= self._thresholds['memory_percent']
                }
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtém resumo de performance"""
        metrics = self.get_system_metrics_history()
        
        summary = {
            'system': {
                'samples': len(metrics)
            },
            'operations': self.get_operation_stats()
        }
        
        if metrics:
            cpu_values = [m['cpu_percent'] for m in metrics]
            mem_values = [m['memory_percent'] for m in metrics]
            
            summary['system']['cpu_percent'] = {
                'min': min(cpu_values),
                'max': max(cpu_values),
                'mean': statistics.mean(cpu_values)
            }
            summary['system']['memory_percent'] = {
                'min': min(mem_values),
                'max': max(mem_values),
                'mean': statistics.mean(mem_values)
            }
        
        return summary
    
    def reset(self):
        """Reseta todas as métricas"""
        with self._lock:
            self._operations.clear()
            self._system_metrics.clear()
            self._operation_stats.clear()
        logger.info("Métricas resetadas")


# Instância global
_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Obtém monitor global"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


__all__ = [
    'OperationMetric',
    'SystemMetrics',
    'PerformanceMonitor',
    'get_performance_monitor',
]
