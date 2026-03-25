#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎨 Themes - Speech Scribe Pro V3
Sistema de temas Dark/Light para a interface
"""

from typing import Dict
from speech_scribe.utils.logger import logger


class ThemeManager:
    """Gerenciador de temas da aplicação"""
    
    LIGHT_THEME = {
        'name': 'Light',
        'background': '#ffffff',
        'surface': '#f5f5f5',
        'primary': '#0078d4',
        'primary_hover': '#006cbd',
        'secondary': '#6c757d',
        'text': '#212529',
        'text_secondary': '#6c757d',
        'border': '#dee2e6',
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'input_bg': '#ffffff',
        'input_border': '#ced4da',
        'button_bg': '#e9ecef',
        'button_hover': '#dee2e6',
        'scrollbar_bg': '#f1f1f1',
        'scrollbar_handle': '#c1c1c1',
        'tab_bg': '#e9ecef',
        'tab_selected': '#ffffff',
        'group_bg': '#f8f9fa',
    }
    
    DARK_THEME = {
        'name': 'Dark',
        'background': '#1e1e1e',
        'surface': '#252526',
        'primary': '#0078d4',
        'primary_hover': '#1e90ff',
        'secondary': '#6c757d',
        'text': '#e0e0e0',
        'text_secondary': '#a0a0a0',
        'border': '#3c3c3c',
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'input_bg': '#2d2d2d',
        'input_border': '#3c3c3c',
        'button_bg': '#3c3c3c',
        'button_hover': '#4a4a4a',
        'scrollbar_bg': '#2d2d2d',
        'scrollbar_handle': '#5a5a5a',
        'tab_bg': '#2d2d2d',
        'tab_selected': '#1e1e1e',
        'group_bg': '#252526',
    }
    
    def __init__(self):
        self.current_theme_name = 'light'
        self.themes = {
            'light': self.LIGHT_THEME,
            'dark': self.DARK_THEME,
        }
        
    def get_theme(self, name: str = None) -> Dict:
        """Retorna tema por nome"""
        if name is None:
            name = self.current_theme_name
        return self.themes.get(name, self.LIGHT_THEME)
        
    def set_theme(self, name: str):
        """Define tema atual"""
        if name in self.themes:
            self.current_theme_name = name
            logger.info(f"Tema alterado para: {name}")
        else:
            logger.warning(f"Tema não encontrado: {name}")
            
    def get_stylesheet(self, theme_name: str = None) -> str:
        """Gera stylesheet CSS para o tema"""
        theme = self.get_theme(theme_name)
        
        return f"""
            /* ===== TEMA: {theme['name']} ===== */
            
            /* Janela principal */
            QMainWindow, QWidget {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            
            /* Labels */
            QLabel {{
                color: {theme['text']};
            }}
            
            /* Botões */
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {theme['button_hover']};
                border-color: {theme['primary']};
            }}
            
            QPushButton:pressed {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            QPushButton:disabled {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
            }}
            
            /* Botões primários */
            QPushButton[primary="true"] {{
                background-color: {theme['primary']};
                color: white;
                border: none;
            }}
            
            QPushButton[primary="true"]:hover {{
                background-color: {theme['primary_hover']};
            }}
            
            /* Inputs de texto */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['text']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {theme['primary']};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {theme['primary']};
            }}
            
            /* ComboBox */
            QComboBox {{
                background-color: {theme['input_bg']};
                color: {theme['text']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 100px;
            }}
            
            QComboBox:hover {{
                border-color: {theme['primary']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                selection-background-color: {theme['primary']};
            }}
            
            /* Checkboxes */
            QCheckBox {{
                color: {theme['text']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {theme['border']};
                border-radius: 3px;
                background-color: {theme['input_bg']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {theme['primary']};
                border-color: {theme['primary']};
            }}
            
            /* GroupBox */
            QGroupBox {{
                background-color: {theme['group_bg']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {theme['text']};
            }}
            
            /* TabWidget */
            QTabWidget::pane {{
                background-color: {theme['background']};
                border: 1px solid {theme['border']};
                border-top: none;
            }}
            
            QTabBar::tab {{
                background-color: {theme['tab_bg']};
                color: {theme['text_secondary']};
                border: 1px solid {theme['border']};
                border-bottom: none;
                padding: 10px 20px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme['tab_selected']};
                color: {theme['text']};
                border-bottom: 2px solid {theme['primary']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {theme['button_hover']};
            }}
            
            /* ProgressBar */
            QProgressBar {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                text-align: center;
                color: {theme['text']};
            }}
            
            QProgressBar::chunk {{
                background-color: {theme['primary']};
                border-radius: 3px;
            }}
            
            /* Sliders */
            QSlider::groove:horizontal {{
                background-color: {theme['surface']};
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background-color: {theme['primary']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {theme['primary_hover']};
            }}
            
            /* ScrollBars */
            QScrollBar:vertical {{
                background-color: {theme['scrollbar_bg']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['primary']};
            }}
            
            QScrollBar:horizontal {{
                background-color: {theme['scrollbar_bg']};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {theme['scrollbar_handle']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::add-line, QScrollBar::sub-line {{
                width: 0;
                height: 0;
            }}
            
            /* ListWidget */
            QListWidget {{
                background-color: {theme['input_bg']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme['border']};
            }}
            
            QListWidget::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            QListWidget::item:hover:!selected {{
                background-color: {theme['button_hover']};
            }}
            
            /* Menu */
            QMenuBar {{
                background-color: {theme['surface']};
                color: {theme['text']};
            }}
            
            QMenuBar::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            QMenu {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
            }}
            
            QMenu::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            /* StatusBar */
            QStatusBar {{
                background-color: {theme['surface']};
                color: {theme['text_secondary']};
                border-top: 1px solid {theme['border']};
            }}
            
            /* ToolTip */
            QToolTip {{
                background-color: {theme['surface']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                padding: 4px 8px;
            }}
            
            /* MessageBox */
            QMessageBox {{
                background-color: {theme['background']};
            }}
            
            QMessageBox QLabel {{
                color: {theme['text']};
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {theme['border']};
            }}
            
            QSplitter::handle:hover {{
                background-color: {theme['primary']};
            }}
        """
        
    def get_available_themes(self) -> list:
        """Retorna lista de temas disponíveis"""
        return list(self.themes.keys())
        
    def toggle_theme(self) -> str:
        """Alterna entre light e dark"""
        if self.current_theme_name == 'light':
            self.set_theme('dark')
        else:
            self.set_theme('light')
        return self.current_theme_name


# Instância global
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Retorna instância global do gerenciador de temas"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
