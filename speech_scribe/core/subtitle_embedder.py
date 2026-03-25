#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎬 Subtitle Embedder - Speech Scribe Pro V3
Embutir legendas (SRT) em arquivos de vídeo usando FFmpeg
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from speech_scribe.utils.logger import logger


# Extensões de vídeo suportadas
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}


@dataclass
class EmbedResult:
    """Resultado da operação de embutir legenda"""
    success: bool
    output_path: str
    srt_path: str
    error: Optional[str] = None


def is_video_file(file_path: str) -> bool:
    """Verifica se o arquivo é um vídeo"""
    return Path(file_path).suffix.lower() in VIDEO_EXTENSIONS


def _find_ffmpeg_path() -> Optional[str]:
    """
    Busca o ffmpeg no sistema, incluindo caminhos comuns de instalação no Windows.
    Retorna o caminho completo do ffmpeg.exe ou None se não encontrado.
    """
    # 1. Verificar no PATH padrão
    found = shutil.which("ffmpeg")
    if found:
        return found
    
    # 2. Buscar em caminhos comuns de instalação (Windows)
    import os
    import glob
    
    search_paths = [
        # Winget install location
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe"),
        # Chocolatey
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        # Scoop
        os.path.expandvars(r"%USERPROFILE%\scoop\apps\ffmpeg\current\bin\ffmpeg.exe"),
        # Instalação manual comum
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        # Winget links
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
    ]
    
    for pattern in search_paths:
        matches = glob.glob(pattern)
        if matches:
            ffmpeg_path = matches[0]
            if os.path.isfile(ffmpeg_path):
                # Adicionar o diretório ao PATH da sessão atual
                ffmpeg_dir = os.path.dirname(ffmpeg_path)
                if ffmpeg_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                    logger.info(f"FFmpeg encontrado e adicionado ao PATH da sessão: {ffmpeg_dir}")
                return ffmpeg_path
    
    return None


def check_ffmpeg() -> bool:
    """Verifica se o FFmpeg está disponível no sistema"""
    return _find_ffmpeg_path() is not None


def get_ffmpeg_path() -> Optional[str]:
    """Retorna o caminho do FFmpeg ou None"""
    return _find_ffmpeg_path()


def _generate_srt_content(segments: List[Dict[str, Any]]) -> str:
    """
    Gera conteúdo SRT a partir dos segmentos da transcrição.
    
    Args:
        segments: Lista de segmentos com 'start', 'end' e 'text'
        
    Returns:
        Conteúdo formatado em SRT
    """
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_srt_timestamp(seg.get('start', 0))
        end = _format_srt_timestamp(seg.get('end', seg.get('start', 0) + 3))
        text = seg.get('text', '').strip()
        
        if text:
            lines.append(str(i))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
    
    return '\n'.join(lines)


def _format_srt_timestamp(seconds: float) -> str:
    """Formata timestamp no padrão SRT: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_file(transcription_result: Dict[str, Any], output_path: Path) -> Path:
    """
    Gera arquivo SRT a partir do resultado da transcrição.
    
    Args:
        transcription_result: Resultado da transcrição com 'segments'
        output_path: Caminho do arquivo SRT de saída
        
    Returns:
        Caminho do arquivo SRT gerado
    """
    segments = transcription_result.get('segments', [])
    
    if not segments:
        # Criar segmento único se não houver segmentos
        segments = [{
            'start': 0,
            'end': transcription_result.get('duration', 5),
            'text': transcription_result.get('text', '')
        }]
    
    srt_content = _generate_srt_content(segments)
    output_path = Path(output_path)
    
    if output_path.suffix.lower() != '.srt':
        output_path = output_path.with_suffix('.srt')
    
    output_path.write_text(srt_content, encoding='utf-8')
    logger.info(f"Arquivo SRT gerado: {output_path}")
    
    return output_path


def embed_subtitle_in_video(
    video_path: str,
    srt_path: str,
    output_path: Optional[str] = None,
    burn_in: bool = True,
    font_size: int = 24,
    font_color: str = "white",
    outline_color: str = "black",
    progress_callback=None
) -> EmbedResult:
    """
    Embutir legenda SRT em um arquivo de vídeo usando FFmpeg.
    
    Args:
        video_path: Caminho do vídeo original
        srt_path: Caminho do arquivo SRT
        output_path: Caminho de saída (opcional, gera automaticamente)
        burn_in: Se True, queima a legenda no vídeo (hardcoded).
                 Se False, adiciona como faixa de legenda (softcoded).
        font_size: Tamanho da fonte (apenas para burn_in=True)
        font_color: Cor da fonte (apenas para burn_in=True)
        outline_color: Cor do contorno (apenas para burn_in=True)
        progress_callback: Callback para progresso (opcional)
        
    Returns:
        EmbedResult com informações do resultado
    """
    video_path = Path(video_path)
    srt_path = Path(srt_path)
    
    if not video_path.exists():
        return EmbedResult(
            success=False,
            output_path="",
            srt_path=str(srt_path),
            error=f"Vídeo não encontrado: {video_path}"
        )
    
    if not srt_path.exists():
        return EmbedResult(
            success=False,
            output_path="",
            srt_path=str(srt_path),
            error=f"Arquivo SRT não encontrado: {srt_path}"
        )
    
    if not check_ffmpeg():
        return EmbedResult(
            success=False,
            output_path="",
            srt_path=str(srt_path),
            error="FFmpeg não encontrado. Instale o FFmpeg e adicione ao PATH."
        )
    
    # Gerar caminho de saída se não fornecido
    if output_path is None:
        suffix = "_legendado" if burn_in else "_sub"
        output_path = str(video_path.parent / f"{video_path.stem}{suffix}{video_path.suffix}")
    
    output_path = Path(output_path)
    
    try:
        if burn_in:
            # Hardcoded: queima a legenda diretamente no vídeo
            # Escapar caminho do SRT para filtro do FFmpeg (Windows)
            srt_escaped = str(srt_path).replace('\\', '/').replace(':', '\\:')
            
            style = f"FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3"
            
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vf', f"subtitles='{srt_escaped}':force_style='{style}'",
                '-c:a', 'copy',
                str(output_path)
            ]
        else:
            # Softcoded: adiciona como faixa de legenda separada
            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(srt_path),
                '-c', 'copy',
                '-c:s', 'mov_text',
                '-metadata:s:s:0', 'language=por',
                str(output_path)
            ]
        
        logger.info(f"Executando FFmpeg: {' '.join(cmd)}")
        
        if progress_callback:
            progress_callback("Embutindo legenda no vídeo...")
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos de timeout
        )
        
        if process.returncode != 0:
            error_msg = process.stderr.strip()
            
            # Tentar método alternativo se o filtro subtitles falhar
            if burn_in and "subtitles" in error_msg.lower():
                logger.warning("Filtro subtitles falhou, tentando método alternativo (softcoded)...")
                return embed_subtitle_in_video(
                    str(video_path), str(srt_path), str(output_path),
                    burn_in=False, progress_callback=progress_callback
                )
            
            logger.error(f"FFmpeg erro: {error_msg}")
            return EmbedResult(
                success=False,
                output_path=str(output_path),
                srt_path=str(srt_path),
                error=f"Erro do FFmpeg: {error_msg[-500:]}"  # Últimos 500 chars
            )
        
        if output_path.exists():
            logger.info(f"Legenda embutida com sucesso: {output_path}")
            return EmbedResult(
                success=True,
                output_path=str(output_path),
                srt_path=str(srt_path)
            )
        else:
            return EmbedResult(
                success=False,
                output_path=str(output_path),
                srt_path=str(srt_path),
                error="Arquivo de saída não foi gerado"
            )
            
    except subprocess.TimeoutExpired:
        return EmbedResult(
            success=False,
            output_path=str(output_path),
            srt_path=str(srt_path),
            error="Timeout: o processamento do FFmpeg excedeu 10 minutos"
        )
    except Exception as e:
        logger.error(f"Erro ao embutir legenda: {e}")
        return EmbedResult(
            success=False,
            output_path=str(output_path),
            srt_path=str(srt_path),
            error=str(e)
        )


def embed_subtitle_from_transcription(
    video_path: str,
    transcription_result: Dict[str, Any],
    output_path: Optional[str] = None,
    burn_in: bool = True,
    keep_srt: bool = True,
    **kwargs
) -> EmbedResult:
    """
    Conveniência: gera SRT a partir da transcrição e embutir no vídeo.
    
    Args:
        video_path: Caminho do vídeo original
        transcription_result: Resultado da transcrição
        output_path: Caminho de saída (opcional)
        burn_in: Queimar legenda no vídeo
        keep_srt: Manter arquivo SRT após embutir
        **kwargs: Argumentos extras para embed_subtitle_in_video
        
    Returns:
        EmbedResult
    """
    video_path = Path(video_path)
    
    if not is_video_file(str(video_path)):
        return EmbedResult(
            success=False,
            output_path="",
            srt_path="",
            error=f"Arquivo não é um vídeo suportado: {video_path.suffix}"
        )
    
    # Gerar SRT temporário ao lado do vídeo
    srt_path = video_path.parent / f"{video_path.stem}.srt"
    
    try:
        srt_path = generate_srt_file(transcription_result, srt_path)
        
        result = embed_subtitle_in_video(
            str(video_path),
            str(srt_path),
            output_path,
            burn_in=burn_in,
            **kwargs
        )
        
        # Remover SRT se não quiser manter
        if not keep_srt and srt_path.exists():
            srt_path.unlink()
            logger.info(f"SRT temporário removido: {srt_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no processo de embutir legenda: {e}")
        return EmbedResult(
            success=False,
            output_path="",
            srt_path=str(srt_path),
            error=str(e)
        )


__all__ = [
    'VIDEO_EXTENSIONS',
    'EmbedResult',
    'is_video_file',
    'check_ffmpeg',
    'get_ffmpeg_path',
    'generate_srt_file',
    'embed_subtitle_in_video',
    'embed_subtitle_from_transcription',
]
