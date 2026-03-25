#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌍 Internacionalização (i18n) - Speech Scribe Pro V3
Sistema de tradução da interface com dicionários pt/en/es
"""

from typing import Dict
from speech_scribe.utils.logger import logger


# Dicionários de tradução
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "pt": {
        # Header
        "theme_dark": "🌙 Tema Escuro",
        "theme_light": "☀️ Tema Claro",
        
        # Tabs
        "tab_transcription": "🎙️ Transcrição",
        "tab_analysis": "🧠 Análise IA",
        "tab_settings": "⚙️ Configurações",
        "tab_batch": "📦 Lote",
        "tab_microphone": "🎤 Microfone",
        
        # Transcription config
        "preset": "Preset:",
        "model": "Modelo:",
        "language": "Idioma:",
        "speaker_recognition": "🎭 Reconhecimento de Oradores",
        "embed_subtitle": "🎬 Embutir Legenda no Vídeo",
        "start_transcription": "🎯 Iniciar Transcrição",
        "cancel": "⛔ Cancelar",
        "history": "📜 Histórico",
        "transcribing": "🔄 Transcrevendo...",
        "loading_model": "⏳ Carregando modelo...",
        
        # Actions
        "copy": "📋 Copiar",
        "save": "💾 Salvar",
        "export": "📤 Exportar",
        "search": "🔍 Buscar",
        "clear": "🗑️ Limpar",
        "translate": "🌐 Traduzir",
        "close": "Fechar",
        
        # Status
        "ready": "Pronto",
        "ready_to_transcribe": "Pronto para transcrever",
        "file_selected": "Arquivo selecionado:",
        "transcription_completed": "Concluído em",
        "transcription_cancelled": "Transcrição cancelada pelo usuário",
        "cancelling": "Cancelando transcrição...",
        "text_copied": "Texto copiado para área de transferência!",
        "no_text_to_copy": "Nenhum texto para copiar!",
        "no_file_selected": "Selecione um arquivo primeiro!",
        "file_not_found": "Arquivo não encontrado!",
        "select_file": "Selecionar Arquivo de Áudio/Vídeo",
        "file_saved": "Arquivo salvo:",
        "no_text_to_save": "Nenhum texto para salvar!",
        "confirm": "Confirmar",
        "clear_transcription_confirm": "Deseja limpar a transcrição atual?",
        "transcription_cleared": "Transcrição limpa",
        "settings_restored": "Configurações do usuário restauradas",
        "settings_saved": "Configurações do usuário salvas",
        
        # Analysis
        "analysis_options": "Opções de Análise",
        "sentiment_analysis": "Análise de Sentimento",
        "entity_extraction": "Extração de Entidades",
        "keywords": "Palavras-chave",
        "auto_summary": "Resumo Automático",
        "topic_identification": "Identificação de Tópicos",
        "analyze_transcription": "🧠 Analisar Transcrição",
        "chat_with_ai": "💬 Chat com IA",
        "analyzing": "Analisando transcrição com IA...",
        "no_transcription_for_analysis": "Faça uma transcrição primeiro!",
        "empty_transcription": "Texto da transcrição está vazio!",
        
        # Settings
        "hardware_settings": "Configurações de Hardware",
        "device": "Dispositivo:",
        "workers": "Workers:",
        "vram_usage": "Uso VRAM:",
        "gpu_info": "🎮 Informações da GPU",
        "optimize_gpu": "⚡ Otimizar GPU",
        "cache_settings": "Configurações de Cache",
        "clear_model_cache": "🗑️ Limpar Cache de Modelos",
        "clear_gpu_cache": "🧹 Limpar Cache GPU",
        "system_info": "Informações do Sistema",
        
        # Batch
        "files_in_queue": "📁 Arquivos na Fila",
        "add_files": "➕ Adicionar Arquivos",
        "add_folder": "📂 Adicionar Pasta",
        "remove_selected": "🗑️ Remover Selecionados",
        "clear_list": "🧹 Limpar Lista",
        "batch_settings": "⚙️ Configurações do Lote",
        "diarization": "Diarização",
        "progress": "📊 Progresso",
        "start_processing": "▶️ Iniciar Processamento",
        "cancel_processing": "⏹️ Cancelar",
        "export_all": "📤 Exportar Todos",
        "ready_to_process": "Pronto para processar",
        "processing": "Processando...",
        "drop_hint": "💡 Arraste arquivos ou pastas para cá",
        
        # Streaming
        "recording_settings": "🎤 Configurações de Gravação",
        "audio_device": "Dispositivo:",
        "start_recording": "🔴 Iniciar Gravação",
        "stop_and_transcribe": "⏹️ Parar e Transcrever",
        "ready_to_record": "Pronto para gravar",
        "recording": "Gravando... Fale no microfone",
        "processing_transcription": "Processando transcrição...",
        "transcription_done": "Transcrição concluída!",
        "use_transcription": "✅ Usar Transcrição",
        
        # Errors
        "error": "Erro",
        "warning": "Aviso",
        "info": "Info",
        "success": "Sucesso",
    },
    
    "en": {
        # Header
        "theme_dark": "🌙 Dark Theme",
        "theme_light": "☀️ Light Theme",
        
        # Tabs
        "tab_transcription": "🎙️ Transcription",
        "tab_analysis": "🧠 AI Analysis",
        "tab_settings": "⚙️ Settings",
        "tab_batch": "📦 Batch",
        "tab_microphone": "🎤 Microphone",
        
        # Transcription config
        "preset": "Preset:",
        "model": "Model:",
        "language": "Language:",
        "speaker_recognition": "🎭 Speaker Recognition",
        "embed_subtitle": "🎬 Embed Subtitle in Video",
        "start_transcription": "🎯 Start Transcription",
        "cancel": "⛔ Cancel",
        "history": "📜 History",
        "transcribing": "🔄 Transcribing...",
        "loading_model": "⏳ Loading model...",
        
        # Actions
        "copy": "📋 Copy",
        "save": "💾 Save",
        "export": "📤 Export",
        "search": "🔍 Search",
        "clear": "🗑️ Clear",
        "translate": "🌐 Translate",
        "close": "Close",
        
        # Status
        "ready": "Ready",
        "ready_to_transcribe": "Ready to transcribe",
        "file_selected": "File selected:",
        "transcription_completed": "Completed in",
        "transcription_cancelled": "Transcription cancelled by user",
        "cancelling": "Cancelling transcription...",
        "text_copied": "Text copied to clipboard!",
        "no_text_to_copy": "No text to copy!",
        "no_file_selected": "Select a file first!",
        "file_not_found": "File not found!",
        "select_file": "Select Audio/Video File",
        "file_saved": "File saved:",
        "no_text_to_save": "No text to save!",
        "confirm": "Confirm",
        "clear_transcription_confirm": "Clear current transcription?",
        "transcription_cleared": "Transcription cleared",
        "settings_restored": "User settings restored",
        "settings_saved": "User settings saved",
        
        # Analysis
        "analysis_options": "Analysis Options",
        "sentiment_analysis": "Sentiment Analysis",
        "entity_extraction": "Entity Extraction",
        "keywords": "Keywords",
        "auto_summary": "Auto Summary",
        "topic_identification": "Topic Identification",
        "analyze_transcription": "🧠 Analyze Transcription",
        "chat_with_ai": "💬 Chat with AI",
        "analyzing": "Analyzing transcription with AI...",
        "no_transcription_for_analysis": "Transcribe first!",
        "empty_transcription": "Transcription text is empty!",
        
        # Settings
        "hardware_settings": "Hardware Settings",
        "device": "Device:",
        "workers": "Workers:",
        "vram_usage": "VRAM Usage:",
        "gpu_info": "🎮 GPU Information",
        "optimize_gpu": "⚡ Optimize GPU",
        "cache_settings": "Cache Settings",
        "clear_model_cache": "🗑️ Clear Model Cache",
        "clear_gpu_cache": "🧹 Clear GPU Cache",
        "system_info": "System Information",
        
        # Batch
        "files_in_queue": "📁 Files in Queue",
        "add_files": "➕ Add Files",
        "add_folder": "📂 Add Folder",
        "remove_selected": "🗑️ Remove Selected",
        "clear_list": "🧹 Clear List",
        "batch_settings": "⚙️ Batch Settings",
        "diarization": "Diarization",
        "progress": "📊 Progress",
        "start_processing": "▶️ Start Processing",
        "cancel_processing": "⏹️ Cancel",
        "export_all": "📤 Export All",
        "ready_to_process": "Ready to process",
        "processing": "Processing...",
        "drop_hint": "💡 Drag files or folders here",
        
        # Streaming
        "recording_settings": "🎤 Recording Settings",
        "audio_device": "Device:",
        "start_recording": "🔴 Start Recording",
        "stop_and_transcribe": "⏹️ Stop & Transcribe",
        "ready_to_record": "Ready to record",
        "recording": "Recording... Speak into the microphone",
        "processing_transcription": "Processing transcription...",
        "transcription_done": "Transcription complete!",
        "use_transcription": "✅ Use Transcription",
        
        # Errors
        "error": "Error",
        "warning": "Warning",
        "info": "Info",
        "success": "Success",
    },
    
    "es": {
        # Header
        "theme_dark": "🌙 Tema Oscuro",
        "theme_light": "☀️ Tema Claro",
        
        # Tabs
        "tab_transcription": "🎙️ Transcripción",
        "tab_analysis": "🧠 Análisis IA",
        "tab_settings": "⚙️ Configuración",
        "tab_batch": "📦 Lote",
        "tab_microphone": "🎤 Micrófono",
        
        # Transcription config
        "preset": "Preset:",
        "model": "Modelo:",
        "language": "Idioma:",
        "speaker_recognition": "🎭 Reconocimiento de Hablantes",
        "embed_subtitle": "🎬 Incrustar Subtítulo en Video",
        "start_transcription": "🎯 Iniciar Transcripción",
        "cancel": "⛔ Cancelar",
        "history": "📜 Historial",
        "transcribing": "🔄 Transcribiendo...",
        "loading_model": "⏳ Cargando modelo...",
        
        # Actions
        "copy": "📋 Copiar",
        "save": "💾 Guardar",
        "export": "📤 Exportar",
        "search": "🔍 Buscar",
        "clear": "🗑️ Limpiar",
        "translate": "🌐 Traducir",
        "close": "Cerrar",
        
        # Status
        "ready": "Listo",
        "ready_to_transcribe": "Listo para transcribir",
        "file_selected": "Archivo seleccionado:",
        "transcription_completed": "Completado en",
        "transcription_cancelled": "Transcripción cancelada por el usuario",
        "cancelling": "Cancelando transcripción...",
        "text_copied": "¡Texto copiado al portapapeles!",
        "no_text_to_copy": "¡No hay texto para copiar!",
        "no_file_selected": "¡Seleccione un archivo primero!",
        "file_not_found": "¡Archivo no encontrado!",
        "select_file": "Seleccionar Archivo de Audio/Video",
        "file_saved": "Archivo guardado:",
        "no_text_to_save": "¡No hay texto para guardar!",
        "confirm": "Confirmar",
        "clear_transcription_confirm": "¿Desea limpiar la transcripción actual?",
        "transcription_cleared": "Transcripción limpiada",
        "settings_restored": "Configuraciones del usuario restauradas",
        "settings_saved": "Configuraciones del usuario guardadas",
        
        # Analysis
        "analysis_options": "Opciones de Análisis",
        "sentiment_analysis": "Análisis de Sentimiento",
        "entity_extraction": "Extracción de Entidades",
        "keywords": "Palabras clave",
        "auto_summary": "Resumen Automático",
        "topic_identification": "Identificación de Temas",
        "analyze_transcription": "🧠 Analizar Transcripción",
        "chat_with_ai": "💬 Chat con IA",
        "analyzing": "Analizando transcripción con IA...",
        "no_transcription_for_analysis": "¡Haga una transcripción primero!",
        "empty_transcription": "¡El texto de la transcripción está vacío!",
        
        # Settings
        "hardware_settings": "Configuración de Hardware",
        "device": "Dispositivo:",
        "workers": "Workers:",
        "vram_usage": "Uso VRAM:",
        "gpu_info": "🎮 Información de GPU",
        "optimize_gpu": "⚡ Optimizar GPU",
        "cache_settings": "Configuración de Caché",
        "clear_model_cache": "🗑️ Limpiar Caché de Modelos",
        "clear_gpu_cache": "🧹 Limpiar Caché GPU",
        "system_info": "Información del Sistema",
        
        # Batch
        "files_in_queue": "📁 Archivos en Cola",
        "add_files": "➕ Agregar Archivos",
        "add_folder": "📂 Agregar Carpeta",
        "remove_selected": "🗑️ Eliminar Seleccionados",
        "clear_list": "🧹 Limpiar Lista",
        "batch_settings": "⚙️ Configuración del Lote",
        "diarization": "Diarización",
        "progress": "📊 Progreso",
        "start_processing": "▶️ Iniciar Procesamiento",
        "cancel_processing": "⏹️ Cancelar",
        "export_all": "📤 Exportar Todos",
        "ready_to_process": "Listo para procesar",
        "processing": "Procesando...",
        "drop_hint": "💡 Arrastre archivos o carpetas aquí",
        
        # Streaming
        "recording_settings": "🎤 Configuración de Grabación",
        "audio_device": "Dispositivo:",
        "start_recording": "🔴 Iniciar Grabación",
        "stop_and_transcribe": "⏹️ Detener y Transcribir",
        "ready_to_record": "Listo para grabar",
        "recording": "Grabando... Hable al micrófono",
        "processing_transcription": "Procesando transcripción...",
        "transcription_done": "¡Transcripción completada!",
        "use_transcription": "✅ Usar Transcripción",
        
        # Errors
        "error": "Error",
        "warning": "Aviso",
        "info": "Info",
        "success": "Éxito",
    },
}

AVAILABLE_LANGUAGES = {
    "pt": "Português",
    "en": "English",
    "es": "Español",
}


class I18n:
    """Gerenciador de internacionalização"""
    
    def __init__(self, lang: str = "pt"):
        self._lang = lang if lang in TRANSLATIONS else "pt"
    
    @property
    def lang(self) -> str:
        return self._lang
    
    def set_language(self, lang: str):
        """Define o idioma da interface"""
        if lang in TRANSLATIONS:
            self._lang = lang
            logger.info(f"Idioma da interface alterado para: {lang}")
        else:
            logger.warning(f"Idioma não suportado: {lang}")
    
    def t(self, key: str) -> str:
        """Retorna a tradução para a chave dada"""
        translations = TRANSLATIONS.get(self._lang, TRANSLATIONS["pt"])
        result = translations.get(key)
        if result is None:
            # Fallback para português
            result = TRANSLATIONS["pt"].get(key, key)
        return result
    
    def get_available_languages(self) -> dict:
        """Retorna idiomas disponíveis"""
        return AVAILABLE_LANGUAGES.copy()


# Instância global
_i18n = None

def get_i18n(lang: str = "pt") -> I18n:
    """Retorna instância global de i18n"""
    global _i18n
    if _i18n is None:
        _i18n = I18n(lang)
    return _i18n
