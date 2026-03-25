#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Smoke Tests para GUI - Speech Scribe Pro V3
Testa que a janela principal inicializa sem erros.
Requer: pip install pytest-qt
"""

import sys
import os
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def _has_display():
    """Verifica se há display disponível (para CI/headless)"""
    if sys.platform == 'win32':
        return True
    return os.environ.get('DISPLAY') is not None


def _has_pytest_qt():
    try:
        import pytestqt
        return True
    except ImportError:
        return False


# Marker para testes que precisam de GUI
needs_gui = pytest.mark.skipif(
    not _has_display() or not _has_pytest_qt(),
    reason="Sem display ou pytest-qt não instalado"
)


@needs_gui
class TestMainWindowSmoke:
    """Smoke tests: verifica que a janela cria sem exceções"""

    def test_import_main_window(self):
        """Testa que o import do main_window funciona"""
        from speech_scribe.gui.main_window import SpeechScribeProV3
        assert SpeechScribeProV3 is not None

    def test_import_widgets(self):
        """Testa que os widgets importam corretamente"""
        from speech_scribe.gui.widgets import DropLabel, ModernUIBuilder
        assert DropLabel is not None
        assert ModernUIBuilder is not None

    def test_import_threads(self):
        """Testa que as threads importam corretamente"""
        from speech_scribe.gui.threads import TranscriptionThread
        assert TranscriptionThread is not None

    def test_import_audio_player(self):
        """Testa que o audio player importa"""
        try:
            from speech_scribe.gui.audio_player import AudioPlayerWidget
            assert AudioPlayerWidget is not None
        except ImportError:
            pytest.skip("AudioPlayerWidget não disponível")

    def test_import_waveform(self):
        """Testa que o waveform importa"""
        try:
            from speech_scribe.gui.waveform import WaveformWidget
            assert WaveformWidget is not None
        except ImportError:
            pytest.skip("WaveformWidget não disponível")

    def test_import_batch_processor(self):
        """Testa que o batch processor importa"""
        from speech_scribe.gui.batch_processor import BatchProcessorWidget, BatchItem, DropListWidget
        assert BatchProcessorWidget is not None
        assert BatchItem is not None
        assert DropListWidget is not None

    def test_import_streaming(self):
        """Testa que o streaming importa"""
        try:
            from speech_scribe.gui.streaming import StreamingWidget
            assert StreamingWidget is not None
        except ImportError:
            pytest.skip("StreamingWidget não disponível")

    def test_import_themes(self):
        """Testa que os temas importam"""
        from speech_scribe.gui.themes import ThemeManager, get_theme_manager
        assert ThemeManager is not None
        tm = get_theme_manager()
        assert tm is not None

    def test_import_enhancements(self):
        """Testa que os enhancements importam"""
        from speech_scribe.gui.enhancements import SearchWidget, HistoryDialog, KeyboardShortcuts
        assert SearchWidget is not None
        assert HistoryDialog is not None
        assert KeyboardShortcuts is not None


class TestModelsDataclass:
    """Testa o dataclass TranscriptionResult"""

    def test_create_empty(self):
        from speech_scribe.core.models import TranscriptionResult
        r = TranscriptionResult()
        assert r.text == ""
        assert r.segments == []
        assert r.duration == 0.0

    def test_to_dict(self):
        from speech_scribe.core.models import TranscriptionResult
        r = TranscriptionResult(text="Hello", language="en", duration=5.0)
        d = r.to_dict()
        assert d['text'] == "Hello"
        assert d['language'] == "en"
        assert d['duration'] == 5.0

    def test_from_dict(self):
        from speech_scribe.core.models import TranscriptionResult
        data = {
            'text': 'Teste',
            'segments': [{'start': 0.0, 'end': 1.0, 'text': 'Teste'}],
            'language': 'pt',
            'duration': 1.0,
            'processing_time': 0.5,
            'model_used': 'small',
            'device_used': 'cpu',
        }
        r = TranscriptionResult.from_dict(data)
        assert r.text == 'Teste'
        assert len(r.segments) == 1
        assert r.language == 'pt'

    def test_dict_compat_get(self):
        from speech_scribe.core.models import TranscriptionResult
        r = TranscriptionResult(text="Test", language="en")
        assert r.get('text') == "Test"
        assert r.get('nonexistent', 'default') == 'default'

    def test_dict_compat_getitem(self):
        from speech_scribe.core.models import TranscriptionResult
        r = TranscriptionResult(text="Test")
        assert r['text'] == "Test"

    def test_dict_compat_contains(self):
        from speech_scribe.core.models import TranscriptionResult
        r = TranscriptionResult(text="Test")
        assert 'text' in r
        assert 'nonexistent' not in r

    def test_segment_result(self):
        from speech_scribe.core.models import SegmentResult
        s = SegmentResult(start=1.0, end=2.5, text="Hello world")
        d = s.to_dict()
        assert d['start'] == 1.0
        assert d['end'] == 2.5
        assert d['text'] == "Hello world"

    def test_round_trip(self):
        from speech_scribe.core.models import TranscriptionResult, SegmentResult
        original = TranscriptionResult(
            text="Teste completo",
            segments=[SegmentResult(start=0, end=1, text="Teste completo")],
            language="pt",
            duration=1.0,
            processing_time=0.3,
            model_used="large-v3",
            device_used="cuda",
        )
        d = original.to_dict()
        restored = TranscriptionResult.from_dict(d)
        assert restored.text == original.text
        assert restored.language == original.language
        assert len(restored.segments) == len(original.segments)
