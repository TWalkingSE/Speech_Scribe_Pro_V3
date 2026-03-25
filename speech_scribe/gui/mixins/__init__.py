"""
Mixins para a janela principal - Speech Scribe Pro V3
Cada mixin encapsula uma área funcional da interface
"""

from speech_scribe.gui.mixins.transcription_mixin import TranscriptionMixin

# TODO: Mixins planejados para implementação futura
# from speech_scribe.gui.mixins.analysis_mixin import AnalysisMixin
# from speech_scribe.gui.mixins.queue_mixin import QueueMixin
# from speech_scribe.gui.mixins.settings_mixin import SettingsMixin

__all__ = [
    'TranscriptionMixin',
]
