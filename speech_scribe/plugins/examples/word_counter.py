#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 Plugin de Contagem de Palavras - Exemplo
Demonstra como criar um plugin de análise
"""

from typing import Dict, Any, List
from speech_scribe.plugins.base import (
    AnalysisPlugin, PluginInfo, PluginType, HookPriority
)


class WordCounterPlugin(AnalysisPlugin):
    """Plugin que conta palavras e fornece estatísticas de texto"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Word Counter",
            version="1.0.0",
            description="Conta palavras e fornece estatísticas detalhadas do texto",
            author="Speech Scribe Team",
            plugin_type=PluginType.ANALYSIS,
            tags=["statistics", "words", "text-analysis"]
        )
    
    def activate(self):
        """Registra hooks do plugin"""
        self.register_hook('post_transcription', self.on_transcription, HookPriority.NORMAL)
    
    def on_transcription(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Hook chamado após transcrição"""
        text = result.get('text', '')
        stats = self.analyze(text)
        result['word_stats'] = stats
        return result
    
    def analyze(self, text: str, **options) -> Dict[str, Any]:
        """Analisa o texto e retorna estatísticas"""
        words = text.split()
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Contagem de palavras por tamanho
        word_lengths = {}
        for word in words:
            length = len(word.strip('.,!?;:'))
            word_lengths[length] = word_lengths.get(length, 0) + 1
        
        # Palavras mais frequentes
        word_freq = {}
        for word in words:
            clean_word = word.lower().strip('.,!?;:')
            if len(clean_word) > 2:  # Ignorar palavras muito curtas
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_words': len(words),
            'total_characters': len(text),
            'total_sentences': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'word_length_distribution': word_lengths,
            'top_words': top_words,
            'unique_words': len(set(w.lower() for w in words))
        }
    
    def get_analysis_types(self) -> List[str]:
        return ['word_count', 'text_statistics']
