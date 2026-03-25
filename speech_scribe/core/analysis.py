from typing import Dict, List, Any
from speech_scribe.utils.logger import logger

class SmartAnalyzer:
    """Analisador inteligente com múltiplas ferramentas de IA"""
    
    def __init__(self):
        self.analyzers = {
            'sentiment': self._analyze_sentiment,
            'entities': self._extract_entities,
            'keywords': self._extract_keywords,
            'summary': self._generate_summary,
            'topics': self._identify_topics
        }
        
        # Integração com Ollama
        try:
            from speech_scribe.core.ollama_integration import OllamaAnalyzer
            self.ollama_analyzer = OllamaAnalyzer()
            self.ollama_available = True
        except ImportError:
            self.ollama_analyzer = None
            self.ollama_available = False
    
    def analyze_transcription(self, text: str, analyses: List[str] = None, use_ollama: bool = False) -> Dict[str, Any]:
        """Realiza análises múltiplas do texto transcrito"""
        if analyses is None:
            analyses = list(self.analyzers.keys())
        
        results = {}
        
        # Se Ollama estiver disponível e solicitado
        if use_ollama and self.ollama_available:
            try:
                ollama_result = self.ollama_analyzer.analyze_transcription_complete(text)
                results['ollama_analysis'] = ollama_result
            except Exception as e:
                results['ollama_analysis'] = {'error': str(e)}
        
        # Análises tradicionais
        for analysis in analyses:
            if analysis in self.analyzers:
                try:
                    results[analysis] = self.analyzers[analysis](text)
                except Exception as e:
                    results[analysis] = {'error': str(e)}
        
        return results
    
    def chat_with_ollama(self, text: str, question: str, model: str = None) -> str:
        """Faz pergunta sobre a transcrição usando Ollama"""
        if not self.ollama_available:
            return "Ollama não está disponível. Verifique se o serviço está rodando (ollama serve)."
        
        try:
            return self.ollama_analyzer.chat_about_transcription(text, question, model)
        except Exception as e:
            return f"Erro ao usar Ollama: {e}"
    
    def get_ollama_models(self) -> List[str]:
        """Retorna lista de modelos Ollama disponíveis"""
        if not self.ollama_available:
            return []
        
        try:
            return self.ollama_analyzer.manager.get_available_models()
        except Exception:
            return []
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Análise de sentimento simplificada"""
        positive_words = ['bom', 'ótimo', 'excelente', 'positivo', 'feliz', 'sucesso']
        negative_words = ['ruim', 'péssimo', 'negativo', 'triste', 'fracasso', 'problema']
        
        text_lower = text.lower()
        pos_count = sum(word in text_lower for word in positive_words)
        neg_count = sum(word in text_lower for word in negative_words)
        
        if pos_count > neg_count:
            sentiment = 'positive'
            score = 0.7
        elif neg_count > pos_count:
            sentiment = 'negative'
            score = 0.3
        else:
            sentiment = 'neutral'
            score = 0.5
        
        return {
            'sentiment': sentiment,
            'score': score,
            'positive_words': pos_count,
            'negative_words': neg_count
        }
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extração de entidades simples"""
        import re
        
        # Padrões simples para entidades
        patterns = {
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phones': r'\b\d{2,3}[-.\s]?\d{4,5}[-.\s]?\d{4}\b',
            'dates': r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
            'numbers': r'\b\d+[.,]?\d*\b'
        }
        
        entities = {}
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            entities[entity_type] = list(set(matches))
        
        return entities
    
    def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """Extração de palavras-chave"""
        # Palavras comuns a ignorar
        stop_words = set([
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'e', 'ou', 'mas', 'que', 'para', 'com', 'por', 'em', 'no', 'na',
            'é', 'são', 'foi', 'foram', 'ser', 'estar', 'ter', 'haver'
        ])
        
        words = text.lower().split()
        # Filtrar palavras curtas e stop words
        filtered_words = [
            word.strip('.,!?;:') for word in words 
            if len(word) > 3 and word.lower() not in stop_words
        ]
        
        # Contar frequência
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # Top 10 palavras
        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_keywords': top_words,
            'total_words': len(words),
            'unique_words': len(set(filtered_words))
        }
    
    def _generate_summary(self, text: str) -> Dict[str, Any]:
        """Gera resumo simples"""
        sentences = text.split('.')
        # Pegar as 3 primeiras sentenças não vazias
        summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
        
        return {
            'summary': '. '.join(summary_sentences) + '.',
            'original_length': len(text),
            'summary_length': len('. '.join(summary_sentences)),
            'compression_ratio': len('. '.join(summary_sentences)) / len(text) if text else 0
        }
    
    def _identify_topics(self, text: str) -> Dict[str, Any]:
        """Identifica tópicos básicos"""
        # Categorias simples baseadas em palavras-chave
        topics = {
            'tecnologia': ['computador', 'software', 'internet', 'digital', 'tecnologia'],
            'negócios': ['empresa', 'vendas', 'lucro', 'cliente', 'mercado'],
            'educação': ['escola', 'estudar', 'aprender', 'professor', 'aluno'],
            'saúde': ['médico', 'doença', 'tratamento', 'saúde', 'hospital'],
            'política': ['governo', 'presidente', 'político', 'eleição', 'estado']
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topics.items():
            score = sum(keyword in text_lower for keyword in keywords)
            if score > 0:
                topic_scores[topic] = score
        
        return {
            'identified_topics': topic_scores,
            'main_topic': max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else 'geral'
        }
