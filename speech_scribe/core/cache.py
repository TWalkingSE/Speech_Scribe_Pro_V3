#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🗄️ Sistema de Cache Melhorado - Speech Scribe Pro V3
Cache inteligente com gerenciamento de memória e LRU
"""

import time
import threading
from typing import Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from speech_scribe.utils.logger import logger

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Entrada individual do cache"""
    value: T
    size_bytes: int
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    
    def touch(self):
        """Atualiza tempo de acesso"""
        self.last_accessed = time.time()
        self.access_count += 1


class ImprovedModelCache:
    """
    Cache com gerenciamento inteligente de memória para modelos Whisper.
    
    Features:
    - Limite de tamanho em GB
    - LRU (Least Recently Used) eviction
    - Thread-safe
    - Estatísticas de uso
    - Limpeza automática
    """
    
    def __init__(self, max_size_gb: float = 10.0, max_entries: int = 10):
        """
        Inicializa o cache.
        
        Args:
            max_size_gb: Tamanho máximo em GB
            max_entries: Número máximo de entradas
        """
        self.max_size_bytes = int(max_size_gb * 1024 ** 3)
        self.max_entries = max_entries
        self.current_size_bytes = 0
        
        # OrderedDict para manter ordem de inserção (LRU)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Estatísticas
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_gets': 0,
            'total_sets': 0
        }
        
        logger.info(f"Cache inicializado: max_size={max_size_gb}GB, max_entries={max_entries}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém item do cache.
        
        Args:
            key: Chave do item
            
        Returns:
            Valor ou None se não encontrado
        """
        with self._lock:
            self._stats['total_gets'] += 1
            
            if key in self._cache:
                entry = self._cache[key]
                entry.touch()
                
                # Mover para o final (mais recente)
                self._cache.move_to_end(key)
                
                self._stats['hits'] += 1
                logger.debug(f"Cache HIT: {key}")
                return entry.value
            
            self._stats['misses'] += 1
            logger.debug(f"Cache MISS: {key}")
            return None
    
    def set(self, key: str, value: Any, size_bytes: int = 0) -> bool:
        """
        Adiciona item ao cache.
        
        Args:
            key: Chave do item
            value: Valor a armazenar
            size_bytes: Tamanho estimado em bytes
            
        Returns:
            True se adicionado com sucesso
        """
        with self._lock:
            self._stats['total_sets'] += 1
            
            # Se já existe, remover primeiro
            if key in self._cache:
                self._remove_entry(key)
            
            # Verificar se cabe no cache
            if size_bytes > self.max_size_bytes:
                logger.warning(f"Item muito grande para cache: {size_bytes} bytes > {self.max_size_bytes} bytes")
                return False
            
            # Evictar itens até ter espaço suficiente
            while (self.current_size_bytes + size_bytes > self.max_size_bytes or 
                   len(self._cache) >= self.max_entries):
                if not self._evict_oldest():
                    logger.warning("Não foi possível liberar espaço no cache")
                    return False
            
            # Adicionar nova entrada
            entry = CacheEntry(value=value, size_bytes=size_bytes)
            self._cache[key] = entry
            self.current_size_bytes += size_bytes
            
            logger.debug(f"Cache SET: {key} ({size_bytes} bytes)")
            return True
    
    def remove(self, key: str) -> bool:
        """
        Remove item do cache.
        
        Args:
            key: Chave do item
            
        Returns:
            True se removido
        """
        with self._lock:
            return self._remove_entry(key)
    
    def _remove_entry(self, key: str) -> bool:
        """Remove entrada (interno, sem lock)"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self.current_size_bytes -= entry.size_bytes
            logger.debug(f"Cache REMOVE: {key}")
            return True
        return False
    
    def _evict_oldest(self) -> bool:
        """Remove o item menos recentemente usado"""
        if not self._cache:
            return False
        
        # Primeiro item é o mais antigo (LRU)
        oldest_key = next(iter(self._cache))
        self._remove_entry(oldest_key)
        self._stats['evictions'] += 1
        logger.debug(f"Cache EVICT: {oldest_key}")
        return True
    
    def clear(self):
        """Limpa todo o cache"""
        with self._lock:
            self._cache.clear()
            self.current_size_bytes = 0
            logger.info("Cache limpo")
    
    def contains(self, key: str) -> bool:
        """Verifica se chave existe no cache"""
        with self._lock:
            return key in self._cache
    
    @property
    def size(self) -> int:
        """Número de itens no cache"""
        return len(self._cache)
    
    @property
    def size_bytes(self) -> int:
        """Tamanho atual em bytes"""
        return self.current_size_bytes
    
    @property
    def size_gb(self) -> float:
        """Tamanho atual em GB"""
        return self.current_size_bytes / (1024 ** 3)
    
    @property
    def hit_rate(self) -> float:
        """Taxa de acerto do cache"""
        total = self._stats['total_gets']
        if total == 0:
            return 0.0
        return self._stats['hits'] / total
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            return {
                **self._stats,
                'entries': len(self._cache),
                'size_bytes': self.current_size_bytes,
                'size_gb': self.size_gb,
                'max_size_gb': self.max_size_bytes / (1024 ** 3),
                'hit_rate': self.hit_rate,
                'usage_percent': (self.current_size_bytes / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0
            }
    
    def get_entries_info(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre todas as entradas"""
        with self._lock:
            return {
                key: {
                    'size_bytes': entry.size_bytes,
                    'created_at': entry.created_at,
                    'last_accessed': entry.last_accessed,
                    'access_count': entry.access_count,
                    'age_seconds': time.time() - entry.created_at
                }
                for key, entry in self._cache.items()
            }
    
    def cleanup_old_entries(self, max_age_seconds: float = 3600):
        """
        Remove entradas mais antigas que max_age_seconds.
        
        Args:
            max_age_seconds: Idade máxima em segundos (padrão: 1 hora)
        """
        with self._lock:
            current_time = time.time()
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if current_time - entry.last_accessed > max_age_seconds
            ]
            
            for key in keys_to_remove:
                self._remove_entry(key)
            
            if keys_to_remove:
                logger.info(f"Cleanup: {len(keys_to_remove)} entradas antigas removidas")


class WhisperModelCache(ImprovedModelCache):
    """
    Cache especializado para modelos Whisper.
    Estima automaticamente o tamanho dos modelos.
    """
    
    # Tamanhos estimados dos modelos Whisper em bytes
    MODEL_SIZES = {
        'tiny': 75 * 1024 ** 2,      # ~75 MB
        'tiny.en': 75 * 1024 ** 2,
        'base': 142 * 1024 ** 2,     # ~142 MB
        'base.en': 142 * 1024 ** 2,
        'small': 466 * 1024 ** 2,    # ~466 MB
        'small.en': 466 * 1024 ** 2,
        'medium': 1.5 * 1024 ** 3,   # ~1.5 GB
        'medium.en': 1.5 * 1024 ** 3,
        'large': 2.9 * 1024 ** 3,    # ~2.9 GB
        'large-v1': 2.9 * 1024 ** 3,
        'large-v2': 2.9 * 1024 ** 3,
        'large-v3': 2.9 * 1024 ** 3,
    }
    
    def __init__(self, max_size_gb: float = 10.0):
        """
        Inicializa cache de modelos Whisper.
        
        Args:
            max_size_gb: Tamanho máximo em GB (padrão: 10GB)
        """
        # Whisper geralmente tem poucos modelos carregados
        super().__init__(max_size_gb=max_size_gb, max_entries=5)
    
    def get_model_size(self, model_name: str) -> int:
        """Estima tamanho do modelo em bytes"""
        # Extrair nome base do modelo
        base_name = model_name.split('/')[-1].lower()
        
        # Procurar tamanho conhecido
        for name, size in self.MODEL_SIZES.items():
            if name in base_name:
                return int(size)
        
        # Padrão: assumir modelo médio
        return int(1.5 * 1024 ** 3)
    
    def cache_model(self, model_name: str, device: str, model: Any) -> bool:
        """
        Armazena modelo no cache.
        
        Args:
            model_name: Nome do modelo (ex: 'small', 'large-v3')
            device: Dispositivo (ex: 'cpu', 'cuda')
            model: Instância do modelo
            
        Returns:
            True se armazenado com sucesso
        """
        cache_key = f"{model_name}_{device}"
        size = self.get_model_size(model_name)
        
        success = self.set(cache_key, model, size)
        if success:
            logger.info(f"Modelo {model_name} ({device}) armazenado no cache ({size / 1024**2:.0f} MB)")
        
        return success
    
    def get_model(self, model_name: str, device: str) -> Optional[Any]:
        """
        Obtém modelo do cache.
        
        Args:
            model_name: Nome do modelo
            device: Dispositivo
            
        Returns:
            Modelo ou None
        """
        cache_key = f"{model_name}_{device}"
        model = self.get(cache_key)
        
        if model:
            logger.info(f"Modelo {model_name} ({device}) obtido do cache")
        
        return model
    
    def has_model(self, model_name: str, device: str) -> bool:
        """Verifica se modelo está no cache"""
        cache_key = f"{model_name}_{device}"
        return self.contains(cache_key)


# Instância global do cache de modelos
_model_cache: Optional[WhisperModelCache] = None


def get_model_cache(max_size_gb: float = 10.0) -> WhisperModelCache:
    """
    Obtém instância singleton do cache de modelos.
    
    Args:
        max_size_gb: Tamanho máximo (usado apenas na primeira chamada)
        
    Returns:
        Instância do cache
    """
    global _model_cache
    if _model_cache is None:
        _model_cache = WhisperModelCache(max_size_gb=max_size_gb)
    return _model_cache


__all__ = [
    'CacheEntry',
    'ImprovedModelCache', 
    'WhisperModelCache',
    'get_model_cache'
]
