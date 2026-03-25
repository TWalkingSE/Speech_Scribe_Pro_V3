#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📦 Models - Speech Scribe Pro V3
Dataclasses tipadas para resultados de transcrição e análise
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SegmentResult:
    """Segmento individual de transcrição"""
    start: float = 0.0
    end: float = 0.0
    text: str = ""
    speaker: str = ""
    words: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'speaker': self.speaker,
            'words': self.words,
        }


@dataclass
class PerformanceMetrics:
    """Métricas de performance da transcrição"""
    chars_per_second: float = 0.0
    audio_duration: float = 0.0
    realtime_factor: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'chars_per_second': self.chars_per_second,
            'audio_duration': self.audio_duration,
            'realtime_factor': self.realtime_factor,
        }


@dataclass
class HardwareInfo:
    """Informações do hardware usado na transcrição"""
    device: str = "cpu"
    gpu_name: str = "N/A"
    beam_size: int = 5
    best_of: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device': self.device,
            'gpu_name': self.gpu_name,
            'beam_size': self.beam_size,
            'best_of': self.best_of,
        }


@dataclass
class TranscriptionResult:
    """Resultado tipado de uma transcrição completa"""
    text: str = ""
    segments: List[SegmentResult] = field(default_factory=list)
    language: str = ""
    duration: float = 0.0
    processing_time: float = 0.0
    model_used: str = ""
    device_used: str = ""
    diarization_enabled: bool = False
    speaker_stats: Optional[Dict[str, Any]] = None
    speaker_segments: Optional[list] = None
    hardware_info: Optional[HardwareInfo] = None
    performance_metrics: Optional[PerformanceMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (compatível com código existente)"""
        d = {
            'text': self.text,
            'segments': [s.to_dict() if isinstance(s, SegmentResult) else s for s in self.segments],
            'language': self.language,
            'duration': self.duration,
            'processing_time': self.processing_time,
            'model_used': self.model_used,
            'device_used': self.device_used,
            'diarization_enabled': self.diarization_enabled,
        }
        if self.speaker_stats:
            d['speaker_stats'] = self.speaker_stats
        if self.speaker_segments:
            d['speaker_segments'] = self.speaker_segments
        if self.hardware_info:
            d['hardware_info'] = self.hardware_info.to_dict()
        if self.performance_metrics:
            d['performance_metrics'] = self.performance_metrics.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionResult':
        """Cria TranscriptionResult a partir de um dicionário (backward compat)"""
        segments = []
        for seg in data.get('segments', []):
            if isinstance(seg, dict):
                segments.append(SegmentResult(
                    start=seg.get('start', 0.0),
                    end=seg.get('end', 0.0),
                    text=seg.get('text', ''),
                    speaker=seg.get('speaker', ''),
                    words=seg.get('words', []),
                ))
            else:
                segments.append(seg)

        hw = data.get('hardware_info')
        hw_info = HardwareInfo(**hw) if isinstance(hw, dict) else None

        pm = data.get('performance_metrics')
        perf = PerformanceMetrics(**pm) if isinstance(pm, dict) else None

        return cls(
            text=data.get('text', ''),
            segments=segments,
            language=data.get('language', ''),
            duration=data.get('duration', 0.0),
            processing_time=data.get('processing_time', 0.0),
            model_used=data.get('model_used', ''),
            device_used=data.get('device_used', ''),
            diarization_enabled=data.get('diarization_enabled', False),
            speaker_stats=data.get('speaker_stats'),
            speaker_segments=data.get('speaker_segments'),
            hardware_info=hw_info,
            performance_metrics=perf,
        )

    # --- Acesso compatível com dict para backward compatibility ---
    def get(self, key: str, default=None):
        """Permite usar result.get('text') como um dict"""
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str):
        """Permite usar result['text'] como um dict"""
        return self.to_dict()[key]

    def __contains__(self, key: str):
        """Permite usar 'text' in result"""
        return key in self.to_dict()


__all__ = [
    'SegmentResult',
    'PerformanceMetrics',
    'HardwareInfo',
    'TranscriptionResult',
]
