#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 Integração com Ollama - Speech Scribe Pro V3
Módulo para integração com modelos Ollama locais atualizados
"""

import json
import logging
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OllamaModel(Enum):
    """Modelos Ollama conhecidos com configurações otimizadas (fallback defaults)"""
    # Modelo principal para análises gerais e resumos
    GPT_OSS = "gpt-oss:20b"
    # Modelo especializado em raciocínio profundo e análises complexas
    DEEPSEEK_R1 = "deepseek-r1:14b-qwen-distill-q8_0"

@dataclass
class OllamaConfig:
    """Configurações para Ollama - Otimizadas para análise de transcrições"""
    base_url: str = "http://localhost:11434"
    timeout: int = 180  # Maior timeout para análises complexas
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stream: bool = False
    num_gpu: int = -1  # -1 = todas as camadas na GPU (forçar uso total da GPU)
    num_ctx: int = 8192  # 262k estoura a VRAM e força offload parcial para CPU
    keep_alive: str = "30m"
    gpu_headroom_gb: float = 2.0
    
    # Configurações específicas por tipo de análise
    analysis_configs: dict = None
    
    def __post_init__(self):
        """Inicializa configurações específicas por tipo de análise"""
        self.analysis_configs = {
            "general": {"temperature": 0.7, "max_tokens": 4096},
            "sentiment": {"temperature": 0.3, "max_tokens": 2048},
            "summary": {"temperature": 0.5, "max_tokens": 2048},
            "keywords": {"temperature": 0.3, "max_tokens": 1024},
            "qa": {"temperature": 0.6, "max_tokens": 3072},
            "correction": {"temperature": 0.2, "max_tokens": 4096},
            "reasoning": {"temperature": 0.4, "max_tokens": 4096}
        }
        # Detectar VRAM da GPU automaticamente
        if self.num_gpu == -1:
            self._detect_gpu_vram()

    def _detect_gpu_vram(self):
        """Detecta VRAM da GPU para log informativo"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_properties(0).name
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"GPU detectada para Ollama: {gpu_name} ({vram_gb:.1f}GB VRAM)")
                logger.info(f"Ollama configurado para usar GPU com num_gpu={self.num_gpu} (todas as camadas na GPU)")
            else:
                logger.info("CUDA não disponível - Ollama usará configuração padrão do servidor")
        except Exception as e:
            logger.debug(f"Não foi possível detectar GPU: {e}")


class OllamaManager:
    """Gerenciador de integração com Ollama - Otimizado para GPU"""
    
    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.available_models: List[str] = []
        self.is_service_running = False
        self.gpu_info: Optional[Dict[str, Any]] = None
        self._gpu_preloaded_model: Optional[str] = None  # Modelo já pré-carregado na GPU
        self._model_details_cache: Dict[str, Dict[str, Any]] = {}
        self._detect_gpu()
        
        # Mapear engines para modelos conhecidos
        self.model_mapping = {
            "ollama_gpt_oss": OllamaModel.GPT_OSS.value,
            "ollama_deepseek": OllamaModel.DEEPSEEK_R1.value
        }
        
        # Mapeamento de tipo de análise para modelo ideal (usado apenas no modo Auto)
        self.analysis_model_preference = {
            "general": OllamaModel.GPT_OSS.value,
            "summary": OllamaModel.GPT_OSS.value,
            "keywords": OllamaModel.GPT_OSS.value,
            "sentiment": OllamaModel.DEEPSEEK_R1.value,
            "reasoning": OllamaModel.DEEPSEEK_R1.value,
            "qa": OllamaModel.DEEPSEEK_R1.value,
            "correction": OllamaModel.GPT_OSS.value
        }
        
        # Descrições dos modelos conhecidos (modelos não listados aqui ainda funcionam)
        self.model_descriptions = {
            OllamaModel.GPT_OSS.value: {
                "name": "GPT-OSS 20B",
                "description": "Modelo open-source equilibrado para análises gerais, resumos e extração de informações",
                "strengths": ["Resumos", "Extração de keywords", "Análise geral", "Correção de texto"],
                "recommended_for": "Análise geral de transcrições, resumos e extração de informações",
                "best_for_analysis": ["general", "summary", "keywords", "correction"]
            },
            OllamaModel.DEEPSEEK_R1.value: {
                "name": "DeepSeek R1 14B (Qwen Distill)",
                "description": "Modelo especializado em raciocínio profundo, ideal para análises complexas e inferências",
                "strengths": ["Raciocínio lógico", "Análise de sentimento", "Inferências", "Perguntas complexas"],
                "recommended_for": "Análise de sentimento, raciocínio e perguntas que requerem pensamento profundo",
                "best_for_analysis": ["sentiment", "reasoning", "qa"]
            }
        }
    
    def _detect_gpu(self):
        """Detecta GPU disponível e armazena informações"""
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                self.gpu_info = {
                    'name': props.name,
                    'vram_total_gb': props.total_memory / (1024**3),
                }
                logger.info(f"Ollama GPU: {self.gpu_info['name']} "
                           f"({self.gpu_info['vram_total_gb']:.1f}GB VRAM) - "
                           f"num_gpu={self.config.num_gpu}")
        except Exception:
            self.gpu_info = None

    def get_installed_model_details(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Obtém detalhes dos modelos instalados via /api/tags, incluindo tamanho."""
        if self._model_details_cache and not refresh:
            return self._model_details_cache

        if not self.check_service_status():
            return {}

        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=10
            )
            if response.status_code != 200:
                logger.warning(f"Não foi possível obter detalhes dos modelos: HTTP {response.status_code}")
                return {}

            details: Dict[str, Dict[str, Any]] = {}
            for model in response.json().get("models", []):
                model_name = model.get("name")
                if not model_name:
                    continue

                size_bytes = model.get("size", 0)
                details[model_name] = {
                    "name": model_name,
                    "size_bytes": size_bytes,
                    "size_gb": size_bytes / (1024**3) if size_bytes else 0,
                    "details": model.get("details", {})
                }

            self._model_details_cache = details
            return details
        except Exception as e:
            logger.warning(f"Erro ao obter detalhes dos modelos Ollama: {e}")
            return {}

    def _get_model_size_gb(self, model_name: str) -> Optional[float]:
        """Retorna o tamanho conhecido do modelo em GB."""
        details = self.get_installed_model_details()
        model_details = details.get(model_name)
        if model_details:
            return model_details.get("size_gb")
        return None

    def _get_safe_num_ctx(self, model_name: Optional[str] = None) -> int:
        """Calcula um contexto seguro para evitar offload desnecessário para CPU."""
        num_ctx = self.config.num_ctx
        if not model_name or not self.gpu_info:
            return num_ctx

        model_size_gb = self._get_model_size_gb(model_name)
        if not model_size_gb:
            return num_ctx

        vram_total_gb = self.gpu_info["vram_total_gb"]
        if model_size_gb >= vram_total_gb - 1:
            return min(num_ctx, 4096)
        if model_size_gb >= vram_total_gb - 3:
            return min(num_ctx, 8192)
        return num_ctx

    def _get_vram_budget_gb(self) -> Optional[float]:
        """Retorna orçamento de VRAM com folga para o cache de contexto."""
        if not self.gpu_info:
            return None
        return max(self.gpu_info["vram_total_gb"] - self.config.gpu_headroom_gb, 1.0)

    def _choose_best_fit_model(self, candidates: List[str]) -> Optional[str]:
        """Escolhe o melhor candidato que cabe na VRAM com folga."""
        if not candidates:
            return None

        vram_budget_gb = self._get_vram_budget_gb()
        if not vram_budget_gb:
            return candidates[0]

        for candidate in candidates:
            size_gb = self._get_model_size_gb(candidate)
            if size_gb is None:
                continue
            if size_gb <= vram_budget_gb:
                logger.info(
                    f"Selecionando modelo compatível com VRAM: {candidate} "
                    f"({size_gb:.1f}GB <= {vram_budget_gb:.1f}GB)"
                )
                return candidate

        return candidates[0]

    def _get_num_predict(self, text: str, analysis_type: str, default_max_tokens: int) -> int:
        """Calcula um limite de saída mais seguro para evitar loops em correções."""
        if analysis_type != "correction":
            return default_max_tokens

        word_count = max(len(text.split()), 1)
        estimated_tokens = int(word_count * 1.75) + 96
        return max(256, min(default_max_tokens, estimated_tokens))

    def _sanitize_correction_output(self, text: str) -> str:
        """Remove títulos e explicações extras, preservando apenas o texto corrigido."""
        cleaned = (text or "").strip().strip("`")
        if not cleaned:
            return ""

        split_markers = [
            "### Análise de Correções",
            "### Analise de Correcoes",
            "## Análise de Correções",
            "## Analise de Correcoes",
            "Análise de Correções Realizadas:",
            "Analise de Correcoes Realizadas:",
        ]
        for marker in split_markers:
            if marker in cleaned:
                cleaned = cleaned.split(marker, 1)[0].rstrip()

        heading_prefixes = {
            "transcrição corrigida",
            "transcricao corrigida",
            "texto corrigido",
            "versão corrigida",
            "versao corrigida",
        }

        lines = cleaned.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)

        while lines:
            normalized = lines[0].strip().strip("*#:").lower()
            if normalized in heading_prefixes:
                lines.pop(0)
                continue
            break

        return "\n".join(lines).strip().strip("`")

    def _should_retry_correction(self, text: str, result: Dict[str, Any], num_predict: int) -> bool:
        """Detecta quando a correção falhou silenciosamente ou ficou presa até o limite."""
        if not text.strip():
            return True
        eval_count = result.get("eval_count", 0)
        return eval_count >= num_predict and len(text.strip()) < 32

    def _get_correction_fallback_model(self, current_model: str) -> Optional[str]:
        """Escolhe um modelo alternativo para correção quando o atual falha."""
        self.get_available_models()
        if not self.available_models:
            return None

        preferred_order = [
            "qwen3.5:9b-q8_0",
            OllamaModel.GPT_OSS.value,
            OllamaModel.DEEPSEEK_R1.value,
        ]

        candidates = [
            model for model in preferred_order
            if model != current_model and self.is_model_available(model)
        ]

        for model in self.available_models:
            if model != current_model and model not in candidates:
                candidates.append(model)

        return self._choose_best_fit_model(candidates)

    def _send_generate_request(
        self,
        model_name: str,
        prompt: str,
        temperature: float,
        num_predict: int,
        num_ctx: int,
    ) -> Dict[str, Any]:
        """Executa uma requisição única ao endpoint generate do Ollama."""
        response = requests.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": self.config.stream,
                "options": {
                    "temperature": temperature,
                    "top_p": self.config.top_p,
                    "num_predict": num_predict,
                    "num_gpu": self.config.num_gpu,
                    "num_ctx": num_ctx
                },
                "keep_alive": self.config.keep_alive
            },
            timeout=self.config.timeout
        )

        if response.status_code != 200:
            raise Exception(f"Erro na API Ollama: {response.text}")

        return response.json()

    def _retry_correction_analysis(
        self,
        text: str,
        model_name: str,
        temperature: float,
        num_predict: int,
        num_ctx: int,
    ) -> Tuple[str, Dict[str, Any], str, int]:
        """Refaz correção com prompt mais restrito e, se necessário, modelo alternativo."""
        retry_prompt = f"""Você é um revisor de transcrições em português brasileiro.
Retorne SOMENTE o texto corrigido final.
Não explique nada.
Não use markdown.
Não adicione títulos.
Preserve parágrafos, sentido e tom original.

Texto original:
{text}

Texto corrigido:
"""

        retry_temperature = min(temperature, 0.1)
        retry_result = self._send_generate_request(
            model_name,
            retry_prompt,
            retry_temperature,
            num_predict,
            num_ctx,
        )
        retry_text = self._sanitize_correction_output(retry_result.get("response", ""))
        if retry_text.strip():
            return retry_text, retry_result, model_name, num_ctx

        fallback_model = self._get_correction_fallback_model(model_name)
        if fallback_model and fallback_model != model_name:
            fallback_num_ctx = self._get_safe_num_ctx(fallback_model)
            if self._gpu_preloaded_model != fallback_model:
                self.preload_model_gpu(fallback_model)

            fallback_result = self._send_generate_request(
                fallback_model,
                retry_prompt,
                retry_temperature,
                num_predict,
                fallback_num_ctx,
            )
            fallback_text = self._sanitize_correction_output(fallback_result.get("response", ""))
            if fallback_text.strip():
                logger.warning(
                    f"Correção vazia com {model_name}; usando fallback {fallback_model}"
                )
                return fallback_text, fallback_result, fallback_model, fallback_num_ctx

        return "", retry_result, model_name, num_ctx
    
    def _unload_model(self, model_name: str) -> bool:
        """Descarrega modelo da memória do Ollama"""
        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": model_name,
                    "keep_alive": 0
                },
                timeout=30
            )
            if response.status_code == 200:
                logger.info(f"Modelo {model_name} descarregado da memória")
                return True
            else:
                logger.warning(f"Erro ao descarregar modelo: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Falha ao descarregar modelo {model_name}: {e}")
            return False
    
    def preload_model_gpu(self, model_name: str) -> Dict[str, Any]:
        """Descarrega e recarrega modelo forçando máximo uso da GPU.
        
        Retorna informações sobre o status GPU do modelo carregado.
        """
        if self._gpu_preloaded_model == model_name:
            logger.info(f"Modelo {model_name} já pré-carregado na GPU, verificando status...")
            return self.get_model_gpu_status(model_name)
        
        logger.info(f"Pré-carregando modelo {model_name} na GPU (num_gpu={self.config.num_gpu})...")
        num_ctx = self._get_safe_num_ctx(model_name)
        
        # Passo 1: Descarregar modelo existente para liberar memória
        self._unload_model(model_name)
        time.sleep(1)  # Dar tempo para Ollama liberar memória
        
        # Passo 2: Carregar modelo com num_gpu=-1 (todas as camadas na GPU)
        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "",  # Prompt vazio = apenas carregar modelo
                    "stream": self.config.stream,
                    "options": {
                        "num_gpu": self.config.num_gpu,
                        "num_ctx": num_ctx
                    },
                    "keep_alive": self.config.keep_alive
                },
                timeout=120  # Carregar modelo pode demorar
            )
            
            if response.status_code == 200:
                self._gpu_preloaded_model = model_name
                logger.info(
                    f"Modelo {model_name} carregado com num_gpu={self.config.num_gpu} "
                    f"e num_ctx={num_ctx}"
                )
                
                # Passo 3: Verificar status real de GPU
                time.sleep(1)  # Dar tempo para Ollama reportar status correto
                gpu_status = self.get_model_gpu_status(model_name)
                return gpu_status
            else:
                logger.error(f"Erro ao pré-carregar modelo: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Falha ao pré-carregar modelo {model_name}: {e}")
            return {"error": str(e)}
    
    def get_model_gpu_status(self, model_name: str = None) -> Dict[str, Any]:
        """Verifica status GPU dos modelos carregados via /api/ps"""
        try:
            response = requests.get(
                f"{self.config.base_url}/api/ps",
                timeout=10
            )
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            models = data.get("models", [])
            
            if not models:
                return {"loaded": False, "message": "Nenhum modelo carregado"}
            
            # Procurar modelo específico ou retornar todos
            for model in models:
                name = model.get("name", "")
                if model_name and model_name not in name:
                    continue
                
                size = model.get("size", 0)
                size_vram = model.get("size_vram", 0)
                
                if size > 0:
                    gpu_pct = (size_vram / size) * 100
                    cpu_pct = 100 - gpu_pct
                else:
                    gpu_pct = 0
                    cpu_pct = 100
                
                status = {
                    "loaded": True,
                    "model": name,
                    "size_total_gb": size / (1024**3),
                    "size_vram_gb": size_vram / (1024**3),
                    "context_length": model.get("context_length", self.config.num_ctx),
                    "gpu_percent": round(gpu_pct, 1),
                    "cpu_percent": round(cpu_pct, 1),
                    "processor": f"{round(cpu_pct)}/{round(gpu_pct)}% CPU/GPU" if cpu_pct > 0 else "100% GPU"
                }
                
                if gpu_pct < 100:
                    vram_gb = self.gpu_info['vram_total_gb'] if self.gpu_info else "?"
                    status["warning"] = (
                        f"Modelo/contexto excedem a VRAM disponível ({vram_gb}GB). "
                        f"GPU está sendo usada ao máximo ({gpu_pct:.0f}%), restante na CPU."
                    )
                    logger.warning(status["warning"])
                else:
                    logger.info(f"Modelo {name} 100% na GPU")
                
                return status
            
            return {"loaded": False, "message": f"Modelo {model_name} não está carregado"}
            
        except Exception as e:
            logger.warning(f"Falha ao verificar status GPU: {e}")
            return {"error": str(e)}
    
    def check_service_status(self) -> bool:
        """Verifica se o serviço Ollama está rodando"""
        try:
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            self.is_service_running = response.status_code == 200
            return self.is_service_running
        except requests.exceptions.RequestException:
            self.is_service_running = False
            return False
    
    def get_available_models(self) -> List[str]:
        """Obtém lista de modelos disponíveis no Ollama"""
        if not self.check_service_status():
            logger.warning("Serviço Ollama não está rodando")
            return []
        
        try:
            # Usar comando ollama list
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                logger.error(f"Erro ao listar modelos: {result.stderr}")
                return []
            
            # Extrair nomes dos modelos
            models = []
            lines = result.stdout.strip().split('\n')[1:]  # Pular cabeçalho
            
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]  # Primeiro campo é o nome
                    models.append(model_name)
            
            self.available_models = models
            self.get_installed_model_details(refresh=True)
            logger.info(f"Modelos Ollama encontrados: {models}")
            return models
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout ao listar modelos Ollama")
            return []
        except Exception as e:
            logger.error(f"Erro ao verificar modelos Ollama: {e}")
            return []
    
    def is_model_available(self, model_name: str) -> bool:
        """Verifica se um modelo específico está disponível"""
        if not self.available_models:
            self.get_available_models()
        
        # Verificar correspondência exata ou por prefixo
        for available in self.available_models:
            if model_name == available or available.startswith(model_name.split(':')[0]):
                return True
        return False
    
    def get_best_available_model(self, analysis_type: str = "general") -> Optional[str]:
        """Retorna o melhor modelo disponível baseado no tipo de análise"""
        self.get_available_models()
        if not self.available_models:
            return None
        
        # Primeiro, tentar o modelo preferido para este tipo de análise
        preferred_model = self.analysis_model_preference.get(analysis_type, OllamaModel.GPT_OSS.value)
        candidates: List[str] = []
        if self.is_model_available(preferred_model):
            candidates.append(preferred_model)
        
        # Fallback: ordem de prioridade (modelos conhecidos primeiro)
        priority_order = [
            OllamaModel.GPT_OSS.value,
            OllamaModel.DEEPSEEK_R1.value
        ]
        
        for model in priority_order:
            if self.is_model_available(model) and model not in candidates:
                candidates.append(model)
        
        for model in self.available_models:
            if model not in candidates:
                candidates.append(model)
        
        best_model = self._choose_best_fit_model(candidates)
        if best_model:
            logger.info(f"Usando modelo para '{analysis_type}': {best_model}")
            return best_model
        
        # Último fallback: usar o primeiro modelo disponível
        if self.available_models:
            first_model = self.available_models[0]
            logger.info(f"Usando primeiro modelo disponível: {first_model}")
            return first_model
        
        return None
    
    def get_model_for_analysis(self, analysis_type: str) -> Optional[str]:
        """Retorna o modelo mais adequado para um tipo específico de análise"""
        return self.get_best_available_model(analysis_type)
    
    def pull_model(self, model_name: str) -> bool:
        """Baixa um modelo do Ollama"""
        try:
            logger.info(f"Baixando modelo {model_name}...")
            
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutos timeout
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.info(f"Modelo {model_name} baixado com sucesso")
                self.get_available_models()  # Atualizar lista
                return True
            else:
                logger.error(f"Erro ao baixar modelo {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao baixar modelo {model_name}")
            return False
        except Exception as e:
            logger.error(f"Erro ao baixar modelo {model_name}: {e}")
            return False
    
    def analyze_transcription(self, 
                            text: str, 
                            model_name: Optional[str] = None,
                            analysis_type: str = "general") -> Dict[str, Any]:
        """Analisa transcrição usando Ollama com seleção inteligente de modelo"""

        requested_model = model_name
        
        if not self.check_service_status():
            raise Exception("Serviço Ollama não está rodando. Execute 'ollama serve'")
        
        # Usar modelo mais adequado para o tipo de análise se não especificado
        if not model_name:
            model_name = self.get_model_for_analysis(analysis_type)
            if not model_name:
                raise Exception("Nenhum modelo Ollama disponível. Instale um modelo com 'ollama pull <modelo>'")
        
        # Verificar se modelo está disponível
        if not self.is_model_available(model_name):
            # Tentar fallback
            fallback = self.get_best_available_model(analysis_type)
            if fallback:
                logger.warning(f"Modelo {model_name} não disponível, usando fallback: {fallback}")
                model_name = fallback
            else:
                raise Exception(f"Modelo {model_name} não está disponível e não há fallback")
        
        # Gerar prompt baseado no tipo de análise e modelo
        prompt = self._generate_analysis_prompt(text, analysis_type, model_name)
        
        # Obter configurações específicas para este tipo de análise
        analysis_config = self.config.analysis_configs.get(analysis_type, {})
        temperature = analysis_config.get("temperature", self.config.temperature)
        max_tokens = analysis_config.get("max_tokens", self.config.max_tokens)
        num_predict = self._get_num_predict(text, analysis_type, max_tokens)
        num_ctx = self._get_safe_num_ctx(model_name)
        
        # Pré-carregar modelo na GPU se ainda não foi feito
        if self._gpu_preloaded_model != model_name:
            logger.info(f"Forçando pré-carregamento de {model_name} na GPU antes da análise...")
            self.preload_model_gpu(model_name)
        
        try:
            logger.info(
                f"Iniciando análise '{analysis_type}' com {model_name} "
                f"(temp={temperature}, num_predict={num_predict})"
            )

            result = self._send_generate_request(
                model_name,
                prompt,
                temperature,
                num_predict,
                num_ctx,
            )
            response_text = result.get("response", "")

            if analysis_type == "correction":
                response_text = self._sanitize_correction_output(response_text)
                if self._should_retry_correction(response_text, result, num_predict):
                    logger.warning(
                        f"Correção vazia ou incompleta com {model_name}; tentando novamente"
                    )
                    response_text, result, model_name, num_ctx = self._retry_correction_analysis(
                        text,
                        model_name,
                        temperature,
                        num_predict,
                        num_ctx,
                    )

                if not response_text.strip():
                    selected_hint = (
                        f"modelo selecionado ({requested_model})"
                        if requested_model else "modelo automático"
                    )
                    raise Exception(
                        f"O Ollama não retornou texto corrigido com o {selected_hint}. "
                        "Tente outro modelo na revisão de texto."
                    )
            
            return {
                "model_used": model_name,
                "analysis_type": analysis_type,
                "result": response_text,
                "done": result.get("done", True),
                "context": result.get("context", []),
                "total_duration": result.get("total_duration", 0),
                "prompt_eval_count": result.get("prompt_eval_count", 0),
                "eval_count": result.get("eval_count", 0),
                "config_used": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "num_predict": num_predict,
                    "num_ctx": num_ctx
                }
            }
            
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout na análise com {model_name} (timeout={self.config.timeout}s)")
        except requests.exceptions.ConnectionError:
            raise Exception("Erro de conexão com Ollama. Verifique se o serviço está rodando.")
        except Exception as e:
            raise Exception(f"Erro na análise: {e}")
    
    def _generate_analysis_prompt(self, text: str, analysis_type: str, model_name: str = None) -> str:
        """Gera prompt otimizado para análise baseado no tipo e modelo"""
        
        # Contexto base otimizado
        base_context = """Você é um assistente especializado em análise de transcrições de áudio em português brasileiro.
Seja preciso, objetivo e forneça análises estruturadas."""
        
        # Verificar se é DeepSeek R1 para adicionar instruções de raciocínio
        is_deepseek = model_name and "deepseek" in model_name.lower()
        
        # Prefixo para DeepSeek R1 (modelo de raciocínio)
        reasoning_prefix = """
<think>
Antes de responder, analise cuidadosamente o texto fornecido.
Considere múltiplas perspectivas e fundamente sua análise.
</think>

""" if is_deepseek else ""
        
        prompts = {
            "general": f"""{reasoning_prefix}{base_context}

## TAREFA: Análise Completa de Transcrição

Analise a transcrição abaixo e forneça uma análise estruturada:

### Transcrição:
{text}

### Sua Análise (forneça em formato estruturado):

**1. RESUMO EXECUTIVO** (2-3 frases)

**2. PONTOS-CHAVE IDENTIFICADOS** (lista com bullets)

**3. TOM E SENTIMENTO GERAL**

**4. PALAVRAS/FRASES IMPORTANTES**

**5. INSIGHTS E OBSERVAÇÕES**
""",
            
            "sentiment": f"""{reasoning_prefix}{base_context}

## TAREFA: Análise de Sentimento Profunda

Realize uma análise de sentimento detalhada da transcrição abaixo.

### Transcrição:
{text}

### Análise de Sentimento:

**SENTIMENTO PREDOMINANTE:** [Positivo/Neutro/Negativo/Misto]

**NÍVEL DE CONFIANÇA:** [0-100%]

**EMOÇÕES IDENTIFICADAS:**
- [Liste as emoções detectadas com intensidade]

**EVIDÊNCIAS NO TEXTO:**
- [Cite trechos específicos que justificam sua análise]

**VARIAÇÃO DE SENTIMENTO:**
- [Descreva se o sentimento muda ao longo do texto]
""",
            
            "summary": f"""{base_context}

## TAREFA: Resumo Inteligente

Crie um resumo conciso e informativo da transcrição.

### Transcrição:
{text}

### Resumo Estruturado:

**SÍNTESE PRINCIPAL** (máximo 3 frases):

**TÓPICOS ABORDADOS:**
1. 
2. 
3. 

**CONCLUSÕES/DECISÕES MENCIONADAS:**

**AÇÕES OU PRÓXIMOS PASSOS** (se houver):
""",
            
            "keywords": f"""{base_context}

## TAREFA: Extração de Palavras-chave e Temas

Extraia as informações mais relevantes da transcrição.

### Transcrição:
{text}

### Extração:

**TOP 10 PALAVRAS-CHAVE:**
1. [palavra] - [relevância/contexto]
2. ...

**TEMAS PRINCIPAIS:**
- 

**ENTIDADES IDENTIFICADAS:**
- Pessoas: 
- Organizações: 
- Lugares: 
- Datas/Números: 

**TERMOS TÉCNICOS/ESPECÍFICOS:**
""",
            
            "qa": f"""{reasoning_prefix}{base_context}

## CONTEXTO: Assistente de Perguntas sobre Transcrição

Você tem acesso à seguinte transcrição e deve responder perguntas sobre ela de forma precisa e fundamentada.

### Transcrição de Referência:
{text}

### Instruções:
- Responda APENAS com base nas informações presentes na transcrição
- Se a informação não estiver no texto, diga claramente
- Cite trechos relevantes quando apropriado
- Seja objetivo e direto nas respostas

Aguardando pergunta do usuário...
""",

            "correction": f"""{base_context}

## TAREFA: Revisão e Correção de Transcrição

Você é um revisor especializado. Corrija a transcrição mantendo o sentido original.

### Transcrição Original:
{text}

### Instruções de Correção:
1. Corrija erros de transcrição evidentes
2. Ajuste pontuação e capitalização
3. Mantenha o estilo e tom original
4. NÃO altere o significado
5. Preserve expressões coloquiais intencionais
6. Retorne APENAS a transcrição corrigida
7. NÃO inclua explicações, markdown, títulos ou listas

### Transcrição Corrigida:
""",

            "reasoning": f"""{reasoning_prefix}{base_context}

## TAREFA: Análise com Raciocínio Profundo

Analise a transcrição usando raciocínio estruturado.

### Transcrição:
{text}

### Análise com Raciocínio:

**OBSERVAÇÕES INICIAIS:**

**INFERÊNCIAS E DEDUÇÕES:**

**CONEXÕES IDENTIFICADAS:**

**CONCLUSÕES FUNDAMENTADAS:**

**PONTOS QUE REQUEREM MAIS CONTEXTO:**
"""
        }
        
        return prompts.get(analysis_type, prompts["general"])
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Obtém informações detalhadas sobre um modelo"""
        if model_name in self.model_descriptions:
            info = self.model_descriptions[model_name].copy()
            info["available"] = self.is_model_available(model_name)
            return info
        
        return {
            "name": model_name,
            "description": "Modelo Ollama",
            "available": self.is_model_available(model_name)
        }
    
    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações de todos os modelos disponíveis no Ollama"""
        self.get_available_models()
        all_info = {}
        for model_name in self.available_models:
            all_info[model_name] = self.get_model_info(model_name)
        return all_info
    
    def install_recommended_models(self) -> Dict[str, bool]:
        """Instala os modelos recomendados (GPT-OSS e DeepSeek R1)"""
        results = {}
        
        recommended_models = [
            OllamaModel.GPT_OSS.value,
            OllamaModel.DEEPSEEK_R1.value
        ]
        
        for model in recommended_models:
            if not self.is_model_available(model):
                logger.info(f"Instalando modelo recomendado: {model}")
                results[model] = self.pull_model(model)
            else:
                logger.info(f"Modelo {model} já está disponível")
                results[model] = True
        
        return results
    
    def get_model_recommendation(self, analysis_type: str) -> Tuple[str, str]:
        """Retorna recomendação de modelo para um tipo de análise"""
        model = self.analysis_model_preference.get(analysis_type, OllamaModel.GPT_OSS.value)
        
        if model == OllamaModel.GPT_OSS.value:
            reason = "GPT-OSS 20B é ideal para análises gerais, resumos e extração de informações"
        else:
            reason = "DeepSeek R1 é especializado em raciocínio profundo e análises complexas"
        
        return model, reason

class OllamaAnalyzer:
    """Analisador avançado usando Ollama com GPT-OSS e DeepSeek R1"""
    
    def __init__(self, config: OllamaConfig = None):
        self.manager = OllamaManager(config)
        self.conversation_context = []  # Cache de contexto para conversas
    
    def analyze_transcription_complete(self, text: str, 
                                     model_name: Optional[str] = None,
                                     analysis_types: List[str] = None) -> Dict[str, Any]:
        """Realiza análise completa da transcrição usando os modelos mais adequados"""
        
        analyses = {}
        models_used = set()
        
        # Tipos de análise padrão
        if analysis_types is None:
            analysis_types = ["general", "sentiment", "summary", "keywords"]
        
        for analysis_type in analysis_types:
            try:
                # Se modelo específico não foi fornecido, usar o mais adequado
                current_model = model_name
                if not current_model:
                    current_model = self.manager.get_model_for_analysis(analysis_type)
                
                result = self.manager.analyze_transcription(
                    text, current_model, analysis_type
                )
                analyses[analysis_type] = result
                models_used.add(result.get("model_used", "unknown"))
                
                # Pequena pausa entre análises para não sobrecarregar
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erro na análise {analysis_type}: {e}")
                analyses[analysis_type] = {"error": str(e)}
        
        return {
            "transcription_text": text[:500] + "..." if len(text) > 500 else text,
            "full_text_length": len(text),
            "models_used": list(models_used),
            "analyses": analyses,
            "timestamp": time.time(),
            "available_models": self.manager.available_models,
            "analysis_summary": self._generate_analysis_summary(analyses)
        }
    
    def _generate_analysis_summary(self, analyses: Dict[str, Any]) -> Dict[str, str]:
        """Gera um resumo consolidado das análises"""
        summary = {}
        
        for analysis_type, result in analyses.items():
            if "error" not in result:
                summary[analysis_type] = {
                    "status": "success",
                    "model": result.get("model_used", "unknown"),
                    "preview": result.get("result", "")[:200] + "..." if len(result.get("result", "")) > 200 else result.get("result", "")
                }
            else:
                summary[analysis_type] = {
                    "status": "error",
                    "error": result["error"]
                }
        
        return summary
    
    def analyze_with_reasoning(self, text: str, question: str = None) -> Dict[str, Any]:
        """Análise usando DeepSeek R1 para raciocínio profundo"""
        
        # Forçar uso do DeepSeek R1 para raciocínio
        model = OllamaModel.DEEPSEEK_R1.value
        
        if not self.manager.is_model_available(model):
            # Fallback para GPT-OSS se DeepSeek não disponível
            model = OllamaModel.GPT_OSS.value
            logger.warning(f"DeepSeek R1 não disponível, usando {model}")
        
        analysis_type = "reasoning" if not question else "qa"
        
        if question:
            # Combinar texto com pergunta
            combined_text = f"{text}\n\nPergunta específica: {question}"
            return self.manager.analyze_transcription(combined_text, model, "qa")
        
        return self.manager.analyze_transcription(text, model, "reasoning")
    
    def chat_about_transcription(self, text: str, question: str,
                               model_name: Optional[str] = None) -> str:
        """Faz perguntas sobre a transcrição usando o modelo mais adequado para Q&A"""
        
        # Usar DeepSeek R1 para perguntas por padrão (melhor raciocínio)
        if not model_name:
            model_name = self.manager.get_model_for_analysis("qa")
        
        prompt = f"""## Contexto da Transcrição:
{text}

## Pergunta do Usuário:
{question}

## Sua Resposta (baseada APENAS no contexto acima):
"""
        
        try:
            result = self.manager.analyze_transcription(
                prompt, model_name, "qa"
            )
            
            # Armazenar contexto para conversas futuras
            self.conversation_context.append({
                "question": question,
                "answer": result.get("result", ""),
                "model": result.get("model_used", "")
            })
            
            # Manter apenas últimas 10 interações
            if len(self.conversation_context) > 10:
                self.conversation_context = self.conversation_context[-10:]
            
            return result.get("result", "Não foi possível gerar resposta")
            
        except Exception as e:
            return f"Erro ao processar pergunta: {e}"
    
    def get_quick_summary(self, text: str) -> str:
        """Gera um resumo rápido usando GPT-OSS"""
        try:
            result = self.manager.analyze_transcription(
                text, OllamaModel.GPT_OSS.value, "summary"
            )
            return result.get("result", "Resumo não disponível")
        except Exception as e:
            return f"Erro ao gerar resumo: {e}"
    
    def clear_conversation_context(self):
        """Limpa o contexto de conversação"""
        self.conversation_context = []
        logger.info("Contexto de conversação limpo")

def main():
    """Função de teste do módulo - Configurado para GPT-OSS e DeepSeek R1"""
    print("🤖 Testando integração com Ollama (GPT-OSS 20B + DeepSeek R1)...")
    print("=" * 60)
    
    manager = OllamaManager()
    
    # Verificar status do serviço
    if manager.check_service_status():
        print("✅ Serviço Ollama está rodando")
        
        # Listar modelos disponíveis
        models = manager.get_available_models()
        print(f"\n📋 Modelos instalados: {len(models)}")
        for m in models:
            print(f"   - {m}")
        
        # Mostrar informações dos modelos configurados
        print("\n📊 Modelos configurados para análise:")
        print("-" * 40)
        for model_name, info in manager.get_all_models_info().items():
            status = "✅ Disponível" if info["available"] else "❌ Não instalado"
            print(f"\n🔹 {info['name']}")
            print(f"   Status: {status}")
            print(f"   Descrição: {info['description']}")
            print(f"   Pontos fortes: {', '.join(info['strengths'])}")
            print(f"   Ideal para: {', '.join(info.get('best_for_analysis', []))}")
        
        # Mostrar recomendações por tipo de análise
        print("\n🎯 Recomendações de modelo por tipo de análise:")
        print("-" * 40)
        for analysis_type in ["general", "summary", "keywords", "sentiment", "qa", "reasoning"]:
            model, reason = manager.get_model_recommendation(analysis_type)
            available = "✅" if manager.is_model_available(model) else "❌"
            print(f"   {analysis_type}: {model.split(':')[0]} {available}")
        
        # Testar análise se houver modelos
        best_model = manager.get_best_available_model()
        if best_model:
            print(f"\n🧪 Testando análise com: {best_model}")
            print("-" * 40)
            
            # Teste de análise
            test_text = """Esta é uma reunião muito produtiva. Discutimos os próximos passos do projeto 
            e definimos que a equipe de desenvolvimento vai entregar a primeira versão na próxima semana.
            O cliente demonstrou satisfação com o progresso até agora."""
            
            try:
                result = manager.analyze_transcription(test_text, best_model, "general")
                print(f"✅ Teste de análise concluído com sucesso")
                print(f"⏱️  Duração: {result.get('total_duration', 0)/1e9:.2f}s")
                print(f"📝 Preview do resultado:")
                preview = result['result'][:300] + "..." if len(result['result']) > 300 else result['result']
                print(f"   {preview}")
            except Exception as e:
                print(f"❌ Erro no teste de análise: {e}")
        else:
            print("\n❌ Nenhum modelo disponível para teste")
            print("\n💡 Instale os modelos recomendados:")
            print("   ollama pull gpt-oss:20b")
            print("   ollama pull deepseek-r1:14b-qwen-distill-q8_0")
    else:
        print("❌ Serviço Ollama não está rodando")
        print("\n💡 Para iniciar o Ollama:")
        print("   1. Execute: ollama serve")
        print("   2. Instale os modelos:")
        print("      ollama pull gpt-oss:20b")
        print("      ollama pull deepseek-r1:14b-qwen-distill-q8_0")

if __name__ == "__main__":
    main()