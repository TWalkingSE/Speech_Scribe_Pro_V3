#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Melhorias de Interface - Speech Scribe Pro V3
Widgets e funcionalidades adicionais para a GUI
"""

from typing import Optional, List, Callable
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QLabel, QComboBox, QDialog, QListWidget, QListWidgetItem,
    QTextEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QTextCursor, QColor, QTextCharFormat, QShortcut


class SearchWidget(QWidget):
    """Widget de busca no texto"""
    
    # Sinais
    search_requested = pyqtSignal(str)  # Emitido quando busca é solicitada
    next_requested = pyqtSignal()       # Ir para próximo resultado
    prev_requested = pyqtSignal()       # Ir para resultado anterior
    closed = pyqtSignal()               # Widget fechado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.matches_count = 0
        self.current_match = 0
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Campo de busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar no texto... (Ctrl+F)")
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_next)
        layout.addWidget(self.search_input)
        
        # Contador de resultados
        self.results_label = QLabel("0/0")
        self.results_label.setMinimumWidth(50)
        layout.addWidget(self.results_label)
        
        # Botões de navegação
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setMaximumWidth(30)
        self.prev_btn.clicked.connect(self._on_prev)
        layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setMaximumWidth(30)
        self.next_btn.clicked.connect(self._on_next)
        layout.addWidget(self.next_btn)
        
        # Botão fechar
        self.close_btn = QPushButton("✕")
        self.close_btn.setMaximumWidth(30)
        self.close_btn.clicked.connect(self._on_close)
        layout.addWidget(self.close_btn)
        
        # Estilo
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 3px;
                background: #2d2d2d;
                color: white;
            }
            QPushButton {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 3px;
                background: #3d3d3d;
                color: white;
            }
            QPushButton:hover {
                background: #4d4d4d;
            }
        """)
    
    def _on_text_changed(self, text: str):
        self.search_requested.emit(text)
    
    def _on_next(self):
        self.next_requested.emit()
    
    def _on_prev(self):
        self.prev_requested.emit()
    
    def _on_close(self):
        self.hide()
        self.closed.emit()
    
    def update_results(self, current: int, total: int):
        """Atualiza contador de resultados"""
        self.matches_count = total
        self.current_match = current
        self.results_label.setText(f"{current}/{total}")
    
    def focus_search(self):
        """Foca no campo de busca"""
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def get_search_text(self) -> str:
        return self.search_input.text()


class TextSearcher:
    """Controlador de busca em QTextEdit"""
    
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.matches: List[int] = []
        self.current_index = -1
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("#FFD700"))
        self.highlight_format.setForeground(QColor("#000000"))
    
    def search(self, query: str) -> int:
        """
        Busca texto e retorna número de ocorrências.
        """
        # Limpar highlights anteriores
        self.clear_highlights()
        self.matches.clear()
        self.current_index = -1
        
        if not query:
            return 0
        
        # Buscar todas as ocorrências
        text = self.text_edit.toPlainText()
        start = 0
        while True:
            pos = text.lower().find(query.lower(), start)
            if pos == -1:
                break
            self.matches.append(pos)
            start = pos + 1
        
        # Destacar todas as ocorrências
        if self.matches:
            self._highlight_all(query)
            self.current_index = 0
            self._goto_match(0)
        
        return len(self.matches)
    
    def _highlight_all(self, query: str):
        """Destaca todas as ocorrências"""
        cursor = self.text_edit.textCursor()
        
        for pos in self.matches:
            cursor.setPosition(pos)
            cursor.setPosition(pos + len(query), QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(self.highlight_format)
    
    def _goto_match(self, index: int):
        """Vai para uma ocorrência específica"""
        if 0 <= index < len(self.matches):
            cursor = self.text_edit.textCursor()
            cursor.setPosition(self.matches[index])
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()
    
    def next_match(self) -> int:
        """Vai para próxima ocorrência"""
        if self.matches:
            self.current_index = (self.current_index + 1) % len(self.matches)
            self._goto_match(self.current_index)
        return self.current_index + 1
    
    def prev_match(self) -> int:
        """Vai para ocorrência anterior"""
        if self.matches:
            self.current_index = (self.current_index - 1) % len(self.matches)
            self._goto_match(self.current_index)
        return self.current_index + 1
    
    def clear_highlights(self):
        """Remove todos os highlights"""
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)
        cursor.clearSelection()


class HistoryDialog(QDialog):
    """Diálogo para visualizar histórico de transcrições"""
    
    record_selected = pyqtSignal(object)  # Emitido quando um registro é selecionado
    
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.setWindowTitle("📜 Histórico de Transcrições")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar no histórico...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Lista de transcrições
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)
        
        # Preview
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(100)
        layout.addWidget(self.preview)
        
        # Estatísticas
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Carregar")
        self.load_btn.clicked.connect(self.load_selected)
        btn_layout.addWidget(self.load_btn)
        
        self.delete_btn = QPushButton("🗑️ Excluir")
        self.delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("🧹 Limpar Tudo")
        self.clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("📤 Exportar Histórico")
        self.export_btn.clicked.connect(self.export_history)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Conectar seleção
        self.list_widget.currentRowChanged.connect(self.on_selection_changed)
        
        # Estilo
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: white; }
            QLineEdit, QTextEdit, QListWidget { 
                background: #2d2d2d; color: white; border: 1px solid #555; 
            }
            QPushButton { 
                padding: 8px 15px; background: #3d3d3d; color: white; 
                border: 1px solid #555; border-radius: 3px;
            }
            QPushButton:hover { background: #4d4d4d; }
        """)
    
    def load_history(self):
        """Carrega histórico na lista"""
        self.list_widget.clear()
        records = self.history.get_recent(50)
        
        for record in records:
            item = QListWidgetItem()
            item.setText(f"📄 {record.file_name} - {record.created_at[:10]} ({record.word_count} palavras)")
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.list_widget.addItem(item)
        
        # Estatísticas
        stats = self.history.get_stats()
        self.stats_label.setText(
            f"📊 Total: {stats['total_transcriptions']} transcrições | "
            f"{stats['total_words']:,} palavras | "
            f"{stats['total_duration_minutes']:.1f} min de áudio"
        )
    
    def on_search(self, query: str):
        """Busca no histórico"""
        self.list_widget.clear()
        
        if query:
            records = self.history.search(query)
        else:
            records = self.history.get_recent(50)
        
        for record in records:
            item = QListWidgetItem()
            item.setText(f"📄 {record.file_name} - {record.created_at[:10]}")
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.list_widget.addItem(item)
    
    def on_selection_changed(self, row: int):
        """Atualiza preview quando seleção muda"""
        if row >= 0:
            item = self.list_widget.item(row)
            record = item.data(Qt.ItemDataRole.UserRole)
            self.preview.setText(record.text[:500] + "..." if len(record.text) > 500 else record.text)
    
    def on_item_selected(self, item):
        """Carrega transcrição selecionada"""
        self.load_selected()
    
    def load_selected(self):
        """Carrega a transcrição selecionada"""
        item = self.list_widget.currentItem()
        if item:
            record = item.data(Qt.ItemDataRole.UserRole)
            self.record_selected.emit(record)
            self.accept()
    
    def delete_selected(self):
        """Exclui a transcrição selecionada"""
        item = self.list_widget.currentItem()
        if item:
            record = item.data(Qt.ItemDataRole.UserRole)
            if QMessageBox.question(self, "Confirmar", f"Excluir '{record.file_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.history.delete(record.id)
                self.load_history()
    
    def clear_history(self):
        """Limpa todo o histórico"""
        if QMessageBox.question(self, "Confirmar", "Limpar todo o histórico?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.load_history()

    def export_history(self):
        """Exporta histórico completo para JSON ou CSV"""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        from datetime import datetime

        filename, selected_filter = QFileDialog.getSaveFileName(
            self, "Exportar Histórico",
            f"historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "JSON (*.json);;CSV (*.csv)"
        )
        if not filename:
            return

        output = Path(filename)
        if output.suffix == '.csv':
            ok = self.history.export_csv(output)
        else:
            ok = self.history.export_json(output)

        if ok:
            QMessageBox.information(self, "Exportação", f"Histórico exportado para:\n{output}")
        else:
            QMessageBox.warning(self, "Erro", "Falha ao exportar histórico.")


class KeyboardShortcuts:
    """Gerenciador de atalhos de teclado"""
    
    def __init__(self, window):
        self.window = window
        self.shortcuts = {}
    
    def register(self, key_sequence: str, callback: Callable, description: str = ""):
        """Registra um atalho de teclado"""
        shortcut = QShortcut(QKeySequence(key_sequence), self.window)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = {
            'shortcut': shortcut,
            'callback': callback,
            'description': description
        }
    
    def setup_default_shortcuts(self, handlers: dict):
        """Configura atalhos padrão"""
        defaults = {
            'Ctrl+O': ('open_file', 'Abrir arquivo'),
            'Ctrl+S': ('save_file', 'Salvar transcrição'),
            'Ctrl+T': ('start_transcription', 'Iniciar transcrição'),
            'Ctrl+F': ('toggle_search', 'Buscar no texto'),
            'Ctrl+H': ('show_history', 'Mostrar histórico'),
            'Ctrl+E': ('export_file', 'Exportar'),
            'Escape': ('close_search', 'Fechar busca'),
            'F5': ('refresh', 'Atualizar'),
        }
        
        for key, (handler_name, desc) in defaults.items():
            if handler_name in handlers:
                self.register(key, handlers[handler_name], desc)
    
    def get_shortcuts_list(self) -> List[tuple]:
        """Retorna lista de atalhos para exibição"""
        return [(key, info['description']) for key, info in self.shortcuts.items()]


__all__ = [
    'SearchWidget',
    'TextSearcher', 
    'HistoryDialog',
    'KeyboardShortcuts'
]
