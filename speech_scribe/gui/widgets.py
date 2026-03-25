from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from speech_scribe.core.config import AppConfig

class DropLabel(QLabel):
    """Label customizado que aceita arquivos arrastados"""
    file_dropped = pyqtSignal(str)

    def __init__(self, text="", parent=None, supported_formats=None):
        super().__init__(text, parent)
        self.supported_formats = supported_formats or AppConfig().supported_formats
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_style = """
            QLabel {
                border: 2px dashed #555555;
                border-radius: 8px;
                padding: 20px;
                background-color: #3b3b3b;
                color: #aaaaaa;
            }
        """
        self.hover_style = """
            QLabel {
                border: 2px dashed #0078d4;
                border-radius: 8px;
                padding: 20px;
                background-color: #4a4a4a;
                color: #0078d4;
            }
        """
        self.setStyleSheet(self.default_style)
    
    def dragEnterEvent(self, event):
        """Evento quando arquivo é arrastado para o widget"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                # Verificar se é um arquivo de áudio/vídeo
                if any(file_path.lower().endswith(ext) for ext in self.supported_formats):
                    event.acceptProposedAction()
                    self.setStyleSheet(self.hover_style)
                    self.setText("📥 Solte o arquivo aqui")
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Evento quando arquivo é movido sobre o widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Evento quando arquivo sai da área do widget"""
        self.setStyleSheet(self.default_style)
        self.setText("Ou arraste arquivos aqui")
    
    def dropEvent(self, event):
        """Evento quando arquivo é solto no widget"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                self.setStyleSheet(self.default_style)
                self.setText("✅ Arquivo recebido!")
                self.file_dropped.emit(file_path)
                event.acceptProposedAction()
                
                # Restaurar texto após 2 segundos
                QTimer.singleShot(2000, lambda: self.setText("Ou arraste arquivos aqui"))
                return
        event.ignore()

class ModernUIBuilder:
    """Construtor de interface moderna com componentes reutilizáveis"""
    
    def __init__(self, app_config: AppConfig):
        self.config = app_config
        self.theme = self._load_modern_theme()
    
    def _load_modern_theme(self) -> str:
        """Tema moderno para a aplicação"""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #3b3b3b;
        }
        
        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        
        QTabBar::tab:selected {
            background-color: #0078d4;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QTextEdit, QLineEdit {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px;
        }
        
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 6px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 6px;
        }
        """
    
    def create_file_selector(self, parent) -> QWidget:
        """Cria seletor de arquivo moderno com drag & drop"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Campo de arquivo
        file_edit = QLineEdit()
        file_edit.setPlaceholderText("Selecione um arquivo de áudio ou vídeo...")
        file_edit.setReadOnly(True)
        
        # Botão de seleção
        select_btn = QPushButton("📁 Selecionar")
        select_btn.setMaximumWidth(100)
        
        # Área de arrastar e soltar (usando classe customizada)
        drop_label = DropLabel("Ou arraste arquivos aqui")
        
        # Armazenar referências para acesso posterior
        widget.file_edit = file_edit
        widget.select_btn = select_btn
        widget.drop_label = drop_label
        
        layout.addWidget(file_edit, 3)
        layout.addWidget(select_btn, 1)
        layout.addWidget(drop_label, 2)
        
        return widget
    
    def create_progress_panel(self, parent) -> QWidget:
        """Cria painel de progresso moderno"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel("Status da Transcrição")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        
        # Barra de progresso
        progress = QProgressBar()
        progress.setTextVisible(True)
        progress.setMinimum(0)
        progress.setMaximum(100)
        
        # Status detalhado
        status_label = QLabel("Pronto para transcrever")
        status_label.setStyleSheet("color: #aaaaaa;")
        
        # Informações do sistema
        info_label = QLabel()
        info_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        layout.addWidget(title)
        layout.addWidget(progress)
        layout.addWidget(status_label)
        layout.addWidget(info_label)
        
        return widget
