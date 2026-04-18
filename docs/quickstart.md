# 🚀 Guia de Início Rápido

## Nota sobre Conectividade

O fluxo principal de transcrição e análise com Ollama pode rodar localmente, mas alguns recursos opcionais podem usar rede:

- **Whisper** pode baixar o modelo na primeira execução, se ele ainda não estiver em cache local.
- **Diarização** com `pyannote.audio` pode acessar o Hugging Face para autenticação e download inicial do pipeline/modelos.
- **Tradução** envia o texto para um serviço externo somente quando essa função é usada.
- **Verificação de atualização** só ocorre se `SPEECH_SCRIBE_VERSION_URL` estiver configurada.
- **Ollama** usa `http://localhost:11434`, ou seja, tráfego local entre a aplicação e o serviço do Ollama.

## Sua Primeira Transcrição

### Via Interface Gráfica

1. **Iniciar aplicação**:
   ```bash
   python main.py
   ```

2. **Selecionar arquivo**: 
   - Clique em "Selecionar Arquivo" ou
   - Arraste e solte o arquivo na janela

3. **Configurar** (opcional):
   - Modelo: `small` (balanceado) ou `large-v3` (máxima qualidade)
   - Idioma: `auto` detecta automaticamente

4. **Transcrever**: 
   - Clique em "Iniciar Transcrição"
   - Aguarde o processamento

5. **Exportar**:
   - Clique em "Salvar" para TXT
   - Ou "Exportar" para outros formatos

### Via Linha de Comando

```bash
# Transcrição simples
python -m speech_scribe.cli transcribe audio.mp3

# Com modelo específico e idioma
python -m speech_scribe.cli transcribe audio.mp3 -m large-v3 -l pt

# Exportar como SRT (legendas)
python -m speech_scribe.cli transcribe video.mp4 -f srt -o legendas.srt

# Múltiplos arquivos
python -m speech_scribe.cli transcribe *.mp3 -o resultados/
```

## Análise de Texto

Após a transcrição, você pode analisar o texto:

### Interface Gráfica
1. Vá para a aba "🧠 Análise IA"
2. Selecione as análises desejadas
3. Clique em "Analisar"

### Linha de Comando
```bash
# Todas as análises
python -m speech_scribe.cli analyze texto.txt --all

# Análises específicas
python -m speech_scribe.cli analyze texto.txt --sentiment --keywords --summary

# Saída em JSON
python -m speech_scribe.cli analyze texto.txt --all --json
```

## Diarização (Múltiplos Oradores)

Para identificar diferentes oradores:

1. Configure o token HuggingFace (ver instalação)
2. Na interface, marque "🎭 Reconhecimento de Oradores"
3. Ou na CLI:
   ```bash
   python -m speech_scribe.cli transcribe reuniao.mp3 --diarize
   ```

## Exemplos Práticos

### Transcrever Podcast
```bash
python -m speech_scribe.cli transcribe podcast.mp3 -m medium -l pt --diarize -f json -o podcast_transcrito.json
```

### Legendar Vídeo
```bash
python -m speech_scribe.cli transcribe video.mp4 -m small -l auto -f srt -o video.srt
```

### Processar Pasta Inteira
```bash
python -m speech_scribe.cli batch audios/*.mp3 -m small -o transcricoes_lote.txt
```

No fluxo atual da CLI, o comando `batch` gera um arquivo TXT consolidado com todas as transcrições concluídas.

### Embutir Legenda no Vídeo
```bash
python -m speech_scribe.cli transcribe video.mp4 -f srt --embed-subtitle
```

### Gerar Relatório de Reunião
```bash
# Transcrever
python -m speech_scribe.cli transcribe reuniao.mp3 --diarize -o reuniao.txt

# Analisar
python -m speech_scribe.cli analyze reuniao.txt --summary --keywords --topics -o relatorio.json
```

## Dicas de Performance

| Cenário | Modelo Recomendado | Dispositivo |
|---------|-------------------|-------------|
| Transcrição rápida | `tiny` ou `base` | CPU |
| Uso geral | `small` | GPU/CPU |
| Alta qualidade | `medium` | GPU |
| Máxima precisão | `large-v3` | GPU (8GB+) |

## Próximos Passos

- [Referência da CLI](cli.md)
- [Criar Plugins](plugins.md)
- [Detecção de GPU](gpu_detection.md)
- [Guia de Instalação](installation.md)
