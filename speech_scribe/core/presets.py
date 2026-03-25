#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎚️ Presets de Qualidade - Speech Scribe Pro V3
Perfis pré-configurados para diferentes cenários de uso
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class PresetType(Enum):
    """Tipos de preset disponíveis"""
    RAPIDO = "rapido"
    BALANCEADO = "balanceado"
    MAXIMA_QUALIDADE = "maxima_qualidade"
    PODCAST = "podcast"
    REUNIAO = "reuniao"
    ENTREVISTA = "entrevista"
    PALESTRA = "palestra"


@dataclass
class QualityPreset:
    """Configurações de um preset de qualidade"""
    name: str
    description: str
    preset_type: PresetType
    model: str = "small"
    language: str = "auto"
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    vad_filter: bool = True
    word_timestamps: bool = False
    compute_type: str = "float16"
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['preset_type'] = self.preset_type.value
        return d


# Presets padrão
PRESETS: Dict[PresetType, QualityPreset] = {
    PresetType.RAPIDO: QualityPreset(
        name="⚡ Rápido",
        description="Transcrição rápida, qualidade básica",
        preset_type=PresetType.RAPIDO,
        model="tiny",
        beam_size=1,
        best_of=1,
        vad_filter=True,
        compute_type="int8"
    ),
    PresetType.BALANCEADO: QualityPreset(
        name="⚖️ Balanceado",
        description="Equilíbrio entre velocidade e qualidade",
        preset_type=PresetType.BALANCEADO,
        model="small",
        beam_size=5,
        best_of=5,
        vad_filter=True,
        compute_type="float16"
    ),
    PresetType.MAXIMA_QUALIDADE: QualityPreset(
        name="🎯 Máxima Qualidade",
        description="Melhor precisão, mais lento",
        preset_type=PresetType.MAXIMA_QUALIDADE,
        model="large-v3",
        beam_size=10,
        best_of=10,
        word_timestamps=True,
        compute_type="float16"
    ),
    PresetType.PODCAST: QualityPreset(
        name="🎙️ Podcast",
        description="Otimizado para podcasts e entrevistas",
        preset_type=PresetType.PODCAST,
        model="medium",
        beam_size=8,
        best_of=5,
        vad_filter=True,
        word_timestamps=True,
        compute_type="float16"
    ),
    PresetType.REUNIAO: QualityPreset(
        name="👥 Reunião",
        description="Otimizado para reuniões com múltiplos falantes",
        preset_type=PresetType.REUNIAO,
        model="medium",
        beam_size=8,
        best_of=8,
        vad_filter=True,
        word_timestamps=True,
        compute_type="float16"
    ),
    PresetType.ENTREVISTA: QualityPreset(
        name="🎤 Entrevista",
        description="Alta qualidade para entrevistas",
        preset_type=PresetType.ENTREVISTA,
        model="large-v2",
        beam_size=8,
        best_of=5,
        vad_filter=True,
        word_timestamps=True,
        compute_type="float16"
    ),
    PresetType.PALESTRA: QualityPreset(
        name="🎓 Palestra",
        description="Otimizado para palestras e aulas",
        preset_type=PresetType.PALESTRA,
        model="medium",
        beam_size=5,
        best_of=5,
        vad_filter=True,
        compute_type="float16"
    ),
}


class PresetManager:
    """Gerenciador de presets"""
    
    def __init__(self):
        self._presets = PRESETS.copy()
        self._current: Optional[PresetType] = PresetType.BALANCEADO
    
    def get_preset(self, preset_type: PresetType) -> QualityPreset:
        """Obtém um preset pelo tipo"""
        return self._presets.get(preset_type, PRESETS[PresetType.BALANCEADO])
    
    def get_current(self) -> QualityPreset:
        """Obtém o preset atual"""
        return self.get_preset(self._current)
    
    def set_current(self, preset_type: PresetType):
        """Define o preset atual"""
        self._current = preset_type
    
    def list_presets(self) -> List[QualityPreset]:
        """Lista todos os presets disponíveis"""
        return list(self._presets.values())
    
    def get_preset_names(self) -> List[str]:
        """Retorna nomes dos presets para UI"""
        return [p.name for p in self._presets.values()]
    
    def get_by_name(self, name: str) -> Optional[QualityPreset]:
        """Obtém preset pelo nome"""
        for preset in self._presets.values():
            if preset.name == name:
                return preset
        return None


_manager: Optional[PresetManager] = None


def get_preset_manager() -> PresetManager:
    """Obtém gerenciador de presets singleton"""
    global _manager
    if _manager is None:
        _manager = PresetManager()
    return _manager


__all__ = ['PresetType', 'QualityPreset', 'PRESETS', 'PresetManager', 'get_preset_manager']
