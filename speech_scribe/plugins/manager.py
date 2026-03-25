#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔌 Gerenciador de Plugins - Speech Scribe Pro V3
Carrega, gerencia e executa plugins
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass

from speech_scribe.plugins.base import (
    Plugin, PluginType, PluginInfo, PluginHook, HookPriority
)
from speech_scribe.utils.logger import logger


@dataclass
class PluginEntry:
    """Entrada de plugin no registro"""
    plugin: Plugin
    info: PluginInfo
    enabled: bool = False
    load_path: Optional[str] = None
    error: Optional[str] = None


class PluginManager:
    """
    Gerenciador central de plugins.
    
    Features:
    - Descoberta automática de plugins
    - Carregamento dinâmico
    - Sistema de hooks
    - Gerenciamento de dependências
    - Isolamento de erros
    """
    
    # Hooks disponíveis no sistema
    AVAILABLE_HOOKS = [
        'pre_transcription',       # Antes de transcrever
        'post_transcription',      # Após transcrição
        'pre_analysis',            # Antes de análise
        'post_analysis',           # Após análise
        'pre_export',              # Antes de exportar
        'post_export',             # Após exportar
        'on_file_loaded',          # Arquivo carregado
        'on_error',                # Quando ocorre erro
        'on_progress',             # Atualização de progresso
        'on_app_start',            # Aplicação iniciando
        'on_app_exit',             # Aplicação fechando
    ]
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador.
        
        Args:
            plugins_dir: Diretório de plugins (padrão: ~/.speech_scribe_v3/plugins)
        """
        self.plugins_dir = plugins_dir or (Path.home() / ".speech_scribe_v3" / "plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Registro de plugins
        self._plugins: Dict[str, PluginEntry] = {}
        
        # Hooks registrados
        self._hooks: Dict[str, List[PluginHook]] = {hook: [] for hook in self.AVAILABLE_HOOKS}
        
        # Configurações de plugins
        self._config_file = self.plugins_dir / "plugins_config.json"
        self._config = self._load_config()
        
        logger.info(f"PluginManager inicializado: {self.plugins_dir}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações salvas"""
        if self._config_file.exists():
            try:
                return json.loads(self._config_file.read_text())
            except Exception as e:
                logger.warning(f"Erro ao carregar config de plugins: {e}")
        return {'enabled_plugins': [], 'plugin_settings': {}}
    
    def _save_config(self):
        """Salva configurações"""
        try:
            self._config_file.write_text(json.dumps(self._config, indent=2))
        except Exception as e:
            logger.error(f"Erro ao salvar config de plugins: {e}")
    
    def discover_plugins(self) -> List[str]:
        """
        Descobre plugins no diretório.
        
        Returns:
            Lista de caminhos de plugins encontrados
        """
        discovered = []
        
        if not self.plugins_dir.exists():
            return discovered
        
        # Procurar arquivos .py e diretórios com __init__.py
        for item in self.plugins_dir.iterdir():
            if item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                discovered.append(str(item))
            elif item.is_dir() and (item / '__init__.py').exists():
                discovered.append(str(item))
        
        logger.info(f"Plugins descobertos: {len(discovered)}")
        return discovered
    
    def load_plugin(self, path: str) -> Optional[Plugin]:
        """
        Carrega um plugin de arquivo ou diretório.
        
        Args:
            path: Caminho do plugin
            
        Returns:
            Instância do plugin ou None se falhar
        """
        path = Path(path)
        
        try:
            # Determinar nome do módulo
            if path.is_file():
                module_name = path.stem
                spec = importlib.util.spec_from_file_location(module_name, path)
            else:
                module_name = path.name
                spec = importlib.util.spec_from_file_location(
                    module_name, path / '__init__.py',
                    submodule_search_locations=[str(path)]
                )
            
            if spec is None or spec.loader is None:
                raise ImportError(f"Não foi possível carregar spec para {path}")
            
            # Carregar módulo
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Procurar classe de plugin
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Plugin) and 
                    attr is not Plugin and
                    not attr.__name__.startswith('_')):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                raise ValueError(f"Nenhuma classe Plugin encontrada em {path}")
            
            # Instanciar plugin
            plugin = plugin_class()
            info = plugin.get_info()
            
            # Registrar
            entry = PluginEntry(
                plugin=plugin,
                info=info,
                load_path=str(path)
            )
            self._plugins[info.name] = entry
            
            logger.info(f"✅ Plugin carregado: {info.name} v{info.version}")
            return plugin
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar plugin {path}: {e}")
            return None
    
    def load_all_plugins(self):
        """Carrega todos os plugins descobertos"""
        for path in self.discover_plugins():
            self.load_plugin(path)
    
    def register_plugin(self, plugin_class: Type[Plugin]) -> Optional[Plugin]:
        """
        Registra um plugin programaticamente.
        
        Args:
            plugin_class: Classe do plugin
            
        Returns:
            Instância do plugin
        """
        try:
            plugin = plugin_class()
            info = plugin.get_info()
            
            entry = PluginEntry(
                plugin=plugin,
                info=info
            )
            self._plugins[info.name] = entry
            
            logger.info(f"✅ Plugin registrado: {info.name}")
            return plugin
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar plugin: {e}")
            return None
    
    def enable_plugin(self, name: str) -> bool:
        """
        Ativa um plugin.
        
        Args:
            name: Nome do plugin
            
        Returns:
            True se ativado com sucesso
        """
        if name not in self._plugins:
            logger.warning(f"Plugin não encontrado: {name}")
            return False
        
        entry = self._plugins[name]
        
        try:
            # Carregar configurações salvas
            if name in self._config.get('plugin_settings', {}):
                entry.plugin.configure(self._config['plugin_settings'][name])
            else:
                entry.plugin.configure(entry.plugin.get_default_config())
            
            # Ativar plugin
            entry.plugin._manager = self
            entry.plugin.activate()
            entry.plugin._enabled = True
            entry.enabled = True
            
            # Registrar hooks do plugin
            for hook in entry.plugin.get_hooks():
                self._register_hook(hook)
            
            # Salvar estado
            if name not in self._config['enabled_plugins']:
                self._config['enabled_plugins'].append(name)
                self._save_config()
            
            logger.info(f"✅ Plugin ativado: {name}")
            return True
            
        except Exception as e:
            entry.error = str(e)
            logger.error(f"❌ Erro ao ativar plugin {name}: {e}")
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Desativa um plugin.
        
        Args:
            name: Nome do plugin
            
        Returns:
            True se desativado com sucesso
        """
        if name not in self._plugins:
            return False
        
        entry = self._plugins[name]
        
        try:
            # Desregistrar hooks
            for hook in entry.plugin.get_hooks():
                self._unregister_hook(hook)
            
            # Desativar plugin
            entry.plugin.deactivate()
            entry.plugin._enabled = False
            entry.enabled = False
            
            # Salvar estado
            if name in self._config['enabled_plugins']:
                self._config['enabled_plugins'].remove(name)
                self._save_config()
            
            logger.info(f"Plugin desativado: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desativar plugin {name}: {e}")
            return False
    
    def _register_hook(self, hook: PluginHook):
        """Registra um hook interno"""
        if hook.name in self._hooks:
            self._hooks[hook.name].append(hook)
            # Ordenar por prioridade (maior primeiro)
            self._hooks[hook.name].sort(key=lambda h: h.priority.value, reverse=True)
    
    def _unregister_hook(self, hook: PluginHook):
        """Remove um hook interno"""
        if hook.name in self._hooks:
            self._hooks[hook.name] = [h for h in self._hooks[hook.name] if h != hook]
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Executa todos os callbacks de um hook.
        
        Args:
            hook_name: Nome do hook
            *args, **kwargs: Argumentos para os callbacks
            
        Returns:
            Lista de resultados dos callbacks
        """
        if hook_name not in self._hooks:
            return []
        
        results = []
        for hook in self._hooks[hook_name]:
            if not hook.enabled:
                continue
                
            try:
                result = hook.callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Erro em hook {hook_name}: {e}")
                results.append(None)
        
        return results
    
    def execute_hook_chain(self, hook_name: str, initial_value: Any, **kwargs) -> Any:
        """
        Executa hooks em cadeia, passando o resultado de um para o próximo.
        
        Args:
            hook_name: Nome do hook
            initial_value: Valor inicial
            **kwargs: Argumentos extras
            
        Returns:
            Valor final após processamento
        """
        value = initial_value
        
        for hook in self._hooks.get(hook_name, []):
            if not hook.enabled:
                continue
                
            try:
                value = hook.callback(value, **kwargs)
            except Exception as e:
                logger.error(f"Erro em hook chain {hook_name}: {e}")
        
        return value
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Obtém plugin por nome"""
        entry = self._plugins.get(name)
        return entry.plugin if entry else None
    
    def get_plugins(self, plugin_type: Optional[PluginType] = None) -> List[Plugin]:
        """
        Obtém lista de plugins.
        
        Args:
            plugin_type: Filtrar por tipo (opcional)
            
        Returns:
            Lista de plugins
        """
        plugins = [e.plugin for e in self._plugins.values()]
        
        if plugin_type:
            plugins = [p for p in plugins if p.get_info().plugin_type == plugin_type]
        
        return plugins
    
    def get_enabled_plugins(self) -> List[Plugin]:
        """Obtém plugins ativos"""
        return [e.plugin for e in self._plugins.values() if e.enabled]
    
    def get_plugins_info(self) -> List[Dict[str, Any]]:
        """Obtém informações de todos os plugins"""
        return [
            {
                **entry.info.to_dict(),
                'enabled': entry.enabled,
                'error': entry.error
            }
            for entry in self._plugins.values()
        ]
    
    def configure_plugin(self, name: str, config: Dict[str, Any]):
        """
        Configura um plugin.
        
        Args:
            name: Nome do plugin
            config: Configurações
        """
        if name in self._plugins:
            self._plugins[name].plugin.configure(config)
            
            # Salvar configurações
            if 'plugin_settings' not in self._config:
                self._config['plugin_settings'] = {}
            self._config['plugin_settings'][name] = config
            self._save_config()
    
    def unload_plugin(self, name: str):
        """Remove plugin do registro"""
        if name in self._plugins:
            self.disable_plugin(name)
            del self._plugins[name]
            logger.info(f"Plugin removido: {name}")
    
    def reload_plugin(self, name: str) -> bool:
        """Recarrega um plugin"""
        if name not in self._plugins:
            return False
        
        entry = self._plugins[name]
        load_path = entry.load_path
        was_enabled = entry.enabled
        
        self.unload_plugin(name)
        
        if load_path:
            plugin = self.load_plugin(load_path)
            if plugin and was_enabled:
                self.enable_plugin(name)
            return plugin is not None
        
        return False


# Instância singleton
_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Obtém gerenciador de plugins singleton"""
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


__all__ = ['PluginManager', 'get_plugin_manager']
