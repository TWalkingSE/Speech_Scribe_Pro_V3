"""
Utilitários de formatação de legendas compartilhados entre CLI e GUI.
"""

from typing import List


def format_timestamp_srt(seconds: float) -> str:
    """Formata timestamp para SRT (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Formata timestamp para VTT (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_srt(segments: List[dict]) -> str:
    """Formata segmentos em formato SRT."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_srt(seg.get('start', 0))
        end = format_timestamp_srt(seg.get('end', 0))
        text = seg.get('text', '').strip()
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def format_vtt(segments: List[dict]) -> str:
    """Formata segmentos em formato VTT."""
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = format_timestamp_vtt(seg.get('start', 0))
        end = format_timestamp_vtt(seg.get('end', 0))
        text = seg.get('text', '').strip()
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)
