"""
Speech Scribe Pro V3 - Core Package
Módulos principais do sistema de transcrição
"""

from speech_scribe.core.config import AppConfig
from speech_scribe.core.dependencies import SmartDependencyManager
from speech_scribe.core.hardware import ModernHardwareDetector
from speech_scribe.core.transcription import IntelligentTranscriptionEngine
from speech_scribe.core.diarization import SpeakerDiarization
from speech_scribe.core.analysis import SmartAnalyzer


__all__ = [
    'AppConfig',
    'SmartDependencyManager',
    'ModernHardwareDetector',
    'IntelligentTranscriptionEngine',
    'SpeakerDiarization',
    'SmartAnalyzer',
]
