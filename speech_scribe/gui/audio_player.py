#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 Audio Player Widget - Speech Scribe Pro V3
Player de áudio integrado com sincronização de timestamps
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from speech_scribe.utils.logger import logger


class AudioPlayerWidget(QWidget):
    """Widget de player de áudio com controles e sincronização"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.duration = 0
        self.segments = []
        self.on_position_changed_callback = None
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Inicializa interface do player"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Botão Play/Pause
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.setToolTip("Play/Pause (Espaço)")
        
        # Botão Stop
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setToolTip("Parar")
        
        # Botões de skip
        self.back_btn = QPushButton()
        self.back_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.setToolTip("Voltar 5s")
        
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.forward_btn.setFixedSize(32, 32)
        self.forward_btn.setToolTip("Avançar 5s")
        
        # Slider de posição
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setToolTip("Posição do áudio")
        
        # Labels de tempo
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        
        # Slider de volume
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(80)
        self.volume_slider.setToolTip("Volume")
        
        # Volume icon
        self.volume_label = QLabel("🔊")
        
        # Layout
        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.back_btn)
        layout.addWidget(self.forward_btn)
        layout.addWidget(self.position_slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.volume_label)
        layout.addWidget(self.volume_slider)
        
    def _connect_signals(self):
        """Conecta sinais do player"""
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.stop)
        self.back_btn.clicked.connect(lambda: self.skip(-5000))
        self.forward_btn.clicked.connect(lambda: self.skip(5000))
        
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        
        # Inicializar volume (PyQt6: escala 0.0–1.0)
        self.audio_output.setVolume(0.7)
        
    def load_file(self, file_path: str):
        """Carrega arquivo de áudio/vídeo"""
        try:
            url = QUrl.fromLocalFile(file_path)
            self.player.setSource(url)
            logger.info(f"Áudio carregado: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar áudio: {e}")
            
    def set_segments(self, segments: list):
        """Define segmentos para sincronização"""
        self.segments = segments
        
    def toggle_play(self):
        """Alterna entre play e pause"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def stop(self):
        """Para reprodução"""
        self.player.stop()
        
    def skip(self, ms: int):
        """Pula posição em milissegundos"""
        new_pos = max(0, min(self.player.position() + ms, self.duration))
        self.player.setPosition(new_pos)
        
    def set_position(self, position: int):
        """Define posição do player"""
        self.player.setPosition(position)
        
    def set_volume(self, volume: int):
        """Define volume"""
        # PyQt6: QAudioOutput usa escala 0.0–1.0
        self.audio_output.setVolume(volume / 100.0)
        if volume == 0:
            self.volume_label.setText("🔇")
        elif volume < 30:
            self.volume_label.setText("🔈")
        elif volume < 70:
            self.volume_label.setText("🔉")
        else:
            self.volume_label.setText("🔊")
            
    def seek_to_time(self, seconds: float):
        """Vai para um timestamp específico em segundos"""
        self.player.setPosition(int(seconds * 1000))
        
    def _on_position_changed(self, position: int):
        """Callback quando posição muda"""
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self._update_time_label()
        
        # Callback externo para sincronização
        if self.on_position_changed_callback:
            self.on_position_changed_callback(position / 1000.0)
            
    def _on_duration_changed(self, duration: int):
        """Callback quando duração é conhecida"""
        self.duration = duration
        self.position_slider.setRange(0, duration)
        self._update_time_label()
        
    def _on_state_changed(self, state):
        """Callback quando estado muda"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            
    def _update_time_label(self):
        """Atualiza label de tempo"""
        pos = self.player.position()
        dur = self.duration
        
        pos_str = f"{pos // 60000:02d}:{(pos // 1000) % 60:02d}"
        dur_str = f"{dur // 60000:02d}:{(dur // 1000) % 60:02d}"
        
        self.time_label.setText(f"{pos_str} / {dur_str}")
        
    def get_current_segment_index(self) -> int:
        """Retorna índice do segmento atual baseado na posição"""
        if not self.segments:
            return -1
            
        current_time = self.player.position() / 1000.0
        
        for i, seg in enumerate(self.segments):
            if seg.get('start', 0) <= current_time <= seg.get('end', 0):
                return i
                
        return -1
