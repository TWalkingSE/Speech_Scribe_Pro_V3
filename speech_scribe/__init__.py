"""
🎙️ Speech Scribe Pro V3
Aplicativo de transcrição de áudio/vídeo com IA avançada
Versão 3.0.0 - Arquitetura Modular
"""

# Carregar variáveis do .env ANTES de qualquer outra importação
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

__version__ = "3.0.0"
__author__ = "Speech Scribe Team"

# IMPORTANTE: Importar torch ANTES de PyQt6 no Windows.
# PyQt6 carrega DLLs Qt que conflitam com c10.dll do torch CUDA.
# Importar torch primeiro garante que suas DLLs sejam carregadas corretamente.
try:
    import torch
except Exception:
    pass

# Silenciar warning do torchcodec (pyannote.audio) - não afeta funcionalidade
import warnings
warnings.filterwarnings("ignore", message="torchcodec", category=UserWarning)
warnings.filterwarnings("ignore", module="pyannote.audio.core.io")

# Importações principais para facilitar o uso
from speech_scribe.core import (
    AppConfig,
    ModernHardwareDetector,
    IntelligentTranscriptionEngine,
    SpeakerDiarization,
    SmartAnalyzer,
)

from speech_scribe.gui import SpeechScribeProV3

__all__ = [
    '__version__',
    'AppConfig',
    'ModernHardwareDetector',
    'IntelligentTranscriptionEngine',
    'SpeakerDiarization',
    'SmartAnalyzer',
    'SpeechScribeProV3',
]
