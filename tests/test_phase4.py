#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes da Fase 4 - Speech Scribe Pro V3
Testes para: Plugins, Exporters
"""

import pytest
from pathlib import Path


class TestPluginBase:
    """Testes para classes base de plugins"""
    
    def test_plugin_info(self):
        """Testa criação de PluginInfo"""
        from speech_scribe.plugins.base import PluginInfo, PluginType
        
        info = PluginInfo(
            name="Test Plugin",
            version="1.0.0",
            description="Plugin de teste",
            author="Tester",
            plugin_type=PluginType.ANALYSIS
        )
        
        assert info.name == "Test Plugin"
        assert info.version == "1.0.0"
        assert info.plugin_type == PluginType.ANALYSIS
    
    def test_plugin_info_to_dict(self):
        """Testa serialização de PluginInfo"""
        from speech_scribe.plugins.base import PluginInfo, PluginType
        
        info = PluginInfo(
            name="Test",
            version="1.0",
            description="Desc",
            author="Author",
            plugin_type=PluginType.EXPORT
        )
        
        d = info.to_dict()
        
        assert d['name'] == "Test"
        assert d['type'] == "EXPORT"
    
    def test_plugin_types(self):
        """Testa todos os tipos de plugin"""
        from speech_scribe.plugins.base import PluginType
        
        assert PluginType.TRANSCRIPTION
        assert PluginType.ANALYSIS
        assert PluginType.EXPORT
        assert PluginType.PRE_PROCESSOR
        assert PluginType.POST_PROCESSOR


class TestPluginManager:
    """Testes para PluginManager"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Fixture de manager"""
        from speech_scribe.plugins.manager import PluginManager
        return PluginManager(plugins_dir=tmp_path)
    
    def test_init(self, manager):
        """Testa inicialização"""
        assert manager.plugins_dir.exists()
    
    def test_available_hooks(self, manager):
        """Testa hooks disponíveis"""
        assert 'pre_transcription' in manager.AVAILABLE_HOOKS
        assert 'post_transcription' in manager.AVAILABLE_HOOKS
        assert 'on_error' in manager.AVAILABLE_HOOKS
    
    def test_execute_hook_empty(self, manager):
        """Testa execução de hook vazio"""
        results = manager.execute_hook('post_transcription', {})
        
        assert results == []
    
    def test_get_plugins_info_empty(self, manager):
        """Testa listagem de plugins vazia"""
        info = manager.get_plugins_info()
        
        assert info == []


class TestWordCounterPlugin:
    """Testes para plugin de exemplo"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture do plugin"""
        from speech_scribe.plugins.examples.word_counter import WordCounterPlugin
        return WordCounterPlugin()
    
    def test_get_info(self, plugin):
        """Testa informações do plugin"""
        info = plugin.get_info()
        
        assert info.name == "Word Counter"
        assert "1.0.0" in info.version
    
    def test_analyze(self, plugin):
        """Testa análise de texto"""
        text = "Esta é uma frase de teste. Esta é outra frase."
        result = plugin.analyze(text)
        
        assert result['total_words'] > 0
        assert result['total_sentences'] == 2
        assert 'top_words' in result


class TestExporters:
    """Testes para exportadores"""
    
    @pytest.fixture
    def sample_data(self):
        """Dados de exemplo"""
        return {
            'text': 'Esta é uma transcrição de teste.',
            'language': 'pt',
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'Esta é uma'},
                {'start': 2.0, 'end': 4.0, 'text': 'transcrição de teste.'}
            ],
            'processing_time': 1.5,
            'model_used': 'small'
        }
    
    def test_txt_exporter(self, sample_data, tmp_path):
        """Testa exportador TXT"""
        from speech_scribe.core.exporters import TXTExporter
        
        exporter = TXTExporter()
        output = tmp_path / "output.txt"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        assert output.exists()
        content = output.read_text(encoding='utf-8')
        assert 'teste' in content.lower()
    
    def test_json_exporter(self, sample_data, tmp_path):
        """Testa exportador JSON"""
        from speech_scribe.core.exporters import JSONExporter
        import json
        
        exporter = JSONExporter()
        output = tmp_path / "output.json"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        data = json.loads(output.read_text())
        assert 'metadata' in data
        assert 'transcription' in data
    
    def test_srt_exporter(self, sample_data, tmp_path):
        """Testa exportador SRT"""
        from speech_scribe.core.exporters import SRTExporter
        
        exporter = SRTExporter()
        output = tmp_path / "output.srt"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        content = output.read_text()
        assert '1\n' in content
        assert '-->' in content
    
    def test_vtt_exporter(self, sample_data, tmp_path):
        """Testa exportador VTT"""
        from speech_scribe.core.exporters import VTTExporter
        
        exporter = VTTExporter()
        output = tmp_path / "output.vtt"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        content = output.read_text()
        assert 'WEBVTT' in content
    
    def test_html_exporter(self, sample_data, tmp_path):
        """Testa exportador HTML"""
        from speech_scribe.core.exporters import HTMLExporter
        
        exporter = HTMLExporter()
        output = tmp_path / "output.html"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        content = output.read_text(encoding='utf-8')
        assert '<html' in content
        assert 'Speech Scribe' in content
    
    def test_csv_exporter(self, sample_data, tmp_path):
        """Testa exportador CSV"""
        from speech_scribe.core.exporters import CSVExporter
        
        exporter = CSVExporter()
        output = tmp_path / "output.csv"
        
        result = exporter.export(sample_data, output)
        
        assert result.success
        content = output.read_text()
        assert 'start' in content
        assert 'text' in content


class TestExportManager:
    """Testes para ExportManager"""
    
    @pytest.fixture
    def manager(self):
        """Fixture de manager"""
        from speech_scribe.core.exporters import ExportManager
        return ExportManager()
    
    def test_available_formats(self, manager):
        """Testa formatos disponíveis"""
        formats = manager.get_available_formats()
        
        assert len(formats) >= 6
        format_keys = [f['key'] for f in formats]
        assert 'txt' in format_keys
        assert 'json' in format_keys
        assert 'srt' in format_keys
    
    def test_get_exporter(self, manager):
        """Testa obter exportador"""
        exporter = manager.get_exporter('txt')
        
        assert exporter is not None
        assert exporter.format_name == "Plain Text"
    
    def test_get_invalid_exporter(self, manager):
        """Testa exportador inválido"""
        exporter = manager.get_exporter('invalid')
        
        assert exporter is None
    
    def test_export(self, manager, tmp_path):
        """Testa exportação via manager"""
        data = {'text': 'Test', 'segments': []}
        output = tmp_path / "test.txt"
        
        result = manager.export(data, output, 'txt')
        
        assert result.success
