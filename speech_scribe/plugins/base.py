#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔌 Classes Base do Sistema de Plugins - Speech Scribe Pro V3
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from pathlib import Path


class PluginType(Enum):
    """Tipos de plugins suportados"""
    TRANSCRIPTION = auto()      # Engines de transcrição alternativos
    ANALYSIS = auto()           # Análises de texto adicionais
    EXPORT = auto()             # Formatos de exportação
    PRE_PROCESSOR = auto()      # Pré-processamento de áudio
    POST_PROCESSOR = auto()     # Pós-processamento de transcrição
    UI_EXTENSION = auto()       # Extensões de interface
    INTEGRATION = auto()        # Integrações externas


class HookPriority(Enum):
    """Prioridade de execução dos hooks"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class PluginInfo:
    """Informações do plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    homepage: str = ""
    license: str = "MIT"
    dependencies: List[str] = field(default_factory=list)
    min_app_version: str = "3.0.0"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'type': self.plugin_type.name,
            'homepage': self.homepage,
            'license': self.license,
            'dependencies': self.dependencies,
            'min_app_version': self.min_app_version,
            'tags': self.tags
        }


@dataclass
class PluginHook:
    """Define um hook que o plugin pode registrar"""
    name: str
    callback: Callable
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True


class Plugin(ABC):
    """
    Classe base abstrata para todos os plugins.
    
    Para criar um plugin:
    1. Herde desta classe
    2. Implemente get_info() e activate()
    3. Opcionalmente implemente deactivate() e configure()
    
    Exemplo:
        class MyPlugin(Plugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    name="My Plugin",
                    version="1.0.0",
                    description="Plugin de exemplo",
                    author="Autor",
                    plugin_type=PluginType.ANALYSIS
                )
            
            def activate(self):
                self.register_hook('post_transcription', self.on_transcription)
            
            def on_transcription(self, text: str) -> str:
                return text.upper()
    """
    
    def __init__(self):
        self._hooks: List[PluginHook] = []
        self._enabled = False
        self._config: Dict[str, Any] = {}
        self._manager = None  # Será definido pelo PluginManager
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """
        Retorna informações do plugin.
        
        Returns:
            PluginInfo com metadados do plugin
        """
        pass
    
    @abstractmethod
    def activate(self):
        """
        Ativa o plugin.
        
        Aqui você deve:
        - Registrar hooks
        - Inicializar recursos
        - Configurar integrações
        """
        pass
    
    def deactivate(self):
        """
        Desativa o plugin.
        
        Aqui você deve:
        - Desregistrar hooks
        - Liberar recursos
        - Limpar estado
        """
        self._hooks.clear()
    
    def configure(self, config: Dict[str, Any]):
        """
        Configura o plugin.
        
        Args:
            config: Dicionário de configurações
        """
        self._config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna configurações atuais"""
        return self._config.copy()
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Retorna configurações padrão do plugin.
        Override para definir configurações padrão.
        """
        return {}
    
    def register_hook(self, hook_name: str, callback: Callable, 
                      priority: HookPriority = HookPriority.NORMAL):
        """
        Registra um hook.
        
        Args:
            hook_name: Nome do hook (ex: 'pre_transcription', 'post_analysis')
            callback: Função a ser chamada
            priority: Prioridade de execução
        """
        hook = PluginHook(
            name=hook_name,
            callback=callback,
            priority=priority
        )
        self._hooks.append(hook)
    
    def unregister_hook(self, hook_name: str):
        """Remove um hook pelo nome"""
        self._hooks = [h for h in self._hooks if h.name != hook_name]
    
    def get_hooks(self) -> List[PluginHook]:
        """Retorna todos os hooks registrados"""
        return self._hooks.copy()
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    @property
    def name(self) -> str:
        return self.get_info().name
    
    @property
    def version(self) -> str:
        return self.get_info().version
    
    def __repr__(self) -> str:
        info = self.get_info()
        return f"<Plugin: {info.name} v{info.version} ({info.plugin_type.name})>"


class TranscriptionPlugin(Plugin):
    """Plugin especializado para engines de transcrição"""
    
    @abstractmethod
    async def transcribe(self, file_path: str, **options) -> Dict[str, Any]:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            file_path: Caminho do arquivo
            **options: Opções de transcrição
            
        Returns:
            Resultado da transcrição
        """
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Retorna formatos de áudio suportados"""
        return ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
    
    def get_supported_languages(self) -> List[str]:
        """Retorna idiomas suportados"""
        return ['auto']


class AnalysisPlugin(Plugin):
    """Plugin especializado para análises de texto"""
    
    @abstractmethod
    def analyze(self, text: str, **options) -> Dict[str, Any]:
        """
        Analisa o texto.
        
        Args:
            text: Texto para analisar
            **options: Opções de análise
            
        Returns:
            Resultado da análise
        """
        pass
    
    def get_analysis_types(self) -> List[str]:
        """Retorna tipos de análise suportados"""
        return []


class ExportPlugin(Plugin):
    """Plugin especializado para exportação"""
    
    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: Path, **options) -> bool:
        """
        Exporta dados para arquivo.
        
        Args:
            data: Dados para exportar
            output_path: Caminho de saída
            **options: Opções de exportação
            
        Returns:
            True se exportado com sucesso
        """
        pass
    
    def get_format_name(self) -> str:
        """Retorna nome do formato"""
        return "Unknown"
    
    def get_file_extension(self) -> str:
        """Retorna extensão do arquivo"""
        return ".txt"


class PreProcessorPlugin(Plugin):
    """Plugin para pré-processamento de áudio"""
    
    @abstractmethod
    def process(self, file_path: str, **options) -> str:
        """
        Processa arquivo de áudio antes da transcrição.
        
        Args:
            file_path: Caminho do arquivo original
            **options: Opções de processamento
            
        Returns:
            Caminho do arquivo processado
        """
        pass


class PostProcessorPlugin(Plugin):
    """Plugin para pós-processamento de transcrição"""
    
    @abstractmethod
    def process(self, transcription: Dict[str, Any], **options) -> Dict[str, Any]:
        """
        Processa transcrição após ser gerada.
        
        Args:
            transcription: Resultado da transcrição
            **options: Opções de processamento
            
        Returns:
            Transcrição processada
        """
        pass


__all__ = [
    'PluginType',
    'HookPriority',
    'PluginInfo',
    'PluginHook',
    'Plugin',
    'TranscriptionPlugin',
    'AnalysisPlugin',
    'ExportPlugin',
    'PreProcessorPlugin',
    'PostProcessorPlugin',
]
