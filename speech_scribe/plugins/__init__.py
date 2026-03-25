#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔌 Sistema de Plugins - Speech Scribe Pro V3
Arquitetura extensível para funcionalidades customizadas
"""

from speech_scribe.plugins.base import (
    Plugin,
    PluginType,
    PluginInfo,
    PluginHook,
    HookPriority
)
from speech_scribe.plugins.manager import (
    PluginManager,
    get_plugin_manager
)

__all__ = [
    'Plugin',
    'PluginType',
    'PluginInfo',
    'PluginHook',
    'HookPriority',
    'PluginManager',
    'get_plugin_manager',
]
