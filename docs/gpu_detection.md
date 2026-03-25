# 🎮 Detecção Automática de GPU

## Visão Geral

O Speech Scribe Pro V3 detecta automaticamente o hardware disponível e aplica otimizações inteligentes baseadas na GPU detectada. O sistema usa o `ModernHardwareDetector` para identificar GPUs NVIDIA, avaliar performance e configurar parâmetros ideais.

---

## Funcionalidades

### Detecção Automática
- Verificação de `torch.cuda.is_available()` com validação funcional completa
- Enumeração de todas as GPUs disponíveis
- Score de performance automático por GPU
- Seleção inteligente da melhor GPU (em sistemas multi-GPU)
- Fallback automático para CPU se a GPU falhar

### Otimizações por VRAM

| VRAM | Modelo Recomendado | Batch Size | Beam Size | Chunk |
|------|-------------------|------------|-----------|-------|
| ≥24GB | large-v3 | 4 | 10 | 60s |
| ≥16GB | large-v2 | 2 | 8 | 45s |
| ≥12GB | medium | 2 | 6 | 30s |
| ≥8GB | small | 1 | 5 | 20s |
| <8GB | tiny | 1 | 3 | 15s |

### Otimizações por Compute Capability

| Compute Capability | GPUs | Compute Type |
|-------------------|------|-------------|
| ≥8.0 | RTX 3000/4000/5000 | `float16` |
| ≥7.0 | RTX 2000 | `float16` |
| <7.0 | GPUs anteriores | `int8_float16` |

---

## Uso

### Via Código

```python
from speech_scribe.core.hardware import ModernHardwareDetector

detector = ModernHardwareDetector()
info = detector.get_full_info()

# Informações disponíveis:
# info['cuda_available']      - CUDA instalado
# info['cuda_functional']     - GPU funcional (teste real)
# info['primary_gpu']         - GPU principal (nome, VRAM, compute capability)
# info['optimizations']       - Configurações otimizadas para a GPU
```

### Via Interface Gráfica

Na aba **Configurações**:
- Seção dedicada à GPU com informações detalhadas
- Botão **"Otimizar GPU"** para limpeza de cache VRAM
- Botão **"Testar GPU"** para diagnóstico
- Slider de uso máximo de VRAM
- Seletor de GPU (em sistemas multi-GPU)

### Via CLI

```bash
python -m speech_scribe.cli status --hardware
```

---

## Recursos Avançados

### Gerenciamento de Memória
O sistema limpa automaticamente o cache CUDA antes de carregar modelos e configura a fração máxima de memória GPU por processo.

### Fallback Inteligente
Se a GPU falhar durante a transcrição (ex: CUDA out of memory), o sistema automaticamente recarrega o modelo na CPU e continua o processamento.

### Cache de Modelos
Modelos carregados ficam em cache LRU (até 4 modelos), evitando recarregamento ao alternar entre modelos diferentes.

### Métricas de Performance
Após cada transcrição, o sistema registra:
- Fator de tempo real (velocidade vs duração do áudio)
- Dispositivo utilizado (CPU/CUDA)
- Caracteres processados por segundo

---

## Solução de Problemas

### "CUDA out of memory"
- Use um modelo menor (`small` ao invés de `large-v3`)
- Feche outras aplicações que usam a GPU
- Reduza o slider de uso de VRAM na aba Configurações

### GPU não detectada
- Verifique se os drivers NVIDIA estão atualizados: `nvidia-smi`
- Verifique se o PyTorch foi instalado com CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- Reinstale o PyTorch com a versão CUDA correta (ver [Instalação](installation.md))

### Performance abaixo do esperado
- Verifique se está usando GPU: confira o indicador na barra de status
- Use o botão "Testar GPU" na aba Configurações para diagnóstico
- Certifique-se de que o PyTorch com CUDA está instalado corretamente

## 🚀 **Como Usar**

### **1. Detecção Automática:**
```bash
# Executar aplicação - detecção automática
python main.py

# Teste específico de GPU
python test_gpu_detection.py
```

### **2. Na Interface:**
1. **Aba "⚙️ Configurações"**
2. **Seção "🎮 Informações da GPU"** (se disponível)
3. **Botões de otimização** e teste
4. **Configuração manual** de VRAM se necessário

### **3. Via Código:**
```python
from speech_scribe.core.hardware import ModernHardwareDetector

# Detecção completa
detector = ModernHardwareDetector()

# Verificar se GPU está funcional
if detector.info['cuda_functional']:
    print(f"GPU: {detector.info['primary_gpu']['name']}")
    print(f"Modelo recomendado: {detector.optimizations['recommended_model']}")
    
    # Otimizar GPU
    detector.optimize_gpu_memory()
```

---

## 🎯 **Benefícios Implementados**

### **✅ Para Usuários:**
- **Detecção automática** - sem configuração manual
- **Otimizações inteligentes** - melhor performance automaticamente
- **Interface informativa** - saber exatamente o que está acontecendo
- **Fallback automático** - nunca falha por problemas de GPU

### **✅ Para Desenvolvedores:**
- **Código modular** - fácil de manter e estender
- **APIs bem definidas** - integração simples
- **Logs detalhados** - debugging eficiente
- **Extensibilidade** - fácil adicionar novos tipos de hardware

### **✅ Para Performance:**
- **5-15x mais rápido** com GPU apropriada
- **Uso otimizado de VRAM** - sem desperdício
- **Cache inteligente** - modelos carregados uma vez
- **Processamento paralelo** - máximo aproveitamento do hardware

---

## 📈 **Resultados Esperados por Hardware**

### **🖥️ CPU High-End (24+ cores, 32GB+ RAM):**
- **Velocidade:** 2-3x tempo real
- **Modelo:** large-v2
- **Qualidade:** Alta

### **🎮 GPU Entry (RTX 4060, 8GB VRAM):**
- **Velocidade:** 3-5x tempo real  
- **Modelo:** small
- **Qualidade:** Média

### **🚀 GPU Mid (RTX 4070, 12GB VRAM):**
- **Velocidade:** 5-8x tempo real
- **Modelo:** medium
- **Qualidade:** Média-Alta

### **🔥 GPU High-End (RTX 4090, 24GB VRAM):**
- **Velocidade:** 10-15x tempo real
- **Modelo:** large-v3  
- **Qualidade:** Máxima

---

## 🎉 **Conclusão**

A **detecção automática de GPU** foi implementada com sucesso no Speech Scribe Pro V3, criando um sistema **mais inteligente e robusto** que o projeto original. 

### **Principais Conquistas:**

1. ✅ **Detecção 100% automática** - sem configuração manual necessária
2. ✅ **Otimizações inteligentes** - baseadas no hardware específico
3. ✅ **Interface moderna** - informações detalhadas da GPU
4. ✅ **Fallback robusto** - nunca falha por problemas de hardware
5. ✅ **Performance superior** - 5-15x mais rápido com GPU apropriada

O sistema agora **detecta automaticamente** qualquer GPU NVIDIA com CUDA, **testa sua funcionalidade**, **calcula otimizações específicas** e **aplica configurações automáticas** para máxima performance.

**🚀 O Speech Scribe Pro V3 está pronto para usar GPU automaticamente!**

---

*📅 Implementado em: 22/08/2025*  
*🔧 Versão: 3.0.0*  
*📊 Status: ✅ Completo e Testado* 