#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔄 Threads - Speech Scribe Pro V3
Threads para processamento assíncrono com progresso real
"""

import time
from PyQt6.QtCore import QThread, pyqtSignal

from speech_scribe.utils.logger import logger


class TranscriptionThread(QThread):
    """Thread para transcrição assíncrona com suporte à diarização e progresso real"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    model_loading = pyqtSignal(str)  # Emitido quando modelo está sendo carregado

    def __init__(self, file_path, model, language, engine, diarization=None, enable_diarization=False):
        super().__init__()
        self.file_path = file_path
        self.model = model
        self.language = language
        self.engine = engine
        self.diarization = diarization
        self.enable_diarization = enable_diarization
        self._is_cancelled = False
    
    def cancel(self):
        """Cancela a transcrição"""
        self._is_cancelled = True
    
    def run(self):
        """Executa transcrição em thread separada com diarização opcional e progresso real"""
        result = None
        speaker_segments = []
        
        try:
            self.progress.emit(2)
            self.status.emit("Iniciando processamento...")
            
            # Obter duração do áudio para calcular progresso real
            audio_duration = self._get_audio_duration()
            
            # Executar diarização se habilitada (0-30%)
            if self.enable_diarization and self.diarization and self.diarization.available:
                self.status.emit("Processando diarização...")
                self.progress.emit(5)
                
                speaker_segments = self.diarization.process_diarization(self.file_path)
                
                if speaker_segments:
                    num_speakers = len(set(s['speaker'] for s in speaker_segments))
                    self.status.emit(f"Diarização: {num_speakers} oradores detectados")
                else:
                    self.status.emit("Diarização não retornou resultados")
                
                self.progress.emit(30)
            else:
                self.progress.emit(10)
            
            if self._is_cancelled:
                self.status.emit("Transcrição cancelada")
                return

            # Executar transcrição com progresso real (30-95%)
            self.status.emit("Transcrevendo áudio...")
            
            result = self._transcribe_with_progress(audio_duration)
            
            if self._is_cancelled:
                self.status.emit("Transcrição cancelada")
                return
            
            if result is None:
                raise Exception("Transcrição retornou resultado vazio")
            
            self.progress.emit(95)
            
            # Combinar com diarização se disponível
            if speaker_segments and 'segments' in result:
                self.status.emit("Combinando transcrição com diarização...")
                
                enhanced_segments = self.diarization.merge_with_transcription(
                    result['segments'], speaker_segments
                )
                result['segments'] = enhanced_segments
                
                result['speaker_stats'] = self.diarization.get_speaker_statistics(enhanced_segments)
                result['speaker_segments'] = speaker_segments
                result['diarization_enabled'] = True
            else:
                result['diarization_enabled'] = False
            
            self.progress.emit(100)
            self.status.emit("Processamento concluído!")
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = f"Erro na transcrição: {str(e)}"
            if result is None:
                error_msg += " (Resultado não foi gerado)"
            logger.error(error_msg)
            self.error.emit(error_msg)
    
    def _get_audio_duration(self) -> float:
        """Obtém duração do áudio em segundos"""
        try:
            import warnings
            import librosa
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="PySoundFile failed")
                warnings.filterwarnings("ignore", message="librosa.core.audio.__audioread_load")
                duration = librosa.get_duration(path=self.file_path)
            return duration
        except Exception:
            return 0.0
            
    def _transcribe_with_progress(self, audio_duration: float) -> dict:
        """Executa transcrição emitindo progresso real baseado nos segmentos"""
        
        # Carregar modelo
        self.model_loading.emit(f"Carregando modelo {self.model}...")
        model = self.engine.load_model(self.model)
        if not model:
            raise Exception("Falha ao carregar modelo")
        self.model_loading.emit("")  # Sinaliza que carregamento terminou
            
        start_time = time.time()
        device = self.engine.hardware.optimizations['device']
        
        # Preparar configurações
        transcribe_kwargs = {
            'language': None if self.language == "auto" else self.language,
            'vad_filter': True,
            'word_timestamps': True,
            'beam_size': self.engine.hardware.optimizations['beam_size'],
            'best_of': self.engine.hardware.optimizations['best_of'],
            'condition_on_previous_text': False,
        }
        
        # Transcrever e iterar pelos segmentos para progresso real
        segments_generator, info = model.transcribe(self.file_path, **transcribe_kwargs)
        
        segments_list = []
        last_progress = 30
        
        for segment in segments_generator:
            if self._is_cancelled:
                return None
                
            segments_list.append(segment)
            
            # Calcular progresso baseado no timestamp do segmento
            if audio_duration > 0:
                segment_progress = (segment.end / audio_duration) * 60  # 30-90%
                current_progress = min(90, 30 + int(segment_progress))
                
                if current_progress > last_progress:
                    self.progress.emit(current_progress)
                    last_progress = current_progress
                    
                    # Atualizar status com tempo restante estimado
                    elapsed = time.time() - start_time
                    if segment.end > 0:
                        total_estimated = (elapsed / segment.end) * audio_duration
                        remaining = max(0, total_estimated - elapsed)
                        self.status.emit(f"Transcrevendo... {int(remaining)}s restantes")
        
        processing_time = time.time() - start_time
        
        # Gerar texto completo
        full_text = ' '.join([seg.text for seg in segments_list])
        
        logger.info(f"Transcrição concluída em {processing_time:.1f}s")
        
        return {
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
            'device_used': device,
            'hardware_info': {
                'device': device,
                'gpu_name': self.engine.hardware.info.get('primary_gpu', {}).get('name', 'N/A'),
                'beam_size': transcribe_kwargs['beam_size'],
                'best_of': transcribe_kwargs['best_of'],
            },
            'performance_metrics': {
                'chars_per_second': len(full_text) / processing_time if processing_time > 0 else 0,
                'audio_duration': info.duration,
                'realtime_factor': info.duration / processing_time if processing_time > 0 else 0
            }
        }


class AnalysisThread(QThread):
    """Thread para análise com Ollama sem bloquear a UI"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, analyzer, text, selected_model, analysis_types, basic_analyses):
        super().__init__()
        self.analyzer = analyzer
        self.text = text
        self.selected_model = selected_model
        self.analysis_types = analysis_types
        self.basic_analyses = basic_analyses

    def run(self):
        """Executa análise em thread separada"""
        try:
            results = {}

            # Análises básicas (rápidas, sem IA)
            if self.basic_analyses:
                self.status.emit("Executando análises básicas...")
                self.progress.emit(10)
                basic_results = self.analyzer.analyze_transcription(
                    self.text, self.basic_analyses
                )
                results.update(basic_results)

            self.progress.emit(30)

            # Análise com Ollama
            if self.analysis_types and self.analyzer.ollama_available and self.analyzer.ollama_analyzer:
                manager = self.analyzer.ollama_analyzer.manager
                
                # Pré-carregar modelo na GPU antes de iniciar análises
                model_to_load = self.selected_model
                if not model_to_load:
                    model_to_load = manager.get_best_available_model(self.analysis_types[0])
                
                if model_to_load:
                    self.status.emit(f"Carregando {model_to_load} na GPU...")
                    gpu_status = manager.preload_model_gpu(model_to_load)
                    
                    if gpu_status.get("loaded"):
                        processor = gpu_status.get("processor", "?")
                        context_length = gpu_status.get("context_length", "?")
                        warning = gpu_status.get("warning", "")
                        if warning:
                            self.status.emit(f"GPU: {processor} | ctx={context_length} - Modelo/contexto excedem VRAM")
                        else:
                            self.status.emit(f"GPU: {processor} | ctx={context_length}")
                
                total = len(self.analysis_types)
                for i, analysis_type in enumerate(self.analysis_types):
                    self.status.emit(f"Ollama: analisando {analysis_type}...")
                    pct = 30 + int(60 * (i / total))
                    self.progress.emit(pct)

                    try:
                        result = self.analyzer.ollama_analyzer.manager.analyze_transcription(
                            self.text,
                            model_name=self.selected_model,
                            analysis_type=analysis_type
                        )
                        if 'ollama_analysis' not in results:
                            results['ollama_analysis'] = {
                                'model_used': result.get('model_used', 'N/A'),
                                'analyses': {}
                            }
                        results['ollama_analysis']['analyses'][analysis_type] = result
                        results['ollama_analysis']['model_used'] = result.get('model_used', 'N/A')
                    except Exception as e:
                        logger.error(f"Erro na análise Ollama '{analysis_type}': {e}")
                        if 'ollama_analysis' not in results:
                            results['ollama_analysis'] = {'analyses': {}}
                        results['ollama_analysis']['analyses'][analysis_type] = {'error': str(e)}

            self.progress.emit(95)
            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Erro na thread de análise: {e}")
            self.error.emit(str(e))
