# 📦 Guia de Instalação

## Requisitos do Sistema

### Mínimos
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **Python**: 3.10 ou superior
- **RAM**: 8GB
- **Disco**: 5GB livres
- **CPU**: 4 cores

### Recomendados
- **RAM**: 16GB+
- **GPU**: NVIDIA com 8GB+ VRAM (CUDA 12.1+)
- **Disco**: SSD com 10GB+ livres
- **CPU**: 8+ cores

## Instalação

### 1. Clonar Repositório

```bash
git clone https://github.com/SEU_USUARIO/Speech_Scribe_Pro_v3.git
cd Speech_Scribe_Pro_v3
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
# Instale PyTorch ANTES das outras dependências (importante no Windows)
# RTX 5000 / CUDA 12.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# RTX 4000 / CUDA 12.1
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CPU apenas
# pip install torch torchvision torchaudio

# Dependências do projeto
pip install -r requirements.txt
```

O `requirements.txt` inclui as dependências diretas do projeto para GUI, transcrição, diarização, tradução, exportação DOCX, configuração YAML, streaming por microfone e testes.

Se o `pyaudio` falhar na instalação, use uma wheel compatível com sua plataforma ou resolva antes as dependências nativas do PortAudio.

Se quiser sobrescrever defaults da aplicação via `.env`, use as chaves `SPEECH_SCRIBE_DEVICE`, `SPEECH_SCRIBE_MODEL`, `SPEECH_SCRIBE_LANGUAGE` e `SPEECH_SCRIBE_VERSION_URL` do arquivo `.env.example`.

## Conectividade e Requisições Externas

O Speech Scribe Pro V3 pode operar localmente para transcrição e análise com Ollama, mas alguns recursos opcionais podem realizar requisições de rede dependendo da configuração e do uso:

- **Transcrição com Whisper**: ao carregar um modelo pelo nome, o `faster-whisper` pode baixar os arquivos do modelo do Hugging Face Hub na primeira execução, caso ainda não estejam em cache local.
- **Diarização**: ao usar `pyannote.audio`, o aplicativo pode acessar o Hugging Face para autenticação e download inicial do pipeline/modelos quando a diarização é habilitada.
- **Tradução**: a tradução integrada usa `deep-translator` com `GoogleTranslator` e envia o texto a ser traduzido para um serviço externo somente quando essa função é utilizada.
- **Verificação de atualização**: a aplicação só faz essa consulta se `SPEECH_SCRIBE_VERSION_URL` estiver configurada. No projeto atual, essa variável vem vazia no `.env.example`, então a checagem fica desativada por padrão.
- **Ollama**: a integração com Ollama usa HTTP para conversar com um serviço local em `http://localhost:11434`. Isso é tráfego local entre a aplicação e o Ollama, não uma requisição para servidores externos do projeto.

O código do projeto não implementa integração explícita com serviços próprios de analytics ou telemetria. Bibliotecas de terceiros podem ter comportamentos opcionais próprios, conforme sua configuração.

### 4. Configurar Diarização (Opcional)

Para usar diarização (separação de oradores):

1. Criar conta no [HuggingFace](https://huggingface.co)
2. Aceitar os termos em:
   - https://huggingface.co/pyannote/speaker-diarization
   - https://huggingface.co/pyannote/segmentation
3. Criar token de acesso em Settings → Access Tokens
4. Criar arquivo `.env` a partir do template:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

5. Editar `.env` e preencher o token:

```env
HUGGINGFACE_TOKEN=hf_seu_token_aqui
```

### 5. Verificar Instalação

```bash
# Verificar status
python -m speech_scribe.cli status --all

# Deve mostrar:
# ✅ Hardware detectado
# ✅ Dependências instaladas
# ✅/❌ GPU disponível
# ✅/❌ Ollama disponível
```

## Instalação com GPU

### NVIDIA (CUDA)

```bash
# Verificar versão CUDA
nvidia-smi

# RTX 5000 / CUDA 12.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# RTX 4000 / CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# RTX 3000 / CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### AMD (ROCm) - Experimental

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

## Instalação do Ollama (Opcional)

Para análise com IA local:

### Windows
1. Baixar de [ollama.ai](https://ollama.ai)
2. Executar instalador
3. Iniciar: `ollama serve`
4. Baixar modelo: `ollama pull llama3.2:3b`

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.2:3b
```

## Solução de Problemas

### Erro: "CUDA out of memory"
- Use modelo menor: `small` ao invés de `large-v3`
- Reduza batch_size nas configurações
- Feche outras aplicações usando GPU

### Erro: "ffmpeg not found"
- Windows: `winget install ffmpeg`
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

### Erro: "PyQt6 not found"
```bash
pip install PyQt6
# ou no Linux
sudo apt install python3-pyqt6
```

### Erro ao instalar `pyaudio`
- Windows: prefira uma wheel compatível com sua versão do Python, quando disponível
- Linux: instale os headers do PortAudio antes de rodar `pip install -r requirements.txt`
- macOS: instale o PortAudio antes de instalar as dependências Python

Exemplos:

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-dev

# macOS
brew install portaudio
```

## Atualização

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```
