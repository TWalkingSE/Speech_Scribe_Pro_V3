import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: Path = None):
    """Configura o logger da aplicação com suporte a UTF-8 e log rotation no Windows"""
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'speech_scribe.log'
    else:
        log_file = 'speech_scribe.log'

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler com rotação (max 5MB, manter 3 backups)
    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Stream handler com UTF-8 para Windows
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(log_format))
    
    # Configurar encoding UTF-8 para stdout no Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
            pass  # Python < 3.7
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    return logging.getLogger("speech_scribe")


logger = logging.getLogger("speech_scribe")
