import os
from typing import List, Dict, Any
from speech_scribe.utils.logger import logger

class SpeakerDiarization:
    """Sistema avançado de diarização (separação de vozes) usando pyannote.audio"""
    
    def __init__(self):
        self.pipeline = None
        self.hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        self.torch_available = False
        
        # Verificar se torch está disponível
        try:
            import torch
            self.torch_available = True
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            self.device = "cpu"
            logger.warning("PyTorch não disponível ou com erro de DLL - diarização usará CPU")
            
        self.available = self._check_availability()
        
        logger.info(f"Diarização inicializada: disponível={self.available}, device={self.device}")
    
    def _check_availability(self) -> bool:
        """Verifica se a diarização está disponível"""
        try:
            # Verificar se pyannote.audio está instalado
            import pyannote.audio
            
            # Verificar token do Hugging Face
            if not self.hf_token:
                logger.warning("Token HUGGINGFACE_TOKEN não encontrado no .env")
                return False
            
            return True
            
        except ImportError:
            logger.warning("pyannote.audio não encontrado. Instale com: pip install pyannote.audio")
            return False
        except Exception as e:
            logger.warning(f"Erro ao verificar diarização: {e}")
            return False
    
    def _load_pipeline(self):
        """Carrega pipeline de diarização"""
        if self.pipeline is not None:
            return self.pipeline
        
        try:
            from pyannote.audio import Pipeline
            
            logger.info("Carregando modelo de diarização...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            
            # Configurar dispositivo
            if self.device == "cuda" and self.torch_available:
                try:
                    import torch
                    self.pipeline = self.pipeline.to(torch.device("cuda"))
                except Exception:
                    logger.warning("Falha ao mover pipeline para GPU")
            
            logger.info(f"Pipeline de diarização carregado no {self.device}")
            return self.pipeline
            
        except Exception as e:
            logger.error(f"Erro ao carregar pipeline de diarização: {e}")
            return None
    
    def process_diarization(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Processa diarização de um arquivo de áudio
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            
        Returns:
            Lista de segmentos com informações dos oradores
        """
        if not self.available:
            logger.warning("Diarização não disponível")
            return []
        
        try:
            # Carregar pipeline
            pipeline = self._load_pipeline()
            if pipeline is None:
                return []
            
            logger.info(f"Processando diarização: {audio_path}")
            
            # Executar diarização
            try:
                diarization = pipeline(audio_path)
            except Exception as cuda_error:
                if "CUDA" in str(cuda_error) and self.device == "cuda":
                    logger.warning("Erro CUDA na diarização, tentando CPU...")
                    
                    # Limpar cache e tentar CPU
                    if self.torch_available:
                        try:
                            import torch
                            torch.cuda.empty_cache()
                        except Exception:
                            pass
                    
                    # Recarregar pipeline em CPU
                    self.pipeline = None
                    self.device = "cpu"
                    pipeline = self._load_pipeline()
                    
                    if pipeline:
                        diarization = pipeline(audio_path)
                    else:
                        return []
                else:
                    raise
            
            # Extrair segmentos
            speakers = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_data = {
                    'start': float(turn.start),
                    'end': float(turn.end), 
                    'speaker': speaker,
                    'duration': float(turn.end - turn.start)
                }
                speakers.append(speaker_data)
            
            # Ordenar por tempo de início
            speakers.sort(key=lambda x: x['start'])
            
            logger.info(f"Diarização concluída: {len(speakers)} segmentos, "
                       f"{len(set(s['speaker'] for s in speakers))} oradores")
            
            return speakers
            
        except Exception as e:
            logger.error(f"Erro na diarização: {e}")
            return []
    
    def merge_with_transcription(self, transcription_segments: List[Dict], 
                               speaker_segments: List[Dict]) -> List[Dict]:
        """
        Combina segmentos de transcrição com informações de oradores
        
        Args:
            transcription_segments: Segmentos da transcrição
            speaker_segments: Segmentos dos oradores
            
        Returns:
            Segmentos combinados com informações de orador
        """
        if not speaker_segments:
            return transcription_segments
        
        try:
            merged_segments = []
            
            for segment in transcription_segments:
                start_time = segment.get('start', 0)
                end_time = segment.get('end', start_time)
                
                # Encontrar orador para este segmento
                speaker = self._find_speaker_for_segment(
                    start_time, end_time, speaker_segments
                )
                
                # Adicionar informação do orador
                enhanced_segment = segment.copy()
                enhanced_segment['speaker'] = speaker
                enhanced_segment['speaker_confidence'] = self._calculate_speaker_confidence(
                    start_time, end_time, speaker, speaker_segments
                )
                
                merged_segments.append(enhanced_segment)
            
            return merged_segments
            
        except Exception as e:
            logger.error(f"Erro ao combinar transcrição com diarização: {e}")
            return transcription_segments
    
    def _find_speaker_for_segment(self, start: float, end: float, 
                                speaker_segments: List[Dict]) -> str:
        """Encontra o orador mais provável para um segmento"""
        try:
            # Calcular sobreposição com cada segmento de orador
            best_speaker = "SPEAKER_00"  # padrão
            max_overlap = 0
            
            segment_duration = end - start
            
            for speaker_seg in speaker_segments:
                # Calcular sobreposição
                overlap_start = max(start, speaker_seg['start'])
                overlap_end = min(end, speaker_seg['end'])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                # Calcular porcentagem de sobreposição
                if segment_duration > 0:
                    overlap_percent = overlap_duration / segment_duration
                    
                    if overlap_percent > max_overlap:
                        max_overlap = overlap_percent
                        best_speaker = speaker_seg['speaker']
            
            return best_speaker
            
        except Exception as e:
            logger.error(f"Erro ao encontrar orador: {e}")
            return "SPEAKER_00"
    
    def _calculate_speaker_confidence(self, start: float, end: float, 
                                    speaker: str, speaker_segments: List[Dict]) -> float:
        """Calcula confiança da atribuição do orador"""
        try:
            total_overlap = 0
            segment_duration = end - start
            
            for speaker_seg in speaker_segments:
                if speaker_seg['speaker'] == speaker:
                    overlap_start = max(start, speaker_seg['start'])
                    overlap_end = min(end, speaker_seg['end'])
                    overlap_duration = max(0, overlap_end - overlap_start)
                    total_overlap += overlap_duration
            
            if segment_duration > 0:
                return min(1.0, total_overlap / segment_duration)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.0
    
    def get_speaker_statistics(self, segments: List[Dict]) -> Dict[str, Any]:
        """Gera estatísticas dos oradores"""
        try:
            if not segments:
                return {}
            
            stats = {}
            speakers = set(seg.get('speaker', 'UNKNOWN') for seg in segments)
            
            for speaker in speakers:
                speaker_segments = [seg for seg in segments if seg.get('speaker') == speaker]
                
                total_duration = sum(
                    seg.get('end', 0) - seg.get('start', 0) 
                    for seg in speaker_segments
                )
                
                total_words = sum(
                    len(seg.get('text', '').split()) 
                    for seg in speaker_segments
                )
                
                stats[speaker] = {
                    'segments_count': len(speaker_segments),
                    'total_duration': total_duration,
                    'total_words': total_words,
                    'avg_segment_duration': total_duration / len(speaker_segments) if speaker_segments else 0,
                    'words_per_minute': (total_words / total_duration * 60) if total_duration > 0 else 0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
