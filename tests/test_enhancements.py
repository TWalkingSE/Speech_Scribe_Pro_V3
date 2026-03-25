#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes das Melhorias - Speech Scribe Pro V3
Testes para: Histórico, Presets, Busca
"""

import pytest
from pathlib import Path


class TestTranscriptionHistory:
    """Testes para histórico de transcrições"""
    
    @pytest.fixture
    def history(self, tmp_path):
        """Fixture de histórico"""
        from speech_scribe.core.history import TranscriptionHistory
        return TranscriptionHistory(db_path=tmp_path / "test_history.db")
    
    def test_add_transcription(self, history):
        """Testa adicionar transcrição"""
        record_id = history.add(
            file_path="/test/audio.mp3",
            text="Texto de teste para transcrição",
            language="pt",
            model="small"
        )
        
        assert record_id > 0
    
    def test_get_transcription(self, history):
        """Testa obter transcrição"""
        record_id = history.add(
            file_path="/test/audio.mp3",
            text="Texto de teste",
            language="pt"
        )
        
        record = history.get(record_id)
        
        assert record is not None
        assert record.text == "Texto de teste"
        assert record.file_name == "audio.mp3"
    
    def test_get_recent(self, history):
        """Testa obter transcrições recentes"""
        for i in range(5):
            history.add(f"/test/audio{i}.mp3", f"Texto {i}")
        
        recent = history.get_recent(3)
        
        assert len(recent) == 3
    
    def test_search(self, history):
        """Testa busca no histórico"""
        history.add("/test/reuniao.mp3", "Reunião de planejamento estratégico")
        history.add("/test/podcast.mp3", "Entrevista sobre tecnologia")
        
        results = history.search("reunião")
        
        assert len(results) == 1
        assert "Reunião" in results[0].text
    
    def test_delete(self, history):
        """Testa exclusão"""
        record_id = history.add("/test/audio.mp3", "Texto para deletar")
        
        result = history.delete(record_id)
        
        assert result is True
        assert history.get(record_id) is None
    
    def test_stats(self, history):
        """Testa estatísticas"""
        history.add("/test/a.mp3", "Um dois três")
        history.add("/test/b.mp3", "Quatro cinco seis sete")
        
        stats = history.get_stats()
        
        assert stats['total_transcriptions'] == 2
        assert stats['total_words'] == 7
    
    def test_word_count(self, history):
        """Testa contagem de palavras"""
        record_id = history.add("/test/audio.mp3", "Uma duas três quatro cinco")
        record = history.get(record_id)
        
        assert record.word_count == 5


class TestQualityPresets:
    """Testes para presets de qualidade"""
    
    @pytest.fixture
    def manager(self):
        """Fixture do manager"""
        from speech_scribe.core.presets import PresetManager
        return PresetManager()
    
    def test_get_preset(self, manager):
        """Testa obter preset"""
        from speech_scribe.core.presets import PresetType
        
        preset = manager.get_preset(PresetType.RAPIDO)
        
        assert preset.name == "⚡ Rápido"
        assert preset.model == "tiny"
    
    def test_list_presets(self, manager):
        """Testa listar presets"""
        presets = manager.list_presets()
        
        assert len(presets) >= 5
    
    def test_get_by_name(self, manager):
        """Testa obter por nome"""
        preset = manager.get_by_name("⚡ Rápido")
        
        assert preset is not None
        assert preset.model == "tiny"
    
    def test_preset_configs(self, manager):
        """Testa configurações dos presets"""
        from speech_scribe.core.presets import PresetType
        
        rapido = manager.get_preset(PresetType.RAPIDO)
        maxima = manager.get_preset(PresetType.MAXIMA_QUALIDADE)
        
        # Rápido deve ter beam_size menor
        assert rapido.beam_size < maxima.beam_size
        # Máxima qualidade deve usar model maior
        assert maxima.model == "large-v3"
    
    def test_set_current(self, manager):
        """Testa definir preset atual"""
        from speech_scribe.core.presets import PresetType
        
        manager.set_current(PresetType.PODCAST)
        current = manager.get_current()
        
        assert current.preset_type == PresetType.PODCAST
    
    def test_preset_names(self, manager):
        """Testa nomes para UI"""
        names = manager.get_preset_names()
        
        assert "⚡ Rápido" in names
        assert "⚖️ Balanceado" in names
        assert len(names) >= 5


class TestTranscriptionRecord:
    """Testes para TranscriptionRecord"""
    
    def test_to_dict(self):
        """Testa serialização"""
        from speech_scribe.core.history import TranscriptionRecord
        
        record = TranscriptionRecord(
            id=1,
            file_path="/test/audio.mp3",
            file_name="audio.mp3",
            text="Texto teste",
            language="pt"
        )
        
        d = record.to_dict()
        
        assert d['id'] == 1
        assert d['file_name'] == "audio.mp3"
    
    def test_from_dict(self):
        """Testa desserialização"""
        from speech_scribe.core.history import TranscriptionRecord
        
        data = {
            'id': 1,
            'file_path': '/test/audio.mp3',
            'file_name': 'audio.mp3',
            'text': 'Texto',
            'language': 'pt',
            'model': 'small',
            'duration_seconds': 60.0,
            'processing_time': 5.0,
            'word_count': 10,
            'created_at': '2024-01-01'
        }
        
        record = TranscriptionRecord.from_dict(data)
        
        assert record.id == 1
        assert record.file_name == 'audio.mp3'
