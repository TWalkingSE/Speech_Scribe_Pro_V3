#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Configuração do Pytest - Speech Scribe Pro V3
Fixtures e configurações compartilhadas
"""

import sys
import os
from pathlib import Path

import pytest

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ================================
# Fixtures Globais
# ================================

@pytest.fixture
def sample_text():
    """Texto de exemplo para testes"""
    return """
    Esta é uma transcrição de exemplo para testes automatizados.
    O Speech Scribe Pro V3 é um aplicativo de transcrição de áudio e vídeo.
    Ele utiliza inteligência artificial avançada para converter fala em texto.
    O sistema suporta múltiplos idiomas e pode identificar diferentes oradores.
    """


@pytest.fixture
def sample_transcription_result():
    """Resultado de transcrição de exemplo"""
    return {
        'text': 'Esta é uma transcrição de teste.',
        'segments': [
            {'start': 0.0, 'end': 2.5, 'text': 'Esta é uma'},
            {'start': 2.5, 'end': 5.0, 'text': 'transcrição de teste.'}
        ],
        'language': 'pt',
        'duration': 5.0,
        'processing_time': 1.2,
        'model_used': 'small',
        'device_used': 'cpu'
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Diretório temporário para testes"""
    return tmp_path


@pytest.fixture
def mock_audio_path(temp_dir):
    """Caminho fictício para arquivo de áudio"""
    audio_file = temp_dir / "test_audio.mp3"
    audio_file.touch()  # Criar arquivo vazio
    return str(audio_file)


# ================================
# Markers Customizados
# ================================

def pytest_configure(config):
    """Configura markers customizados"""
    config.addinivalue_line(
        "markers", "slow: marca testes lentos (deselect com '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "gpu: marca testes que requerem GPU"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca testes unitários"
    )


# ================================
# Hooks
# ================================

def pytest_collection_modifyitems(config, items):
    """Modifica itens coletados"""
    # Adicionar marker 'unit' para testes sem markers específicos
    for item in items:
        if not any(marker in item.keywords for marker in ['slow', 'gpu', 'integration']):
            item.add_marker(pytest.mark.unit)
