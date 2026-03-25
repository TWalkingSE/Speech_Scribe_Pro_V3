#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes dos Módulos Core - Speech Scribe Pro V3
"""

import pytest
from speech_scribe.core.config import AppConfig
from speech_scribe.core.dependencies import SmartDependencyManager
from speech_scribe.core.analysis import SmartAnalyzer


class TestAppConfig:
    """Testes para AppConfig"""
    
    def test_default_values(self):
        """Testa valores padrão"""
        config = AppConfig()
        
        assert config.app_name == "Speech Scribe Pro V3"
        assert config.version == "3.0.0"
        assert config.default_model == "small"
    
    def test_supported_formats(self):
        """Testa formatos suportados"""
        config = AppConfig()
        
        assert '.mp3' in config.supported_formats
        assert '.wav' in config.supported_formats
        assert '.mp4' in config.supported_formats
    
    def test_directories_created(self):
        """Testa criação de diretórios"""
        config = AppConfig()
        
        assert config.cache_dir.exists()
        assert config.temp_dir.exists()
        assert config.log_dir.exists()


class TestSmartDependencyManager:
    """Testes para SmartDependencyManager"""
    
    @pytest.fixture
    def dep_manager(self):
        """Fixture de dependency manager"""
        return SmartDependencyManager()
    
    def test_check_installed_dependency(self, dep_manager):
        """Testa verificação de dependência instalada"""
        # 'os' é sempre disponível
        result = dep_manager.check_dependency('os')
        
        assert result is True
    
    def test_check_missing_dependency(self, dep_manager):
        """Testa verificação de dependência ausente"""
        result = dep_manager.check_dependency('nonexistent_package_xyz')
        
        assert result is False
    
    def test_generate_requirements(self, dep_manager):
        """Testa geração de requirements"""
        requirements = dep_manager.generate_requirements()
        
        assert 'faster-whisper' in requirements
        assert 'torch' in requirements
        assert 'PyQt6' in requirements


class TestSmartAnalyzer:
    """Testes para SmartAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Fixture de analyzer"""
        return SmartAnalyzer()
    
    def test_sentiment_analysis_positive(self, analyzer):
        """Testa análise de sentimento positivo"""
        text = "Este é um ótimo produto, excelente qualidade e bom preço!"
        result = analyzer._analyze_sentiment(text)
        
        assert result['sentiment'] == 'positive'
        assert result['positive_words'] > 0
    
    def test_sentiment_analysis_negative(self, analyzer):
        """Testa análise de sentimento negativo"""
        text = "Produto péssimo, ruim demais, um fracasso total!"
        result = analyzer._analyze_sentiment(text)
        
        assert result['sentiment'] == 'negative'
        assert result['negative_words'] > 0
    
    def test_sentiment_analysis_neutral(self, analyzer):
        """Testa análise de sentimento neutro"""
        text = "O produto chegou na data prevista."
        result = analyzer._analyze_sentiment(text)
        
        assert result['sentiment'] == 'neutral'
    
    def test_extract_entities(self, analyzer):
        """Testa extração de entidades"""
        text = "Entre em contato pelo email teste@email.com ou 11-99999-9999"
        result = analyzer._extract_entities(text)
        
        assert 'emails' in result
        assert len(result['emails']) > 0
    
    def test_extract_keywords(self, analyzer):
        """Testa extração de palavras-chave"""
        text = "Python Python Python é uma linguagem de programação versátil"
        result = analyzer._extract_keywords(text)
        
        assert 'top_keywords' in result
        assert result['total_words'] > 0
    
    def test_generate_summary(self, analyzer):
        """Testa geração de resumo"""
        text = "Primeira frase do texto. Segunda frase importante. Terceira frase. Quarta frase."
        result = analyzer._generate_summary(text)
        
        assert 'summary' in result
        assert result['compression_ratio'] < 1.0
    
    def test_identify_topics(self, analyzer):
        """Testa identificação de tópicos"""
        text = "O computador e a internet são tecnologias digitais essenciais para software moderno."
        result = analyzer._identify_topics(text)
        
        assert 'identified_topics' in result
        assert 'tecnologia' in result['identified_topics'] or result['main_topic'] == 'tecnologia'
    
    def test_analyze_transcription(self, analyzer, sample_text):
        """Testa análise completa"""
        result = analyzer.analyze_transcription(sample_text)
        
        assert 'sentiment' in result
        assert 'keywords' in result
        assert 'entities' in result
        assert 'summary' in result
        assert 'topics' in result
    
    def test_analyze_specific_analyses(self, analyzer, sample_text):
        """Testa análise com opções específicas"""
        result = analyzer.analyze_transcription(sample_text, analyses=['sentiment', 'keywords'])
        
        assert 'sentiment' in result
        assert 'keywords' in result
        # Não deve incluir outras análises
        assert len(result) == 2
