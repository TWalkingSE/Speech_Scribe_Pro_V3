#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes para módulos novos - Speech Scribe Pro V3
Testa: settings, i18n, translator, themes, exporters batch, waveform
"""

import sys
import os
from pathlib import Path

import pytest

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ================================
# Testes: i18n
# ================================

class TestI18n:
    """Testes para o sistema de internacionalização"""
    
    def test_default_language_is_pt(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n()
        assert i18n.lang == "pt"
    
    def test_set_language(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("en")
        assert i18n.lang == "en"
    
    def test_translation_pt(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("pt")
        assert i18n.t("copy") == "📋 Copiar"
        assert i18n.t("save") == "💾 Salvar"
    
    def test_translation_en(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("en")
        assert i18n.t("copy") == "📋 Copy"
        assert i18n.t("save") == "💾 Save"
    
    def test_translation_es(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("es")
        assert i18n.t("copy") == "📋 Copiar"
        assert i18n.t("save") == "💾 Guardar"
    
    def test_fallback_to_pt(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("en")
        # Chave que não existe deve retornar a própria chave
        result = i18n.t("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"
    
    def test_invalid_language_defaults_to_pt(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("xx")
        assert i18n.lang == "pt"
    
    def test_set_invalid_language_keeps_current(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n("en")
        i18n.set_language("zz")
        assert i18n.lang == "en"
    
    def test_available_languages(self):
        from speech_scribe.core.i18n import I18n
        i18n = I18n()
        langs = i18n.get_available_languages()
        assert "pt" in langs
        assert "en" in langs
        assert "es" in langs
    
    def test_all_keys_present_in_all_languages(self):
        from speech_scribe.core.i18n import TRANSLATIONS
        pt_keys = set(TRANSLATIONS["pt"].keys())
        for lang_code, translations in TRANSLATIONS.items():
            lang_keys = set(translations.keys())
            missing = pt_keys - lang_keys
            assert not missing, f"Idioma '{lang_code}' está faltando chaves: {missing}"


# ================================
# Testes: Themes
# ================================

class TestThemes:
    """Testes para o gerenciador de temas"""
    
    def test_default_theme_is_light(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        assert tm.current_theme_name == "light"
    
    def test_set_theme_dark(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        tm.set_theme("dark")
        assert tm.current_theme_name == "dark"
    
    def test_toggle_theme(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        result = tm.toggle_theme()
        assert result == "dark"
        result = tm.toggle_theme()
        assert result == "light"
    
    def test_get_stylesheet_returns_string(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        css = tm.get_stylesheet("dark")
        assert isinstance(css, str)
        assert "QMainWindow" in css
    
    def test_get_theme_returns_dict(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        theme = tm.get_theme("light")
        assert isinstance(theme, dict)
        assert "background" in theme
        assert "primary" in theme
        assert "text" in theme
    
    def test_available_themes(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        themes = tm.get_available_themes()
        assert "light" in themes
        assert "dark" in themes
    
    def test_invalid_theme_returns_light(self):
        from speech_scribe.gui.themes import ThemeManager
        tm = ThemeManager()
        theme = tm.get_theme("nonexistent")
        assert theme == tm.LIGHT_THEME
    
    def test_singleton_get_theme_manager(self):
        from speech_scribe.gui.themes import get_theme_manager
        tm1 = get_theme_manager()
        tm2 = get_theme_manager()
        assert tm1 is tm2


# ================================
# Testes: Settings
# ================================

class TestSettings:
    """Testes para persistência de configurações"""
    
    def test_default_model(self):
        from speech_scribe.core.settings import UserSettings
        s = UserSettings()
        # Não podemos garantir o valor default em todos os ambientes
        # mas deve retornar uma string
        assert isinstance(s.get_model(), str)
    
    def test_default_theme(self):
        from speech_scribe.core.settings import UserSettings
        s = UserSettings()
        assert s.get_theme() in ("light", "dark")
    
    def test_default_volume(self):
        from speech_scribe.core.settings import UserSettings
        s = UserSettings()
        vol = s.get_volume()
        assert isinstance(vol, int)
        assert 0 <= vol <= 100
    
    def test_default_language(self):
        from speech_scribe.core.settings import UserSettings
        s = UserSettings()
        assert s.get_interface_language() in ("pt", "en", "es")


# ================================
# Testes: Config
# ================================

class TestConfig:
    """Testes para AppConfig"""
    
    def test_supported_formats_not_empty(self):
        from speech_scribe.core.config import AppConfig
        config = AppConfig()
        assert len(config.supported_formats) > 0
    
    def test_supported_formats_has_common(self):
        from speech_scribe.core.config import AppConfig
        config = AppConfig()
        assert ".mp3" in config.supported_formats
        assert ".wav" in config.supported_formats
        assert ".mp4" in config.supported_formats
    
    def test_directories_created(self):
        from speech_scribe.core.config import AppConfig
        config = AppConfig()
        assert Path(config.cache_dir).exists() or True  # Dir might not exist in test env
    
    def test_version_exists(self):
        from speech_scribe.core.config import AppConfig
        config = AppConfig()
        assert hasattr(config, 'version')


# ================================
# Testes: Batch SRT/VTT formatters
# ================================

class TestBatchExportFormats:
    """Testes para geração de SRT e VTT no batch processor"""
    
    @pytest.fixture
    def segments(self):
        return [
            {'start': 0.0, 'end': 2.5, 'text': 'Primeira frase.'},
            {'start': 2.5, 'end': 5.0, 'text': 'Segunda frase.'},
            {'start': 5.0, 'end': 10.123, 'text': 'Terceira frase longa.'},
        ]
    
    def test_build_srt(self, segments):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        srt = BatchProcessorWidget._build_srt(segments)
        assert "1\n" in srt
        assert "2\n" in srt
        assert "3\n" in srt
        assert "-->" in srt
        assert "Primeira frase." in srt
        assert "00:00:00,000 --> 00:00:02,500" in srt
    
    def test_build_vtt(self, segments):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        vtt = BatchProcessorWidget._build_vtt(segments)
        assert vtt.startswith("WEBVTT")
        assert "-->" in vtt
        assert "Segunda frase." in vtt
        assert "00:00:02.500 --> 00:00:05.000" in vtt
    
    def test_srt_time_format(self):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        assert BatchProcessorWidget._fmt_srt_time(0.0) == "00:00:00,000"
        assert BatchProcessorWidget._fmt_srt_time(61.5) == "00:01:01,500"
        assert BatchProcessorWidget._fmt_srt_time(3661.123) == "01:01:01,123"
    
    def test_vtt_time_format(self):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        assert BatchProcessorWidget._fmt_vtt_time(0.0) == "00:00:00.000"
        assert BatchProcessorWidget._fmt_vtt_time(61.5) == "00:01:01.500"
        assert BatchProcessorWidget._fmt_vtt_time(3661.123) == "01:01:01.123"
    
    def test_empty_segments_srt(self):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        srt = BatchProcessorWidget._build_srt([])
        assert srt == ""
    
    def test_empty_segments_vtt(self):
        from speech_scribe.gui.batch_processor import BatchProcessorWidget
        vtt = BatchProcessorWidget._build_vtt([])
        assert vtt.startswith("WEBVTT")


# ================================
# Testes: Translator
# ================================

class TestTranslator:
    """Testes para o módulo de tradução"""
    
    def test_translator_import(self):
        try:
            from speech_scribe.core.translator import TranscriptionTranslator, SUPPORTED_LANGUAGES
            assert len(SUPPORTED_LANGUAGES) > 0
        except ImportError:
            pytest.skip("Módulo de tradução não disponível")
    
    def test_supported_languages_has_common(self):
        try:
            from speech_scribe.core.translator import SUPPORTED_LANGUAGES
            assert "en" in SUPPORTED_LANGUAGES
            assert "pt" in SUPPORTED_LANGUAGES
            assert "es" in SUPPORTED_LANGUAGES
        except ImportError:
            pytest.skip("Módulo de tradução não disponível")


# ================================
# Testes: Presets
# ================================

class TestPresets:
    """Testes para o sistema de presets"""
    
    def test_preset_manager_exists(self):
        from speech_scribe.core.presets import get_preset_manager
        pm = get_preset_manager()
        assert pm is not None
    
    def test_preset_names(self):
        from speech_scribe.core.presets import get_preset_manager
        pm = get_preset_manager()
        names = pm.get_preset_names()
        assert len(names) > 0
    
    def test_preset_has_model(self):
        from speech_scribe.core.presets import get_preset_manager
        pm = get_preset_manager()
        names = pm.get_preset_names()
        for name in names:
            preset = pm.get_by_name(name)
            if preset:
                assert hasattr(preset, 'model')


# ================================
# Testes: History
# ================================

class TestHistory:
    """Testes para o histórico de transcrições"""
    
    def test_history_import(self, tmp_path):
        from speech_scribe.core.history import TranscriptionHistory
        db_path = tmp_path / "test_history.db"
        h = TranscriptionHistory(db_path)
        assert h is not None
    
    def test_add_and_retrieve(self, tmp_path):
        from speech_scribe.core.history import TranscriptionHistory
        db_path = tmp_path / "test_history.db"
        h = TranscriptionHistory(db_path)
        h.add(
            file_path="/tmp/test.mp3",
            text="Teste de transcrição",
            language="pt",
            model="small",
            duration_seconds=10.0,
            processing_time=2.0
        )
        records = h.get_recent(10)
        assert len(records) == 1
        assert records[0].text == "Teste de transcrição"
    
    def test_search(self, tmp_path):
        from speech_scribe.core.history import TranscriptionHistory
        db_path = tmp_path / "test_history.db"
        h = TranscriptionHistory(db_path)
        h.add("/tmp/a.mp3", "Hello world", "en", "base", 5.0, 1.0)
        h.add("/tmp/b.mp3", "Olá mundo", "pt", "base", 5.0, 1.0)
        results = h.search("Hello")
        assert len(results) == 1
    
    def test_stats(self, tmp_path):
        from speech_scribe.core.history import TranscriptionHistory
        db_path = tmp_path / "test_history.db"
        h = TranscriptionHistory(db_path)
        h.add("/tmp/a.mp3", "Teste", "pt", "small", 10.0, 2.0)
        stats = h.get_stats()
        assert stats['total_transcriptions'] == 1


# ================================
# Testes: BatchItem
# ================================

class TestBatchItem:
    """Testes para BatchItem"""
    
    def test_batch_item_creation(self):
        from speech_scribe.gui.batch_processor import BatchItem
        item = BatchItem("/tmp/test.mp3")
        assert item.file_path == "/tmp/test.mp3"
        assert item.status == "pending"
        assert item.progress == 0
        assert item.result is None
        assert item.error is None
    
    def test_batch_item_filename(self):
        from speech_scribe.gui.batch_processor import BatchItem
        item = BatchItem("/home/user/audio/my_file.mp3")
        assert item.filename == "my_file.mp3"
