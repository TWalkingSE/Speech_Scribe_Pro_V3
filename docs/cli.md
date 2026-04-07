# 🖥️ Referência da CLI

## Uso Geral

```bash
python -m speech_scribe.cli [opções] <comando> [argumentos]
```

## Opções Globais

| Opção | Descrição |
|-------|-----------|
| `--version, -V` | Mostra versão |
| `--verbose, -v` | Modo verboso |
| `--quiet, -q` | Modo silencioso |
| `--json` | Saída em JSON |
| `--help, -h` | Mostra ajuda |

## Comandos

### transcribe (t)

Transcreve arquivos de áudio/vídeo.

```bash
python -m speech_scribe.cli transcribe <arquivos> [opções]
```

**Argumentos:**
- `arquivos`: Um ou mais arquivos (suporta glob: `*.mp3`)

**Opções:**

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `-m, --model` | `small` | Modelo Whisper |
| `-l, --language` | `auto` | Idioma do áudio |
| `-o, --output` | - | Diretório/arquivo de saída |
| `-f, --format` | `txt` | Formato: txt, json, srt, vtt |
| `--diarize` | - | Habilitar diarização |
| `--timestamps` | - | Incluir timestamps no TXT |
| `--device` | `auto` | Forçar dispositivo: auto, cpu, cuda |
| `--embed-subtitle` | - | Embutir legenda no vídeo via FFmpeg |
| `--burn-in` | `True` | Queimar legenda no vídeo ao embutir |
| `--keep-srt` | `True` | Manter arquivo SRT ao embutir legenda |

**Exemplos:**

```bash
# Básico
python -m speech_scribe.cli t audio.mp3

# Com opções
python -m speech_scribe.cli t video.mp4 -m large-v3 -l pt -f srt -o legendas/

# Múltiplos arquivos
python -m speech_scribe.cli t *.mp3 -o transcritos/

# Com diarização
python -m speech_scribe.cli t reuniao.mp3 --diarize --timestamps

# Embutir legenda diretamente no vídeo
python -m speech_scribe.cli t video.mp4 -f srt --embed-subtitle
```

---

### analyze (a)

Analisa texto transcrito.

```bash
python -m speech_scribe.cli analyze <arquivo> [opções]
```

**Argumentos:**
- `arquivo`: Arquivo de texto para analisar

**Opções:**

| Opção | Descrição |
|-------|-----------|
| `--sentiment` | Análise de sentimento |
| `--keywords` | Extração de palavras-chave |
| `--entities` | Extração de entidades |
| `--summary` | Gerar resumo |
| `--topics` | Identificar tópicos |
| `--all` | Todas as análises |
| `--ollama` | Incluir bloco de análise via Ollama |
| `--ollama-model` | Forçar modelo específico do Ollama |
| `-o, --output` | Arquivo de saída |

**Exemplos:**

```bash
# Análise completa
python -m speech_scribe.cli a texto.txt --all

# Análises específicas
python -m speech_scribe.cli a texto.txt --sentiment --keywords

# Com Ollama
python -m speech_scribe.cli a texto.txt --all --ollama --ollama-model llama3.2:3b

# Saída JSON e arquivo ao mesmo tempo
python -m speech_scribe.cli a texto.txt --all --json -o analise.json
```

Quando `--json` é usado, o resultado continua sendo impresso no stdout. Se `-o` também for informado, o mesmo JSON é salvo em arquivo.

---

### batch (b)

Processa múltiplos arquivos em lote com um único modelo carregado na memória.

```bash
python -m speech_scribe.cli batch <arquivos> [opções]
```

**Opções:**

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `-m, --model` | `small` | Modelo Whisper |
| `-l, --language` | `auto` | Idioma |
| `-o, --output` | - | Arquivo TXT consolidado ou diretório de saída |
| `-w, --workers` | `2` | Opção aceita, mas o fluxo atual da CLI processa arquivos em sequência |
| `--analyze` | - | Opção reservada; não altera a saída consolidada atual |
| `--embed-subtitle` | - | Embute legendas em vídeos transcritos via FFmpeg |

**Exemplos:**

```bash
# Batch simples
python -m speech_scribe.cli b audios/*.mp3 -o transcricoes_lote.txt

# Salvar em diretório (gera nome consolidado automaticamente)
python -m speech_scribe.cli b *.mp3 -o resultados/

# Embutindo legenda em vídeos do lote
python -m speech_scribe.cli b *.mp4 --embed-subtitle -o lote_videos.txt
```

O comando `batch` atual gera um único arquivo TXT consolidado contendo as transcrições bem-sucedidas do lote.

---

### status (s)

Verifica status do sistema.

```bash
python -m speech_scribe.cli status [opções]
```

**Opções:**

| Opção | Descrição |
|-------|-----------|
| `--hardware` | Info de hardware |
| `--dependencies` | Verificar dependências |
| `--ollama` | Status do Ollama |
| `--all` | Mostrar tudo |

**Exemplos:**

```bash
# Status completo
python -m speech_scribe.cli s --all

# Apenas hardware
python -m speech_scribe.cli s --hardware

# JSON para scripts
python -m speech_scribe.cli s --all --json
```

---

### config (c)

Gerencia configurações.

```bash
python -m speech_scribe.cli config <ação> [opções]
```

**Ações:**

| Ação | Descrição |
|------|-----------|
| `show` | Mostra configurações |
| `set` | Define valor |
| `reset` | Reseta para padrões |
| `export` | Exporta para arquivo |
| `import` | Importa de arquivo |

**Opções:**

| Opção | Descrição |
|-------|-----------|
| `--key` | Chave de configuração |
| `--value` | Valor para definir |
| `--file` | Arquivo para import/export |

**Exemplos:**

```bash
# Ver configurações
python -m speech_scribe.cli c show

# Definir valor
python -m speech_scribe.cli c set --key transcription.model_size --value medium

# Exportar
python -m speech_scribe.cli c export --file config_backup.json

# Resetar
python -m speech_scribe.cli c reset
```

## Códigos de Saída

| Código | Significado |
|--------|-------------|
| `0` | Sucesso |
| `1` | Erro geral |
| `130` | Cancelado pelo usuário (Ctrl+C) |

## Integração com Scripts

### Bash

```bash
#!/bin/bash
for file in audios/*.mp3; do
    python -m speech_scribe.cli t "$file" -o transcritos/ --json
done
```

### PowerShell

```powershell
Get-ChildItem *.mp3 | ForEach-Object {
    python -m speech_scribe.cli t $_.FullName -o transcritos/ --json
}
```

### Python

```python
import subprocess
import json

result = subprocess.run(
    ['python', '-m', 'speech_scribe.cli', 'status', '--all', '--json'],
    capture_output=True, text=True
)
status = json.loads(result.stdout)
print(f"GPU disponível: {status['hardware']['cuda_functional']}")
```
