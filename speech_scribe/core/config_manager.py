#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚙️ Gerenciador de Configuração Unificado - Speech Scribe Pro V3
Sistema centralizado de configurações com validação e persistência
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from speech_scribe.utils.logger import logger


class DeviceType(Enum):
    """Tipos de dispositivo para processamento"""
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class ModelSize(Enum):
    """Tamanhos de modelo Whisper disponíveis"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"


class Language(Enum):
    """Idiomas suportados"""
    AUTO = "auto"
    PORTUGUESE = "pt"
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    RUSSIAN = "ru"


class QualityPreset(Enum):
    """Presets de qualidade"""
    FAST = "fast"           # Rápido, menor qualidade
    BALANCED = "balanced"   # Equilíbrio
    QUALITY = "quality"     # Alta qualidade
    BEST = "best"           # Máxima qualidade


class ExportFormat(Enum):
    """Formatos de exportação"""
    TXT = "txt"
    JSON = "json"
    SRT = "srt"
    VTT = "vtt"
    DOCX = "docx"


@dataclass
class HardwareConfig:
    """Configurações de hardware"""
    device: DeviceType = DeviceType.AUTO
    gpu_memory_fraction: float = 0.8
    num_workers: int = 2
    prefer_gpu: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'device': self.device.value,
            'gpu_memory_fraction': self.gpu_memory_fraction,
            'num_workers': self.num_workers,
            'prefer_gpu': self.prefer_gpu
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HardwareConfig':
        return cls(
            device=DeviceType(data.get('device', 'auto')),
            gpu_memory_fraction=data.get('gpu_memory_fraction', 0.8),
            num_workers=data.get('num_workers', 2),
            prefer_gpu=data.get('prefer_gpu', True)
        )


@dataclass
class TranscriptionConfig:
    """Configurações de transcrição"""
    model_size: ModelSize = ModelSize.SMALL
    language: Language = Language.AUTO
    quality_preset: QualityPreset = QualityPreset.BALANCED
    enable_vad: bool = True
    enable_word_timestamps: bool = True
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    chunk_length_s: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_size': self.model_size.value,
            'language': self.language.value,
            'quality_preset': self.quality_preset.value,
            'enable_vad': self.enable_vad,
            'enable_word_timestamps': self.enable_word_timestamps,
            'beam_size': self.beam_size,
            'best_of': self.best_of,
            'temperature': self.temperature,
            'chunk_length_s': self.chunk_length_s
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionConfig':
        return cls(
            model_size=ModelSize(data.get('model_size', 'small')),
            language=Language(data.get('language', 'auto')),
            quality_preset=QualityPreset(data.get('quality_preset', 'balanced')),
            enable_vad=data.get('enable_vad', True),
            enable_word_timestamps=data.get('enable_word_timestamps', True),
            beam_size=data.get('beam_size', 5),
            best_of=data.get('best_of', 5),
            temperature=data.get('temperature', 0.0),
            chunk_length_s=data.get('chunk_length_s', 30)
        )


@dataclass
class DiarizationConfig:
    """Configurações de diarização"""
    enabled: bool = False
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'min_speakers': self.min_speakers,
            'max_speakers': self.max_speakers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiarizationConfig':
        return cls(
            enabled=data.get('enabled', False),
            min_speakers=data.get('min_speakers'),
            max_speakers=data.get('max_speakers')
        )


@dataclass
class AnalysisConfig:
    """Configurações de análise IA"""
    enable_sentiment: bool = True
    enable_keywords: bool = True
    enable_entities: bool = True
    enable_summary: bool = True
    enable_topics: bool = True
    ollama_model: str = "gpt-oss:20b"
    use_ollama: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enable_sentiment': self.enable_sentiment,
            'enable_keywords': self.enable_keywords,
            'enable_entities': self.enable_entities,
            'enable_summary': self.enable_summary,
            'enable_topics': self.enable_topics,
            'ollama_model': self.ollama_model,
            'use_ollama': self.use_ollama
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisConfig':
        return cls(
            enable_sentiment=data.get('enable_sentiment', True),
            enable_keywords=data.get('enable_keywords', True),
            enable_entities=data.get('enable_entities', True),
            enable_summary=data.get('enable_summary', True),
            enable_topics=data.get('enable_topics', True),
            ollama_model=data.get('ollama_model', 'gpt-oss:20b'),
            use_ollama=data.get('use_ollama', False)
        )


@dataclass
class UIConfig:
    """Configurações de interface"""
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    show_advanced_options: bool = False
    auto_copy_result: bool = False
    confirm_before_exit: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AppConfiguration:
    """Configuração completa da aplicação"""
    version: str = "3.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    diarization: DiarizationConfig = field(default_factory=DiarizationConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'hardware': self.hardware.to_dict(),
            'transcription': self.transcription.to_dict(),
            'diarization': self.diarization.to_dict(),
            'analysis': self.analysis.to_dict(),
            'ui': self.ui.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfiguration':
        return cls(
            version=data.get('version', '3.0.0'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            modified_at=data.get('modified_at', datetime.now().isoformat()),
            hardware=HardwareConfig.from_dict(data.get('hardware', {})),
            transcription=TranscriptionConfig.from_dict(data.get('transcription', {})),
            diarization=DiarizationConfig.from_dict(data.get('diarization', {})),
            analysis=AnalysisConfig.from_dict(data.get('analysis', {})),
            ui=UIConfig.from_dict(data.get('ui', {}))
        )


class ConfigManager:
    """
    Gerenciador centralizado de configurações.
    
    Features:
    - Carregamento/salvamento de arquivos YAML/JSON
    - Validação de configurações
    - Presets de qualidade
    - Merge com variáveis de ambiente
    - Backup automático
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".speech_scribe_v3"
    DEFAULT_CONFIG_FILE = "config.json"
    BACKUP_DIR = "config_backups"
    
    # Presets de qualidade com configurações otimizadas
    QUALITY_PRESETS = {
        QualityPreset.FAST: {
            'model_size': ModelSize.TINY,
            'beam_size': 1,
            'best_of': 1,
            'chunk_length_s': 20
        },
        QualityPreset.BALANCED: {
            'model_size': ModelSize.SMALL,
            'beam_size': 5,
            'best_of': 5,
            'chunk_length_s': 30
        },
        QualityPreset.QUALITY: {
            'model_size': ModelSize.MEDIUM,
            'beam_size': 8,
            'best_of': 5,
            'chunk_length_s': 30
        },
        QualityPreset.BEST: {
            'model_size': ModelSize.LARGE_V3,
            'beam_size': 10,
            'best_of': 5,
            'chunk_length_s': 30
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa o gerenciador.
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config_dir = self.DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = config_path or (self.config_dir / self.DEFAULT_CONFIG_FILE)
        self.backup_dir = self.config_dir / self.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar ou criar configuração
        self.config = self._load_config()
        
        # Aplicar variáveis de ambiente
        self._apply_env_vars()
        
        logger.info(f"ConfigManager inicializado: {self.config_path}")
    
    def _load_config(self) -> AppConfiguration:
        """Carrega configuração do arquivo"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config = AppConfiguration.from_dict(data)
                logger.info("Configuração carregada do arquivo")
                return config
            except Exception as e:
                logger.warning(f"Erro ao carregar configuração: {e}. Usando padrões.")
        
        return AppConfiguration()
    
    def _apply_env_vars(self):
        """Aplica variáveis de ambiente sobre a configuração"""
        # Device
        if os.environ.get('SPEECH_SCRIBE_DEVICE'):
            try:
                self.config.hardware.device = DeviceType(os.environ['SPEECH_SCRIBE_DEVICE'])
            except ValueError:
                pass
        
        # Model
        if os.environ.get('SPEECH_SCRIBE_MODEL'):
            try:
                self.config.transcription.model_size = ModelSize(os.environ['SPEECH_SCRIBE_MODEL'])
            except ValueError:
                pass
        
        # Language
        if os.environ.get('SPEECH_SCRIBE_LANGUAGE'):
            try:
                self.config.transcription.language = Language(os.environ['SPEECH_SCRIBE_LANGUAGE'])
            except ValueError:
                pass
    
    def save(self):
        """Salva configuração no arquivo"""
        try:
            # Atualizar timestamp
            self.config.modified_at = datetime.now().isoformat()
            
            # Criar backup antes de salvar
            self._create_backup()
            
            # Salvar
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info("Configuração salva")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            raise
    
    def _create_backup(self):
        """Cria backup da configuração atual"""
        if self.config_path.exists():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
                
                with open(self.config_path, 'r') as src:
                    with open(backup_file, 'w') as dst:
                        dst.write(src.read())
                
                # Manter apenas últimos 10 backups
                self._cleanup_old_backups(keep=10)
                
            except Exception as e:
                logger.warning(f"Erro ao criar backup: {e}")
    
    def _cleanup_old_backups(self, keep: int = 10):
        """Remove backups antigos"""
        backups = sorted(self.backup_dir.glob("config_backup_*.json"))
        for backup in backups[:-keep]:
            try:
                backup.unlink()
            except Exception:
                pass
    
    def restore_backup(self, backup_file: Path) -> bool:
        """
        Restaura configuração de um backup.
        
        Args:
            backup_file: Arquivo de backup
            
        Returns:
            True se restaurado com sucesso
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config = AppConfiguration.from_dict(data)
            self.save()
            
            logger.info(f"Configuração restaurada de: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False
    
    def get_backups(self) -> List[Path]:
        """Retorna lista de backups disponíveis"""
        return sorted(self.backup_dir.glob("config_backup_*.json"), reverse=True)
    
    def reset_to_defaults(self):
        """Reseta para configurações padrão"""
        self._create_backup()
        self.config = AppConfiguration()
        self.save()
        logger.info("Configurações resetadas para padrões")
    
    def validate_config(self) -> List[str]:
        """
        Valida a configuração atual.
        
        Returns:
            Lista de erros encontrados
        """
        errors = []
        
        # Validar GPU memory fraction
        if not 0.1 <= self.config.hardware.gpu_memory_fraction <= 1.0:
            errors.append("gpu_memory_fraction deve estar entre 0.1 e 1.0")
        
        # Validar num_workers
        if not 1 <= self.config.hardware.num_workers <= 32:
            errors.append("num_workers deve estar entre 1 e 32")
        
        # Validar beam_size
        if not 1 <= self.config.transcription.beam_size <= 20:
            errors.append("beam_size deve estar entre 1 e 20")
        
        # Validar temperature
        if not 0.0 <= self.config.transcription.temperature <= 1.0:
            errors.append("temperature deve estar entre 0.0 e 1.0")
        
        return errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração por chave pontilhada.
        
        Args:
            key: Chave no formato 'section.key' (ex: 'transcription.model_size')
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração
        """
        try:
            parts = key.split('.')
            value = self.config
            
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default
            
            # Converter Enum para valor
            if isinstance(value, Enum):
                return value.value
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """
        Define valor de configuração por chave pontilhada.
        
        Args:
            key: Chave no formato 'section.key'
            value: Novo valor
        """
        try:
            parts = key.split('.')
            obj = self.config
            
            # Navegar até o penúltimo nível
            for part in parts[:-1]:
                obj = getattr(obj, part)
            
            # Definir valor
            final_key = parts[-1]
            current_value = getattr(obj, final_key)
            
            # Converter para Enum se necessário
            if isinstance(current_value, Enum):
                value = type(current_value)(value)
            
            setattr(obj, final_key, value)
            
        except Exception as e:
            logger.error(f"Erro ao definir configuração {key}: {e}")
            raise
    
    def apply_quality_preset(self, preset: QualityPreset):
        """
        Aplica preset de qualidade.
        
        Args:
            preset: Preset a aplicar
        """
        if preset in self.QUALITY_PRESETS:
            settings = self.QUALITY_PRESETS[preset]
            
            self.config.transcription.model_size = settings['model_size']
            self.config.transcription.beam_size = settings['beam_size']
            self.config.transcription.best_of = settings['best_of']
            self.config.transcription.chunk_length_s = settings['chunk_length_s']
            self.config.transcription.quality_preset = preset
            
            logger.info(f"Preset '{preset.value}' aplicado")
    
    def get_quality_preset_settings(self, preset: QualityPreset) -> Dict[str, Any]:
        """Retorna configurações de um preset"""
        return self.QUALITY_PRESETS.get(preset, {})
    
    def export_config(self, path: Path, format: str = 'json'):
        """
        Exporta configuração para arquivo.
        
        Args:
            path: Caminho do arquivo
            format: Formato ('json' ou 'yaml')
        """
        data = self.config.to_dict()
        
        if format == 'yaml':
            try:
                import yaml
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                logger.warning("PyYAML não instalado. Exportando como JSON.")
                format = 'json'
        
        if format == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Configuração exportada para: {path}")
    
    def import_config(self, path: Path):
        """
        Importa configuração de arquivo.
        
        Args:
            path: Caminho do arquivo
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    import yaml
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self.config = AppConfiguration.from_dict(data)
            self.save()
            
            logger.info(f"Configuração importada de: {path}")
            
        except Exception as e:
            logger.error(f"Erro ao importar configuração: {e}")
            raise


# Instância singleton
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Obtém instância singleton do ConfigManager.
    
    Returns:
        Instância do ConfigManager
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


__all__ = [
    # Enums
    'DeviceType',
    'ModelSize',
    'Language',
    'QualityPreset',
    'ExportFormat',
    
    # Config classes
    'HardwareConfig',
    'TranscriptionConfig',
    'DiarizationConfig',
    'AnalysisConfig',
    'UIConfig',
    'AppConfiguration',
    
    # Manager
    'ConfigManager',
    'get_config_manager',
]
