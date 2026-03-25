# 🔌 Guia de Plugins

## Visão Geral

O sistema de plugins permite estender o Speech Scribe Pro V3 com:

- **Engines de transcrição** alternativos
- **Análises de texto** customizadas
- **Formatos de exportação** novos
- **Pré/pós-processamento** de áudio e texto
- **Integrações** com serviços externos

## Criando seu Primeiro Plugin

### Estrutura Básica

```python
from speech_scribe.plugins.base import Plugin, PluginInfo, PluginType

class MeuPlugin(Plugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Meu Plugin",
            version="1.0.0",
            description="Descrição do plugin",
            author="Seu Nome",
            plugin_type=PluginType.ANALYSIS
        )
    
    def activate(self):
        # Registrar hooks quando ativado
        self.register_hook('post_transcription', self.meu_callback)
    
    def meu_callback(self, result):
        # Processar resultado
        return result
```

### Tipos de Plugin

| Tipo | Uso | Classe Base |
|------|-----|-------------|
| `TRANSCRIPTION` | Engines de transcrição | `TranscriptionPlugin` |
| `ANALYSIS` | Análises de texto | `AnalysisPlugin` |
| `EXPORT` | Formatos de exportação | `ExportPlugin` |
| `PRE_PROCESSOR` | Pré-processamento | `PreProcessorPlugin` |
| `POST_PROCESSOR` | Pós-processamento | `PostProcessorPlugin` |
| `INTEGRATION` | Integrações externas | `Plugin` |

## Plugin de Análise

```python
from speech_scribe.plugins.base import AnalysisPlugin, PluginInfo, PluginType

class SentimentAnalyzerPlugin(AnalysisPlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Advanced Sentiment",
            version="1.0.0",
            description="Análise de sentimento avançada",
            author="Dev",
            plugin_type=PluginType.ANALYSIS,
            dependencies=["textblob"]
        )
    
    def activate(self):
        self.register_hook('post_transcription', self.analyze_sentiment)
    
    def analyze(self, text: str, **options) -> dict:
        from textblob import TextBlob
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def analyze_sentiment(self, result: dict) -> dict:
        result['advanced_sentiment'] = self.analyze(result['text'])
        return result
```

## Plugin de Exportação

```python
from pathlib import Path
from speech_scribe.plugins.base import ExportPlugin, PluginInfo, PluginType

class MarkdownExporter(ExportPlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Markdown Exporter",
            version="1.0.0",
            description="Exporta para Markdown",
            author="Dev",
            plugin_type=PluginType.EXPORT
        )
    
    def activate(self):
        pass  # Exportadores não precisam de hooks
    
    def export(self, data: dict, output_path: Path, **options) -> bool:
        md_content = f"# Transcrição\n\n{data['text']}"
        output_path.with_suffix('.md').write_text(md_content)
        return True
    
    def get_format_name(self) -> str:
        return "Markdown"
    
    def get_file_extension(self) -> str:
        return ".md"
```

## Hooks Disponíveis

| Hook | Quando | Parâmetros |
|------|--------|------------|
| `pre_transcription` | Antes de transcrever | `file_path` |
| `post_transcription` | Após transcrição | `result` |
| `pre_analysis` | Antes de analisar | `text` |
| `post_analysis` | Após análise | `result` |
| `pre_export` | Antes de exportar | `data, format` |
| `post_export` | Após exportar | `result` |
| `on_file_loaded` | Arquivo carregado | `file_info` |
| `on_error` | Quando ocorre erro | `error` |
| `on_progress` | Atualização de progresso | `progress` |

## Instalando Plugins

### Diretório de Plugins

Coloque seus plugins em:
- Windows: `%USERPROFILE%\.speech_scribe_v3\plugins\`
- Linux/macOS: `~/.speech_scribe_v3/plugins/`

### Estrutura de Arquivos

```
plugins/
├── meu_plugin.py           # Plugin único
└── meu_pacote/             # Plugin como pacote
    ├── __init__.py
    └── core.py
```

## Gerenciando Plugins

### Via Código

```python
from speech_scribe.plugins import get_plugin_manager

manager = get_plugin_manager()

# Descobrir e carregar plugins
manager.load_all_plugins()

# Listar plugins
for info in manager.get_plugins_info():
    print(f"{info['name']} v{info['version']}")

# Ativar plugin
manager.enable_plugin("Meu Plugin")

# Configurar plugin
manager.configure_plugin("Meu Plugin", {'opcao': 'valor'})

# Desativar
manager.disable_plugin("Meu Plugin")
```

## Boas Práticas

1. **Versionamento**: Use [SemVer](https://semver.org/)
2. **Dependências**: Liste todas em `dependencies`
3. **Documentação**: Docstrings em todas as classes/métodos
4. **Tratamento de Erros**: Nunca deixe exceções escaparem
5. **Performance**: Evite operações bloqueantes longas
6. **Configuração**: Use `get_default_config()` para defaults

## Exemplo Completo

Veja exemplos em:
- `speech_scribe/plugins/examples/word_counter.py`
