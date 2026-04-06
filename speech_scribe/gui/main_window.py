#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎙️ Speech Scribe Pro V3 - Main Window
Janela principal da aplicação de transcrição
Arquitetura modular - importa dos módulos do pacote speech_scribe
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QTabWidget, QGroupBox, QLabel, QPushButton, QComboBox, QCheckBox,
        QTextEdit, QLineEdit, QProgressBar, QFileDialog, QMessageBox,
        QApplication, QSpinBox, QSlider, QScrollArea, QTableWidget,
        QTableWidgetItem, QHeaderView, QProgressDialog, QDialog,
        QListWidget, QListWidgetItem
    )
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QTextCursor, QKeySequence, QShortcut
    PyQt6_available = True
except ImportError as e:
    import traceback
    with open("pyqt6_import_error.txt", "w") as f: f.write(traceback.format_exc())
    PyQt6_available = False

from speech_scribe.core.config import AppConfig
from speech_scribe.core.hardware import ModernHardwareDetector
from speech_scribe.core.transcription import IntelligentTranscriptionEngine
from speech_scribe.core.diarization import SpeakerDiarization
from speech_scribe.core.analysis import SmartAnalyzer
from speech_scribe.core.dependencies import SmartDependencyManager
from speech_scribe.core.settings import get_user_settings
from speech_scribe.core.version_checker import check_for_updates, get_update_message
from speech_scribe.core.i18n import get_i18n
from speech_scribe.utils.logger import logger

# Importar módulos de melhorias
try:
    from speech_scribe.core.history import TranscriptionHistory, get_history
    from speech_scribe.core.presets import PresetType, QualityPreset, PRESETS, get_preset_manager
    ENHANCEMENTS_AVAILABLE = True
except ImportError:
    ENHANCEMENTS_AVAILABLE = False
    logger.info("Módulos de melhorias não disponíveis")

# Importar exportadores
try:
    from speech_scribe.core.exporters import (
        TXTExporter, JSONExporter, SRTExporter, VTTExporter, DOCXExporter,
        ExportResult
    )
    EXPORTERS_AVAILABLE = True
except (ImportError, Exception):
    EXPORTERS_AVAILABLE = False
    logger.info("Módulos de exportação avançada não disponíveis")

# Importar novos módulos de melhorias
try:
    from speech_scribe.core.translator import TranscriptionTranslator, SUPPORTED_LANGUAGES
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    SUPPORTED_LANGUAGES = {}

try:
    from speech_scribe.gui.themes import get_theme_manager
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False

# Importar embutidor de legendas
try:
    from speech_scribe.core.subtitle_embedder import (
        is_video_file, check_ffmpeg, embed_subtitle_from_transcription
    )
    SUBTITLE_EMBEDDER_AVAILABLE = True
except ImportError:
    SUBTITLE_EMBEDDER_AVAILABLE = False

if PyQt6_available:
    from speech_scribe.gui.widgets import DropLabel, ModernUIBuilder
    from speech_scribe.gui.threads import TranscriptionThread, AnalysisThread
    
    # Importar módulos opcionais de GUI
    try:
        from speech_scribe.gui.audio_player import AudioPlayerWidget
        AUDIO_PLAYER_AVAILABLE = True
    except ImportError:
        AUDIO_PLAYER_AVAILABLE = False
    
    try:
        from speech_scribe.gui.waveform import WaveformWidget
        WAVEFORM_AVAILABLE = True
    except ImportError:
        WAVEFORM_AVAILABLE = False
        
    try:
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        BATCH_AVAILABLE = True
    except ImportError:
        BATCH_AVAILABLE = False
        
    try:
        from speech_scribe.gui.streaming import StreamingWidget, PYAUDIO_AVAILABLE
        STREAMING_AVAILABLE = True
    except ImportError:
        STREAMING_AVAILABLE = False
        PYAUDIO_AVAILABLE = False

    class SpeechScribeProV3(QMainWindow):
        """Aplicação principal modernizada"""

        def __init__(self):
            super().__init__()
            self.config = AppConfig()
            self.hardware = ModernHardwareDetector()
            self.engine = IntelligentTranscriptionEngine(self.config, self.hardware)
            self.analyzer = SmartAnalyzer()
            self.ui_builder = ModernUIBuilder(self.config)
            self.diarization = SpeakerDiarization()

            self.current_file = None
            self.transcription_result = None
            self.speaker_segments = None
            self._is_cancelled = False

            # Melhorias: Histórico e Presets
            if ENHANCEMENTS_AVAILABLE:
                self.history = get_history()
                self.preset_manager = get_preset_manager()
            else:
                self.history = None
                self.preset_manager = None

            # Busca no texto
            self.search_matches = []
            self.current_search_index = -1

            # Novos módulos: Tradutor e Temas
            self.translator = TranscriptionTranslator() if TRANSLATOR_AVAILABLE else None
            self.theme_manager = get_theme_manager() if THEMES_AVAILABLE else None
            self.current_theme = 'light'

            # Configurações persistentes do usuário
            self.user_settings = get_user_settings()

            # Internacionalização
            self.i18n = get_i18n(self.user_settings.get_interface_language())

            self.init_ui()
            self._connect_events()
            self._setup_shortcuts()
            self._restore_user_settings()

            # Verificar status do Ollama na inicialização
            QTimer.singleShot(1000, self._check_ollama_status)

            # Verificar atualizações (3s delay para não atrasar inicialização)
            QTimer.singleShot(3000, self._check_for_updates)

            logger.info(f"Speech Scribe Pro V3 iniciado | {self.hardware.get_device_info()}")

        # ================================
        # UI INITIALIZATION
        # ================================

        def init_ui(self):
            """Inicializa interface moderna"""
            self.setWindowTitle(f"{self.config.app_name} | Hardware: {self.hardware.get_device_info()}")
            self.setGeometry(100, 100, 1200, 800)
            self.setMinimumSize(800, 600)

            # Aplicar tema moderno
            self.setStyleSheet(self.ui_builder.theme)

            # Widget central
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            # Layout principal
            main_layout = QVBoxLayout(central_widget)

            # Cabeçalho
            header = self._create_header()
            main_layout.addWidget(header)

            # Área principal com tabs
            tab_widget = QTabWidget()

            # Tab 1: Transcrição
            transcription_tab = self._create_transcription_tab()
            tab_widget.addTab(transcription_tab, self.i18n.t("tab_transcription"))

            # Tab 2: Análise
            analysis_tab = self._create_analysis_tab()
            tab_widget.addTab(analysis_tab, self.i18n.t("tab_analysis"))

            # Tab 3: Configurações
            settings_tab = self._create_settings_tab()
            tab_widget.addTab(settings_tab, self.i18n.t("tab_settings"))

            # Tab 4: Processamento em Lote
            if BATCH_AVAILABLE:
                batch_tab = self._create_batch_tab()
                tab_widget.addTab(batch_tab, self.i18n.t("tab_batch"))

            # Tab 5: Microfone/Streaming
            if STREAMING_AVAILABLE:
                streaming_tab = self._create_streaming_tab()
                tab_widget.addTab(streaming_tab, self.i18n.t("tab_microphone"))

            main_layout.addWidget(tab_widget)

            # Status bar moderna
            self._create_status_bar()

        def _create_header(self) -> QWidget:
            """Cria cabeçalho moderno"""
            header = QWidget()
            header.setMaximumHeight(80)
            layout = QHBoxLayout(header)

            # Logo/Título
            title_label = QLabel(f"🎙️ {self.config.app_name}")
            title_label.setStyleSheet("""
                font-size: 24px;
                font-weight: bold;
                color: #0078d4;
                padding: 10px;
            """)

            # Informações do sistema
            sys_info = QLabel(self.hardware.get_device_info())
            sys_info.setStyleSheet("""
                color: #888888;
                font-size: 12px;
                padding: 10px;
            """)

            layout.addWidget(title_label)
            layout.addStretch()
            layout.addWidget(sys_info)

            # Botão de tema (Dark/Light)
            if THEMES_AVAILABLE:
                self.theme_btn = QPushButton("🌙 Tema Escuro")
                self.theme_btn.setToolTip("Alternar entre tema claro e escuro")
                self.theme_btn.setMaximumWidth(120)
                layout.addWidget(self.theme_btn)

            return header

        def _create_transcription_tab(self) -> QWidget:
            """Cria aba de transcrição"""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Seletor de arquivo - guardar referências diretamente
            file_selector = self.ui_builder.create_file_selector(self)
            layout.addWidget(file_selector)
            self.file_edit = file_selector.file_edit
            self.select_btn = file_selector.select_btn
            self.drop_label = file_selector.drop_label

            # Configurações de transcrição
            config_group = QGroupBox("Configurações de Transcrição")
            config_layout = QGridLayout(config_group)

            # Preset de qualidade
            config_layout.addWidget(QLabel("Preset:"), 0, 0)
            self.preset_combo = QComboBox()
            if self.preset_manager:
                self.preset_combo.addItems(self.preset_manager.get_preset_names())
                self.preset_combo.setCurrentText("⚖️ Balanceado")
            else:
                self.preset_combo.addItems(["Balanceado", "Rápido", "Máxima Qualidade"])
            self.preset_combo.setToolTip("Perfis pré-configurados para diferentes cenários")
            config_layout.addWidget(self.preset_combo, 0, 1)

            # Modelo
            config_layout.addWidget(QLabel("Modelo:"), 0, 2)
            self.model_combo = QComboBox()
            self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v2", "large-v3"])

            # Selecionar automaticamente o modelo recomendado pelo hardware
            recommended_model = self.hardware.optimizations.get('recommended_model', 'small')
            model_index = self.model_combo.findText(recommended_model)
            if model_index >= 0:
                self.model_combo.setCurrentIndex(model_index)

            self.model_combo.setToolTip(f"Modelo recomendado para seu hardware: {recommended_model}")
            config_layout.addWidget(self.model_combo, 0, 3)

            # Idioma
            config_layout.addWidget(QLabel("Idioma:"), 1, 0)
            self.lang_combo = QComboBox()
            self.lang_combo.addItems(["auto", "pt", "en", "es", "fr", "de"])
            config_layout.addWidget(self.lang_combo, 1, 1)

            # Diarização (separação de vozes)
            self.diarization_check = QCheckBox("🎭 Reconhecimento de Oradores")
            self.diarization_check.setToolTip("Identifica diferentes oradores no áudio\nRequer token do Hugging Face")
            self.diarization_check.setEnabled(self.diarization.available)
            config_layout.addWidget(self.diarization_check, 1, 2)

            # Status da diarização
            diarization_status = QLabel()
            if self.diarization.available:
                diarization_status.setText("✅ Disponível")
                diarization_status.setStyleSheet("color: green; font-size: 11px;")
            else:
                diarization_status.setText("❌ Indisponível (verifique .env)")
                diarization_status.setStyleSheet("color: red; font-size: 11px;")
            config_layout.addWidget(diarization_status, 1, 3)

            # Embutir legenda em vídeo
            self.embed_subtitle_check = QCheckBox("🎬 Embutir Legenda no Vídeo")
            self.embed_subtitle_check.setToolTip(
                "Após transcrever um vídeo, embutir a legenda diretamente no arquivo.\n"
                "Requer FFmpeg instalado no sistema."
            )
            ffmpeg_ok = SUBTITLE_EMBEDDER_AVAILABLE and check_ffmpeg() if SUBTITLE_EMBEDDER_AVAILABLE else False
            self.embed_subtitle_check.setEnabled(ffmpeg_ok)
            config_layout.addWidget(self.embed_subtitle_check, 2, 0, 1, 2)

            # Status do FFmpeg
            ffmpeg_status = QLabel()
            if SUBTITLE_EMBEDDER_AVAILABLE and ffmpeg_ok:
                ffmpeg_status.setText("✅ FFmpeg disponível")
                ffmpeg_status.setStyleSheet("color: green; font-size: 11px;")
            else:
                ffmpeg_status.setText("❌ FFmpeg não encontrado")
                ffmpeg_status.setStyleSheet("color: red; font-size: 11px;")
            config_layout.addWidget(ffmpeg_status, 2, 2, 1, 2)

            # Botão de transcrição e histórico
            btn_layout = QHBoxLayout()
            self.transcribe_btn = QPushButton(self.i18n.t("start_transcription"))
            self.transcribe_btn.setMinimumHeight(40)
            btn_layout.addWidget(self.transcribe_btn)

            self.cancel_btn = QPushButton(self.i18n.t("cancel"))
            self.cancel_btn.setMinimumHeight(40)
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setStyleSheet("QPushButton { background-color: #c0392b; } QPushButton:hover { background-color: #e74c3c; }")
            btn_layout.addWidget(self.cancel_btn)

            self.history_btn = QPushButton(self.i18n.t("history"))
            self.history_btn.setMinimumHeight(40)
            self.history_btn.setToolTip("Ver transcrições anteriores (Ctrl+H)")
            btn_layout.addWidget(self.history_btn)

            self.queue_btn = QPushButton("📋 Fila")
            self.queue_btn.setMinimumHeight(40)
            self.queue_btn.setToolTip("Adicionar arquivos à fila de transcrição")
            self.queue_btn.clicked.connect(self._toggle_queue)
            btn_layout.addWidget(self.queue_btn)

            config_layout.addLayout(btn_layout, 3, 0, 1, 4)

            # Fila de transcrição (oculta por padrão)
            self.queue_widget = QWidget()
            queue_layout = QVBoxLayout(self.queue_widget)
            queue_layout.setContentsMargins(0, 0, 0, 0)

            queue_header = QHBoxLayout()
            queue_header.addWidget(QLabel("📋 Fila de Transcrição:"))
            self.queue_add_btn = QPushButton("➕ Adicionar")
            self.queue_add_btn.clicked.connect(self._queue_add_files)
            queue_header.addWidget(self.queue_add_btn)
            self.queue_clear_btn = QPushButton("🧹 Limpar")
            self.queue_clear_btn.clicked.connect(self._queue_clear)
            queue_header.addWidget(self.queue_clear_btn)
            self.queue_start_btn = QPushButton("▶️ Processar Fila")
            self.queue_start_btn.clicked.connect(self._queue_start)
            queue_header.addWidget(self.queue_start_btn)
            queue_header.addStretch()
            queue_layout.addLayout(queue_header)

            self.queue_list = QListWidget()
            self.queue_list.setMaximumHeight(120)
            self.queue_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
            queue_layout.addWidget(self.queue_list)

            self.queue_widget.hide()
            layout.addWidget(self.queue_widget)

            # Estado da fila
            self._transcription_queue = []
            self._queue_index = -1

            layout.addWidget(config_group)

            # Painel de progresso
            progress_panel = self.ui_builder.create_progress_panel(self)
            layout.addWidget(progress_panel)
            self.progress_bar = progress_panel.findChild(QProgressBar)
            self.status_label = progress_panel.findChildren(QLabel)[1]

            # Resultado da transcrição
            result_group = QGroupBox("Resultado da Transcrição")
            result_layout = QVBoxLayout(result_group)

            # Widget de busca (inicialmente oculto)
            self.search_widget = QWidget()
            search_layout = QHBoxLayout(self.search_widget)
            search_layout.setContentsMargins(5, 5, 5, 5)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Buscar no texto... (Ctrl+F)")
            search_layout.addWidget(self.search_input)

            self.search_results_label = QLabel("0/0")
            self.search_results_label.setMinimumWidth(50)
            search_layout.addWidget(self.search_results_label)

            search_prev_btn = QPushButton("◀")
            search_prev_btn.setMaximumWidth(30)
            search_prev_btn.clicked.connect(self._search_prev)
            search_layout.addWidget(search_prev_btn)

            search_next_btn = QPushButton("▶")
            search_next_btn.setMaximumWidth(30)
            search_next_btn.clicked.connect(self._search_next)
            search_layout.addWidget(search_next_btn)

            search_close_btn = QPushButton("✕")
            search_close_btn.setMaximumWidth(30)
            search_close_btn.clicked.connect(self._close_search)
            search_layout.addWidget(search_close_btn)

            self.search_widget.hide()
            result_layout.addWidget(self.search_widget)

            self.result_text = QTextEdit()
            self.result_text.setPlaceholderText("O resultado da transcrição aparecerá aqui...")
            result_layout.addWidget(self.result_text)

            # Botões de ação
            action_layout = QHBoxLayout()

            self.copy_btn = QPushButton(self.i18n.t("copy"))
            self.save_btn = QPushButton(self.i18n.t("save"))
            self.export_btn = QPushButton(self.i18n.t("export"))
            self.search_btn = QPushButton(self.i18n.t("search"))
            self.search_btn.setToolTip("Buscar no texto (Ctrl+F)")
            self.clear_btn = QPushButton(self.i18n.t("clear"))
            self.clear_btn.setToolTip("Limpar transcrição atual")

            action_layout.addWidget(self.copy_btn)
            action_layout.addWidget(self.save_btn)
            action_layout.addWidget(self.export_btn)
            action_layout.addWidget(self.search_btn)
            action_layout.addWidget(self.clear_btn)

            # Botão de tradução
            if TRANSLATOR_AVAILABLE:
                self.translate_btn = QPushButton(self.i18n.t("translate"))
                self.translate_btn.setToolTip("Traduzir transcrição para outro idioma")
                action_layout.addWidget(self.translate_btn)

            action_layout.addStretch()

            result_layout.addLayout(action_layout)

            # Player de áudio
            if AUDIO_PLAYER_AVAILABLE:
                self.audio_player = AudioPlayerWidget()
                result_layout.addWidget(self.audio_player)
            else:
                self.audio_player = None

            # Waveform
            if WAVEFORM_AVAILABLE:
                self.waveform = WaveformWidget()
                self.waveform.position_clicked.connect(self._on_waveform_clicked)
                result_layout.addWidget(self.waveform)
            else:
                self.waveform = None

            layout.addWidget(result_group)

            return tab

        def _create_analysis_tab(self) -> QWidget:
            """Cria aba de análise"""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Opções de análise básica (sem IA)
            options_group = QGroupBox("📊 Análise Básica (Local)")
            options_layout = QGridLayout(options_group)

            self.keywords_check = QCheckBox("Palavras-chave")
            self.summary_check = QCheckBox("Resumo Automático")
            self.entities_check = QCheckBox("Extração de Entidades")
            self.topics_check = QCheckBox("Identificação de Tópicos")
            self.sentiment_check = QCheckBox("Análise de Sentimento")

            options_layout.addWidget(self.keywords_check, 0, 0)
            options_layout.addWidget(self.summary_check, 0, 1)
            options_layout.addWidget(self.entities_check, 1, 0)
            options_layout.addWidget(self.topics_check, 1, 1)
            options_layout.addWidget(self.sentiment_check, 2, 0)

            # Opções Ollama
            ollama_group = QGroupBox("🤖 Análise com Ollama (IA Local)")
            ollama_layout = QVBoxLayout(ollama_group)

            self.use_ollama_check = QCheckBox("Usar análise Ollama")
            ollama_layout.addWidget(self.use_ollama_check)

            # Tipos de análise Ollama
            ollama_types_layout = QGridLayout()
            self.ollama_general_check = QCheckBox("Análise Geral")
            self.ollama_summary_check = QCheckBox("Resumo Inteligente")
            self.ollama_sentiment_check = QCheckBox("Análise de Sentimento")
            self.ollama_keywords_check = QCheckBox("Extração de Palavras-chave")
            self.ollama_correction_check = QCheckBox("Correção de Texto")
            self.ollama_reasoning_check = QCheckBox("Raciocínio Profundo")

            ollama_types_layout.addWidget(self.ollama_general_check, 0, 0)
            ollama_types_layout.addWidget(self.ollama_summary_check, 0, 1)
            ollama_types_layout.addWidget(self.ollama_sentiment_check, 1, 0)
            ollama_types_layout.addWidget(self.ollama_keywords_check, 1, 1)
            ollama_types_layout.addWidget(self.ollama_correction_check, 2, 0)
            ollama_types_layout.addWidget(self.ollama_reasoning_check, 2, 1)

            ollama_layout.addLayout(ollama_types_layout)

            # Seleção de modelo Ollama
            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("Modelo:"))
            self.ollama_model_combo = QComboBox()
            # Modelo Auto + modelos serão carregados dinamicamente
            self.ollama_model_combo.addItem("Auto (Melhor Disponível)")
            self.ollama_model_combo.setToolTip(
                "Selecione um modelo Ollama para análise.\n"
                "Clique em 🔄 para atualizar a lista de modelos disponíveis."
            )
            model_layout.addWidget(self.ollama_model_combo)

            self.refresh_ollama_btn = QPushButton("🔄")
            self.refresh_ollama_btn.setMaximumWidth(30)
            self.refresh_ollama_btn.setToolTip("Atualizar lista de modelos")
            model_layout.addWidget(self.refresh_ollama_btn)

            ollama_layout.addLayout(model_layout)

            # Status do Ollama
            self.ollama_status = QLabel("Status: Verificando...")
            self.ollama_status.setStyleSheet("color: #888888; font-size: 11px;")
            ollama_layout.addWidget(self.ollama_status)

            options_layout.addWidget(ollama_group, 3, 0, 1, 2)

            # Botões de análise
            buttons_layout = QHBoxLayout()

            self.analyze_btn = QPushButton("🧠 Analisar Transcrição")
            self.analyze_btn.setMinimumHeight(40)
            buttons_layout.addWidget(self.analyze_btn)

            self.chat_btn = QPushButton("💬 Chat com IA")
            self.chat_btn.setMinimumHeight(40)
            buttons_layout.addWidget(self.chat_btn)

            options_layout.addLayout(buttons_layout, 4, 0, 1, 2)

            layout.addWidget(options_group)

            # Área de chat (inicialmente oculta)
            self.chat_widget = QWidget()
            chat_layout = QVBoxLayout(self.chat_widget)

            chat_input_layout = QHBoxLayout()
            self.chat_input = QLineEdit()
            self.chat_input.setPlaceholderText("Faça uma pergunta sobre a transcrição...")
            chat_input_layout.addWidget(self.chat_input)

            self.send_btn = QPushButton("Enviar")
            chat_input_layout.addWidget(self.send_btn)

            chat_layout.addLayout(chat_input_layout)

            self.chat_history = QTextEdit()
            self.chat_history.setMaximumHeight(200)
            self.chat_history.setPlaceholderText("Histórico do chat aparecerá aqui...")
            chat_layout.addWidget(self.chat_history)

            self.chat_widget.setVisible(False)
            layout.addWidget(self.chat_widget)

            # Resultados da análise
            self.analysis_results = QTextEdit()
            self.analysis_results.setPlaceholderText("Os resultados da análise aparecerão aqui...")
            layout.addWidget(self.analysis_results)

            return tab

        def _create_settings_tab(self) -> QWidget:
            """Cria aba de configurações"""
            tab = QWidget()
            layout = QVBoxLayout(tab)

            # Configurações de hardware
            hw_group = QGroupBox("Configurações de Hardware")
            hw_layout = QGridLayout(hw_group)

            hw_layout.addWidget(QLabel("Dispositivo:"), 0, 0)
            device_combo = QComboBox()
            device_combo.addItems(["auto", "cpu", "cuda"])
            device_combo.setCurrentText(self.hardware.optimizations['device'])
            hw_layout.addWidget(device_combo, 0, 1)

            hw_layout.addWidget(QLabel("Workers:"), 1, 0)
            workers_spin = QSpinBox()
            workers_spin.setRange(1, 16)
            workers_spin.setValue(self.hardware.optimizations['num_workers'])
            hw_layout.addWidget(workers_spin, 1, 1)

            # Configurações específicas de GPU
            if self.hardware.info['cuda_functional']:
                # Seleção de GPU (multi-device)
                gpu_list = self.hardware.info.get('gpu_info', [])
                if len(gpu_list) > 1:
                    hw_layout.addWidget(QLabel("GPU:"), 2, 0)
                    self.gpu_device_combo = QComboBox()
                    self.gpu_device_combo.addItem("Auto (Melhor GPU)")
                    for gpu in gpu_list:
                        self.gpu_device_combo.addItem(
                            f"GPU {gpu['id']}: {gpu['name']} ({gpu['vram_total_gb']:.1f}GB)"
                        )
                    self.gpu_device_combo.currentIndexChanged.connect(self._on_gpu_device_changed)
                    hw_layout.addWidget(self.gpu_device_combo, 2, 1)
                    vram_row = 3
                else:
                    vram_row = 2

                hw_layout.addWidget(QLabel("Uso VRAM:"), vram_row, 0)

                self.gpu_memory_slider = QSlider(Qt.Orientation.Horizontal)
                self.gpu_memory_slider.setRange(30, 95)
                self.gpu_memory_slider.setValue(int(self.hardware.optimizations['gpu_memory_fraction'] * 100))
                self.gpu_memory_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                self.gpu_memory_slider.setTickInterval(10)

                self.gpu_memory_label = QLabel(f"{int(self.hardware.optimizations['gpu_memory_fraction'] * 100)}%")
                self.gpu_memory_label.setMinimumWidth(40)
                self.gpu_memory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                self.gpu_memory_slider.valueChanged.connect(self._update_vram_usage)

                gpu_layout = QHBoxLayout()
                gpu_layout.addWidget(self.gpu_memory_slider)
                gpu_layout.addWidget(self.gpu_memory_label)

                hw_layout.addLayout(gpu_layout, vram_row, 1)

            layout.addWidget(hw_group)

            # Informações detalhadas da GPU
            if self.hardware.info['cuda_functional']:
                gpu_group = QGroupBox("🎮 Informações da GPU")
                gpu_group_layout = QVBoxLayout(gpu_group)

                gpu_info = self.hardware.get_detailed_gpu_info()
                gpu_text = QTextEdit()
                gpu_text.setReadOnly(True)
                gpu_text.setMaximumHeight(150)

                primary_gpu = gpu_info['primary_gpu']
                gpu_details = f"""
🎯 GPU Primária: {primary_gpu['name']}
💾 VRAM: {primary_gpu['vram_total_gb']:.1f}GB total | {primary_gpu['vram_free_gb']:.1f}GB livre
🔧 Compute Capability: {primary_gpu['compute_capability']}
⚡ Score Performance: {primary_gpu['performance_score']:.2f}
🔢 Multiprocessors: {primary_gpu['multiprocessor_count']}

📊 Configurações Otimizadas:
   Modelo recomendado: {self.hardware.optimizations['recommended_model']}
   Batch size: {self.hardware.optimizations['batch_size']}
   Beam size: {self.hardware.optimizations['beam_size']}
   Compute type: {self.hardware.optimizations['compute_type']}
                """

                gpu_text.setPlainText(gpu_details.strip())
                gpu_group_layout.addWidget(gpu_text)

                # Botões de GPU
                gpu_buttons_layout = QHBoxLayout()

                optimize_gpu_btn = QPushButton("⚡ Otimizar GPU")
                optimize_gpu_btn.setToolTip("Limpar cache e otimizar memória da GPU")
                optimize_gpu_btn.clicked.connect(lambda: self.hardware.optimize_gpu_memory())
                gpu_buttons_layout.addWidget(optimize_gpu_btn)

                gpu_group_layout.addLayout(gpu_buttons_layout)
                layout.addWidget(gpu_group)

            # Configurações de cache
            cache_group = QGroupBox("Configurações de Cache")
            cache_layout_h = QHBoxLayout(cache_group)

            clear_cache_btn = QPushButton("🗑️ Limpar Cache de Modelos")
            clear_cache_btn.clicked.connect(self._clear_model_cache)
            cache_layout_h.addWidget(clear_cache_btn)

            clear_gpu_cache_btn = QPushButton("🧹 Limpar Cache GPU")
            clear_gpu_cache_btn.setEnabled(self.hardware.info['cuda_functional'])
            clear_gpu_cache_btn.clicked.connect(self._clear_gpu_cache)
            cache_layout_h.addWidget(clear_gpu_cache_btn)

            layout.addWidget(cache_group)

            # Informações do sistema
            info_group = QGroupBox("Informações do Sistema")
            info_layout_v = QVBoxLayout(info_group)

            info_text = QTextEdit()
            info_text.setReadOnly(True)
            info_text.setMaximumHeight(200)

            dep_manager = SmartDependencyManager()
            missing_deps = dep_manager.get_missing_dependencies()

            cuda_status = "❌ Não disponível"
            if self.hardware.info['cuda_available']:
                if self.hardware.info['cuda_functional']:
                    cuda_status = f"✅ Funcional ({self.hardware.info['cuda_devices']} GPU(s))"
                else:
                    cuda_status = "⚠️ Detectado mas não funcional"

            system_info = f"""
🖥️ Hardware:
   CPU: {self.hardware.info['cpu_count']} cores
   RAM: {self.hardware.info['memory_gb']:.1f} GB
   CUDA: {cuda_status}

⚙️ Otimizações Ativas:
   Dispositivo: {self.hardware.optimizations['device'].upper()}
   Workers: {self.hardware.optimizations['num_workers']}
   Tipo de cálculo: {self.hardware.optimizations['compute_type']}
   Modelo recomendado: {self.hardware.optimizations['recommended_model']}

📦 Dependências:
   Status: {'✅ Todas instaladas' if not missing_deps else f'❌ {len(missing_deps)} ausentes'}
   Ausentes: {', '.join(missing_deps) if missing_deps else 'Nenhuma'}
            """

            info_text.setPlainText(system_info.strip())
            info_layout_v.addWidget(info_text)

            layout.addWidget(info_group)

            # Configurações de Interface
            ui_group = QGroupBox("🌍 Idioma da Interface")
            ui_layout = QHBoxLayout(ui_group)
            ui_layout.addWidget(QLabel("Idioma:"))
            self.ui_language_combo = QComboBox()
            self.ui_language_combo.addItems(["pt - Português", "en - English", "es - Español"])
            self.ui_language_combo.setToolTip("Altera o idioma da interface (requer reiniciar)")
            ui_layout.addWidget(self.ui_language_combo)
            ui_layout.addStretch()
            layout.addWidget(ui_group)

            layout.addStretch()

            return tab

        def _create_status_bar(self):
            """Cria barra de status moderna"""
            status_bar = self.statusBar()
            status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border-top: 1px solid #555555;
                }
            """)

            # Status principal
            self.status_message = QLabel("Pronto")
            status_bar.addWidget(self.status_message)

            # Informações permanentes
            permanent_info = QLabel(f"V{self.config.version} | {self.hardware.get_device_info()}")
            status_bar.addPermanentWidget(permanent_info)

        def _create_batch_tab(self) -> QWidget:
            """Cria aba de processamento em lote"""
            self.batch_widget = BatchProcessorWidget(self.engine, self.diarization)
            return self.batch_widget

        def _create_streaming_tab(self) -> QWidget:
            """Cria aba de streaming/microfone"""
            self.streaming_widget = StreamingWidget(self.engine)
            self.streaming_widget.transcription_ready.connect(self._on_streaming_transcription)
            return self.streaming_widget

        def _on_streaming_transcription(self, text: str):
            """Callback quando transcrição do microfone está pronta"""
            self.result_text.setPlainText(text)
            self.status_message.setText("Transcrição do microfone recebida")

        # ================================
        # EVENT CONNECTIONS (direct references, no findChildren)
        # ================================

        def _connect_events(self):
            """Configura eventos da interface usando referências diretas"""
            try:
                self.select_btn.clicked.connect(self.select_file)
                self.drop_label.file_dropped.connect(self._on_file_dropped)
                self.transcribe_btn.clicked.connect(self.start_transcription)
                self.cancel_btn.clicked.connect(self._cancel_transcription)
                self.copy_btn.clicked.connect(self._copy_text)
                self.save_btn.clicked.connect(self._save_file)
                self.export_btn.clicked.connect(self._export_file)
                self.search_btn.clicked.connect(self._toggle_search)
                self.clear_btn.clicked.connect(self._clear_transcription)
                self.search_input.textChanged.connect(self._on_search_text_changed)
                self.search_input.returnPressed.connect(self._search_next)
                self.analyze_btn.clicked.connect(self._start_analysis)
                self.refresh_ollama_btn.clicked.connect(self._refresh_ollama_models)
                self.chat_btn.clicked.connect(self._start_chat_with_ai)
                self.send_btn.clicked.connect(self._send_chat_message)
                self.chat_input.returnPressed.connect(self._send_chat_message)
                self.history_btn.clicked.connect(self._show_history)

                if self.preset_manager:
                    self.preset_combo.currentTextChanged.connect(self._on_preset_changed)

                # Novos eventos
                if TRANSLATOR_AVAILABLE and hasattr(self, 'translate_btn'):
                    self.translate_btn.clicked.connect(self._translate_transcription)

                if THEMES_AVAILABLE and hasattr(self, 'theme_btn'):
                    self.theme_btn.clicked.connect(self._toggle_theme)

                logger.info("Eventos da interface conectados com sucesso")

            except Exception as e:
                logger.error(f"Erro ao conectar eventos: {e}")

        # ================================
        # FILE HANDLING
        # ================================

        def select_file(self):
            """Seleciona arquivo de áudio/vídeo"""
            try:
                formats = ' '.join(f'*{ext}' for ext in self.config.supported_formats)
                filename, _ = QFileDialog.getOpenFileName(
                    self,
                    "Selecionar Arquivo de Áudio/Vídeo",
                    "",
                    f"Arquivos de Mídia ({formats});;Todos os arquivos (*.*)"
                )

                if filename:
                    self.current_file = filename
                    self.file_edit.setText(filename)
                    self.status_label.setText(f"Arquivo selecionado: {Path(filename).name}")
                    self.transcribe_btn.setEnabled(True)
                    logger.info(f"Arquivo selecionado: {filename}")
                    
                    # Carregar no player de áudio
                    self._load_audio_player(filename)

            except Exception as e:
                logger.error(f"Erro ao selecionar arquivo: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao selecionar arquivo: {e}")

        def _on_file_dropped(self, file_path: str):
            """Processa arquivo arrastado e solto"""
            try:
                if not Path(file_path).exists():
                    QMessageBox.warning(self, "Aviso", "Arquivo não encontrado!")
                    return

                # Usar extensões centralizadas do config
                if not any(file_path.lower().endswith(ext) for ext in self.config.supported_formats):
                    QMessageBox.warning(self, "Aviso", "Formato de arquivo não suportado!")
                    return

                self.current_file = file_path
                self.file_edit.setText(file_path)
                self.status_label.setText(f"Arquivo recebido: {Path(file_path).name}")
                self.transcribe_btn.setEnabled(True)
                self.status_message.setText(f"✅ Arquivo carregado: {Path(file_path).name}")
                logger.info(f"Arquivo arrastado recebido: {file_path}")
                
                # Carregar no player de áudio
                self._load_audio_player(file_path)

            except Exception as e:
                logger.error(f"Erro ao processar arquivo arrastado: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao processar arquivo: {e}")

        # ================================
        # TRANSCRIPTION
        # ================================

        def _validate_audio_file(self, file_path: str) -> bool:
            """Valida se o arquivo é um áudio/vídeo válido antes de transcrever"""
            try:
                import warnings
                import librosa
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="PySoundFile failed")
                    warnings.filterwarnings("ignore", message="librosa.core.audio.__audioread_load")
                    duration = librosa.get_duration(path=file_path)
                if duration <= 0:
                    QMessageBox.warning(self, self.i18n.t("warning"),
                        "Arquivo de áudio inválido ou vazio (duração = 0).")
                    return False
                return True
            except Exception as e:
                logger.warning(f"Validação do arquivo falhou: {e}")
                reply = QMessageBox.question(
                    self, self.i18n.t("warning"),
                    f"Não foi possível validar o arquivo:\n{e}\n\nDeseja tentar transcrever mesmo assim?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                return reply == QMessageBox.StandardButton.Yes

        def start_transcription(self):
            """Inicia transcrição do arquivo"""
            try:
                if not self.current_file:
                    QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro!")
                    return

                if not Path(self.current_file).exists():
                    QMessageBox.critical(self, "Erro", "Arquivo não encontrado!")
                    return

                if not self._validate_audio_file(self.current_file):
                    return

                self._is_cancelled = False

                enable_diarization = (
                    self.diarization_check.isChecked() and
                    self.diarization.available
                )

                self.transcription_thread = TranscriptionThread(
                    self.current_file,
                    self.model_combo.currentText(),
                    self.lang_combo.currentText(),
                    self.engine,
                    self.diarization,
                    enable_diarization
                )

                self.transcription_thread.progress.connect(self._update_progress)
                self.transcription_thread.finished.connect(self._transcription_finished)
                self.transcription_thread.error.connect(self._transcription_error)
                self.transcription_thread.status.connect(self._update_status)
                self.transcription_thread.model_loading.connect(self._on_model_loading)

                # UI state during transcription
                self.transcribe_btn.setEnabled(False)
                self.transcribe_btn.setText("🔄 Transcrevendo...")
                self.cancel_btn.setEnabled(True)

                self.transcription_thread.start()
                logger.info(f"Transcrição iniciada: {self.current_file}")

            except Exception as e:
                logger.error(f"Erro ao iniciar transcrição: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao iniciar transcrição: {e}")

        def _cancel_transcription(self):
            """Cancela a transcrição em andamento de forma segura"""
            self._is_cancelled = True
            if hasattr(self, 'transcription_thread') and self.transcription_thread.isRunning():
                self.transcription_thread.cancel()
                self.status_label.setText("Cancelando transcrição...")
                self.cancel_btn.setEnabled(False)
                # Esperar thread finalizar sem bloquear UI por muito tempo
                if not self.transcription_thread.wait(5000):
                    # Só usa terminate como último recurso
                    logger.warning("Thread não respondeu ao cancel, forçando terminate")
                    self.transcription_thread.terminate()
                    self.transcription_thread.wait(2000)
            self._restore_transcription_ui()
            self.status_label.setText("Transcrição cancelada pelo usuário")
            logger.info("Transcrição cancelada pelo usuário")

        def _restore_transcription_ui(self):
            """Restaura o estado da UI após transcrição"""
            self.transcribe_btn.setEnabled(True)
            self.transcribe_btn.setText("🎯 Iniciar Transcrição")
            self.cancel_btn.setEnabled(False)

        def _on_model_loading(self, message: str):
            """Mostra indicador de carregamento de modelo"""
            if message:
                self.status_label.setText(f"⏳ {message}")
                self.transcribe_btn.setText("⏳ Carregando modelo...")
                QApplication.processEvents()
            else:
                self.transcribe_btn.setText("🔄 Transcrevendo...")

        def _update_progress(self, value):
            """Atualiza barra de progresso"""
            if not self._is_cancelled:
                self.progress_bar.setValue(value)

        def _update_status(self, message):
            """Atualiza mensagem de status"""
            if not self._is_cancelled:
                self.status_label.setText(message)
            logger.info(f"Status: {message}")

        def _transcription_finished(self, result):
            """Chamado quando transcrição termina"""
            if self._is_cancelled:
                return

            try:
                self.transcription_result = result

                if 'speaker_segments' in result:
                    self.speaker_segments = result['speaker_segments']

                # Formatar texto com informações de oradores
                if result.get('diarization_enabled', False) and 'segments' in result:
                    formatted_text = self._format_text_with_speakers(result['segments'])
                    self.result_text.setPlainText(formatted_text)

                    if 'speaker_stats' in result:
                        self._show_speaker_stats(result['speaker_stats'])
                else:
                    self.result_text.setPlainText(result['text'])

                self._restore_transcription_ui()

                status_msg = f"Concluído em {result.get('processing_time', 0):.1f}s"
                if result.get('diarization_enabled', False):
                    num_speakers = len(set(seg.get('speaker', '') for seg in result.get('segments', [])))
                    status_msg += f" | {num_speakers} oradores detectados"

                self.status_label.setText(status_msg)
                logger.info(f"Transcrição concluída: {len(result['text'])} caracteres")

                # Salvar no histórico
                self._save_to_history(result)

                # Embutir legenda no vídeo se solicitado
                if (self.embed_subtitle_check.isChecked() and 
                    self.current_file and 
                    SUBTITLE_EMBEDDER_AVAILABLE and
                    is_video_file(self.current_file)):
                    self._embed_subtitle_in_video(result)

            except Exception as e:
                logger.error(f"Erro ao processar resultado: {e}")

        def _format_text_with_speakers(self, segments):
            """Formata texto incluindo informações dos oradores"""
            try:
                formatted_lines = []
                current_speaker = None

                for segment in segments:
                    speaker = segment.get('speaker', 'SPEAKER_00')
                    text = segment.get('text', '').strip()
                    start = segment.get('start', 0)

                    if text:
                        if speaker != current_speaker:
                            if current_speaker is not None:
                                formatted_lines.append("")
                            formatted_lines.append(f"[{speaker}] ({start:.1f}s)")
                            current_speaker = speaker

                        formatted_lines.append(text)

                return "\n".join(formatted_lines)

            except Exception as e:
                logger.error(f"Erro ao formatar texto com oradores: {e}")
                return "\n".join(seg.get('text', '') for seg in segments)

        def _show_speaker_stats(self, speaker_stats):
            """Exibe estatísticas dos oradores em um diálogo"""
            try:
                if not speaker_stats:
                    return

                stats_dialog = QDialog(self)
                stats_dialog.setWindowTitle("📊 Estatísticas dos Oradores")
                stats_dialog.setModal(False)
                stats_dialog.resize(500, 400)

                dlg_layout = QVBoxLayout(stats_dialog)

                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels([
                    "Orador", "Segmentos", "Duração (min)", "Palavras", "Palavras/min"
                ])

                table.setRowCount(len(speaker_stats))
                for row, (speaker, stats) in enumerate(speaker_stats.items()):
                    table.setItem(row, 0, QTableWidgetItem(speaker))
                    table.setItem(row, 1, QTableWidgetItem(str(stats['segments_count'])))
                    table.setItem(row, 2, QTableWidgetItem(f"{stats['total_duration']/60:.1f}"))
                    table.setItem(row, 3, QTableWidgetItem(str(stats['total_words'])))
                    table.setItem(row, 4, QTableWidgetItem(f"{stats['words_per_minute']:.1f}"))

                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                dlg_layout.addWidget(table)

                close_btn = QPushButton("Fechar")
                close_btn.clicked.connect(stats_dialog.close)
                dlg_layout.addWidget(close_btn)

                stats_dialog.show()

            except Exception as e:
                logger.error(f"Erro ao mostrar estatísticas: {e}")

        def _transcription_error(self, error_msg):
            """Chamado quando há erro na transcrição"""
            if self._is_cancelled:
                return
            try:
                self._restore_transcription_ui()
                QMessageBox.critical(self, "Erro na Transcrição", error_msg)
                logger.error(f"Erro na transcrição: {error_msg}")
            except Exception as e:
                logger.error(f"Erro ao processar erro: {e}")

        def _embed_subtitle_in_video(self, result: dict):
            """Embutir legenda no vídeo após transcrição"""
            try:
                if not SUBTITLE_EMBEDDER_AVAILABLE:
                    return

                self.status_label.setText("Embutindo legenda no vídeo...")
                QApplication.processEvents()

                embed_result = embed_subtitle_from_transcription(
                    self.current_file,
                    result,
                    burn_in=True,
                    keep_srt=True,
                    progress_callback=lambda msg: self.status_label.setText(msg)
                )

                if embed_result.success:
                    self.status_label.setText(
                        f"Legenda embutida com sucesso! Arquivo: {Path(embed_result.output_path).name}"
                    )
                    QMessageBox.information(
                        self,
                        "Legenda Embutida",
                        f"Legenda embutida com sucesso!\n\n"
                        f"Vídeo: {embed_result.output_path}\n"
                        f"SRT: {embed_result.srt_path}"
                    )
                    logger.info(f"Legenda embutida: {embed_result.output_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Erro ao Embutir Legenda",
                        f"Não foi possível embutir a legenda:\n{embed_result.error}"
                    )
                    logger.error(f"Erro ao embutir legenda: {embed_result.error}")

            except Exception as e:
                logger.error(f"Erro ao embutir legenda: {e}")
                QMessageBox.warning(
                    self,
                    "Erro",
                    f"Erro ao embutir legenda no vídeo:\n{e}"
                )

        # ================================
        # TEXT ACTIONS
        # ================================

        def _copy_text(self):
            """Copia texto para área de transferência"""
            try:
                text = self.result_text.toPlainText()
                if text:
                    QApplication.clipboard().setText(text)
                    self.status_label.setText("Texto copiado para área de transferência!")
                    logger.info("Texto copiado para área de transferência")
                else:
                    QMessageBox.warning(self, "Aviso", "Nenhum texto para copiar!")
            except Exception as e:
                logger.error(f"Erro ao copiar texto: {e}")

        def _clear_transcription(self):
            """Limpa a transcrição atual"""
            try:
                if not self.result_text.toPlainText():
                    return

                reply = QMessageBox.question(
                    self,
                    "Confirmar",
                    "Deseja limpar a transcrição atual?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.result_text.clear()
                    self.transcription_result = None
                    self.speaker_segments = None
                    self.current_file = None
                    self.file_edit.clear()
                    self.progress_bar.setValue(0)
                    self.status_label.setText("Transcrição limpa")
                    logger.info("Transcrição limpa pelo usuário")

            except Exception as e:
                logger.error(f"Erro ao limpar transcrição: {e}")

        def _save_file(self):
            """Salva resultado em arquivo"""
            try:
                text = self.result_text.toPlainText()
                if not text:
                    QMessageBox.warning(self, "Aviso", "Nenhum texto para salvar!")
                    return

                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Salvar Transcrição",
                    f"transcricao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "Arquivo de Texto (*.txt);;Todos os arquivos (*.*)"
                )

                if filename:
                    Path(filename).write_text(text, encoding='utf-8')
                    self.status_label.setText(f"Arquivo salvo: {Path(filename).name}")
                    logger.info(f"Arquivo salvo: {filename}")

            except Exception as e:
                logger.error(f"Erro ao salvar arquivo: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo: {e}")

        def _export_file(self):
            """Exporta resultado em formato avançado usando exportadores modulares"""
            try:
                if not self.transcription_result:
                    QMessageBox.warning(self, "Aviso", "Nenhuma transcrição para exportar!")
                    return

                filter_str = "JSON (*.json);;TXT (*.txt)"
                if EXPORTERS_AVAILABLE:
                    filter_str = "JSON (*.json);;TXT (*.txt);;SRT (*.srt);;VTT (*.vtt);;DOCX (*.docx)"

                filename, selected_filter = QFileDialog.getSaveFileName(
                    self,
                    "Exportar Transcrição",
                    f"transcricao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    filter_str
                )

                if not filename:
                    return

                if EXPORTERS_AVAILABLE:
                    exporters = {
                        '.txt': TXTExporter(),
                        '.json': JSONExporter(),
                        '.srt': SRTExporter(),
                        '.vtt': VTTExporter(),
                        '.docx': DOCXExporter(),
                    }
                    ext = Path(filename).suffix.lower()
                    exporter = exporters.get(ext)
                    if exporter:
                        result = exporter.export(self.transcription_result, Path(filename))
                        if result.success:
                            self.status_label.setText(f"Exportado: {Path(filename).name}")
                            logger.info(f"Arquivo exportado via {exporter.format_name}: {filename}")
                        else:
                            QMessageBox.critical(self, "Erro", f"Falha na exportação: {result.error}")
                        return

                # Fallback para exportação básica
                if filename.endswith('.json'):
                    export_data = {
                        "metadata": {
                            "file": self.current_file,
                            "timestamp": datetime.now().isoformat(),
                            "model": self.model_combo.currentText(),
                            "language": self.lang_combo.currentText()
                        },
                        "transcription": self.transcription_result
                    }
                    Path(filename).write_text(
                        json.dumps(export_data, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
                else:
                    Path(filename).write_text(
                        self.transcription_result['text'],
                        encoding='utf-8'
                    )

                self.status_label.setText(f"Exportado: {Path(filename).name}")
                logger.info(f"Arquivo exportado: {filename}")

            except Exception as e:
                logger.error(f"Erro ao exportar arquivo: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao exportar arquivo: {e}")

        # ================================
        # ANALYSIS
        # ================================

        def _start_analysis(self):
            """Inicia análise da transcrição em thread separada"""
            try:
                if not self.transcription_result:
                    QMessageBox.warning(self, "Aviso", "Faça uma transcrição primeiro!")
                    return

                transcription_text = self.transcription_result.get('text', '')
                if not transcription_text.strip():
                    QMessageBox.warning(self, "Aviso", "Texto da transcrição está vazio!")
                    return

                # Coletar análises básicas selecionadas
                basic_analyses = []
                if self.sentiment_check.isChecked():
                    basic_analyses.append('sentiment')
                if self.entities_check.isChecked():
                    basic_analyses.append('entities')
                if self.keywords_check.isChecked():
                    basic_analyses.append('keywords')
                if self.summary_check.isChecked():
                    basic_analyses.append('summary')
                if self.topics_check.isChecked():
                    basic_analyses.append('topics')

                # Coletar tipos de análise Ollama selecionados
                ollama_types = []
                if self.use_ollama_check.isChecked():
                    if self.ollama_general_check.isChecked():
                        ollama_types.append('general')
                    if self.ollama_summary_check.isChecked():
                        ollama_types.append('summary')
                    if self.ollama_sentiment_check.isChecked():
                        ollama_types.append('sentiment')
                    if self.ollama_keywords_check.isChecked():
                        ollama_types.append('keywords')
                    if self.ollama_correction_check.isChecked():
                        ollama_types.append('correction')
                    if self.ollama_reasoning_check.isChecked():
                        ollama_types.append('reasoning')

                if not basic_analyses and not ollama_types:
                    QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma opção de análise!")
                    return

                # Modelo Ollama selecionado
                selected_model = None
                if ollama_types:
                    model_text = self.ollama_model_combo.currentText()
                    if model_text != "Auto (Melhor Disponível)":
                        selected_model = model_text

                # Configurar progress dialog
                self.analysis_progress = QProgressDialog(
                    "Analisando transcrição com IA...", "Cancelar", 0, 100, self
                )
                self.analysis_progress.setWindowModality(Qt.WindowModality.WindowModal)
                self.analysis_progress.setAutoClose(False)
                self.analysis_progress.setAutoReset(False)
                self.analysis_progress.show()
                self.analysis_progress.setValue(5)

                # Desabilitar botão durante análise
                self.analyze_btn.setEnabled(False)

                # Iniciar thread de análise
                self.analysis_thread = AnalysisThread(
                    self.analyzer, transcription_text,
                    selected_model, ollama_types, basic_analyses
                )
                self.analysis_thread.progress.connect(self.analysis_progress.setValue)
                self.analysis_thread.status.connect(
                    lambda msg: self.analysis_progress.setLabelText(msg)
                )
                self.analysis_thread.finished.connect(self._on_analysis_finished)
                self.analysis_thread.error.connect(self._on_analysis_error)
                self.analysis_progress.canceled.connect(self._on_analysis_canceled)
                self.analysis_thread.start()

            except Exception as e:
                logger.error(f"Erro ao iniciar análise: {e}")
                QMessageBox.critical(self, "Erro", f"Erro durante análise: {str(e)}")

        def _on_analysis_finished(self, results):
            """Callback quando análise termina com sucesso"""
            self.analyze_btn.setEnabled(True)
            if hasattr(self, 'analysis_progress') and self.analysis_progress:
                self.analysis_progress.setValue(100)
                self.analysis_progress.close()
            self._display_analysis_results(results)
            logger.info("Análise com IA concluída com sucesso")

        def _on_analysis_error(self, error_msg):
            """Callback quando análise falha"""
            self.analyze_btn.setEnabled(True)
            if hasattr(self, 'analysis_progress') and self.analysis_progress:
                self.analysis_progress.close()
            QMessageBox.critical(self, "Erro", f"Erro durante análise: {error_msg}")

        def _on_analysis_canceled(self):
            """Callback quando análise é cancelada"""
            if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
                self.analysis_thread.terminate()
                self.analysis_thread.wait(2000)
            self.analyze_btn.setEnabled(True)
            logger.info("Análise cancelada pelo usuário")

        def _display_analysis_results(self, results: Dict[str, Any]):
            """Exibe resultados da análise em uma janela dedicada"""
            try:
                results_window = QDialog(self)
                results_window.setWindowTitle("🧠 Resultados da Análise com IA")
                results_window.setModal(True)
                results_window.resize(800, 600)

                dlg_layout = QVBoxLayout(results_window)

                scroll_area = QScrollArea()
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout(scroll_widget)

                # Análise de Sentimento
                if 'sentiment' in results:
                    group = QGroupBox("😊 Análise de Sentimento")
                    grp_layout = QVBoxLayout(group)
                    data = results['sentiment']
                    text = (f"Sentimento: {data.get('sentiment', 'N/A').title()}\n"
                            f"Pontuação: {data.get('score', 0):.2f}\n"
                            f"Palavras Positivas: {data.get('positive_words', 0)}\n"
                            f"Palavras Negativas: {data.get('negative_words', 0)}")
                    grp_layout.addWidget(QLabel(text))
                    scroll_layout.addWidget(group)

                # Palavras-chave
                if 'keywords' in results:
                    group = QGroupBox("🔑 Palavras-chave Principais")
                    grp_layout = QVBoxLayout(group)
                    data = results['keywords']
                    text = "Top 10 Palavras-chave:\n"
                    for word, count in data.get('top_keywords', []):
                        text += f"• {word}: {count} ocorrências\n"
                    text += f"\nTotal de palavras: {data.get('total_words', 0)}\n"
                    text += f"Palavras únicas: {data.get('unique_words', 0)}"
                    grp_layout.addWidget(QLabel(text))
                    scroll_layout.addWidget(group)

                # Entidades
                if 'entities' in results:
                    group = QGroupBox("🏷️ Entidades Identificadas")
                    grp_layout = QVBoxLayout(group)
                    data = results['entities']
                    text = ""
                    for entity_type, entities in data.items():
                        if entities:
                            text += f"{entity_type.title()}: {', '.join(entities)}\n"
                    if not text:
                        text = "Nenhuma entidade específica identificada."
                    grp_layout.addWidget(QLabel(text))
                    scroll_layout.addWidget(group)

                # Resumo
                if 'summary' in results:
                    group = QGroupBox("📄 Resumo Automático")
                    grp_layout = QVBoxLayout(group)
                    data = results['summary']
                    text = data.get('summary', 'Resumo não disponível')
                    text += f"\n\nTaxa de compressão: {data.get('compression_ratio', 0):.2%}"
                    lbl = QLabel(text)
                    lbl.setWordWrap(True)
                    grp_layout.addWidget(lbl)
                    scroll_layout.addWidget(group)

                # Tópicos
                if 'topics' in results:
                    group = QGroupBox("🎯 Tópicos Identificados")
                    grp_layout = QVBoxLayout(group)
                    data = results['topics']
                    text = f"Tópico principal: {data.get('main_topic', 'N/A')}\n\n"
                    text += "Pontuações por tópico:\n"
                    for topic, score in data.get('identified_topics', {}).items():
                        text += f"• {topic.title()}: {score} pontos\n"
                    grp_layout.addWidget(QLabel(text))
                    scroll_layout.addWidget(group)

                # Análise Ollama
                if 'ollama_analysis' in results:
                    group = QGroupBox("🤖 Análise Avançada (Ollama)")
                    grp_layout = QVBoxLayout(group)
                    data = results['ollama_analysis']
                    if 'error' not in data:
                        text = f"Modelo usado: {data.get('model_used', 'N/A')}\n\n"
                        analyses = data.get('analyses', {})
                        for analysis_type, analysis_result in analyses.items():
                            if 'error' not in analysis_result:
                                content = analysis_result.get('result', analysis_result.get('analysis', 'N/A'))
                                text += f"━━━ {analysis_type.upper()} ━━━\n{content}\n\n"
                            else:
                                text += f"━━━ {analysis_type.upper()} ━━━\nErro: {analysis_result['error']}\n\n"
                    else:
                        text = f"Erro na análise Ollama: {data['error']}"
                    lbl = QLabel(text)
                    lbl.setWordWrap(True)
                    grp_layout.addWidget(lbl)
                    scroll_layout.addWidget(group)

                scroll_area.setWidget(scroll_widget)
                scroll_area.setWidgetResizable(True)
                dlg_layout.addWidget(scroll_area)

                # Botões
                button_layout = QHBoxLayout()

                export_analysis_btn = QPushButton("💾 Exportar Análise")
                export_analysis_btn.clicked.connect(lambda: self._export_analysis_results(results))
                button_layout.addWidget(export_analysis_btn)

                close_btn = QPushButton("✖️ Fechar")
                close_btn.clicked.connect(results_window.close)
                button_layout.addWidget(close_btn)

                dlg_layout.addLayout(button_layout)
                results_window.exec()

            except Exception as e:
                logger.error(f"Erro ao exibir resultados: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao exibir resultados: {str(e)}")

        def _export_analysis_results(self, results: Dict[str, Any]):
            """Exporta resultados da análise para arquivo"""
            try:
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Salvar Análise",
                    f"analise_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "JSON Files (*.json);;Text Files (*.txt)"
                )

                if filename:
                    if filename.endswith('.json'):
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                    else:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"🧠 ANÁLISE COM IA - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                            f.write("=" * 60 + "\n\n")
                            for analysis_type, data in results.items():
                                f.write(f"{analysis_type.upper()}:\n")
                                f.write(str(data) + "\n\n")

                    QMessageBox.information(self, "Sucesso", f"Análise exportada para: {filename}")
                    logger.info(f"Análise exportada: {filename}")

            except Exception as e:
                logger.error(f"Erro ao exportar análise: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao exportar análise: {str(e)}")

        # ================================
        # OLLAMA / CHAT
        # ================================

        def _check_ollama_status(self):
            """Verifica status do Ollama na inicialização"""
            try:
                self.ollama_status.setText("Status: Verificando...")

                if self.analyzer.ollama_available:
                    try:
                        manager = self.analyzer.ollama_analyzer.manager
                        available_models = manager.get_available_models()

                        if available_models:
                            current_selection = self.ollama_model_combo.currentText()
                            saved_selection = self.user_settings.get_ollama_model()
                            self.ollama_model_combo.clear()
                            self.ollama_model_combo.addItem("Auto (Melhor Disponível)")
                            for model in available_models:
                                self.ollama_model_combo.addItem(model)

                            preferred_selection = current_selection
                            if not preferred_selection or preferred_selection == "Auto (Melhor Disponível)":
                                preferred_selection = saved_selection

                            preferred_index = self.ollama_model_combo.findText(preferred_selection)
                            if preferred_index >= 0:
                                self.ollama_model_combo.setCurrentIndex(preferred_index)

                            gpu_label = ""
                            if manager.gpu_info:
                                gpu_name = manager.gpu_info['name']
                                vram = manager.gpu_info['vram_total_gb']
                                gpu_label = f" | GPU: {gpu_name} ({vram:.0f}GB)"
                            
                            # Verificar status GPU dos modelos carregados
                            gpu_status = manager.get_model_gpu_status()
                            gpu_loaded_label = ""
                            if gpu_status.get("loaded"):
                                processor = gpu_status.get("processor", "")
                                context_length = gpu_status.get("context_length", "?")
                                gpu_loaded_label = f" | {processor} | ctx={context_length}"

                            self.ollama_status.setText(
                                f"Status: ✅ {len(available_models)} modelo(s){gpu_label}{gpu_loaded_label}"
                            )
                            logger.info(f"Ollama: {', '.join(available_models)}")
                        else:
                            self.ollama_status.setText("Status: ⚠️ Ollama instalado, mas sem modelos")
                    except Exception as e:
                        self.ollama_status.setText("Status: ❌ Erro ao conectar")
                        logger.error(f"Erro ao verificar modelos Ollama: {e}")
                else:
                    self.ollama_status.setText("Status: ❌ Ollama não disponível")

            except Exception as e:
                logger.error(f"Erro ao verificar status do Ollama: {e}")
                self.ollama_status.setText("Status: ❌ Erro na verificação")

        def _refresh_ollama_models(self):
            """Atualiza lista de modelos Ollama"""
            self._check_ollama_status()

        def _start_chat_with_ai(self):
            """Inicia chat com IA sobre a transcrição"""
            try:
                if not self.transcription_result:
                    QMessageBox.warning(self, "Aviso", "Nenhuma transcrição disponível para chat!")
                    return

                transcription_text = self.transcription_result.get('text', '')
                if not transcription_text.strip():
                    QMessageBox.warning(self, "Aviso", "Texto da transcrição está vazio!")
                    return

                is_visible = self.chat_widget.isVisible()
                self.chat_widget.setVisible(not is_visible)

                if not is_visible:
                    self.chat_history.append("🤖 Chat iniciado! Faça perguntas sobre a transcrição.")
                    self.chat_input.setFocus()

            except Exception as e:
                logger.error(f"Erro ao iniciar chat: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao iniciar chat: {str(e)}")

        def _send_chat_message(self):
            """Envia mensagem no chat com IA"""
            try:
                question = self.chat_input.text().strip()
                if not question:
                    return

                self.chat_input.clear()
                self.chat_history.append(f"👤 Você: {question}")

                if not self.transcription_result:
                    self.chat_history.append("🤖 IA: Nenhuma transcrição disponível.")
                    return

                transcription_text = self.transcription_result.get('text', '')

                selected_model = None
                model_text = self.ollama_model_combo.currentText()
                if model_text != "Auto (Melhor Disponível)":
                    selected_model = model_text

                self.chat_history.append("🤖 IA: Pensando...")
                QApplication.processEvents()

                if self.analyzer.ollama_available:
                    try:
                        response = self.analyzer.chat_with_ollama(transcription_text, question, selected_model)
                        self._remove_last_chat_line()
                        self.chat_history.append(f"🤖 IA: {response}")
                    except Exception as e:
                        self._remove_last_chat_line()
                        self.chat_history.append(f"🤖 IA: Erro ao processar pergunta: {str(e)}")
                        logger.error(f"Erro no chat Ollama: {e}")
                else:
                    self._remove_last_chat_line()
                    self.chat_history.append("🤖 IA: Ollama não está disponível. Instale e configure o Ollama.")

                scrollbar = self.chat_history.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")

        def _remove_last_chat_line(self):
            """Remove a última linha do chat (indicador de carregamento)"""
            cursor = self.chat_history.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()

        # ================================
        # SEARCH
        # ================================

        def _toggle_search(self):
            """Alterna visibilidade do widget de busca"""
            if self.search_widget.isVisible():
                self._close_search()
            else:
                self.search_widget.show()
                self.search_input.setFocus()
                self.search_input.selectAll()

        def _on_search_text_changed(self, query: str):
            """Busca texto quando query muda"""
            try:
                self.search_matches.clear()
                self.current_search_index = -1

                if not query:
                    self.search_results_label.setText("0/0")
                    return

                text = self.result_text.toPlainText().lower()
                query_lower = query.lower()

                start = 0
                while True:
                    pos = text.find(query_lower, start)
                    if pos == -1:
                        break
                    self.search_matches.append(pos)
                    start = pos + 1

                total = len(self.search_matches)
                if total > 0:
                    self.current_search_index = 0
                    self._goto_match(0, len(query))
                    self.search_results_label.setText(f"1/{total}")
                else:
                    self.search_results_label.setText("0/0")

            except Exception as e:
                logger.error(f"Erro na busca: {e}")

        def _search_next(self):
            """Vai para próxima ocorrência"""
            if self.search_matches:
                self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
                self._goto_match(self.current_search_index, len(self.search_input.text()))
                self.search_results_label.setText(
                    f"{self.current_search_index + 1}/{len(self.search_matches)}"
                )

        def _search_prev(self):
            """Vai para ocorrência anterior"""
            if self.search_matches:
                self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
                self._goto_match(self.current_search_index, len(self.search_input.text()))
                self.search_results_label.setText(
                    f"{self.current_search_index + 1}/{len(self.search_matches)}"
                )

        def _goto_match(self, index: int, query_len: int):
            """Vai para uma ocorrência específica"""
            if 0 <= index < len(self.search_matches):
                pos = self.search_matches[index]
                cursor = self.result_text.textCursor()
                cursor.setPosition(pos)
                cursor.setPosition(pos + query_len, QTextCursor.MoveMode.KeepAnchor)
                self.result_text.setTextCursor(cursor)
                self.result_text.ensureCursorVisible()

        def _close_search(self):
            """Fecha widget de busca"""
            self.search_widget.hide()
            self.search_input.clear()
            self.search_matches.clear()
            self.current_search_index = -1
            self.search_results_label.setText("0/0")

        # ================================
        # SHORTCUTS
        # ================================

        def _setup_shortcuts(self):
            """Configura atalhos de teclado"""
            try:
                QShortcut(QKeySequence("Ctrl+O"), self, self.select_file)
                QShortcut(QKeySequence("Ctrl+S"), self, self._save_file)
                QShortcut(QKeySequence("Ctrl+T"), self, self.start_transcription)
                QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search)
                QShortcut(QKeySequence("Ctrl+H"), self, self._show_history)
                QShortcut(QKeySequence("Ctrl+E"), self, self._export_file)
                QShortcut(QKeySequence("Escape"), self, self._close_search)
                QShortcut(QKeySequence("F3"), self, self._search_next)
                QShortcut(QKeySequence("Shift+F3"), self, self._search_prev)
                logger.info("Atalhos de teclado configurados")
            except Exception as e:
                logger.error(f"Erro ao configurar atalhos: {e}")

        # ================================
        # PRESETS
        # ================================

        def _on_preset_changed(self, preset_name: str):
            """Aplica configurações do preset selecionado"""
            try:
                if not self.preset_manager:
                    return

                preset = self.preset_manager.get_by_name(preset_name)
                if preset:
                    model_index = self.model_combo.findText(preset.model)
                    if model_index >= 0:
                        self.model_combo.setCurrentIndex(model_index)

                    lang_index = self.lang_combo.findText(preset.language)
                    if lang_index >= 0:
                        self.lang_combo.setCurrentIndex(lang_index)

                    self._current_preset = preset
                    logger.info(f"Preset aplicado: {preset_name}")
                    self.status_label.setText(f"Preset: {preset_name}")

            except Exception as e:
                logger.error(f"Erro ao aplicar preset: {e}")

        # ================================
        # HISTORY
        # ================================

        def _show_history(self):
            """Mostra diálogo de histórico"""
            try:
                if not self.history:
                    QMessageBox.information(self, "Info", "Histórico não disponível")
                    return

                from speech_scribe.gui.enhancements import HistoryDialog
                dialog = HistoryDialog(self.history, self)
                dialog.record_selected.connect(self._load_from_history)
                dialog.exec()

            except Exception as e:
                logger.error(f"Erro ao mostrar histórico: {e}")
                QMessageBox.warning(self, "Erro", f"Erro ao abrir histórico: {e}")

        def _load_from_history(self, record):
            """Carrega transcrição do histórico"""
            try:
                self.result_text.setPlainText(record.text)
                self.current_file = record.file_path
                self.file_edit.setText(record.file_path)
                self.status_label.setText(f"Carregado do histórico: {record.file_name}")
                logger.info(f"Transcrição carregada do histórico: {record.file_name}")
            except Exception as e:
                logger.error(f"Erro ao carregar do histórico: {e}")

        def _save_to_history(self, result: dict):
            """Salva transcrição no histórico"""
            try:
                if not self.history or not self.current_file:
                    return

                self.history.add(
                    file_path=self.current_file,
                    text=result.get('text', ''),
                    language=result.get('language', ''),
                    model=self.model_combo.currentText(),
                    duration_seconds=result.get('duration', 0),
                    processing_time=result.get('processing_time', 0)
                )
            except Exception as e:
                logger.error(f"Erro ao salvar no histórico: {e}")

        # ================================
        # SETTINGS ACTIONS
        # ================================

        def _on_gpu_device_changed(self, index: int):
            """Altera a GPU utilizada para transcrição"""
            try:
                gpu_list = self.hardware.info.get('gpu_info', [])
                if index == 0:
                    # Auto: usar a melhor GPU
                    if gpu_list:
                        best = max(gpu_list, key=lambda x: x['performance_score'])
                        device_index = best['id']
                    else:
                        device_index = 0
                else:
                    device_index = index - 1  # -1 porque index 0 é "Auto"

                self.hardware.optimizations['device_index'] = device_index
                gpu_name = gpu_list[device_index]['name'] if device_index < len(gpu_list) else "?"
                self.status_message.setText(f"GPU selecionada: {gpu_name}")
                logger.info(f"GPU alterada para device_index={device_index} ({gpu_name})")
            except Exception as e:
                logger.error(f"Erro ao alterar GPU: {e}")

        def _update_vram_usage(self, value):
            """Atualiza o uso de VRAM em tempo real"""
            try:
                if hasattr(self, 'gpu_memory_label'):
                    self.gpu_memory_label.setText(f"{value}%")

                memory_fraction = value / 100.0
                self.hardware.optimizations['gpu_memory_fraction'] = memory_fraction

                if self.hardware.info['cuda_functional']:
                    try:
                        self.hardware.optimize_gpu_memory()
                        logger.info(f"VRAM atualizada para {value}% ({memory_fraction:.2f})")
                        self.status_label.setText(f"VRAM configurada para {value}%")
                    except Exception as gpu_error:
                        logger.warning(f"Erro ao aplicar nova configuração de VRAM: {gpu_error}")

            except Exception as e:
                logger.error(f"Erro ao atualizar VRAM: {e}")

        def _clear_model_cache(self):
            """Limpa cache de modelos"""
            try:
                self.engine.model_cache.clear()
                self.status_message.setText("Cache de modelos limpo")
                logger.info("Cache de modelos limpo")
            except Exception as e:
                logger.error(f"Erro ao limpar cache: {e}")

        def _clear_gpu_cache(self):
            """Limpa cache da GPU"""
            try:
                import torch
                torch.cuda.empty_cache()
                self.status_message.setText("Cache da GPU limpo")
                logger.info("Cache da GPU limpo")
            except Exception as e:
                logger.error(f"Erro ao limpar cache GPU: {e}")

        def _translate_transcription(self):
            """Traduz a transcrição para outro idioma"""
            if not self.translator or not self.translator.available:
                QMessageBox.warning(self, "Aviso", "Módulo de tradução não disponível!")
                return

            if not self.transcription_result or not self.transcription_result.get('text'):
                QMessageBox.warning(self, "Aviso", "Nenhuma transcrição para traduzir!")
                return

            # Diálogo para selecionar idioma de destino
            from PyQt6.QtWidgets import QInputDialog
            
            languages = list(SUPPORTED_LANGUAGES.keys())
            language_names = [f"{code} - {name}" for code, name in SUPPORTED_LANGUAGES.items()]
            
            selected, ok = QInputDialog.getItem(
                self,
                "Traduzir Transcrição",
                "Selecione o idioma de destino:",
                language_names,
                0,
                False
            )
            
            if ok and selected:
                target_lang = selected.split(' - ')[0]
                
                progress = QProgressDialog("Traduzindo...", "Cancelar", 0, 0, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
                QApplication.processEvents()
                
                try:
                    translated_text = self.translator.translate_text(
                        self.transcription_result['text'],
                        source_lang=self.transcription_result.get('language', 'auto'),
                        target_lang=target_lang
                    )
                    
                    if translated_text:
                        self.result_text.setPlainText(translated_text)
                        self.status_message.setText(f"Traduzido para {SUPPORTED_LANGUAGES.get(target_lang, target_lang)}")
                        logger.info(f"Transcrição traduzida para {target_lang}")
                    else:
                        QMessageBox.warning(self, "Erro", "Falha na tradução!")
                        
                except Exception as e:
                    logger.error(f"Erro na tradução: {e}")
                    QMessageBox.critical(self, "Erro", f"Erro na tradução: {e}")
                finally:
                    progress.close()

        def _toggle_theme(self):
            """Alterna entre tema claro e escuro"""
            if not self.theme_manager:
                return

            new_theme = self.theme_manager.toggle_theme()
            self.current_theme = new_theme
            
            # Aplicar novo stylesheet
            stylesheet = self.theme_manager.get_stylesheet(new_theme)
            self.setStyleSheet(stylesheet)
            
            # Atualizar texto do botão
            if new_theme == 'dark':
                self.theme_btn.setText("☀️ Tema Claro")
            else:
                self.theme_btn.setText("🌙 Tema Escuro")
                
            self.status_message.setText(f"Tema alterado para {new_theme}")
            logger.info(f"Tema alterado para {new_theme}")

        # ================================
        # TRANSCRIPTION QUEUE
        # ================================

        def _toggle_queue(self):
            """Alterna visibilidade da fila de transcrição"""
            self.queue_widget.setVisible(not self.queue_widget.isVisible())

        def _queue_add_files(self):
            """Adiciona arquivos à fila"""
            formats = ' '.join(f'*{ext}' for ext in self.config.supported_formats)
            files, _ = QFileDialog.getOpenFileNames(
                self, "Adicionar à Fila", "",
                f"Arquivos de Mídia ({formats});;Todos os arquivos (*.*)"
            )
            for f in files:
                if f not in self._transcription_queue:
                    self._transcription_queue.append(f)
                    self.queue_list.addItem(f"⏳ {Path(f).name}")
            if files:
                self.queue_btn.setText(f"📋 Fila ({len(self._transcription_queue)})")

        def _queue_clear(self):
            """Limpa a fila"""
            self._transcription_queue.clear()
            self._queue_index = -1
            self.queue_list.clear()
            self.queue_btn.setText("📋 Fila")

        def _queue_start(self):
            """Inicia processamento sequencial da fila"""
            if not self._transcription_queue:
                QMessageBox.warning(self, "Aviso", "A fila está vazia!")
                return

            self._queue_index = 0
            self.queue_start_btn.setEnabled(False)
            self.queue_add_btn.setEnabled(False)
            self._queue_process_next()

        def _queue_process_next(self):
            """Processa o próximo item da fila"""
            if self._queue_index >= len(self._transcription_queue):
                # Fila concluída
                self.queue_start_btn.setEnabled(True)
                self.queue_add_btn.setEnabled(True)
                self.status_label.setText(f"Fila concluída: {len(self._transcription_queue)} arquivos")
                QMessageBox.information(self, "Fila Concluída",
                    f"Todos os {len(self._transcription_queue)} arquivos foram transcritos!")
                return

            file_path = self._transcription_queue[self._queue_index]

            # Atualizar UI da fila
            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if i < self._queue_index:
                    item.setText(f"✅ {Path(self._transcription_queue[i]).name}")
                elif i == self._queue_index:
                    item.setText(f"🔄 {Path(file_path).name}")
                else:
                    item.setText(f"⏳ {Path(self._transcription_queue[i]).name}")

            # Selecionar arquivo e iniciar transcrição
            self.current_file = file_path
            self.file_edit.setText(file_path)
            self._load_audio_player(file_path)
            self.status_label.setText(f"Fila [{self._queue_index + 1}/{len(self._transcription_queue)}]: {Path(file_path).name}")

            # Usar a lógica existente de transcrição
            self._is_cancelled = False
            enable_diarization = (
                self.diarization_check.isChecked() and
                self.diarization.available
            )

            self.transcription_thread = TranscriptionThread(
                file_path,
                self.model_combo.currentText(),
                self.lang_combo.currentText(),
                self.engine,
                self.diarization,
                enable_diarization
            )

            self.transcription_thread.progress.connect(self._update_progress)
            self.transcription_thread.finished.connect(self._queue_on_finished)
            self.transcription_thread.error.connect(self._queue_on_error)
            self.transcription_thread.status.connect(self._update_status)
            self.transcription_thread.model_loading.connect(self._on_model_loading)

            self.transcribe_btn.setEnabled(False)
            self.transcribe_btn.setText("🔄 Transcrevendo...")
            self.cancel_btn.setEnabled(True)

            self.transcription_thread.start()

        def _queue_on_finished(self, result):
            """Callback quando um item da fila termina"""
            if self._is_cancelled:
                return

            # Processar resultado normalmente
            self._transcription_finished(result)

            # Atualizar item da fila
            if 0 <= self._queue_index < self.queue_list.count():
                self.queue_list.item(self._queue_index).setText(
                    f"✅ {Path(self._transcription_queue[self._queue_index]).name}")

            # Próximo da fila
            self._queue_index += 1
            self._queue_process_next()

        def _queue_on_error(self, error_msg):
            """Callback quando um item da fila falha"""
            if self._is_cancelled:
                return

            logger.error(f"Erro na fila [{self._queue_index}]: {error_msg}")

            # Marcar como erro
            if 0 <= self._queue_index < self.queue_list.count():
                self.queue_list.item(self._queue_index).setText(
                    f"❌ {Path(self._transcription_queue[self._queue_index]).name}")

            self._restore_transcription_ui()

            # Continuar com próximo da fila
            self._queue_index += 1
            self._queue_process_next()

        def _check_for_updates(self):
            """Verifica se há atualizações disponíveis (em thread separada)"""
            from PyQt6.QtCore import QThread, pyqtSignal

            class UpdateChecker(QThread):
                update_found = pyqtSignal(dict)

                def run(self_thread):
                    try:
                        version_url = os.environ.get("SPEECH_SCRIBE_VERSION_URL", "")
                        update_info = check_for_updates(version_url)
                        if update_info:
                            self_thread.update_found.emit(update_info)
                    except Exception as e:
                        logger.debug(f"Verificação de atualização ignorada: {e}")

            def _on_update_found(update_info):
                msg = get_update_message(update_info)
                self.status_message.setText(f"🆕 Nova versão: v{update_info['new_version']}")
                QMessageBox.information(self, "Atualização Disponível", msg)

            self._update_checker = UpdateChecker()
            self._update_checker.update_found.connect(_on_update_found)
            self._update_checker.start()

        def _load_audio_player(self, file_path: str):
            """Carrega arquivo no player de áudio e waveform"""
            if self.audio_player:
                self.audio_player.load_file(file_path)
                # Sincronizar waveform com posição do player
                if self.waveform:
                    self.audio_player.on_position_changed_callback = self._sync_waveform_position
            if self.waveform:
                self.waveform.load_file(file_path)

        def _sync_waveform_position(self, seconds: float):
            """Sincroniza posição do waveform com o player"""
            if self.waveform:
                self.waveform.set_position(seconds)

        def _on_waveform_clicked(self, seconds: float):
            """Quando o usuário clica no waveform, pula para a posição"""
            if self.audio_player:
                self.audio_player.seek_to_time(seconds)

        # ================================
        # USER SETTINGS PERSISTENCE
        # ================================

        def _restore_user_settings(self):
            """Restaura configurações do usuário da sessão anterior"""
            try:
                s = self.user_settings

                # Modelo
                model_idx = self.model_combo.findText(s.get_model())
                if model_idx >= 0:
                    self.model_combo.setCurrentIndex(model_idx)

                # Idioma
                lang_idx = self.lang_combo.findText(s.get_language())
                if lang_idx >= 0:
                    self.lang_combo.setCurrentIndex(lang_idx)

                # Preset
                if self.preset_manager:
                    preset_idx = self.preset_combo.findText(s.get_preset())
                    if preset_idx >= 0:
                        self.preset_combo.setCurrentIndex(preset_idx)

                # Diarização
                if self.diarization.available:
                    self.diarization_check.setChecked(s.get_diarization_enabled())

                # Volume do player
                if self.audio_player:
                    self.audio_player.volume_slider.setValue(s.get_volume())

                # Tema
                saved_theme = s.get_theme()
                if saved_theme != self.current_theme and THEMES_AVAILABLE and self.theme_manager:
                    self.theme_manager.set_theme(saved_theme)
                    self.current_theme = saved_theme
                    self.setStyleSheet(self.theme_manager.get_stylesheet(saved_theme))
                    if hasattr(self, 'theme_btn'):
                        self.theme_btn.setText("☀️ Tema Claro" if saved_theme == 'dark' else "🌙 Tema Escuro")

                # Geometria da janela
                geometry = s.get_window_geometry()
                if geometry:
                    self.restoreGeometry(geometry)

                # Idioma da interface
                saved_lang = s.get_interface_language()
                lang_map = {"pt": 0, "en": 1, "es": 2}
                if saved_lang in lang_map and hasattr(self, 'ui_language_combo'):
                    self.ui_language_combo.setCurrentIndex(lang_map[saved_lang])

                logger.info("Configurações do usuário restauradas")

            except Exception as e:
                logger.warning(f"Erro ao restaurar configurações: {e}")

        def _save_user_settings(self):
            """Salva configurações do usuário para próxima sessão"""
            try:
                s = self.user_settings

                s.set_model(self.model_combo.currentText())
                s.set_language(self.lang_combo.currentText())
                s.set_preset(self.preset_combo.currentText())
                s.set_diarization_enabled(self.diarization_check.isChecked())
                s.set_theme(self.current_theme)

                if self.audio_player:
                    s.set_volume(self.audio_player.volume_slider.value())

                s.set_window_geometry(self.saveGeometry())

                if self.current_file:
                    s.set_last_directory(str(Path(self.current_file).parent))

                s.set_ollama_model(self.ollama_model_combo.currentText())

                # Idioma da interface
                if hasattr(self, 'ui_language_combo'):
                    lang_text = self.ui_language_combo.currentText()
                    lang_code = lang_text.split(" - ")[0] if " - " in lang_text else "pt"
                    s.set_interface_language(lang_code)

                s.sync()
                logger.info("Configurações do usuário salvas")

            except Exception as e:
                logger.warning(f"Erro ao salvar configurações: {e}")

        def closeEvent(self, event):
            """Salva configurações ao fechar a janela, confirma se transcrição ativa"""
            # Verificar se há transcrição em andamento
            if hasattr(self, 'transcription_thread') and self.transcription_thread.isRunning():
                reply = QMessageBox.question(
                    self, self.i18n.t("confirm"),
                    "Há uma transcrição em andamento.\nDeseja cancelar e sair?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                # Cancelar transcrição
                self.transcription_thread.cancel()
                self.transcription_thread.wait(3000)

            self._save_user_settings()
            # Parar player se estiver tocando
            if self.audio_player:
                self.audio_player.stop()
            super().closeEvent(event)

else:
    class SpeechScribeProV3:
        """Stub class - PyQt6 não disponível"""
        def __init__(self):
            raise ImportError("PyQt6 não está disponível. Instale com: pip install PyQt6")

        def show(self):
            pass


__all__ = ['SpeechScribeProV3']
