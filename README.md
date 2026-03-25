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

Speech Scribe Pro V3 é uma aplicação desktop completa para transcrição de áudio/vídeo, construída com Python, PyQt6 e modelos Whisper via `faster-whisper`. Funciona offline, roda na sua GPU NVIDIA (ou CPU), e oferece uma suíte de recursos avançados numa interface gráfica moderna.

**Stack principal:** Python 3.12 · PyQt6 · faster-whisper · PyTorch CUDA · pyannote.audio · Ollama

---

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
- **Ollama** (IA local): análise completa, resumo executivo, pontos de ação
- **Chat interativo**: converse com a IA sobre a transcrição usando modelos locais

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
- Modelo, idioma, preset, tema, volume e geometria da janela salvos automaticamente
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
- Suite de **51+ testes** cobrindo: i18n, themes, settings, config, history, presets, batch export, translator, models dataclass
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

# Para player de áudio integrado (necessário)
pip install PyQt6-Multimedia

# Para transcrição via microfone (opcional)
pip install pyaudio
```

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
    ├── utils/                       # Utilitários
    │   ├── logger.py                # Logging com RotatingFileHandler
    │   └── performance.py           # Monitoramento de performance

tests/                               # Testes automatizados
├── conftest.py                      # Fixtures compartilhadas
├── test_new_modules.py              # 43 testes (i18n, themes, settings, etc.)
├── test_gui_smoke.py                # Smoke tests GUI + TranscriptionResult
└── test_core.py                     # Testes dos módulos core
```

---

## Configuração

### Variáveis de Ambiente (.env)

| Variável | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| `HUGGINGFACE_TOKEN` | Token para diarização (pyannote.audio) | Para diarização |
| `OLLAMA_HOST` | URL do servidor Ollama | Não (padrão: localhost:11434) |
| `OLLAMA_MODEL` | Modelo padrão para análise | Não |
| `OPENAI_API_KEY` | Chave da API OpenAI | Não |
| `SPEECH_SCRIBE_VERSION_URL` | URL para verificação de atualização | Não |

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

---

## Notas Técnicas

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
# Executar todos os testes (51+ testes)
python -m pytest tests/ -v

# Apenas testes de módulos core
python -m pytest tests/test_new_modules.py -v

# Smoke tests GUI (requer pytest-qt)
pip install pytest-qt
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
