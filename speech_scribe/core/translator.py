#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌐 Translator - Speech Scribe Pro V3
Tradução integrada usando deep-translator
"""

from typing import Optional, List, Dict
from speech_scribe.utils.logger import logger

# Idiomas suportados com nomes legíveis
SUPPORTED_LANGUAGES = {
    'pt': 'Português',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'ja': '日本語',
    'zh-CN': '中文 (简体)',
    'zh-TW': '中文 (繁體)',
    'ko': '한국어',
    'ru': 'Русский',
    'ar': 'العربية',
    'hi': 'हिन्दी',
    'nl': 'Nederlands',
    'pl': 'Polski',
    'tr': 'Türkçe',
    'vi': 'Tiếng Việt',
    'th': 'ไทย',
    'id': 'Bahasa Indonesia',
    'sv': 'Svenska',
    'da': 'Dansk',
    'no': 'Norsk',
    'fi': 'Suomi',
    'cs': 'Čeština',
    'el': 'Ελληνικά',
    'he': 'עברית',
    'uk': 'Українська',
    'ro': 'Română',
    'hu': 'Magyar',
}


class TranscriptionTranslator:
    """Tradutor de transcrições usando múltiplos backends"""
    
    def __init__(self):
        self.available = self._check_availability()
        self.translator = None
        self._init_translator()
        
    def _check_availability(self) -> bool:
        """Verifica se deep-translator está disponível"""
        try:
            from deep_translator import GoogleTranslator
            return True
        except ImportError:
            logger.warning("deep-translator não disponível. Instale com: pip install deep-translator")
            return False
            
    def _init_translator(self):
        """Inicializa tradutor"""
        if self.available:
            try:
                from deep_translator import GoogleTranslator
                self.translator = GoogleTranslator
                logger.info("Tradutor inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar tradutor: {e}")
                self.available = False
                
    def translate_text(self, text: str, source_lang: str = 'auto', 
                       target_lang: str = 'en') -> Optional[str]:
        """
        Traduz texto para idioma alvo
        
        Args:
            text: Texto a traduzir
            source_lang: Idioma de origem ('auto' para detecção automática)
            target_lang: Idioma de destino
            
        Returns:
            Texto traduzido ou None se falhar
        """
        if not self.available or not self.translator:
            logger.error("Tradutor não disponível")
            return None
            
        if not text or not text.strip():
            return text
            
        try:
            translator = self.translator(source=source_lang, target=target_lang)
            
            # Dividir texto longo em chunks (limite de ~5000 chars por request)
            max_chunk_size = 4500
            
            if len(text) <= max_chunk_size:
                translated = translator.translate(text)
            else:
                # Dividir por parágrafos ou sentenças
                chunks = self._split_text(text, max_chunk_size)
                translated_chunks = []
                
                for chunk in chunks:
                    translated_chunk = translator.translate(chunk)
                    translated_chunks.append(translated_chunk)
                    
                translated = ' '.join(translated_chunks)
                
            logger.info(f"Tradução concluída: {source_lang} -> {target_lang}")
            return translated
            
        except Exception as e:
            logger.error(f"Erro na tradução: {e}")
            return None
            
    def translate_segments(self, segments: List[Dict], source_lang: str = 'auto',
                          target_lang: str = 'en') -> List[Dict]:
        """
        Traduz segmentos mantendo timestamps
        
        Args:
            segments: Lista de segmentos com 'text', 'start', 'end'
            source_lang: Idioma de origem
            target_lang: Idioma de destino
            
        Returns:
            Segmentos com texto traduzido
        """
        if not self.available or not segments:
            return segments
            
        translated_segments = []
        
        try:
            translator = self.translator(source=source_lang, target=target_lang)
            
            for seg in segments:
                new_seg = seg.copy()
                
                if 'text' in seg and seg['text'].strip():
                    try:
                        new_seg['text'] = translator.translate(seg['text'])
                        new_seg['original_text'] = seg['text']
                    except Exception as e:
                        logger.warning(f"Erro ao traduzir segmento: {e}")
                        
                translated_segments.append(new_seg)
                
            logger.info(f"Traduzidos {len(translated_segments)} segmentos")
            return translated_segments
            
        except Exception as e:
            logger.error(f"Erro ao traduzir segmentos: {e}")
            return segments
            
    def translate_result(self, result: Dict, target_lang: str = 'en') -> Dict:
        """
        Traduz resultado completo de transcrição
        
        Args:
            result: Resultado da transcrição
            target_lang: Idioma de destino
            
        Returns:
            Resultado com textos traduzidos
        """
        if not self.available or not result:
            return result
            
        translated_result = result.copy()
        source_lang = result.get('language', 'auto')
        
        # Traduzir texto principal
        if 'text' in result:
            translated_text = self.translate_text(result['text'], source_lang, target_lang)
            if translated_text:
                translated_result['original_text'] = result['text']
                translated_result['text'] = translated_text
                translated_result['translated_to'] = target_lang
                
        # Traduzir segmentos
        if 'segments' in result:
            translated_result['segments'] = self.translate_segments(
                result['segments'], source_lang, target_lang
            )
            
        return translated_result
        
    def _split_text(self, text: str, max_size: int) -> List[str]:
        """Divide texto em chunks respeitando limites"""
        chunks = []
        current_chunk = ""
        
        # Dividir por parágrafos primeiro
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_size:
                current_chunk += para + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                # Se parágrafo é maior que max_size, dividir por sentenças
                if len(para) > max_size:
                    sentences = para.replace('. ', '.|').split('|')
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= max_size:
                            current_chunk += sent + ' '
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent + ' '
                else:
                    current_chunk = para + '\n\n'
                    
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
        
    def get_supported_languages(self) -> Dict[str, str]:
        """Retorna dicionário de idiomas suportados"""
        return SUPPORTED_LANGUAGES.copy()
        
    def detect_language(self, text: str) -> Optional[str]:
        """Detecta idioma do texto"""
        if not self.available:
            return None
            
        try:
            from deep_translator import single_detection
            detected = single_detection(text[:500], api_key=None)
            return detected
        except Exception:
            return None
