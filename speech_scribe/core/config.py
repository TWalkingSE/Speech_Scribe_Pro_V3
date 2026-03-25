from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass
class AppConfig:
    """Configurações centralizadas da aplicação"""
    app_name: str = "Speech Scribe Pro V3"
    version: str = "3.0.0"
    default_model: str = "small"
    supported_formats: List[str] = field(default_factory=lambda: [
        '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac',
        '.mp4', '.mkv', '.avi', '.mov', '.webm'
    ])
    max_file_size_mb: int = 2048
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".speech_scribe_v3")
    temp_dir: Path = field(default_factory=lambda: Path.home() / ".speech_scribe_v3" / "temp")
    log_dir: Path = field(default_factory=lambda: Path.home() / ".speech_scribe_v3" / "logs")
    
    def __post_init__(self):
        """Criar diretórios necessários"""
        for directory in [self.cache_dir, self.temp_dir, self.log_dir]:
            directory.mkdir(parents=True, exist_ok=True)
