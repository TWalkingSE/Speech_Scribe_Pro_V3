import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from speech_scribe.utils.logger import logger
from speech_scribe.core.config import AppConfig
from speech_scribe.core.hardware import ModernHardwareDetector

class IntelligentTranscriptionEngine:
    """Motor de transcrição inteligente com cache e otimizações"""
    
    def __init__(self, config: AppConfig, hardware: ModernHardwareDetector):
        self.config = config
        self.hardware = hardware
        self.model_cache = {}
        self._cache_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=hardware.optimizations['num_workers'])

    def load_model(self, model_name: str, device: str = "auto"):
        """Carrega modelo com cache inteligente e otimização de GPU"""
        if device == "auto":
            device = self.hardware.optimizations['device']
            
        # Se estiver usando GPU, otimizar memória antes de carregar
        if device == "cuda" and self.hardware.info['cuda_functional']:
            self.hardware.optimize_gpu_memory()
            
        cache_key = f"{model_name}_{device}"
        with self._cache_lock:
            if cache_key in self.model_cache:
                logger.info(f"Modelo {model_name} carregado do cache")
                return self.model_cache[cache_key]
        
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Carregando modelo {model_name} em {device}")
            
            # Usar configurações otimizadas baseadas no hardware
            model_kwargs = {
                'device': device,
                'compute_type': self.hardware.optimizations['compute_type']
            }
            
            # Configurações específicas para GPU
            if device == "cuda":
                model_kwargs.update({
                    'device_index': 0,  # Usar GPU primária
                    'num_workers': self.hardware.optimizations['num_workers']
                })
            
            model = WhisperModel(model_name, **model_kwargs)

            with self._cache_lock:
                self.model_cache[cache_key] = model
            
            # Log das configurações usadas
            logger.info(f"Modelo carregado com sucesso: {model_name}")
            logger.info(f"Configurações: device={device}, compute_type={model_kwargs['compute_type']}")
            
            return model
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            
            # Fallback para CPU se GPU falhar
            if device == "cuda":
                logger.warning("Tentando fallback para CPU...")
                return self.load_model(model_name, "cpu")
            
            return None
    
    async def transcribe_async(self, audio_path: str, model_name: str = "auto", 
                               language: str = "auto") -> Dict[str, Any]:
        """Transcrição assíncrona com progresso e otimização de GPU"""
        
        # Usar modelo recomendado se auto
        if model_name == "auto":
            model_name = self.hardware.optimizations['recommended_model']
            logger.info(f"Modelo automático selecionado: {model_name}")
        
        model = self.load_model(model_name)
        if not model:
            raise Exception("Falha ao carregar modelo")
        
        start_time = time.time()
        device = self.hardware.optimizations['device']
        
        try:
            # Preparar configurações de transcrição otimizadas
            transcribe_kwargs = {
                'language': None if language == "auto" else language,
                'vad_filter': True,
                'word_timestamps': True,
                'beam_size': self.hardware.optimizations['beam_size'],
                'best_of': self.hardware.optimizations['best_of'],
                'condition_on_previous_text': False,
                'initial_prompt': None
            }
            
            # Configurações específicas para GPU
            if device == "cuda":
                # Limpar cache antes da transcrição
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception:
                    pass

                # Nota: batch_size não é usado no método transcribe() do faster-whisper
                # É usado na inicialização do modelo
            
            logger.info(f"Iniciando transcrição com {device.upper()}: {audio_path}")
            logger.info(f"Configurações: beam_size={transcribe_kwargs['beam_size']}, "
                       f"best_of={transcribe_kwargs['best_of']}")
            
            # Usar executor para não bloquear a thread principal
            loop = asyncio.get_running_loop()
            segments, info = await loop.run_in_executor(
                self.executor,
                lambda: model.transcribe(audio_path, **transcribe_kwargs)
            )
            
            # Converter para lista
            segments_list = list(segments)
            
            processing_time = time.time() - start_time
            
            # Gerar texto completo
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
                'model_used': model_name,
                'device_used': device,
                'hardware_info': {
                    'device': device,
                    'gpu_name': self.hardware.info.get('primary_gpu', {}).get('name', 'N/A'),
                    'beam_size': transcribe_kwargs['beam_size'],
                    'best_of': transcribe_kwargs['best_of']
                },
                'performance_metrics': {
                    'chars_per_second': len(full_text) / processing_time if processing_time > 0 else 0,
                    'audio_duration': info.duration,
                    'realtime_factor': info.duration / processing_time if processing_time > 0 else 0
                }
            }
            
            # Log de performance
            logger.info(f"Transcrição concluída em {processing_time:.1f}s")
            logger.info(f"Fator tempo real: {result['performance_metrics']['realtime_factor']:.2f}x")
            
            # Limpar cache da GPU após transcrição
            if device == "cuda":
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception:
                    pass

            return result
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            
            # Fallback para CPU se GPU falhar
            if device == "cuda" and "CUDA" in str(e):
                logger.warning("Erro de CUDA detectado, tentando fallback para CPU...")
                # Recarregar modelo em CPU
                self.model_cache.clear()
                cpu_model = self.load_model(model_name, "cpu")
                if cpu_model:
                    return await self.transcribe_async(audio_path, model_name, language)
            
            raise
