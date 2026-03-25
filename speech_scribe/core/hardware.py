import os
from typing import Dict, Any
from speech_scribe.utils.logger import logger

class ModernHardwareDetector:
    """Detector de hardware moderno com otimizações automáticas e suporte completo a GPU"""
    
    def __init__(self):
        self.info = self._detect_hardware()
        self.optimizations = self._generate_optimizations()
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """Detecta hardware disponível com foco em GPU"""
        info = {
            'cpu_count': os.cpu_count(),
            'memory_gb': self._get_memory_gb(),
            'cuda_available': False,
            'cuda_functional': False,
            'cuda_devices': 0,
            'gpu_info': [],
            'primary_gpu': None,
            'recommended_workers': 2,
            'recommended_device': 'cpu'
        }
        
        # Detecção completa de GPU
        try:
            import torch  # Pode falhar com OSError se DLL corrompida
            logger.info("Iniciando detecção de GPU...")
            
            # Verificação básica de CUDA
            if not torch.cuda.is_available():
                logger.info("CUDA não está disponível neste sistema")
                return info
            
            info['cuda_available'] = True
            logger.info("CUDA detectado, testando funcionalidade...")
            
            # Teste funcional da GPU
            try:
                torch.cuda.init()
                test_tensor = torch.zeros(1, device='cuda')
                del test_tensor  # Limpar memória
                torch.cuda.empty_cache()
                info['cuda_functional'] = True
                logger.info("CUDA testado e funcionando corretamente")
            except Exception as e:
                logger.warning(f"CUDA detectado mas não funcional: {e}")
                return info
            
            # Enumerar todas as GPUs
            num_gpus = torch.cuda.device_count()
            info['cuda_devices'] = num_gpus
            
            for i in range(num_gpus):
                try:
                    gpu_props = torch.cuda.get_device_properties(i)
                    gpu_details = {
                        'id': i,
                        'name': gpu_props.name,
                        'vram_total_gb': gpu_props.total_memory / (1024**3),
                        'vram_free_gb': self._get_gpu_free_memory(i) / (1024**3),
                        'compute_capability': f"{gpu_props.major}.{gpu_props.minor}",
                        'multiprocessor_count': gpu_props.multi_processor_count,
                        'max_threads_per_mp': gpu_props.max_threads_per_multi_processor,
                        'performance_score': self._calculate_gpu_performance_score(gpu_props)
                    }
                    info['gpu_info'].append(gpu_details)
                    logger.info(f"GPU {i}: {gpu_details['name']} - "
                              f"{gpu_details['vram_total_gb']:.1f}GB VRAM "
                              f"(Compute {gpu_details['compute_capability']})")
                except Exception as e:
                    logger.error(f"Erro ao acessar GPU {i}: {e}")
            
            # Definir GPU primária (melhor GPU disponível)
            if info['gpu_info']:
                info['primary_gpu'] = max(info['gpu_info'], key=lambda x: x['performance_score'])
                info['recommended_device'] = 'cuda'
                info['recommended_workers'] = min(4, num_gpus * 2)
                
                logger.info(f"GPU primária selecionada: {info['primary_gpu']['name']} "
                          f"({info['primary_gpu']['vram_total_gb']:.1f}GB)")
            
        except ImportError:
            logger.warning("PyTorch não está instalado - GPU não disponível")
        except Exception as e:
            logger.error(f"Erro inesperado na detecção de GPU: {e}")
            
        return info
    
    def _get_memory_gb(self) -> float:
        """Obtém quantidade de RAM em GB"""
        try:
            import psutil
            return psutil.virtual_memory().total / 1e9
        except ImportError:
            return 8.0  # Estimativa padrão
    
    def _get_gpu_free_memory(self, gpu_id: int = 0) -> int:
        """Obtém memória livre da GPU em bytes"""
        try:
            import torch
            torch.cuda.set_device(gpu_id)
            return torch.cuda.get_device_properties(gpu_id).total_memory - torch.cuda.memory_allocated(gpu_id)
        except Exception:
            return 0
    
    def _calculate_gpu_performance_score(self, gpu_props) -> float:
        """Calcula score de performance da GPU baseado nas especificações"""
        # Score baseado em compute capability, VRAM e multiprocessors
        compute_score = float(f"{gpu_props.major}.{gpu_props.minor}")
        vram_score = gpu_props.total_memory / (1024**3)  # GB
        mp_score = gpu_props.multi_processor_count / 100  # Normalizado
        
        # Peso: 40% compute capability, 40% VRAM, 20% multiprocessors
        total_score = (compute_score * 0.4) + (vram_score * 0.4) + (mp_score * 0.2)
        return total_score
    
    def _generate_optimizations(self) -> Dict[str, Any]:
        """Gera otimizações baseadas no hardware detectado"""
        opts = {
            'batch_size': 1,
            'num_workers': 2,
            'device': 'cpu',
            'compute_type': 'int8',
            'gpu_memory_fraction': 0.8,
            'recommended_model': 'small',
            'chunk_length': 30,
            'beam_size': 5,
            'best_of': 1
        }
        
        # Otimizações para GPU
        if self.info['cuda_functional'] and self.info['primary_gpu']:
            gpu = self.info['primary_gpu']
            opts['device'] = 'cuda'
            opts['compute_type'] = 'float16'
            opts['num_workers'] = 1  # GPU funciona melhor com 1 worker
            opts['best_of'] = 5  # Mais tentativas para melhor qualidade
            
            # Otimizações baseadas na VRAM da GPU
            # Nota: GPUs reportam VRAM ligeiramente menor (ex: 16GB = 15.9GB)
            vram_gb = gpu['vram_total_gb']
            
            if vram_gb >= 20:  # GPU high-end (RTX 4090, A100, etc.)
                opts.update({
                    'recommended_model': 'large-v3',
                    'batch_size': 4,
                    'gpu_memory_fraction': 0.7,
                    'chunk_length': 60,
                    'beam_size': 10
                })
            elif vram_gb >= 15:  # GPU 16GB (RTX 5060 Ti, RTX 4080, etc.) - ajustado para 15 pois GPUs reportam ~15.9GB
                opts.update({
                    'recommended_model': 'large-v3',  # 16GB pode rodar large-v3 tranquilo
                    'batch_size': 2,
                    'gpu_memory_fraction': 0.75,
                    'chunk_length': 45,
                    'beam_size': 8
                })
            elif vram_gb >= 11:  # GPU 12GB (RTX 4070, RTX 3080, etc.)
                opts.update({
                    'recommended_model': 'large-v2',
                    'batch_size': 2,
                    'gpu_memory_fraction': 0.8,
                    'chunk_length': 30,
                    'beam_size': 6
                })
            elif vram_gb >= 7:  # GPU 8GB (RTX 4060, RTX 3070, etc.)
                opts.update({
                    'recommended_model': 'medium',
                    'batch_size': 1,
                    'gpu_memory_fraction': 0.85,
                    'chunk_length': 20,
                    'beam_size': 5
                })
            else:  # GPU com pouca VRAM (<8GB)
                opts.update({
                    'recommended_model': 'small',
                    'batch_size': 1,
                    'gpu_memory_fraction': 0.9,
                    'chunk_length': 15,
                    'beam_size': 3
                })
            
            # Ajuste adicional baseado na compute capability
            compute_capability = float(gpu['compute_capability'])
            if compute_capability >= 12.0:  # RTX 50 series (Blackwell) - mais recente
                opts['compute_type'] = 'float16'
                # Blackwell tem melhor performance, pode usar configurações mais agressivas
                if vram_gb >= 15:
                    opts['batch_size'] = min(opts['batch_size'] + 1, 4)
            elif compute_capability >= 8.9:  # RTX 40 series (Ada Lovelace)
                opts['compute_type'] = 'float16'
            elif compute_capability >= 8.0:  # RTX 30 series (Ampere)
                opts['compute_type'] = 'float16'
            elif compute_capability >= 7.0:  # RTX 20 series, Volta
                opts['compute_type'] = 'float16'
            else:  # GPUs mais antigas
                opts['compute_type'] = 'int8_float16'
        
        # Otimizações baseadas na RAM do sistema
        if self.info['memory_gb'] > 32:
            opts['num_workers'] = min(opts['num_workers'] * 2, 4)
            if opts['device'] == 'cpu':
                opts['batch_size'] *= 2
        elif self.info['memory_gb'] > 16:
            if opts['device'] == 'cpu':
                opts['batch_size'] = 2
        
        # Otimizações para CPU
        if opts['device'] == 'cpu':
            cpu_cores = self.info['cpu_count']
            opts['num_workers'] = min(cpu_cores // 2, 8)
            opts['compute_type'] = 'int8'
            opts['best_of'] = 1  # CPU é mais lento, menos tentativas
            
            # Modelo recomendado baseado na RAM para CPU
            if self.info['memory_gb'] >= 32:
                opts['recommended_model'] = 'large-v2'
            elif self.info['memory_gb'] >= 16:
                opts['recommended_model'] = 'medium'
            else:
                opts['recommended_model'] = 'small'
            
        return opts
    
    def get_device_info(self) -> str:
        """Retorna informações formatadas do hardware"""
        if self.info['cuda_functional'] and self.info['primary_gpu']:
            gpu = self.info['primary_gpu']
            device_info = (f"GPU: {gpu['name']} | "
                          f"VRAM: {gpu['vram_total_gb']:.1f}GB | "
                          f"Compute: {gpu['compute_capability']}")
        elif self.info['cuda_available']:
            device_info = "CUDA detectado mas não funcional"
        else:
            device_info = f"CPU: {self.info['cpu_count']} cores"
        
        return (f"{device_info} | "
                f"RAM: {self.info['memory_gb']:.1f}GB | "
                f"Modelo recomendado: {self.optimizations['recommended_model']}")
    
    def get_detailed_gpu_info(self) -> Dict[str, Any]:
        """Retorna informações detalhadas de todas as GPUs"""
        if not self.info['cuda_functional']:
            return {'status': 'No GPU available or functional'}
        
        return {
            'status': 'GPU available and functional',
            'cuda_version': self._get_cuda_version(),
            'primary_gpu': self.info['primary_gpu'],
            'all_gpus': self.info['gpu_info'],
            'optimizations': self.optimizations
        }
    
    def _get_cuda_version(self) -> str:
        """Obtém versão do CUDA"""
        try:
            import torch
            return torch.version.cuda if torch.version.cuda else "Unknown"
        except Exception:
            return "Unknown"
    
    def optimize_gpu_memory(self, gpu_id: int = 0) -> bool:
        """Otimiza uso de memória da GPU"""
        if not self.info['cuda_functional']:
            return False
        
        try:
            import torch
            
            # Limpar cache da GPU
            torch.cuda.empty_cache()
            
            # Definir fração de memória
            memory_fraction = self.optimizations['gpu_memory_fraction']
            torch.cuda.set_per_process_memory_fraction(memory_fraction, gpu_id)
            
            logger.info(f"GPU {gpu_id} otimizada: {memory_fraction*100:.0f}% da VRAM alocada")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao otimizar GPU: {e}")
            return False
