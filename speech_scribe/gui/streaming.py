#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎤 Streaming/Microphone - Speech Scribe Pro V3
Transcrição em tempo real de áudio do microfone
"""

import queue
import tempfile
import wave
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from speech_scribe.utils.logger import logger

# Verificar disponibilidade de pyaudio
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio não disponível. Instale com: pip install pyaudio")


class AudioRecorder(QThread):
    """Thread para gravação de áudio"""
    level_changed = pyqtSignal(int)  # Nível de áudio 0-100
    recording_stopped = pyqtSignal(str)  # Caminho do arquivo gravado
    error = pyqtSignal(str)
    
    def __init__(self, device_index: int = None, sample_rate: int = 16000):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = 1
        self.chunk_size = 1024
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        
        self._is_recording = False
        self._audio_queue = queue.Queue()
        self.output_path = None
        
    def run(self):
        """Grava áudio do microfone"""
        if not PYAUDIO_AVAILABLE:
            self.error.emit("PyAudio não está disponível")
            return
            
        try:
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            self._is_recording = True
            
            logger.info("Gravação iniciada")
            
            while self._is_recording:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Calcular nível de áudio
                    level = self._calculate_level(data)
                    self.level_changed.emit(level)
                    
                except Exception as e:
                    logger.warning(f"Erro ao ler áudio: {e}")
                    
            stream.stop_stream()
            stream.close()
            
            # Salvar arquivo ANTES de terminar PyAudio
            if frames:
                self.output_path = self._save_audio(frames, p)
                p.terminate()
                self.recording_stopped.emit(self.output_path)
                logger.info(f"Gravação salva: {self.output_path}")
            else:
                p.terminate()
                self.error.emit("Nenhum áudio gravado")
                
        except Exception as e:
            logger.error(f"Erro na gravação: {e}")
            self.error.emit(str(e))
            
    def stop_recording(self):
        """Para gravação"""
        self._is_recording = False
        
    def _calculate_level(self, data: bytes) -> int:
        """Calcula nível de áudio (0-100)"""
        import struct
        
        try:
            count = len(data) // 2
            shorts = struct.unpack(f"{count}h", data)
            
            # RMS
            sum_squares = sum(s * s for s in shorts)
            rms = (sum_squares / count) ** 0.5
            
            # Normalizar para 0-100
            level = min(100, int(rms / 327.67))
            return level
            
        except Exception:
            return 0
            
    def _save_audio(self, frames: list, p) -> str:
        """Salva áudio em arquivo temporário"""
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.wav', 
            delete=False,
            prefix='speech_scribe_rec_'
        )
        
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            
        return temp_file.name


class MicTranscriptionWorker(QThread):
    """Thread para transcrever áudio gravado do microfone sem bloquear a GUI"""
    transcription_done = pyqtSignal(str)   # Texto transcrito
    error = pyqtSignal(str)
    
    def __init__(self, engine, audio_path: str, model: str = "base", language: str = "auto"):
        super().__init__()
        self.engine = engine
        self.audio_path = audio_path
        self.model = model
        self.language = language
        
    def run(self):
        """Executa transcrição em thread separada"""
        try:
            model = self.engine.load_model(self.model)
            if not model:
                self.error.emit("Falha ao carregar modelo")
                return
            
            transcribe_kwargs = {
                'language': None if self.language == "auto" else self.language,
                'vad_filter': True,
                'word_timestamps': True,
                'beam_size': self.engine.hardware.optimizations['beam_size'],
                'best_of': self.engine.hardware.optimizations['best_of'],
                'condition_on_previous_text': False,
            }
            
            segments, info = model.transcribe(self.audio_path, **transcribe_kwargs)
            segments_list = list(segments)
            full_text = ' '.join([seg.text for seg in segments_list]).strip()
            
            if full_text:
                self.transcription_done.emit(full_text)
            else:
                self.error.emit("Nenhum texto detectado no áudio")
                
        except Exception as e:
            logger.error(f"Erro na transcrição do microfone: {e}")
            self.error.emit(str(e))
        finally:
            # Limpar arquivo temporário
            try:
                Path(self.audio_path).unlink()
            except Exception:
                pass


class StreamingWidget(QWidget):
    """Widget para transcrição de microfone em tempo real"""
    
    transcription_ready = pyqtSignal(str)  # Emitido quando transcrição está pronta
    
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.recorder = None
        self.is_recording = False
        
        self._init_ui()
        
    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout(self)
        
        # Status do PyAudio
        if not PYAUDIO_AVAILABLE:
            warning = QLabel("⚠️ PyAudio não disponível. Instale com: pip install pyaudio")
            warning.setStyleSheet("color: orange; padding: 10px;")
            layout.addWidget(warning)
            
        # Configurações
        config_group = QGroupBox("🎤 Configurações de Gravação")
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Dispositivo:"))
        self.device_combo = QComboBox()
        self._populate_devices()
        config_layout.addWidget(self.device_combo)
        
        config_layout.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["base", "small", "medium", "large-v2", "large-v3"])
        self.model_combo.setCurrentText("base")  # Modelo rápido para tempo real
        config_layout.addWidget(self.model_combo)
        
        config_layout.addWidget(QLabel("Idioma:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["auto", "pt", "en", "es", "fr", "de"])
        config_layout.addWidget(self.language_combo)
        
        config_layout.addStretch()
        layout.addWidget(config_group)
        
        # Nível de áudio
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("📊 Nível:"))
        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setTextVisible(False)
        self.level_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
            }
        """)
        level_layout.addWidget(self.level_bar, 1)
        layout.addLayout(level_layout)
        
        # Botões de controle
        control_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("🔴 Iniciar Gravação")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 15px 30px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.record_btn.setEnabled(PYAUDIO_AVAILABLE)
        
        self.stop_btn = QPushButton("⏹️ Parar e Transcrever")
        self.stop_btn.setEnabled(False)
        
        control_layout.addStretch()
        control_layout.addWidget(self.record_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Status
        self.status_label = QLabel("Pronto para gravar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Texto transcrito
        result_group = QGroupBox("📝 Transcrição")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("O texto transcrito aparecerá aqui...")
        self.result_text.setMinimumHeight(150)
        result_layout.addWidget(self.result_text)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Copiar")
        self.use_btn = QPushButton("✅ Usar Transcrição")
        self.clear_btn = QPushButton("🗑️ Limpar")
        
        action_layout.addWidget(self.copy_btn)
        action_layout.addWidget(self.use_btn)
        action_layout.addWidget(self.clear_btn)
        action_layout.addStretch()
        
        result_layout.addLayout(action_layout)
        layout.addWidget(result_group)
        
        # Conectar sinais
        self._connect_signals()
        
    def _populate_devices(self):
        """Popula combo de dispositivos de áudio"""
        self.device_combo.clear()
        self.device_combo.addItem("Padrão do Sistema", None)
        
        if not PYAUDIO_AVAILABLE:
            return
            
        try:
            p = pyaudio.PyAudio()
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    name = info['name']
                    self.device_combo.addItem(name, i)
                    
            p.terminate()
            
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos: {e}")
            
    def _connect_signals(self):
        """Conecta sinais"""
        self.record_btn.clicked.connect(self._toggle_recording)
        self.stop_btn.clicked.connect(self._stop_recording)
        self.copy_btn.clicked.connect(self._copy_text)
        self.use_btn.clicked.connect(self._use_transcription)
        self.clear_btn.clicked.connect(self._clear_text)
        
    def _toggle_recording(self):
        """Inicia/para gravação"""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
            
    def _start_recording(self):
        """Inicia gravação"""
        device_index = self.device_combo.currentData()
        
        self.recorder = AudioRecorder(device_index=device_index)
        self.recorder.level_changed.connect(self._on_level_changed)
        self.recorder.recording_stopped.connect(self._on_recording_stopped)
        self.recorder.error.connect(self._on_error)
        
        self.recorder.start()
        
        self.is_recording = True
        self.record_btn.setText("🔴 Gravando...")
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Gravando... Fale no microfone")
        
    def _stop_recording(self):
        """Para gravação e inicia transcrição"""
        if self.recorder:
            self.recorder.stop_recording()
            
        self.is_recording = False
        self.record_btn.setText("🔴 Iniciar Gravação")
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Processando transcrição...")
        
    def _on_level_changed(self, level: int):
        """Atualiza barra de nível"""
        self.level_bar.setValue(level)
        
    def _on_recording_stopped(self, audio_path: str):
        """Callback quando gravação para - inicia transcrição em thread separada"""
        self.status_label.setText("Transcrevendo áudio...")
        self.level_bar.setValue(0)
        
        # Transcrever áudio em thread separada para não bloquear a GUI
        self._transcription_worker = MicTranscriptionWorker(
            self.engine,
            audio_path,
            self.model_combo.currentText(),
            self.language_combo.currentText()
        )
        self._transcription_worker.transcription_done.connect(self._on_transcription_done)
        self._transcription_worker.error.connect(self._on_error)
        self._transcription_worker.start()
    
    def _on_transcription_done(self, text: str):
        """Callback quando transcrição do microfone termina com sucesso"""
        self.result_text.setPlainText(text)
        self.status_label.setText("Transcrição concluída!")
        logger.info("Transcrição de microfone concluída")
            
    def _on_error(self, error: str):
        """Callback de erro"""
        self.status_label.setText(f"Erro: {error}")
        self.is_recording = False
        self.record_btn.setText("🔴 Iniciar Gravação")
        self.stop_btn.setEnabled(False)
        self.level_bar.setValue(0)
        logger.error(f"Erro no streaming: {error}")
        
    def _copy_text(self):
        """Copia texto para clipboard"""
        from PyQt6.QtWidgets import QApplication
        text = self.result_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("Texto copiado!")
            
    def _clear_text(self):
        """Limpa texto da transcrição"""
        self.result_text.clear()
        self.status_label.setText("Pronto para gravar")

    def _use_transcription(self):
        """Emite sinal com transcrição para uso na aba principal"""
        text = self.result_text.toPlainText()
        if text:
            self.transcription_ready.emit(text)
            self.status_label.setText("Transcrição enviada para aba principal")
