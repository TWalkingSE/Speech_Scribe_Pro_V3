# 🎮 Detecção Automática de GPU

## Visão Geral

O Speech Scribe Pro V3 usa `ModernHardwareDetector` para detectar CUDA, validar se a GPU realmente funciona e gerar parâmetros automáticos para transcrição.

## O que é detectado

- Disponibilidade de CUDA via `torch.cuda.is_available()`
- Teste funcional real da GPU com alocação de tensor
- Número de GPUs disponíveis
- Nome, VRAM, compute capability e score de performance de cada GPU
- Melhor GPU disponível em cenários multi-GPU

## Otimizações aplicadas

### Por VRAM

| VRAM detectada | Modelo recomendado | Batch size | Beam size | Chunk |
|----------------|--------------------|------------|-----------|-------|
| `>= 20 GB` | `large-v3` | `4` | `10` | `60s` |
| `>= 15 GB` | `large-v3` | `2` | `8` | `45s` |
| `>= 11 GB` | `large-v2` | `2` | `6` | `30s` |
| `>= 7 GB` | `medium` | `1` | `5` | `20s` |
| `< 7 GB` | `small` | `1` | `3` | `15s` |

### Por Compute Capability

| Compute Capability | Perfil | Compute type |
|-------------------|--------|--------------|
| `>= 12.0` | RTX 50 Series | `float16` |
| `>= 8.9` | RTX 40 Series | `float16` |
| `>= 8.0` | RTX 30 Series | `float16` |
| `>= 7.0` | RTX 20 Series / Volta | `float16` |
| `< 7.0` | GPUs mais antigas | `int8_float16` |

## Uso via código

```python
from speech_scribe.core.hardware import ModernHardwareDetector

detector = ModernHardwareDetector()

print(detector.info['cuda_available'])
print(detector.info['cuda_functional'])
print(detector.info['primary_gpu'])
print(detector.optimizations)

gpu_details = detector.get_detailed_gpu_info()
print(gpu_details)
```

## Uso na interface

Na aba de configurações, o app expõe:

- seletor de dispositivo (`auto`, `cpu`, `cuda`)
- seletor de GPU quando há múltiplas GPUs
- slider de uso de VRAM
- botão `⚡ Otimizar GPU`
- painel com informações detalhadas da GPU detectada

## Uso via CLI

```bash
python -m speech_scribe.cli status --hardware
```

## Comportamentos importantes

### Fallback para CPU
Se CUDA falhar durante a transcrição, o engine tenta recarregar o modelo em CPU e continuar o processamento.

### Cache de modelos
Os modelos carregados pelo engine ficam em cache em memória por combinação de modelo e dispositivo, evitando recarregamentos desnecessários.

### Otimização de memória
`optimize_gpu_memory()` limpa o cache CUDA e aplica a fração de VRAM configurada para o processo atual.

## Solução de Problemas

### GPU não detectada
- verifique drivers com `nvidia-smi`
- confirme o build CUDA do PyTorch com `python -c "import torch; print(torch.cuda.is_available())"`
- reinstale PyTorch com o índice CUDA correto, conforme [installation.md](installation.md)

### CUDA detectado, mas não funcional
- reinicie o ambiente Python
- valide se outras bibliotecas não carregaram DLLs conflitantes antes do `torch`
- em Windows, prefira iniciar o app pelo fluxo normal do projeto, que importa `torch` antes de `PyQt6`

### CUDA out of memory
- use um modelo menor
- reduza a fração de VRAM na interface
- feche outros processos que usam GPU

### Performance abaixo do esperado
- confira no status do sistema se o device efetivo é `cuda`
- confirme se a GPU selecionada é a correta em sistemas multi-GPU
- use o modelo recomendado exibido pelo detector para o hardware atual
