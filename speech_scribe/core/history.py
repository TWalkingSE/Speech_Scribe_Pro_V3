#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📜 Histórico de Transcrições - Speech Scribe Pro V3
Salva e gerencia histórico de transcrições automaticamente
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from speech_scribe.utils.logger import logger


@dataclass
class TranscriptionRecord:
    """Registro de uma transcrição"""
    id: int = 0
    file_path: str = ""
    file_name: str = ""
    text: str = ""
    language: str = ""
    model: str = ""
    duration_seconds: float = 0.0
    processing_time: float = 0.0
    word_count: int = 0
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionRecord':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TranscriptionHistory:
    """
    Gerenciador de histórico de transcrições.
    
    Features:
    - Armazenamento em SQLite
    - Busca por texto
    - Limite de registros
    - Exportação/Importação
    """
    
    def __init__(self, db_path: Optional[Path] = None, max_records: int = 100):
        """
        Inicializa o histórico.
        
        Args:
            db_path: Caminho do banco de dados
            max_records: Número máximo de registros a manter
        """
        self.db_path = db_path or (Path.home() / ".speech_scribe_v3" / "history.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_records = max_records
        
        self._init_db()
        logger.info(f"Histórico inicializado: {self.db_path}")
    
    def _init_db(self):
        """Inicializa o banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    file_name TEXT,
                    text TEXT,
                    language TEXT,
                    model TEXT,
                    duration_seconds REAL,
                    processing_time REAL,
                    word_count INTEGER,
                    created_at TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON transcriptions(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON transcriptions(file_name)')
            conn.commit()
    
    def add(self, file_path: str, text: str, language: str = "", model: str = "",
            duration_seconds: float = 0.0, processing_time: float = 0.0) -> int:
        """
        Adiciona uma transcrição ao histórico.
        
        Returns:
            ID do registro criado
        """
        file_name = Path(file_path).name
        word_count = len(text.split())
        created_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO transcriptions 
                (file_path, file_name, text, language, model, duration_seconds, processing_time, word_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, file_name, text, language, model, duration_seconds, processing_time, word_count, created_at))
            record_id = cursor.lastrowid
            conn.commit()
        
        # Limpar registros antigos
        self._cleanup()
        
        logger.info(f"📜 Transcrição salva no histórico: {file_name}")
        return record_id
    
    def get(self, record_id: int) -> Optional[TranscriptionRecord]:
        """Obtém um registro pelo ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM transcriptions WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            
            if row:
                return TranscriptionRecord(**dict(row))
        return None
    
    def get_recent(self, limit: int = 10) -> List[TranscriptionRecord]:
        """Obtém as transcrições mais recentes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM transcriptions 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [TranscriptionRecord(**dict(row)) for row in cursor.fetchall()]
    
    def search(self, query: str, limit: int = 20) -> List[TranscriptionRecord]:
        """
        Busca transcrições por texto.
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM transcriptions 
                WHERE text LIKE ? OR file_name LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            
            return [TranscriptionRecord(**dict(row)) for row in cursor.fetchall()]
    
    def delete(self, record_id: int) -> bool:
        """Remove um registro"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM transcriptions WHERE id = ?', (record_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self):
        """Limpa todo o histórico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM transcriptions')
            conn.commit()
        logger.info("Histórico limpo")
    
    def _cleanup(self):
        """Remove registros antigos para manter o limite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM transcriptions 
                WHERE id NOT IN (
                    SELECT id FROM transcriptions 
                    ORDER BY created_at DESC 
                    LIMIT ?
                )
            ''', (self.max_records,))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do histórico"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(word_count) as total_words,
                    SUM(duration_seconds) as total_duration,
                    AVG(processing_time) as avg_processing_time
                FROM transcriptions
            ''')
            row = cursor.fetchone()
            
            return {
                'total_transcriptions': row[0] or 0,
                'total_words': row[1] or 0,
                'total_duration_minutes': (row[2] or 0) / 60,
                'avg_processing_time': row[3] or 0
            }
    
    def export_json(self, output_path: Path) -> bool:
        """Exporta histórico para JSON"""
        try:
            records = self.get_recent(self.max_records)
            data = {
                'exported_at': datetime.now().isoformat(),
                'records': [r.to_dict() for r in records]
            }
            output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar histórico: {e}")
            return False

    def export_csv(self, output_path: Path) -> bool:
        """Exporta histórico para CSV"""
        import csv
        try:
            records = self.get_recent(self.max_records)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'file_path', 'file_name', 'language', 'model',
                    'duration_seconds', 'processing_time', 'word_count', 'created_at', 'text'
                ])
                for r in records:
                    writer.writerow([
                        r.id, r.file_path, r.file_name, r.language, r.model,
                        r.duration_seconds, r.processing_time, r.word_count, r.created_at,
                        r.text[:500]  # Limitar texto para CSV
                    ])
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar histórico CSV: {e}")
            return False


# Instância global
_history: Optional[TranscriptionHistory] = None


def get_history() -> TranscriptionHistory:
    """Obtém instância global do histórico"""
    global _history
    if _history is None:
        _history = TranscriptionHistory()
    return _history


__all__ = ['TranscriptionRecord', 'TranscriptionHistory', 'get_history']
