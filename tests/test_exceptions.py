#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 Testes do Sistema de Exceções - Speech Scribe Pro V3
"""

import pytest
from speech_scribe.core.exceptions import (
    SpeechScribeError,
    TranscriptionError,
    ModelLoadError,
    ModelNotFoundError,
    GPUError,
    CUDAOutOfMemoryError,
    CUDANotAvailableError,
    OllamaNotAvailableError,
    FileNotFoundError as SSFileNotFoundError,
    UnsupportedFormatError,
    FileTooLargeError,
    MissingDependencyError,
    ErrorHandler
)


class TestSpeechScribeError:
    """Testes para exceção base"""
    
    def test_basic_error(self):
        """Testa criação de erro básico"""
        error = SpeechScribeError("Erro de teste")
        
        assert str(error) == "Erro de teste"
        assert error.message == "Erro de teste"
    
    def test_error_with_details(self):
        """Testa erro com detalhes"""
        error = SpeechScribeError("Erro", details={'key': 'value'})
        
        assert 'key' in error.details
        assert "Detalhes:" in str(error)
    
    def test_to_dict(self):
        """Testa conversão para dicionário"""
        error = SpeechScribeError("Erro", details={'info': 123})
        result = error.to_dict()
        
        assert result['error_type'] == 'SpeechScribeError'
        assert result['message'] == 'Erro'
        assert result['details'] == {'info': 123}


class TestModelErrors:
    """Testes para erros de modelo"""
    
    def test_model_load_error(self):
        """Testa erro de carregamento de modelo"""
        error = ModelLoadError("large-v3", "Memória insuficiente")
        
        assert "large-v3" in str(error)
        assert "Memória insuficiente" in str(error)
        assert error.model_name == "large-v3"
    
    def test_model_not_found(self):
        """Testa erro de modelo não encontrado"""
        error = ModelNotFoundError("unknown-model")
        
        assert error.model_name == "unknown-model"
        assert "não encontrado" in str(error).lower()


class TestGPUErrors:
    """Testes para erros de GPU"""
    
    def test_cuda_not_available(self):
        """Testa erro de CUDA não disponível"""
        error = CUDANotAvailableError()
        
        assert "CUDA" in str(error)
    
    def test_cuda_out_of_memory(self):
        """Testa erro de memória GPU"""
        error = CUDAOutOfMemoryError(
            required_mb=8000,
            available_mb=4000,
            gpu_id=0
        )
        
        assert error.required_mb == 8000
        assert error.available_mb == 4000
        assert "8000" in str(error)
        assert "4000" in str(error)


class TestFileErrors:
    """Testes para erros de arquivo"""
    
    def test_file_not_found(self):
        """Testa erro de arquivo não encontrado"""
        error = SSFileNotFoundError("/path/to/file.mp3")
        
        assert error.file_path == "/path/to/file.mp3"
    
    def test_unsupported_format(self):
        """Testa erro de formato não suportado"""
        error = UnsupportedFormatError(
            file_path="/file.xyz",
            format=".xyz",
            supported_formats=[".mp3", ".wav"]
        )
        
        assert error.format == ".xyz"
        assert ".mp3" in error.supported_formats
    
    def test_file_too_large(self):
        """Testa erro de arquivo muito grande"""
        error = FileTooLargeError(
            file_path="/large_file.mp4",
            size_mb=5000,
            max_size_mb=2048
        )
        
        assert error.size_mb == 5000
        assert error.max_size_mb == 2048


class TestDependencyErrors:
    """Testes para erros de dependência"""
    
    def test_missing_dependency(self):
        """Testa erro de dependência ausente"""
        error = MissingDependencyError("torch")
        
        assert "torch" in str(error)
        assert "pip install" in str(error)
    
    def test_missing_dependency_with_command(self):
        """Testa erro com comando customizado"""
        error = MissingDependencyError(
            "cuda",
            install_command="conda install cudatoolkit"
        )
        
        assert "conda install" in str(error)


class TestErrorHandler:
    """Testes para ErrorHandler"""
    
    def test_user_message_cuda_oom(self):
        """Testa mensagem amigável para OOM"""
        error = CUDAOutOfMemoryError(8000, 4000)
        message = ErrorHandler.get_user_message(error)
        
        assert "GPU" in message or "memória" in message.lower()
    
    def test_user_message_generic(self):
        """Testa mensagem para erro genérico"""
        error = SpeechScribeError("Erro personalizado")
        message = ErrorHandler.get_user_message(error)
        
        assert "Erro personalizado" in message
    
    def test_user_message_unknown(self):
        """Testa mensagem para erro desconhecido"""
        error = ValueError("Erro padrão Python")
        message = ErrorHandler.get_user_message(error)
        
        assert "Erro" in message
    
    def test_recovery_suggestion_cuda(self):
        """Testa sugestão de recuperação para CUDA"""
        error = CUDAOutOfMemoryError(8000, 4000)
        suggestion = ErrorHandler.get_recovery_suggestion(error)
        
        assert suggestion is not None
        assert "modelo" in suggestion.lower() or "small" in suggestion.lower()
    
    def test_recovery_suggestion_ollama(self):
        """Testa sugestão para Ollama"""
        error = OllamaNotAvailableError()
        suggestion = ErrorHandler.get_recovery_suggestion(error)
        
        assert suggestion is not None
        assert "ollama" in suggestion.lower()
    
    def test_recovery_suggestion_none(self):
        """Testa que erros sem sugestão retornam None"""
        error = SpeechScribeError("Erro genérico")
        suggestion = ErrorHandler.get_recovery_suggestion(error)
        
        assert suggestion is None
