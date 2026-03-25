#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 Waveform Widget - Speech Scribe Pro V3
Visualização da forma de onda do áudio com posição de reprodução
"""

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient

from speech_scribe.utils.logger import logger


class _WaveformLoader(QThread):
    """Thread para carregar waveform sem bloquear a UI"""
    loaded = pyqtSignal(object, float)  # (samples_array, duration)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            import warnings
            import librosa
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="PySoundFile failed")
                warnings.filterwarnings("ignore", message="librosa.core.audio.__audioread_load")
                y, sr = librosa.load(self.file_path, sr=8000, mono=True)
            duration = len(y) / sr

            target_points = min(2000, len(y))
            if len(y) > target_points:
                chunks = np.array_split(y, target_points)
                samples = np.array([np.max(np.abs(c)) for c in chunks])
            else:
                samples = np.abs(y)

            max_val = np.max(samples)
            if max_val > 0:
                samples = samples / max_val

            self.loaded.emit(samples, duration)
        except ImportError:
            self.error.emit("librosa não disponível")
        except Exception as e:
            self.error.emit(str(e))


class WaveformWidget(QWidget):
    """Widget que renderiza a forma de onda de um arquivo de áudio"""
    
    position_clicked = pyqtSignal(float)  # Posição em segundos onde o usuário clicou
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        
        self._samples = None  # Array numpy normalizado
        self._duration = 0.0  # Duração em segundos
        self._position = 0.0  # Posição atual em segundos
        self._is_loaded = False
        self._loader = None
        
        # Cores
        self._wave_color = QColor("#0078d4")
        self._wave_played_color = QColor("#00b4d8")
        self._position_color = QColor("#ff6b6b")
        self._bg_color = QColor("#2d2d2d")
        self._text_color = QColor("#888888")
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def load_file(self, file_path: str):
        """Carrega e processa arquivo de áudio em thread separada"""
        self._is_loaded = False
        self.update()

        self._loader = _WaveformLoader(file_path)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.error.connect(self._on_load_error)
        self._loader.start()

    def _on_loaded(self, samples, duration):
        """Callback quando waveform foi carregado"""
        self._samples = samples
        self._duration = duration
        self._is_loaded = True
        self._position = 0.0
        self.update()
        logger.info(f"Waveform carregado: {self._duration:.1f}s, {len(self._samples)} pontos")

    def _on_load_error(self, error_msg: str):
        """Callback quando carregamento falha"""
        logger.warning(f"Waveform: {error_msg}")
        self._is_loaded = False
    
    def set_position(self, seconds: float):
        """Atualiza a posição atual de reprodução"""
        self._position = seconds
        self.update()
    
    def set_colors(self, wave: str, played: str, bg: str):
        """Permite alterar as cores (para temas)"""
        self._wave_color = QColor(wave)
        self._wave_played_color = QColor(played)
        self._bg_color = QColor(bg)
        self.update()
    
    def paintEvent(self, event):
        """Renderiza a forma de onda"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        mid_y = h / 2
        
        # Fundo
        painter.fillRect(0, 0, w, h, self._bg_color)
        
        if not self._is_loaded or self._samples is None or len(self._samples) == 0:
            # Sem dados: mostrar texto placeholder
            painter.setPen(QPen(self._text_color))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Carregue um arquivo para ver a forma de onda")
            painter.end()
            return
        
        num_samples = len(self._samples)
        position_fraction = self._position / self._duration if self._duration > 0 else 0
        position_x = int(position_fraction * w)
        
        # Desenhar barras da waveform
        bar_width = max(1, w / num_samples)
        
        for i in range(num_samples):
            x = int(i * w / num_samples)
            amplitude = self._samples[i]
            bar_h = amplitude * (mid_y - 2)
            
            # Cor: já tocado vs não tocado
            if x < position_x:
                color = self._wave_played_color
            else:
                color = self._wave_color
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            
            # Barra espelhada (cima e baixo)
            bw = max(1, int(bar_width) - 1)
            painter.drawRect(x, int(mid_y - bar_h), bw, int(bar_h * 2))
        
        # Linha de posição
        if position_fraction > 0:
            pen = QPen(self._position_color, 2)
            painter.setPen(pen)
            painter.drawLine(position_x, 0, position_x, h)
        
        # Timestamp da posição
        if self._position > 0:
            painter.setPen(QPen(self._text_color))
            pos_str = f"{int(self._position // 60):02d}:{int(self._position % 60):02d}"
            painter.drawText(position_x + 4, 14, pos_str)
        
        painter.end()
    
    def mousePressEvent(self, event):
        """Permite clicar para ir para uma posição"""
        if self._is_loaded and self._duration > 0:
            fraction = event.position().x() / self.width()
            fraction = max(0.0, min(1.0, fraction))
            seconds = fraction * self._duration
            self._position = seconds
            self.position_clicked.emit(seconds)
            self.update()
    
    def clear(self):
        """Limpa a waveform"""
        self._samples = None
        self._duration = 0.0
        self._position = 0.0
        self._is_loaded = False
        self.update()
