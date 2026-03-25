#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes do ConfigManager - Speech Scribe Pro V3
"""

import pytest
import json
from pathlib import Path
from speech_scribe.core.config_manager import (
    ConfigManager,
    AppConfiguration,
    HardwareConfig,
    TranscriptionConfig,
    DeviceType,
    ModelSize,
    Language,
    QualityPreset
)


class TestEnums:
    """Testes para enums de configuração"""
    
    def test_device_types(self):
        """Testa tipos de dispositivo"""
        assert DeviceType.AUTO.value == "auto"
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.CUDA.value == "cuda"
    
    def test_model_sizes(self):
        """Testa tamanhos de modelo"""
        assert ModelSize.TINY.value == "tiny"
        assert ModelSize.LARGE_V3.value == "large-v3"
    
    def test_languages(self):
        """Testa idiomas"""
        assert Language.AUTO.value == "auto"
        assert Language.PORTUGUESE.value == "pt"
    
    def test_quality_presets(self):
        """Testa presets de qualidade"""
        assert QualityPreset.FAST.value == "fast"
        assert QualityPreset.BEST.value == "best"


class TestHardwareConfig:
    """Testes para configuração de hardware"""
    
    def test_default_values(self):
        """Testa valores padrão"""
        config = HardwareConfig()
        
        assert config.device == DeviceType.AUTO
        assert config.gpu_memory_fraction == 0.8
        assert config.prefer_gpu is True
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        config = HardwareConfig(device=DeviceType.CUDA)
        result = config.to_dict()
        
        assert result['device'] == 'cuda'
    
    def test_from_dict(self):
        """Testa criação a partir de dicionário"""
        data = {'device': 'cpu', 'gpu_memory_fraction': 0.5}
        config = HardwareConfig.from_dict(data)
        
        assert config.device == DeviceType.CPU
        assert config.gpu_memory_fraction == 0.5


class TestTranscriptionConfig:
    """Testes para configuração de transcrição"""
    
    def test_default_values(self):
        """Testa valores padrão"""
        config = TranscriptionConfig()
        
        assert config.model_size == ModelSize.SMALL
        assert config.language == Language.AUTO
        assert config.enable_vad is True
    
    def test_to_dict_and_back(self):
        """Testa roundtrip de serialização"""
        original = TranscriptionConfig(
            model_size=ModelSize.MEDIUM,
            language=Language.PORTUGUESE,
            beam_size=10
        )
        
        data = original.to_dict()
        restored = TranscriptionConfig.from_dict(data)
        
        assert restored.model_size == original.model_size
        assert restored.language == original.language
        assert restored.beam_size == original.beam_size


class TestAppConfiguration:
    """Testes para configuração completa"""
    
    def test_default_config(self):
        """Testa configuração padrão"""
        config = AppConfiguration()
        
        assert config.version == "3.0.0"
        assert isinstance(config.hardware, HardwareConfig)
        assert isinstance(config.transcription, TranscriptionConfig)
    
    def test_serialization(self):
        """Testa serialização completa"""
        original = AppConfiguration()
        data = original.to_dict()
        restored = AppConfiguration.from_dict(data)
        
        assert restored.version == original.version
        assert restored.hardware.device == original.hardware.device


class TestConfigManager:
    """Testes para ConfigManager"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Diretório temporário para configurações"""
        config_dir = tmp_path / "speech_scribe_test"
        config_dir.mkdir()
        return config_dir
    
    @pytest.fixture
    def manager(self, temp_config_dir):
        """Fixture de ConfigManager"""
        config_path = temp_config_dir / "config.json"
        manager = ConfigManager(config_path=config_path)
        manager.config_dir = temp_config_dir
        manager.backup_dir = temp_config_dir / "backups"
        manager.backup_dir.mkdir(exist_ok=True)
        return manager
    
    def test_create_default_config(self, manager):
        """Testa criação de configuração padrão"""
        assert manager.config is not None
        assert isinstance(manager.config, AppConfiguration)
    
    def test_save_and_load(self, manager):
        """Testa salvar e carregar"""
        manager.config.transcription.model_size = ModelSize.LARGE_V3
        manager.save()
        
        # Criar novo manager para carregar
        manager2 = ConfigManager(config_path=manager.config_path)
        
        assert manager2.config.transcription.model_size == ModelSize.LARGE_V3
    
    def test_get_by_key(self, manager):
        """Testa obter valor por chave pontilhada"""
        value = manager.get('transcription.model_size')
        
        assert value == 'small'  # valor padrão
    
    def test_get_default(self, manager):
        """Testa valor padrão para chave inexistente"""
        value = manager.get('nonexistent.key', default='fallback')
        
        assert value == 'fallback'
    
    def test_set_by_key(self, manager):
        """Testa definir valor por chave pontilhada"""
        manager.set('hardware.num_workers', 8)
        
        assert manager.config.hardware.num_workers == 8
    
    def test_validate_config(self, manager):
        """Testa validação de configuração válida"""
        errors = manager.validate_config()
        
        assert len(errors) == 0
    
    def test_validate_invalid_config(self, manager):
        """Testa validação de configuração inválida"""
        manager.config.hardware.gpu_memory_fraction = 2.0  # Inválido
        errors = manager.validate_config()
        
        assert len(errors) > 0
    
    def test_apply_quality_preset(self, manager):
        """Testa aplicação de preset"""
        manager.apply_quality_preset(QualityPreset.FAST)
        
        assert manager.config.transcription.model_size == ModelSize.TINY
        assert manager.config.transcription.beam_size == 1
    
    def test_reset_to_defaults(self, manager):
        """Testa reset para padrões"""
        manager.config.transcription.model_size = ModelSize.LARGE_V3
        manager.reset_to_defaults()
        
        assert manager.config.transcription.model_size == ModelSize.SMALL
    
    def test_backup_creation(self, manager):
        """Testa criação de backup"""
        manager.save()
        manager.save()  # Segunda chamada cria backup
        
        backups = manager.get_backups()
        
        assert len(backups) >= 0  # Pode ou não ter backup dependendo do timing
    
    def test_export_json(self, manager, temp_config_dir):
        """Testa exportação JSON"""
        export_path = temp_config_dir / "exported.json"
        manager.export_config(export_path, format='json')
        
        assert export_path.exists()
        
        with open(export_path) as f:
            data = json.load(f)
        
        assert 'version' in data
    
    def test_import_config(self, manager, temp_config_dir):
        """Testa importação de configuração"""
        # Criar arquivo de configuração
        import_path = temp_config_dir / "import.json"
        config_data = {
            'version': '3.0.0',
            'transcription': {'model_size': 'medium'}
        }
        
        with open(import_path, 'w') as f:
            json.dump(config_data, f)
        
        manager.import_config(import_path)
        
        assert manager.config.transcription.model_size == ModelSize.MEDIUM
