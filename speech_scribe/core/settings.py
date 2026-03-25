#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚙️ Settings - Speech Scribe Pro V3
Persistência de configurações do usuário via QSettings
"""

from PyQt6.QtCore import QSettings
from speech_scribe.utils.logger import logger


class UserSettings:
    """Gerencia configurações persistentes do usuário"""
    
    def __init__(self):
        self.settings = QSettings("SpeechScribePro", "V3")
    
    # --- Transcrição ---
    
    def get_model(self) -> str:
        return self.settings.value("transcription/model", "large-v3")
    
    def set_model(self, model: str):
        self.settings.setValue("transcription/model", model)
    
    def get_language(self) -> str:
        return self.settings.value("transcription/language", "auto")
    
    def set_language(self, lang: str):
        self.settings.setValue("transcription/language", lang)
    
    def get_preset(self) -> str:
        return self.settings.value("transcription/preset", "⚖️ Balanceado")
    
    def set_preset(self, preset: str):
        self.settings.setValue("transcription/preset", preset)
    
    def get_diarization_enabled(self) -> bool:
        return self.settings.value("transcription/diarization", False, type=bool)
    
    def set_diarization_enabled(self, enabled: bool):
        self.settings.setValue("transcription/diarization", enabled)
    
    # --- Tema ---
    
    def get_theme(self) -> str:
        return self.settings.value("ui/theme", "light")
    
    def set_theme(self, theme: str):
        self.settings.setValue("ui/theme", theme)
    
    # --- Player de áudio ---
    
    def get_volume(self) -> int:
        return self.settings.value("player/volume", 70, type=int)
    
    def set_volume(self, volume: int):
        self.settings.setValue("player/volume", volume)
    
    # --- Janela ---
    
    def get_window_geometry(self) -> bytes:
        return self.settings.value("ui/geometry", None)
    
    def set_window_geometry(self, geometry: bytes):
        self.settings.setValue("ui/geometry", geometry)
    
    def get_window_state(self) -> bytes:
        return self.settings.value("ui/state", None)
    
    def set_window_state(self, state: bytes):
        self.settings.setValue("ui/state", state)
    
    # --- Último diretório ---
    
    def get_last_directory(self) -> str:
        return self.settings.value("files/last_directory", "")
    
    def set_last_directory(self, directory: str):
        self.settings.setValue("files/last_directory", directory)
    
    # --- GPU ---
    
    def get_gpu_device(self) -> str:
        return self.settings.value("hardware/device", "auto")
    
    def set_gpu_device(self, device: str):
        self.settings.setValue("hardware/device", device)
    
    def get_vram_fraction(self) -> int:
        return self.settings.value("hardware/vram_fraction", 80, type=int)
    
    def set_vram_fraction(self, fraction: int):
        self.settings.setValue("hardware/vram_fraction", fraction)
    
    # --- Ollama ---
    
    def get_ollama_model(self) -> str:
        return self.settings.value("ollama/model", "Auto (Melhor Disponível)")
    
    def set_ollama_model(self, model: str):
        self.settings.setValue("ollama/model", model)
    
    # --- Interface Language ---
    
    def get_interface_language(self) -> str:
        return self.settings.value("ui/language", "pt")
    
    def set_interface_language(self, lang: str):
        self.settings.setValue("ui/language", lang)
    
    # --- Utilitários ---
    
    def sync(self):
        """Força escrita no disco"""
        self.settings.sync()
    
    def clear(self):
        """Limpa todas as configurações"""
        self.settings.clear()
        logger.info("Configurações do usuário limpas")


# Instância global
_user_settings = None

def get_user_settings() -> UserSettings:
    """Retorna instância global de configurações"""
    global _user_settings
    if _user_settings is None:
        _user_settings = UserSettings()
    return _user_settings
