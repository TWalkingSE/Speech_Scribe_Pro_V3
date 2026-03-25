"""
Speech Scribe Pro V3 - GUI Package
Componentes da interface gráfica
"""

from speech_scribe.gui.widgets import DropLabel, ModernUIBuilder
from speech_scribe.gui.threads import TranscriptionThread
from speech_scribe.gui.main_window import SpeechScribeProV3

# Módulos opcionais de melhorias
try:
    from speech_scribe.gui.audio_player import AudioPlayerWidget
except ImportError:
    AudioPlayerWidget = None

try:
    from speech_scribe.gui.batch_processor import BatchProcessorWidget, BatchItem
except ImportError:
    BatchProcessorWidget = None
    BatchItem = None

try:
    from speech_scribe.gui.streaming import StreamingWidget
except ImportError:
    StreamingWidget = None

try:
    from speech_scribe.gui.themes import ThemeManager, get_theme_manager
except ImportError:
    ThemeManager = None
    get_theme_manager = None

__all__ = [
    'DropLabel',
    'ModernUIBuilder',
    'TranscriptionThread',
    'SpeechScribeProV3',
    'AudioPlayerWidget',
    'BatchProcessorWidget',
    'BatchItem',
    'StreamingWidget',
    'ThemeManager',
    'get_theme_manager',
]
