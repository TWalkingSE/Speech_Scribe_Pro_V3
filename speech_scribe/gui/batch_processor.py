#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📦 Batch Processor - Speech Scribe Pro V3
Processamento em lote de múltiplos arquivos
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QProgressBar, QLabel, QFileDialog, QGroupBox,
    QComboBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

from speech_scribe.utils.logger import logger
from speech_scribe.core.config import AppConfig


class DropListWidget(QListWidget):
    """QListWidget com suporte a drag & drop de arquivos"""
    files_dropped = pyqtSignal(list)  # Lista de caminhos de arquivos
    
    def __init__(self, supported_formats, parent=None):
        super().__init__(parent)
        self.supported_formats = supported_formats
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    p = Path(file_path)
                    if p.is_file() and any(file_path.lower().endswith(ext) for ext in self.supported_formats):
                        paths.append(file_path)
                    elif p.is_dir():
                        for ext in self.supported_formats:
                            for f in p.glob(f"*{ext}"):
                                paths.append(str(f))
            if paths:
                self.files_dropped.emit(paths)
                event.acceptProposedAction()
                return
        event.ignore()


class BatchItem:
    """Representa um item na fila de processamento"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.status = "pending"  # pending, processing, completed, error
        self.progress = 0
        self.result = None
        self.error = None
        
    @property
    def filename(self) -> str:
        return Path(self.file_path).name


class BatchWorker(QThread):
    """Worker thread para processamento em lote"""
    item_started = pyqtSignal(int)  # index
    item_progress = pyqtSignal(int, int)  # index, progress
    item_completed = pyqtSignal(int, dict)  # index, result
    item_error = pyqtSignal(int, str)  # index, error
    batch_completed = pyqtSignal()
    
    def __init__(self, items: list, engine, model: str, language: str, 
                 diarization=None, enable_diarization=False):
        super().__init__()
        self.items = items
        self.engine = engine
        self.model = model
        self.language = language
        self.diarization = diarization
        self.enable_diarization = enable_diarization
        self._is_cancelled = False
        
    def run(self):
        """Processa todos os itens da fila usando lógica direta do faster-whisper"""
        import time
        
        # Carregar modelo uma vez para todo o lote
        model = self.engine.load_model(self.model)
        if not model:
            for i in range(len(self.items)):
                self.item_error.emit(i, "Falha ao carregar modelo")
            self.batch_completed.emit()
            return
        
        transcribe_kwargs = {
            'language': None if self.language == "auto" else self.language,
            'vad_filter': True,
            'word_timestamps': True,
            'beam_size': self.engine.hardware.optimizations['beam_size'],
            'best_of': self.engine.hardware.optimizations['best_of'],
            'condition_on_previous_text': False,
        }
        
        for i, item in enumerate(self.items):
            if self._is_cancelled:
                break
                
            self.item_started.emit(i)
            
            try:
                start_time = time.time()
                
                # Diarização opcional
                speaker_segments = []
                if self.enable_diarization and self.diarization and self.diarization.available:
                    self.item_progress.emit(i, 10)
                    speaker_segments = self.diarization.process_diarization(item.file_path)
                    self.item_progress.emit(i, 30)
                
                if self._is_cancelled:
                    break
                
                # Transcrição direta com progresso
                self.item_progress.emit(i, 35)
                
                # Obter duração do áudio
                audio_duration = 0.0
                try:
                    import librosa
                    audio_duration = librosa.get_duration(path=item.file_path)
                except Exception:
                    pass
                
                segments_generator, info = model.transcribe(item.file_path, **transcribe_kwargs)
                
                segments_list = []
                for segment in segments_generator:
                    if self._is_cancelled:
                        break
                    segments_list.append(segment)
                    
                    # Progresso baseado no timestamp
                    if audio_duration > 0:
                        seg_progress = int((segment.end / audio_duration) * 55)  # 35-90%
                        self.item_progress.emit(i, min(90, 35 + seg_progress))
                
                if self._is_cancelled:
                    break
                
                processing_time = time.time() - start_time
                full_text = ' '.join([seg.text for seg in segments_list])
                
                result = {
                    'text': full_text,
                    'segments': [
                        {
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text,
                            'words': seg.words if hasattr(seg, 'words') else []
                        }
                        for seg in segments_list
                    ],
                    'language': info.language,
                    'duration': info.duration,
                    'processing_time': processing_time,
                    'model_used': self.model,
                    'device_used': self.engine.hardware.optimizations['device'],
                }
                
                self.item_progress.emit(i, 92)
                
                # Combinar com diarização
                if speaker_segments and 'segments' in result:
                    enhanced_segments = self.diarization.merge_with_transcription(
                        result['segments'], speaker_segments
                    )
                    result['segments'] = enhanced_segments
                    result['diarization_enabled'] = True
                else:
                    result['diarization_enabled'] = False
                
                self.item_progress.emit(i, 100)
                self.item_completed.emit(i, result)
                
            except Exception as e:
                self.item_error.emit(i, str(e))
                
        self.batch_completed.emit()
        
    def cancel(self):
        """Cancela processamento"""
        self._is_cancelled = True


class BatchProcessorWidget(QWidget):
    """Widget para processamento em lote"""
    
    def __init__(self, engine, diarization=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.diarization = diarization
        self.items = []
        self.worker = None
        self.config = AppConfig()
        
        self._init_ui()
        
    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout(self)
        
        # Lista de arquivos
        files_group = QGroupBox("📁 Arquivos na Fila")
        files_layout = QVBoxLayout(files_group)
        
        self.file_list = DropListWidget(self.config.supported_formats)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.files_dropped.connect(self._on_files_dropped)
        files_layout.addWidget(self.file_list)
        
        drop_hint = QLabel("💡 Arraste arquivos ou pastas para cá")
        drop_hint.setStyleSheet("color: #888; font-style: italic; padding: 2px;")
        files_layout.addWidget(drop_hint)
        
        # Botões de arquivo
        file_buttons = QHBoxLayout()
        
        self.add_files_btn = QPushButton("➕ Adicionar Arquivos")
        self.add_folder_btn = QPushButton("📂 Adicionar Pasta")
        self.remove_btn = QPushButton("🗑️ Remover Selecionados")
        self.clear_btn = QPushButton("🧹 Limpar Lista")
        
        file_buttons.addWidget(self.add_files_btn)
        file_buttons.addWidget(self.add_folder_btn)
        file_buttons.addWidget(self.remove_btn)
        file_buttons.addWidget(self.clear_btn)
        
        files_layout.addLayout(file_buttons)
        layout.addWidget(files_group)
        
        # Configurações
        config_group = QGroupBox("⚙️ Configurações do Lote")
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["large-v3", "large-v2", "medium", "small", "base", "tiny"])
        config_layout.addWidget(self.model_combo)
        
        config_layout.addWidget(QLabel("Idioma:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["auto", "pt", "en", "es", "fr", "de", "it", "ja", "zh"])
        config_layout.addWidget(self.language_combo)
        
        self.diarization_check = QCheckBox("Diarização")
        self.diarization_check.setEnabled(self.diarization and self.diarization.available)
        config_layout.addWidget(self.diarization_check)
        
        config_layout.addStretch()
        layout.addWidget(config_group)
        
        # Progresso geral
        progress_group = QGroupBox("📊 Progresso")
        progress_layout = QVBoxLayout(progress_group)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setFormat("Total: %v/%m arquivos")
        progress_layout.addWidget(self.overall_progress)
        
        self.current_progress = QProgressBar()
        self.current_progress.setFormat("Arquivo atual: %p%")
        progress_layout.addWidget(self.current_progress)
        
        self.status_label = QLabel("Pronto para processar")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Iniciar Processamento")
        self.start_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px;")
        
        self.cancel_btn = QPushButton("⏹️ Cancelar")
        self.cancel_btn.setEnabled(False)
        
        self.export_all_btn = QPushButton("📤 Exportar Todos")
        self.export_all_btn.setEnabled(False)
        
        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.export_all_btn)
        
        layout.addLayout(action_layout)
        
        # Conectar sinais
        self._connect_signals()
        
    def _connect_signals(self):
        """Conecta sinais"""
        self.add_files_btn.clicked.connect(self._add_files)
        self.add_folder_btn.clicked.connect(self._add_folder)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.clear_btn.clicked.connect(self._clear_list)
        self.start_btn.clicked.connect(self._start_processing)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.export_all_btn.clicked.connect(self._export_all)
        
    def _on_files_dropped(self, file_paths: list):
        """Callback quando arquivos são arrastados para a lista"""
        for file_path in file_paths:
            self._add_item(file_path)
        self.status_label.setText(f"{len(file_paths)} arquivo(s) adicionado(s) via drag & drop")
    
    def _add_files(self):
        """Adiciona arquivos à fila"""
        extensions = " ".join([f"*{ext}" for ext in self.config.supported_formats])
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos",
            "",
            f"Arquivos de Mídia ({extensions})"
        )
        
        for file_path in files:
            self._add_item(file_path)
            
    def _add_folder(self):
        """Adiciona todos os arquivos de uma pasta"""
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        
        if folder:
            folder_path = Path(folder)
            for ext in self.config.supported_formats:
                for file_path in folder_path.glob(f"*{ext}"):
                    self._add_item(str(file_path))
                    
    def _add_item(self, file_path: str):
        """Adiciona um item à lista"""
        # Evitar duplicatas
        for item in self.items:
            if item.file_path == file_path:
                return
                
        item = BatchItem(file_path)
        self.items.append(item)
        
        list_item = QListWidgetItem(f"⏳ {item.filename}")
        list_item.setData(Qt.ItemDataRole.UserRole, len(self.items) - 1)
        self.file_list.addItem(list_item)
        
        self._update_progress()
        
    def _remove_selected(self):
        """Remove itens selecionados"""
        for item in self.file_list.selectedItems():
            index = item.data(Qt.ItemDataRole.UserRole)
            if index < len(self.items):
                self.items[index] = None
            self.file_list.takeItem(self.file_list.row(item))
            
        # Limpar Nones
        self.items = [i for i in self.items if i is not None]
        self._refresh_list()
        
    def _clear_list(self):
        """Limpa toda a lista"""
        self.items.clear()
        self.file_list.clear()
        self._update_progress()
        
    def _refresh_list(self):
        """Atualiza lista visual"""
        self.file_list.clear()
        for i, item in enumerate(self.items):
            status_icon = {
                "pending": "⏳",
                "processing": "🔄",
                "completed": "✅",
                "error": "❌"
            }.get(item.status, "⏳")
            
            list_item = QListWidgetItem(f"{status_icon} {item.filename}")
            list_item.setData(Qt.ItemDataRole.UserRole, i)
            self.file_list.addItem(list_item)
            
    def _update_progress(self):
        """Atualiza barra de progresso geral"""
        total = len(self.items)
        completed = sum(1 for i in self.items if i.status in ["completed", "error"])
        
        self.overall_progress.setMaximum(max(1, total))
        self.overall_progress.setValue(completed)
        
    def _start_processing(self):
        """Inicia processamento em lote"""
        if not self.items:
            QMessageBox.warning(self, "Aviso", "Adicione arquivos à fila primeiro!")
            return
            
        # Filtrar apenas pendentes
        pending_items = [i for i in self.items if i.status == "pending"]
        
        if not pending_items:
            QMessageBox.warning(self, "Aviso", "Todos os arquivos já foram processados!")
            return
            
        self.worker = BatchWorker(
            pending_items,
            self.engine,
            self.model_combo.currentText(),
            self.language_combo.currentText(),
            self.diarization,
            self.diarization_check.isChecked()
        )
        
        self.worker.item_started.connect(self._on_item_started)
        self.worker.item_progress.connect(self._on_item_progress)
        self.worker.item_completed.connect(self._on_item_completed)
        self.worker.item_error.connect(self._on_item_error)
        self.worker.batch_completed.connect(self._on_batch_completed)
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Processando...")
        
        self.worker.start()
        
    def _cancel_processing(self):
        """Cancela processamento"""
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelando...")
            
    def _on_item_started(self, index: int):
        """Callback quando item inicia"""
        if index < len(self.items):
            self.items[index].status = "processing"
            self._refresh_list()
            self.status_label.setText(f"Processando: {self.items[index].filename}")
            
    def _on_item_progress(self, index: int, progress: int):
        """Callback de progresso do item"""
        self.current_progress.setValue(progress)
        
    def _on_item_completed(self, index: int, result: dict):
        """Callback quando item completa"""
        if index < len(self.items):
            self.items[index].status = "completed"
            self.items[index].result = result
            self.items[index].progress = 100
            self._refresh_list()
            self._update_progress()
            logger.info(f"Batch: {self.items[index].filename} concluído")
            
    def _on_item_error(self, index: int, error: str):
        """Callback quando item falha"""
        if index < len(self.items):
            self.items[index].status = "error"
            self.items[index].error = error
            self._refresh_list()
            self._update_progress()
            logger.error(f"Batch: {self.items[index].filename} erro: {error}")
            
    def _on_batch_completed(self):
        """Callback quando lote completa"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_all_btn.setEnabled(True)
        
        completed = sum(1 for i in self.items if i.status == "completed")
        errors = sum(1 for i in self.items if i.status == "error")
        
        self.status_label.setText(f"Concluído! ✅ {completed} sucesso, ❌ {errors} erros")
        
        # Auto-salvar todas as transcrições em um único arquivo
        if completed > 0:
            self._auto_save_consolidated()
        
        error_details = ""
        if errors > 0:
            error_items = [i for i in self.items if i.status == "error"]
            error_details = "\n\nArquivos com erro:\n" + "\n".join(
                f"  • {i.filename}: {i.error}" for i in error_items
            )
        
        QMessageBox.information(
            self, 
            "Processamento Concluído",
            f"Processamento em lote concluído!\n\n"
            f"✅ Sucesso: {completed}\n❌ Erros: {errors}"
            f"{error_details}"
        )
    
    def _auto_save_consolidated(self):
        """Salva automaticamente todas as transcrições em um único arquivo consolidado"""
        try:
            completed_items = [i for i in self.items if i.status == "completed" and i.result]
            if not completed_items:
                return
            
            # Usar pasta do primeiro arquivo como destino padrão
            first_file = Path(completed_items[0].file_path)
            output_dir = first_file.parent
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = output_dir / f"transcricoes_lote_{timestamp}.txt"
            
            content = self._build_consolidated_content(completed_items)
            output_file.write_text(content, encoding='utf-8')
            
            self.status_label.setText(
                f"Concluído! ✅ {len(completed_items)} transcrições salvas em: {output_file.name}"
            )
            logger.info(f"Batch: Transcrições consolidadas salvas em {output_file}")
            
        except Exception as e:
            logger.error(f"Erro ao auto-salvar transcrições: {e}")
    
    def _build_consolidated_content(self, completed_items: list) -> str:
        """
        Monta o conteúdo consolidado de todas as transcrições.
        
        Formato:
        Caminho: <caminho_do_arquivo>
        
        <texto da transcrição>
        
        ============================================================
        """
        parts = []
        separator = "=" * 60
        
        for item in completed_items:
            text = item.result.get('text', '').strip()
            path = item.file_path
            
            parts.append(f"Caminho: {path}")
            parts.append("")
            parts.append(text)
            parts.append("")
            parts.append(separator)
            parts.append("")
        
        return "\n".join(parts)
        
    def _export_all(self):
        """Exporta resultados em múltiplos formatos"""
        completed_items = [i for i in self.items if i.status == "completed" and i.result]
        
        if not completed_items:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado para exportar!")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        formats = ["TXT (consolidado)", "SRT (individual por arquivo)", "VTT (individual por arquivo)", "JSON (individual por arquivo)"]
        selected, ok = QInputDialog.getItem(
            self, "Formato de Exportação", "Selecione o formato:", formats, 0, False
        )
        
        if not ok:
            return
        
        if "consolidado" in selected:
            self._export_consolidated_txt(completed_items)
        elif "SRT" in selected:
            self._export_individual(completed_items, "srt")
        elif "VTT" in selected:
            self._export_individual(completed_items, "vtt")
        elif "JSON" in selected:
            self._export_individual(completed_items, "json")
    
    def _export_consolidated_txt(self, completed_items: list):
        """Exporta todas as transcrições em um único TXT"""
        from datetime import datetime
        default_name = f"transcricoes_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Transcrições Consolidadas", default_name,
            "Arquivo de Texto (*.txt);;Todos os arquivos (*.*)"
        )
        
        if filename:
            content = self._build_consolidated_content(completed_items)
            Path(filename).write_text(content, encoding='utf-8')
            QMessageBox.information(self, "Exportação Concluída",
                f"{len(completed_items)} transcrições salvas em:\n{filename}")
            logger.info(f"Batch TXT: {len(completed_items)} exportadas para {filename}")
    
    def _export_individual(self, completed_items: list, fmt: str):
        """Exporta cada transcrição como arquivo individual no formato escolhido"""
        output_dir = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        if not output_dir:
            return
        
        output_path = Path(output_dir)
        count = 0
        
        for item in completed_items:
            result = item.result
            segments = result.get('segments', [])
            base_name = Path(item.file_path).stem
            file_out = output_path / f"{base_name}.{fmt}"
            
            try:
                if fmt == "srt":
                    content = self._build_srt(segments)
                elif fmt == "vtt":
                    content = self._build_vtt(segments)
                elif fmt == "json":
                    import json
                    content = json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    content = result.get('text', '')
                
                file_out.write_text(content, encoding='utf-8')
                count += 1
            except Exception as e:
                logger.error(f"Erro ao exportar {base_name}.{fmt}: {e}")
        
        QMessageBox.information(self, "Exportação Concluída",
            f"{count} arquivos .{fmt} exportados para:\n{output_dir}")
        logger.info(f"Batch {fmt.upper()}: {count} arquivos exportados para {output_dir}")
    
    @staticmethod
    def _build_srt(segments: list) -> str:
        """Gera conteúdo SRT a partir de segmentos"""
        lines = []
        for i, seg in enumerate(segments, 1):
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = seg.get('text', '').strip()
            lines.append(str(i))
            lines.append(f"{BatchProcessorWidget._fmt_srt_time(start)} --> {BatchProcessorWidget._fmt_srt_time(end)}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def _build_vtt(segments: list) -> str:
        """Gera conteúdo VTT a partir de segmentos"""
        lines = ["WEBVTT", ""]
        for seg in segments:
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            text = seg.get('text', '').strip()
            lines.append(f"{BatchProcessorWidget._fmt_vtt_time(start)} --> {BatchProcessorWidget._fmt_vtt_time(end)}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def _fmt_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    @staticmethod
    def _fmt_vtt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    
    def get_results(self) -> list:
        """Retorna lista de resultados"""
        return [i.result for i in self.items if i.status == "completed" and i.result]
