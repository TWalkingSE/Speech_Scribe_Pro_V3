#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔄 Version Checker - Speech Scribe Pro V3
Verificação de atualização ao iniciar a aplicação
"""

import json
from typing import Optional, Tuple
from speech_scribe.utils.logger import logger


# URL do arquivo de versão remoto (configurável)
DEFAULT_VERSION_URL = ""

CURRENT_VERSION = "3.0.0"


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Converte string de versão em tupla para comparação"""
    try:
        parts = version_str.strip().lstrip("v").split(".")
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_newer(remote: str, local: str) -> bool:
    """Verifica se a versão remota é mais nova que a local"""
    return parse_version(remote) > parse_version(local)


def check_for_updates(version_url: str = "", timeout: float = 5.0) -> Optional[dict]:
    """
    Verifica se há atualizações disponíveis.
    
    Retorna dict com info da atualização ou None se estiver atualizado.
    Formato esperado do JSON remoto:
    {
        "version": "3.1.0",
        "release_date": "2026-03-01",
        "changelog": "Novidades...",
        "download_url": "https://..."
    }
    """
    if not version_url:
        logger.debug("URL de verificação de versão não configurada")
        return None
    
    try:
        import requests
        response = requests.get(version_url, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        remote_version = data.get("version", "0.0.0")
        
        if is_newer(remote_version, CURRENT_VERSION):
            logger.info(f"Nova versão disponível: {remote_version} (atual: {CURRENT_VERSION})")
            return {
                "current_version": CURRENT_VERSION,
                "new_version": remote_version,
                "release_date": data.get("release_date", ""),
                "changelog": data.get("changelog", ""),
                "download_url": data.get("download_url", ""),
            }
        else:
            logger.debug(f"Versão atual ({CURRENT_VERSION}) está atualizada")
            return None
            
    except ImportError:
        logger.debug("requests não disponível para verificação de versão")
        return None
    except Exception as e:
        logger.debug(f"Erro ao verificar atualizações: {e}")
        return None


def get_update_message(update_info: dict) -> str:
    """Gera mensagem formatada sobre a atualização"""
    msg = f"Nova versão disponível: v{update_info['new_version']}"
    if update_info.get('release_date'):
        msg += f" ({update_info['release_date']})"
    if update_info.get('changelog'):
        msg += f"\n\n{update_info['changelog']}"
    if update_info.get('download_url'):
        msg += f"\n\nDownload: {update_info['download_url']}"
    return msg
