#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes do Sistema de Cache - Speech Scribe Pro V3
"""

import pytest
import time
from speech_scribe.core.cache import (
    ImprovedModelCache, 
    WhisperModelCache, 
    CacheEntry,
    get_model_cache
)


class TestCacheEntry:
    """Testes para CacheEntry"""
    
    def test_create_entry(self):
        """Testa criação de entrada"""
        entry = CacheEntry(value="test", size_bytes=100)
        
        assert entry.value == "test"
        assert entry.size_bytes == 100
        assert entry.access_count == 0
    
    def test_touch_updates_access(self):
        """Testa atualização de acesso"""
        entry = CacheEntry(value="test", size_bytes=100)
        initial_time = entry.last_accessed
        
        time.sleep(0.01)
        entry.touch()
        
        assert entry.last_accessed > initial_time
        assert entry.access_count == 1


class TestImprovedModelCache:
    """Testes para ImprovedModelCache"""
    
    @pytest.fixture
    def cache(self):
        """Fixture de cache para testes"""
        return ImprovedModelCache(max_size_gb=0.001, max_entries=5)  # 1MB, 5 entries
    
    def test_set_and_get(self, cache):
        """Testa set e get básicos"""
        cache.set("key1", "value1", 100)
        
        result = cache.get("key1")
        
        assert result == "value1"
    
    def test_get_nonexistent(self, cache):
        """Testa get de chave inexistente"""
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_cache_hit_rate(self, cache):
        """Testa cálculo de hit rate"""
        cache.set("key1", "value1", 100)
        
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        assert cache.hit_rate == pytest.approx(2/3, 0.01)
    
    def test_lru_eviction(self, cache):
        """Testa eviction LRU"""
        # Preencher cache
        for i in range(5):
            cache.set(f"key{i}", f"value{i}", 100)
        
        # Acessar key0 para torná-la recente
        cache.get("key0")
        
        # Adicionar nova entrada (deve evictar key1, não key0)
        cache.set("key5", "value5", 100)
        
        assert cache.contains("key0")  # key0 deve permanecer
        assert not cache.contains("key1")  # key1 deve ser evictada
    
    def test_size_limit(self, cache):
        """Testa limite de tamanho"""
        # Tentar adicionar item muito grande
        result = cache.set("big", "value", 10 * 1024 * 1024)  # 10MB
        
        assert result is False
    
    def test_remove(self, cache):
        """Testa remoção"""
        cache.set("key1", "value1", 100)
        cache.remove("key1")
        
        assert cache.get("key1") is None
    
    def test_clear(self, cache):
        """Testa limpeza"""
        cache.set("key1", "value1", 100)
        cache.set("key2", "value2", 100)
        cache.clear()
        
        assert cache.size == 0
        assert cache.size_bytes == 0
    
    def test_stats(self, cache):
        """Testa estatísticas"""
        cache.set("key1", "value1", 100)
        cache.get("key1")
        cache.get("key2")
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['entries'] == 1
    
    def test_cleanup_old_entries(self, cache):
        """Testa limpeza de entradas antigas"""
        cache.set("key1", "value1", 100)
        
        # Simular entrada antiga
        cache._cache["key1"].last_accessed = time.time() - 3700
        
        cache.cleanup_old_entries(max_age_seconds=3600)
        
        assert not cache.contains("key1")


class TestWhisperModelCache:
    """Testes para WhisperModelCache"""
    
    @pytest.fixture
    def whisper_cache(self):
        """Fixture de cache Whisper"""
        return WhisperModelCache(max_size_gb=5.0)
    
    def test_model_size_estimation(self, whisper_cache):
        """Testa estimativa de tamanho de modelo"""
        small_size = whisper_cache.get_model_size("small")
        large_size = whisper_cache.get_model_size("large-v3")
        
        assert small_size < large_size
        assert small_size > 0
    
    def test_cache_model(self, whisper_cache):
        """Testa armazenamento de modelo"""
        mock_model = {"type": "mock_model"}
        
        result = whisper_cache.cache_model("small", "cpu", mock_model)
        
        assert result is True
        assert whisper_cache.has_model("small", "cpu")
    
    def test_get_model(self, whisper_cache):
        """Testa recuperação de modelo"""
        mock_model = {"type": "mock_model"}
        whisper_cache.cache_model("small", "cpu", mock_model)
        
        result = whisper_cache.get_model("small", "cpu")
        
        assert result == mock_model
    
    def test_has_model(self, whisper_cache):
        """Testa verificação de existência"""
        assert not whisper_cache.has_model("small", "cpu")
        
        whisper_cache.cache_model("small", "cpu", {})
        
        assert whisper_cache.has_model("small", "cpu")


class TestGetModelCache:
    """Testes para função singleton"""
    
    def test_singleton(self):
        """Testa que retorna mesma instância"""
        cache1 = get_model_cache()
        cache2 = get_model_cache()
        
        assert cache1 is cache2
