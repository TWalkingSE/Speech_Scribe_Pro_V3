# 🎙️ Speech Scribe Pro V3

<p align="center">
  <b>Transcreva áudio e vídeo com precisão profissional usando IA — direto no seu PC, com aceleração por GPU.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/PyQt6-GUI-green?logo=qt" alt="PyQt6">
  <img src="https://img.shields.io/badge/CUDA-GPU%20Accelerated-76B900?logo=nvidia" alt="CUDA">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="MIT License">
  <img src="https://img.shields.io/badge/whisper-faster--whisper-red" alt="Whisper">
</p>

Speech Scribe Pro V3 é uma aplicação desktop completa para transcrição de áudio/vídeo, construída com Python, PyQt6 e modelos Whisper via `faster-whisper`. Pode operar offline para transcrição e análise local após a instalação e o cache dos modelos, roda na sua GPU NVIDIA (ou CPU), e oferece uma suíte de recursos avançados numa interface gráfica moderna.

<img width="1818" height="1150" alt="image" src="https://github.com/user-attachments/assets/69c79353-0deb-4b8d-85e4-f9ce248e4e7e" />

<img width="1821" height="1144" alt="image" src="https://github.com/user-attachments/assets/b96a493c-6c45-4aa8-99da-de76239fd213" />


**Stack principal:** Python 3.12 · PyQt6 · faster-whisper · PyTorch CUDA · pyannote.audio · Ollama

## Funcionalidades

### 🎯 Transcrição Inteligente
- **Modelos Whisper** (tiny, base, small, medium, large-v2, large-v3) via `faster-whisper`
- **Aceleração GPU** com CUDA (detecta automaticamente RTX 3000/4000/5000)
- **Progresso real** com estimativa de tempo restante baseado nos segmentos processados
- **Detecção automática de idioma** ou seleção manual
- **Word timestamps** e filtragem VAD integrada
- **Presets de qualidade** (Rápido, Balanceado, Máxima Qualidade, Podcast)

### 🗣️ Diarização (Separação de Vozes)
- Identificação automática de múltiplos oradores via `pyannote.audio`
- Estatísticas por orador (tempo de fala, porcentagem)
- Requer token do HuggingFace (gratuito)

### 🧠 Análise com IA
- **Análise básica**: sentimento, entidades, palavras-chave, resumo, tópicos
- **Ollama** (IA local): análise completa, resumo executivo, pontos de ação e correção de texto
- **Execução otimizada em GPU**: usa `num_gpu=-1` com contexto seguro automático (`num_ctx`) para evitar split CPU/GPU quando possível
- **Seleção dinâmica de modelos**: todos os modelos instalados no Ollama ficam disponíveis para o usuário escolher
- **Modo Auto**: prioriza modelos compatíveis com a VRAM disponível, mantendo a escolha manual do usuário quando selecionada
- **Análise em thread separada**: não trava a interface durante processamento com Ollama
- **Correção de texto robusta**: retry automático, limpeza do output e fallback quando o modelo devolve resposta vazia
- **Chat interativo**: converse com a IA sobre a transcrição usando qualquer modelo local instalado

### 🌐 Tradução Integrada
- Tradução automática para **30+ idiomas** via `deep-translator`
- Suporte a textos longos com divisão inteligente por parágrafos
- Tradução por segmentos mantendo timestamps

### 🎤 Streaming / Microfone
- **Gravação em tempo real** do microfone
- Seleção de dispositivo de entrada
- Indicador visual de nível de áudio
- Transcrição automática ao parar a gravação

### 📦 Processamento em Lote
- Fila de múltiplos arquivos com progresso individual e geral
- **Drag & Drop** de arquivos e pastas direto na lista
- Exportação multi-formato: **TXT consolidado**, **SRT**, **VTT**, **JSON** individual por arquivo
- Configurações de modelo e idioma por lote

### 📋 Fila de Transcrição (aba principal)
- Adicionar múltiplos arquivos à fila sem sair da aba de transcrição
- Processamento sequencial automático com progresso por arquivo
- Status visual: ⏳ pendente, 🔄 processando, ✅ concluído, ❌ erro

### 🎵 Player de Áudio + Waveform
- Player integrado na aba de transcrição
- Controles: play/pause, stop, avançar/voltar 5s
- **Visualização de forma de onda** (waveform) com posição de reprodução
- Clique na waveform para saltar para qualquer posição
- Barra de posição e controle de volume
- **Carregamento assíncrono** da waveform (não trava a UI)

### 📤 Exportação Multi-formato
- **TXT** — Texto simples
- **JSON** — Dados completos com metadados
- **SRT** — Legendas (compatível com players de vídeo)
- **VTT** — Web Video Text Tracks
- **DOCX** — Documento Word formatado

### Embutir Legendas em Vídeo
- Geração automática de arquivo SRT após transcrição de vídeo
- Embutir legenda diretamente no vídeo via FFmpeg (burn-in)
- Requer FFmpeg instalado no sistema

### Temas
- **Tema Claro** (padrão)
- **Tema Escuro** com alternância por botão no header
- Stylesheet completo para todos os widgets

### Histórico
- Histórico de transcrições em banco SQLite
- Busca, estatísticas e exportação do histórico
- **Exportação completa** em JSON ou CSV

### Persistência de Configurações
- Modelo de transcrição, modelo Ollama, idioma, preset, tema, volume e geometria da janela salvos automaticamente
- Restauração automática ao reabrir a aplicação
- Baseado em `QSettings` (registro do Windows / plist no macOS)

### Internacionalização (i18n)
- Dicionários de tradução para **Português**, **English** e **Español**
- Seletor de idioma na aba de configurações
- Interface traduzida dinamicamente (tabs, botões, labels)

### Suporte Multi-GPU
- Detecção automática de múltiplas GPUs NVIDIA
- Seletor de GPU na aba de configurações (para sistemas com 2+ GPUs)

### Verificação de Atualização
- Verificação automática de nova versão ao iniciar (configurável via `SPEECH_SCRIBE_VERSION_URL`)

### Validação de Arquivos
- Verificação automática se o arquivo é áudio/vídeo válido antes de transcrever
- Diálogo de confirmação se validação falhar

### Segurança ao Fechar
- Confirmação antes de fechar com transcrição em andamento
- Cancelamento automático da transcrição ao sair

### Log Rotation
- Logs com rotação automática (máx 5MB, 3 backups)
- Evita acumulação de arquivos de log grandes

### Testes Automatizados
- Suite de testes cobrindo: i18n, themes, settings, config, history, presets, batch export, translator, integração com Ollama, cache, plugins e smoke tests de GUI
- Smoke tests para GUI (com `pytest-qt`)

### Atalhos de Teclado
| Atalho | Ação |
|--------|------|
| `Ctrl+O` | Abrir arquivo |
| `Ctrl+T` | Iniciar transcrição |
| `Ctrl+S` | Salvar |
| `Ctrl+E` | Exportar |
| `Ctrl+F` | Buscar no texto |
| `Ctrl+H` | Histórico |
| `F3` / `Shift+F3` | Próxima / anterior ocorrência |
| `Escape` | Fechar busca |

---

## Instalação

### Pré-requisitos
- Python 3.10+
- GPU NVIDIA com CUDA (recomendado, mas funciona em CPU)
- [Ollama](https://ollama.ai) (opcional, para análise com IA local)

### 1. Clonar e criar ambiente virtual
```bash
git clone https://github.com/SEU_USUARIO/Speech_Scribe_Pro_v3.git
cd Speech_Scribe_Pro_v3
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. Instalar PyTorch com CUDA
Instale o PyTorch **antes** das outras dependências (importante no Windows):

```bash
# RTX 5000 / CUDA 12.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# RTX 4000 / CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CPU apenas
pip install torch torchvision torchaudio
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

O `requirements.txt` agora inclui as dependências diretas do projeto para GUI, transcrição, diarização, tradução, exportação DOCX, configuração YAML, streaming por microfone e testes. Se o `pyaudio` falhar no seu ambiente, instale uma wheel compatível com sua plataforma ou resolva antes a dependência nativa do PortAudio.

Em Linux e macOS, isso normalmente significa instalar o PortAudio antes de repetir o `pip install -r requirements.txt`.

### 4. Configurar variáveis de ambiente
```bash
copy .env.example .env
# Edite .env com seu token do HuggingFace (para diarização)
```

### 5. Executar
```bash
python main.py
```

---

## Estrutura do Projeto

```
Speech_Scribe_Pro_v3/
├── main.py                          # Entry point principal (único)
├── requirements.txt                 # Dependências
├── .env.example                     # Template de configuração
├── .gitignore                       # Proteção de arquivos sensíveis
│
└── speech_scribe/                   # Pacote modular
    ├── __init__.py                  # Inicialização (torch antes de PyQt6)
    ├── main.py                      # Lógica de inicialização
    ├── cli.py                       # Interface de linha de comando
    │
    ├── core/                        # Módulos principais
    │   ├── config.py                # AppConfig (configurações centralizadas)
    │   ├── hardware.py              # ModernHardwareDetector (CPU/GPU)
    │   ├── transcription.py         # IntelligentTranscriptionEngine
    │   ├── diarization.py           # SpeakerDiarization (pyannote.audio)
    │   ├── analysis.py              # SmartAnalyzer + Ollama
    │   ├── models.py                # TranscriptionResult dataclass tipado
    │   ├── translator.py            # TranscriptionTranslator (deep-translator)
    │   ├── subtitle_embedder.py     # Embutir legendas em vídeo (FFmpeg)
    │   ├── exporters.py             # TXT, JSON, SRT, VTT, DOCX
    │   ├── history.py               # Histórico em SQLite + export JSON/CSV
    │   ├── presets.py               # Presets de qualidade
    │   ├── settings.py              # UserSettings (QSettings persistência)
    │   ├── i18n.py                  # Internacionalização (pt/en/es)
    │   ├── version_checker.py       # Verificação de atualização (thread-safe)
    │   ├── dependencies.py          # Verificação de dependências
    │   ├── exceptions.py            # Hierarquia de exceções
    │   ├── cache.py                 # Cache LRU de modelos
    │   ├── config_manager.py        # Enums e configurações avançadas
    │   └── ollama_integration.py    # Integração com Ollama
    │
    ├── gui/                         # Interface gráfica
    │   ├── main_window.py           # SpeechScribeProV3 (janela principal)
    │   ├── widgets.py               # DropLabel, ModernUIBuilder
    │   ├── threads.py               # TranscriptionThread (progresso real)
    │   ├── audio_player.py          # AudioPlayerWidget
    │   ├── waveform.py              # WaveformWidget (async, thread-safe)
    │   ├── batch_processor.py       # BatchProcessorWidget + DropListWidget
    │   ├── streaming.py             # StreamingWidget (microfone)
    │   ├── themes.py                # ThemeManager (dark/light)
    │   ├── enhancements.py          # SearchWidget, HistoryDialog + export
    │   └── mixins/                  # Documentação de organização
    │
    ├── plugins/                     # Sistema de plugins
    │   ├── base.py                  # Interfaces e tipos base
    │   ├── manager.py               # Descoberta e carregamento
    │   └── examples/                # Plugins de exemplo
    │
    ├── utils/                       # Utilitários
    │   ├── logger.py                # Logging com RotatingFileHandler
    │   ├── performance.py           # Monitoramento de performance
    │   └── structured_logger.py     # Logging estruturado

tests/                               # Testes automatizados
├── conftest.py                      # Fixtures compartilhadas
├── test_cache.py                    # Cache e expiração
├── test_config_manager.py           # Configuração avançada
├── test_core.py                     # Módulos centrais
├── test_enhancements.py             # Melhorias e presets
├── test_exceptions.py               # Hierarquia de exceções
├── test_gui_smoke.py                # Smoke tests GUI
├── test_new_modules.py              # i18n, themes, settings, history, etc.
├── test_ollama_integration.py       # Integração com Ollama
├── test_phase3.py                   # Performance, cache e batch core
└── test_phase4.py                   # Plugins e exportação
```

---

## Configuração

### Variáveis de Ambiente (.env)

| Variável | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| `HUGGINGFACE_TOKEN` | Token para diarização (pyannote.audio) | Para diarização |
| `SPEECH_SCRIBE_DEVICE` | Override do dispositivo padrão (`auto`, `cpu`, `cuda`) | Não |
| `SPEECH_SCRIBE_MODEL` | Override do modelo padrão de transcrição | Não |
| `SPEECH_SCRIBE_LANGUAGE` | Override do idioma padrão da transcrição | Não |
| `SPEECH_SCRIBE_VERSION_URL` | URL para verificação de atualização | Não |
| `CUDA_VISIBLE_DEVICES` | Limita as GPUs visíveis para CUDA/PyTorch | Não, avançado |

O modelo padrão do Ollama é persistido nas configurações do usuário pela interface, e não via `.env`.

### Conectividade e Requisições Externas

O aplicativo pode operar localmente para transcrição e análise com Ollama, mas alguns recursos opcionais podem realizar requisições de rede dependendo da configuração e do uso:

- **Transcrição com Whisper**: ao carregar um modelo pelo nome, o `faster-whisper` pode baixar os arquivos do modelo do Hugging Face Hub na primeira execução, caso ainda não estejam em cache local.
- **Diarização**: ao usar `pyannote.audio`, o aplicativo pode acessar o Hugging Face para autenticação e download inicial do pipeline/modelos quando a diarização é habilitada.
- **Tradução**: a tradução integrada usa `deep-translator` com `GoogleTranslator` e envia o texto a ser traduzido para um serviço externo somente quando essa função é utilizada.
- **Verificação de atualização**: a aplicação só faz essa consulta se `SPEECH_SCRIBE_VERSION_URL` estiver configurada. No projeto atual, essa variável vem vazia no `.env.example`, então a checagem fica desativada por padrão.
- **Ollama**: a integração com Ollama usa HTTP para conversar com um serviço local em `http://localhost:11434`. Isso é tráfego local entre a aplicação e o Ollama, não uma requisição para servidores externos do projeto.

O código do projeto não implementa integração explícita com serviços próprios de analytics ou telemetria.

### Hardware Recomendado

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| GPU | - | NVIDIA RTX 3060+ (8GB VRAM) |
| CUDA | - | 12.1+ |

### Modelos Whisper

| Modelo | VRAM | Velocidade | Qualidade |
|--------|------|------------|-----------|
| tiny | ~1 GB | Muito rápido | Básica |
| base | ~1 GB | Rápido | Boa |
| small | ~2 GB | Moderado | Boa |
| medium | ~5 GB | Lento | Alta |
| large-v2 | ~10 GB | Muito lento | Muito alta |
| large-v3 | ~10 GB | Muito lento | Máxima |

### Modelos Ollama (Análise com IA Local)

A análise com IA usa o Ollama com **prioridade máxima de GPU** (`num_gpu=-1`) e um **contexto seguro automático** para evitar cargas desnecessárias em CPU. Em GPUs de 16 GB, um contexto muito alto no Ollama pode inflar o uso total do modelo e causar split CPU/GPU, mesmo quando o modelo em si cabe na VRAM. O aplicativo agora reduz o `num_ctx` automaticamente e o modo Auto prioriza modelos que cabem com folga na VRAM.

| GPU VRAM | Faixa prática para análise local | Exemplos |
|----------|----------------------------------|----------|
| 6 GB | Modelos pequenos ou quantizados até ~4-6 GB | `qwen2.5:3b`, `phi3:mini` |
| 8 GB | Modelos até ~7-8 GB em disco | `llama3.1:8b`, `qwen2.5:7b` |
| 16 GB | Modelos até ~12-14 GB em disco com `num_ctx` controlado | `qwen3.5:9b-q8_0`, `gpt-oss:20b`, `deepseek-r1:14b-qwen-distill-q8_0` |
| 24 GB | Modelos médios/grandes com mais folga para contexto | `gpt-oss:20b`, `codellama:34b-q4` |
| 32 GB+ | Modelos grandes e contextos mais altos | 20B+ e quantizações maiores |

> **Notas:**
> - Todos os modelos instalados no Ollama aparecem automaticamente na interface.
> - `100% GPU` só acontece quando **modelo + cache de contexto** cabem na VRAM disponível.
> - O aplicativo exibe na interface o processador efetivo (`CPU/GPU`) e o `ctx` carregado pelo Ollama.
> - Em testes locais, `qwen3.5:9b-q8_0` em 16 GB ficou `100% GPU` com `num_ctx=8192`, enquanto contextos muito altos faziam o modelo subir para ~25 GB e dividir CPU/GPU.

---

## Notas Técnicas

### Ollama, VRAM e Contexto
- O app descarrega e recarrega o modelo do Ollama antes da análise para aplicar as opções de GPU corretamente.
- O status real do modelo é lido de `/api/ps`, incluindo `size_vram` e `context_length`.
- A revisão de texto agora pede somente a transcrição corrigida e tenta novamente com um prompt mais restrito se o modelo retornar vazio.

### Migração PyQt5 → PyQt6
O projeto foi migrado de PyQt5 para PyQt6. Mudanças principais:
- Enums totalmente qualificados (`Qt.AlignmentFlag.AlignCenter` em vez de `Qt.AlignCenter`)
- `QMessageBox.StandardButton.Yes` em vez de `QMessageBox.Yes`
- `QTextCursor.MoveMode.KeepAnchor` em vez de `QTextCursor.KeepAnchor`
- `QMediaPlayer` usa `QAudioOutput` e `setSource()` (API Qt6)
- `exec()` em vez de `exec_()`

### Conflito PyQt6 / torch no Windows
No Windows, as DLLs do PyQt6 conflitam com `c10.dll` do torch CUDA. O projeto resolve isso importando `torch` antes de `PyQt6` no `speech_scribe/__init__.py`.

### Verificação de Dependências
O `SmartDependencyManager` usa `importlib.util.find_spec()` (sem efeitos colaterais) em vez de `__import__()` para evitar conflitos de DLL durante a checagem.

---

## Testes

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Apenas testes dos módulos adicionais
python -m pytest tests/test_new_modules.py -v

# Smoke tests GUI (pytest-qt já incluído no requirements.txt)
python -m pytest tests/test_gui_smoke.py -v
```

---

## CLI (Interface de Linha de Comando)

O projeto inclui uma CLI completa para uso sem interface gráfica:

```bash
# Transcrever arquivo
python -m speech_scribe.cli transcribe audio.mp3 -m large-v3 -l pt

# Processamento em lote (modelo carregado uma única vez)
python -m speech_scribe.cli batch *.mp3 -m small -o resultados/

# Verificar status do sistema
python -m speech_scribe.cli status --all

# Análise com IA
python -m speech_scribe.cli analyze transcricao.txt --all
```

---

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

1. Fork o repositório
2. Crie sua branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## Licença

MIT License — veja o arquivo [LICENSE](LICENSE) para detalhes.

Copyright (c) 2025-2026 Speech Scribe Pro V3
