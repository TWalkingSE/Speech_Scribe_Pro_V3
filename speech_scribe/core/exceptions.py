#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚠️ Exceções Customizadas - Speech Scribe Pro V3
Hierarquia de exceções para tratamento granular de erros
"""

from typing import Optional, Dict, Any


class SpeechScribeError(Exception):
    """
    Exceção base para todos os erros do Speech Scribe Pro.
    
    Todas as exceções customizadas devem herdar desta classe.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Inicializa a exceção.
        
        Args:
            message: Mensagem de erro descritiva
            details: Detalhes adicionais sobre o erro
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Detalhes: {self.details}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte exceção para dicionário"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


# ================================
# Erros de Transcrição
# ================================

class TranscriptionError(SpeechScribeError):
    """Erro base de transcrição"""
    pass


class ModelLoadError(TranscriptionError):
    """Erro ao carregar modelo de transcrição"""
    
    def __init__(self, model_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Falha ao carregar modelo '{model_name}': {reason}"
        super().__init__(message, details)
        self.model_name = model_name
        self.reason = reason


class ModelNotFoundError(ModelLoadError):
    """Modelo não encontrado"""
    
    def __init__(self, model_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, "Modelo não encontrado ou não disponível", details)


class TranscriptionProcessError(TranscriptionError):
    """Erro durante o processo de transcrição"""
    
    def __init__(self, file_path: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Erro ao transcrever '{file_path}': {reason}"
        super().__init__(message, details)
        self.file_path = file_path
        self.reason = reason


class AudioExtractionError(TranscriptionError):
    """Erro ao extrair áudio de arquivo"""
    
    def __init__(self, file_path: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Falha ao extrair áudio de '{file_path}': {reason}"
        super().__init__(message, details)
        self.file_path = file_path


# ================================
# Erros de Hardware/GPU
# ================================

class HardwareError(SpeechScribeError):
    """Erro base relacionado a hardware"""
    pass


class GPUError(HardwareError):
    """Erro relacionado à GPU/CUDA"""
    
    def __init__(self, message: str, gpu_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.gpu_id = gpu_id


class CUDANotAvailableError(GPUError):
    """CUDA não está disponível"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("CUDA não está disponível neste sistema", details=details)


class CUDAOutOfMemoryError(GPUError):
    """Memória GPU insuficiente"""
    
    def __init__(self, required_mb: float, available_mb: float, gpu_id: int = 0, 
                 details: Optional[Dict[str, Any]] = None):
        message = f"Memória GPU insuficiente: necessário {required_mb:.0f}MB, disponível {available_mb:.0f}MB"
        super().__init__(message, gpu_id, details)
        self.required_mb = required_mb
        self.available_mb = available_mb


class GPUInitializationError(GPUError):
    """Erro ao inicializar GPU"""
    
    def __init__(self, gpu_id: int, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Falha ao inicializar GPU {gpu_id}: {reason}"
        super().__init__(message, gpu_id, details)


# ================================
# Erros de Diarização
# ================================

class DiarizationError(SpeechScribeError):
    """Erro base na diarização"""
    pass


class DiarizationNotAvailableError(DiarizationError):
    """Diarização não está disponível"""
    
    def __init__(self, reason: str = "Dependências não instaladas ou token não configurado",
                 details: Optional[Dict[str, Any]] = None):
        message = f"Diarização não disponível: {reason}"
        super().__init__(message, details)


class DiarizationProcessError(DiarizationError):
    """Erro durante processo de diarização"""
    
    def __init__(self, file_path: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Erro na diarização de '{file_path}': {reason}"
        super().__init__(message, details)
        self.file_path = file_path


# ================================
# Erros de Análise IA
# ================================

class AnalysisError(SpeechScribeError):
    """Erro base de análise"""
    pass


class OllamaError(AnalysisError):
    """Erro relacionado ao Ollama"""
    pass


class OllamaNotAvailableError(OllamaError):
    """Ollama não está disponível"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__("Ollama não está disponível. Verifique se o serviço está em execução.", details)


class OllamaModelNotFoundError(OllamaError):
    """Modelo Ollama não encontrado"""
    
    def __init__(self, model_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Modelo Ollama '{model_name}' não encontrado. Execute: ollama pull {model_name}"
        super().__init__(message, details)
        self.model_name = model_name


class OllamaRequestError(OllamaError):
    """Erro na requisição ao Ollama"""
    
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Erro na requisição ao Ollama: {reason}"
        super().__init__(message, details)


# ================================
# Erros de Arquivo
# ================================

class FileError(SpeechScribeError):
    """Erro base de arquivo"""
    pass


class SpeechScribeFileNotFoundError(FileError):
    """Arquivo não encontrado"""

    def __init__(self, file_path: str, details: Optional[Dict[str, Any]] = None):
        message = f"Arquivo não encontrado: '{file_path}'"
        super().__init__(message, details)
        self.file_path = file_path


class UnsupportedFormatError(FileError):
    """Formato de arquivo não suportado"""

    def __init__(self, file_path: str, file_format: str, supported_formats: list,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Formato '{file_format}' não suportado. Formatos suportados: {', '.join(supported_formats)}"
        super().__init__(message, details)
        self.file_path = file_path
        self.file_format = file_format
        self.supported_formats = supported_formats


class FileTooLargeError(FileError):
    """Arquivo muito grande"""
    
    def __init__(self, file_path: str, size_mb: float, max_size_mb: float,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Arquivo muito grande: {size_mb:.1f}MB (máximo: {max_size_mb:.1f}MB)"
        super().__init__(message, details)
        self.file_path = file_path
        self.size_mb = size_mb
        self.max_size_mb = max_size_mb


class ExportError(FileError):
    """Erro ao exportar arquivo"""

    def __init__(self, file_path: str, file_format: str, reason: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Falha ao exportar para '{file_path}' ({file_format}): {reason}"
        super().__init__(message, details)
        self.file_format = file_format


# ================================
# Erros de Configuração
# ================================

class ConfigurationError(SpeechScribeError):
    """Erro base de configuração"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Configuração inválida"""
    
    def __init__(self, config_key: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Configuração inválida '{config_key}': {reason}"
        super().__init__(message, details)
        self.config_key = config_key


class MissingConfigurationError(ConfigurationError):
    """Configuração obrigatória ausente"""
    
    def __init__(self, config_key: str, details: Optional[Dict[str, Any]] = None):
        message = f"Configuração obrigatória ausente: '{config_key}'"
        super().__init__(message, details)
        self.config_key = config_key


# ================================
# Erros de Dependência
# ================================

class DependencyError(SpeechScribeError):
    """Erro base de dependência"""
    pass


class MissingDependencyError(DependencyError):
    """Dependência ausente"""
    
    def __init__(self, package_name: str, install_command: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        if install_command:
            message = f"Dependência '{package_name}' não instalada. Execute: {install_command}"
        else:
            message = f"Dependência '{package_name}' não instalada. Execute: pip install {package_name}"
        super().__init__(message, details)
        self.package_name = package_name
        self.install_command = install_command


# ================================
# Handler de Erros
# ================================

class ErrorHandler:
    """
    Centralizador de tratamento de erros.
    Converte exceções em mensagens amigáveis para o usuário.
    """
    
    ERROR_MESSAGES = {
        CUDAOutOfMemoryError: "💾 Memória da GPU insuficiente. Tente usar um modelo menor ou processar arquivos menores.",
        CUDANotAvailableError: "🖥️ GPU não disponível. O processamento será feito pela CPU (mais lento).",
        ModelNotFoundError: "📦 Modelo não encontrado. Verifique sua conexão com a internet para baixar o modelo.",
        OllamaNotAvailableError: "🤖 Ollama não está em execução. Inicie o serviço Ollama para usar análises de IA.",
        DiarizationNotAvailableError: "🎭 Diarização não disponível. Configure o token do HuggingFace no arquivo .env",
        UnsupportedFormatError: "📁 Formato de arquivo não suportado. Use arquivos MP3, WAV, MP4, MKV, etc.",
        FileTooLargeError: "📏 Arquivo muito grande. Tente dividir o arquivo em partes menores.",
    }
    
    @classmethod
    def get_user_message(cls, error: Exception) -> str:
        """
        Retorna mensagem amigável para o usuário.
        
        Args:
            error: Exceção ocorrida
            
        Returns:
            Mensagem formatada para exibição
        """
        # Verificar se temos mensagem específica
        for error_type, message in cls.ERROR_MESSAGES.items():
            if isinstance(error, error_type):
                return message
        
        # Mensagem genérica para erros do Speech Scribe
        if isinstance(error, SpeechScribeError):
            return f"❌ {error.message}"
        
        # Erros desconhecidos
        return f"❌ Erro inesperado: {str(error)}"
    
    @classmethod
    def get_recovery_suggestion(cls, error: Exception) -> Optional[str]:
        """
        Retorna sugestão de recuperação para o erro.
        
        Args:
            error: Exceção ocorrida
            
        Returns:
            Sugestão de recuperação ou None
        """
        if isinstance(error, CUDAOutOfMemoryError):
            return "💡 Sugestão: Use o modelo 'small' ou 'medium' ao invés de 'large'"
        
        if isinstance(error, OllamaNotAvailableError):
            return "💡 Execute 'ollama serve' no terminal para iniciar o serviço"
        
        if isinstance(error, MissingDependencyError):
            return f"💡 Execute: {error.install_command or f'pip install {error.package_name}'}"
        
        if isinstance(error, DiarizationNotAvailableError):
            return "💡 Adicione HUGGINGFACE_TOKEN=seu_token no arquivo .env"
        
        return None


__all__ = [
    # Base
    'SpeechScribeError',
    
    # Transcrição
    'TranscriptionError',
    'ModelLoadError',
    'ModelNotFoundError',
    'TranscriptionProcessError',
    'AudioExtractionError',
    
    # Hardware
    'HardwareError',
    'GPUError',
    'CUDANotAvailableError',
    'CUDAOutOfMemoryError',
    'GPUInitializationError',
    
    # Diarização
    'DiarizationError',
    'DiarizationNotAvailableError',
    'DiarizationProcessError',
    
    # Análise
    'AnalysisError',
    'OllamaError',
    'OllamaNotAvailableError',
    'OllamaModelNotFoundError',
    'OllamaRequestError',
    
    # Arquivo
    'FileError',
    'SpeechScribeFileNotFoundError',
    'UnsupportedFormatError',
    'FileTooLargeError',
    'ExportError',
    
    # Configuração
    'ConfigurationError',
    'InvalidConfigurationError',
    'MissingConfigurationError',
    
    # Dependência
    'DependencyError',
    'MissingDependencyError',
    
    # Handler
    'ErrorHandler',
]
