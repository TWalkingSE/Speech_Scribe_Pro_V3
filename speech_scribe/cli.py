#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🖥️ Interface de Linha de Comando - Speech Scribe Pro V3
CLI completa para transcrição e análise sem interface gráfica
"""

import sys
import argparse
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Verificar se estamos em modo CLI
CLI_MODE = True


def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos"""
    parser = argparse.ArgumentParser(
        prog='speech-scribe',
        description='🎙️ Speech Scribe Pro V3 - Transcrição de áudio/vídeo com IA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Transcrever um arquivo
  speech-scribe transcribe audio.mp3
  
  # Transcrever com modelo específico
  speech-scribe transcribe audio.mp3 -m large-v3 -l pt
  
  # Transcrever múltiplos arquivos
  speech-scribe transcribe *.mp3 -o resultados/
  
  # Analisar transcrição existente
  speech-scribe analyze transcricao.txt --sentiment --keywords
  
  # Verificar status do sistema
  speech-scribe status
"""
    )
    
    parser.add_argument('--version', '-V', action='version', version='Speech Scribe Pro V3 3.0.0')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')
    parser.add_argument('--quiet', '-q', action='store_true', help='Modo silencioso')
    parser.add_argument('--json', action='store_true', help='Saída em formato JSON')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # === Comando: transcribe ===
    transcribe_parser = subparsers.add_parser('transcribe', aliases=['t'],
                                               help='Transcrever arquivos de áudio/vídeo')
    transcribe_parser.add_argument('files', nargs='+', help='Arquivos para transcrever')
    transcribe_parser.add_argument('-m', '--model', default='small',
                                    choices=['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'],
                                    help='Modelo Whisper (padrão: small)')
    transcribe_parser.add_argument('-l', '--language', default='auto',
                                    help='Idioma (auto, pt, en, es, etc.)')
    transcribe_parser.add_argument('-o', '--output', help='Diretório ou arquivo de saída')
    transcribe_parser.add_argument('-f', '--format', default='txt',
                                    choices=['txt', 'json', 'srt', 'vtt'],
                                    help='Formato de saída (padrão: txt)')
    transcribe_parser.add_argument('--diarize', action='store_true',
                                    help='Habilitar diarização (separação de oradores)')
    transcribe_parser.add_argument('--timestamps', action='store_true',
                                    help='Incluir timestamps')
    transcribe_parser.add_argument('--device', choices=['auto', 'cpu', 'cuda'],
                                    default='auto', help='Dispositivo para processamento')
    transcribe_parser.add_argument('--embed-subtitle', action='store_true',
                                    help='Embutir legenda no vídeo (requer FFmpeg)')
    transcribe_parser.add_argument('--burn-in', action='store_true', default=True,
                                    help='Queimar legenda no vídeo (hardcoded, padrão: True)')
    transcribe_parser.add_argument('--keep-srt', action='store_true', default=True,
                                    help='Manter arquivo SRT após embutir (padrão: True)')
    
    # === Comando: analyze ===
    analyze_parser = subparsers.add_parser('analyze', aliases=['a'],
                                            help='Analisar texto transcrito')
    analyze_parser.add_argument('file', help='Arquivo de texto para analisar')
    analyze_parser.add_argument('--sentiment', action='store_true', help='Análise de sentimento')
    analyze_parser.add_argument('--keywords', action='store_true', help='Extração de palavras-chave')
    analyze_parser.add_argument('--entities', action='store_true', help='Extração de entidades')
    analyze_parser.add_argument('--summary', action='store_true', help='Gerar resumo')
    analyze_parser.add_argument('--topics', action='store_true', help='Identificar tópicos')
    analyze_parser.add_argument('--all', action='store_true', help='Todas as análises')
    analyze_parser.add_argument('--ollama', action='store_true', help='Usar Ollama para análise')
    analyze_parser.add_argument('--ollama-model', default='gpt-oss:20b', help='Modelo Ollama')
    analyze_parser.add_argument('-o', '--output', help='Arquivo de saída')
    
    # === Comando: batch ===
    batch_parser = subparsers.add_parser('batch', aliases=['b'],
                                          help='Processar múltiplos arquivos em batch')
    batch_parser.add_argument('files', nargs='+', help='Arquivos para processar')
    batch_parser.add_argument('-m', '--model', default='small', help='Modelo Whisper')
    batch_parser.add_argument('-l', '--language', default='auto', help='Idioma')
    batch_parser.add_argument('-o', '--output', help='Diretório de saída')
    batch_parser.add_argument('-w', '--workers', type=int, default=2,
                               help='Número de workers paralelos')
    batch_parser.add_argument('--analyze', action='store_true',
                               help='Analisar após transcrever')
    batch_parser.add_argument('--embed-subtitle', action='store_true',
                               help='Embutir legenda nos vídeos transcritos (requer FFmpeg)')
    
    # === Comando: status ===
    status_parser = subparsers.add_parser('status', aliases=['s'],
                                           help='Verificar status do sistema')
    status_parser.add_argument('--hardware', action='store_true', help='Mostrar info de hardware')
    status_parser.add_argument('--dependencies', action='store_true', help='Verificar dependências')
    status_parser.add_argument('--ollama', action='store_true', help='Verificar status do Ollama')
    status_parser.add_argument('--all', action='store_true', help='Mostrar tudo')
    
    # === Comando: config ===
    config_parser = subparsers.add_parser('config', aliases=['c'],
                                           help='Gerenciar configurações')
    config_parser.add_argument('action', choices=['show', 'set', 'reset', 'export', 'import'],
                                help='Ação a executar')
    config_parser.add_argument('--key', help='Chave de configuração')
    config_parser.add_argument('--value', help='Valor para definir')
    config_parser.add_argument('--file', help='Arquivo para import/export')
    
    return parser


def print_colored(text: str, color: str = 'white', bold: bool = False):
    """Imprime texto colorido"""
    colors = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
    }
    reset = '\033[0m'
    bold_code = '\033[1m' if bold else ''
    
    color_code = colors.get(color, '')
    print(f"{bold_code}{color_code}{text}{reset}")


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print()
    print_colored(f"{'='*60}", 'cyan')
    print_colored(f"  {text}", 'cyan', bold=True)
    print_colored(f"{'='*60}", 'cyan')
    print()


def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print_colored(f"✅ {text}", 'green')


def print_error(text: str):
    """Imprime mensagem de erro"""
    print_colored(f"❌ {text}", 'red')


def print_warning(text: str):
    """Imprime aviso"""
    print_colored(f"⚠️  {text}", 'yellow')


def print_info(text: str):
    """Imprime informação"""
    print_colored(f"ℹ️  {text}", 'blue')


def cmd_transcribe(args, output_json: bool = False):
    """Comando de transcrição"""
    from speech_scribe.core.config import AppConfig
    from speech_scribe.core.hardware import ModernHardwareDetector
    from speech_scribe.core.transcription import IntelligentTranscriptionEngine
    
    # Importar embutidor de legendas se necessário
    embed_subtitle = getattr(args, 'embed_subtitle', False)
    subtitle_embedder = None
    if embed_subtitle:
        try:
            from speech_scribe.core.subtitle_embedder import (
                is_video_file, embed_subtitle_from_transcription, check_ffmpeg
            )
            if not check_ffmpeg():
                print_error("FFmpeg não encontrado. Instale o FFmpeg para embutir legendas.")
                embed_subtitle = False
            else:
                subtitle_embedder = embed_subtitle_from_transcription
                if not output_json:
                    print_info("Embutir legenda: ativado")
        except ImportError:
            print_error("Módulo de embutir legendas não disponível.")
            embed_subtitle = False
    
    if not output_json:
        print_header("🎙️ Transcrição de Áudio/Vídeo")
    
    # Inicializar componentes
    config = AppConfig()
    hardware = ModernHardwareDetector()
    engine = IntelligentTranscriptionEngine(config, hardware)
    
    if not output_json:
        print_info(f"Modelo: {args.model} | Idioma: {args.language} | Device: {hardware.get_device_info()}")
        print()
    
    results = []
    
    for file_path in args.files:
        path = Path(file_path)
        
        if not path.exists():
            if output_json:
                results.append({'file': str(path), 'error': 'Arquivo não encontrado'})
            else:
                print_error(f"Arquivo não encontrado: {path}")
            continue
        
        if not output_json:
            print_info(f"Processando: {path.name}")
        
        try:
            # Transcrever
            result = asyncio.run(engine.transcribe_async(
                str(path), args.model, args.language
            ))
            
            if result:
                # Salvar resultado
                if args.output:
                    output_path = Path(args.output)
                    if output_path.is_dir():
                        output_file = output_path / f"{path.stem}.{args.format}"
                    else:
                        output_file = output_path
                else:
                    output_file = path.with_suffix(f'.{args.format}')
                
                # Formatar saída
                if args.format == 'json':
                    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
                elif args.format == 'srt':
                    srt_content = _format_srt(result.get('segments', []))
                    output_file.write_text(srt_content, encoding='utf-8')
                elif args.format == 'vtt':
                    vtt_content = _format_vtt(result.get('segments', []))
                    output_file.write_text(vtt_content, encoding='utf-8')
                else:  # txt
                    output_file.write_text(result['text'], encoding='utf-8')
                
                if output_json:
                    results.append({
                        'file': str(path),
                        'output': str(output_file),
                        'duration': result.get('processing_time', 0),
                        'text_length': len(result.get('text', ''))
                    })
                else:
                    print_success(f"Salvo: {output_file} ({result.get('processing_time', 0):.1f}s)")
                
                # Embutir legenda no vídeo se solicitado
                if embed_subtitle and subtitle_embedder and is_video_file(str(path)):
                    if not output_json:
                        print_info(f"Embutindo legenda no vídeo: {path.name}")
                    
                    embed_result = subtitle_embedder(
                        str(path),
                        result,
                        burn_in=getattr(args, 'burn_in', True),
                        keep_srt=getattr(args, 'keep_srt', True)
                    )
                    
                    if embed_result.success:
                        if not output_json:
                            print_success(f"Legenda embutida: {embed_result.output_path}")
                        else:
                            results[-1]['subtitle_embedded'] = embed_result.output_path
                    else:
                        if not output_json:
                            print_error(f"Erro ao embutir legenda: {embed_result.error}")
                        else:
                            results[-1]['subtitle_error'] = embed_result.error
            else:
                raise Exception("Resultado vazio")
                
        except Exception as e:
            if output_json:
                results.append({'file': str(path), 'error': str(e)})
            else:
                print_error(f"Erro: {e}")
    
    if output_json:
        print(json.dumps({'transcriptions': results}, indent=2))
    else:
        print()
        print_success(f"Processamento concluído: {len(results)} arquivos")


def cmd_analyze(args, output_json: bool = False):
    """Comando de análise"""
    from speech_scribe.core.analysis import SmartAnalyzer
    
    if not output_json:
        print_header("🧠 Análise de Texto com IA")
    
    # Verificar arquivo
    path = Path(args.file)
    if not path.exists():
        if output_json:
            print(json.dumps({'error': 'Arquivo não encontrado'}))
        else:
            print_error(f"Arquivo não encontrado: {path}")
        return
    
    # Ler texto
    text = path.read_text(encoding='utf-8')
    
    if not output_json:
        print_info(f"Analisando: {path.name} ({len(text)} caracteres)")
    
    # Determinar análises
    analyses = []
    if args.all:
        analyses = ['sentiment', 'keywords', 'entities', 'summary', 'topics']
    else:
        if args.sentiment: analyses.append('sentiment')
        if args.keywords: analyses.append('keywords')
        if args.entities: analyses.append('entities')
        if args.summary: analyses.append('summary')
        if args.topics: analyses.append('topics')
    
    if not analyses:
        analyses = ['sentiment', 'keywords', 'summary']  # Padrão
    
    # Executar análise
    analyzer = SmartAnalyzer()
    results = analyzer.analyze_transcription(text, analyses)
    
    # Saída
    if output_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print()
        _print_analysis_results(results)
        
        # Salvar se solicitado
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
            print_success(f"Resultados salvos: {output_path}")


def cmd_status(args, output_json: bool = False):
    """Comando de status"""
    from speech_scribe.core.hardware import ModernHardwareDetector
    from speech_scribe.core.dependencies import SmartDependencyManager
    
    status = {}
    
    if args.all or args.hardware or not any([args.hardware, args.dependencies, args.ollama]):
        hardware = ModernHardwareDetector()
        status['hardware'] = {
            'cpu_cores': hardware.info['cpu_count'],
            'memory_gb': hardware.info['memory_gb'],
            'cuda_available': hardware.info['cuda_available'],
            'cuda_functional': hardware.info['cuda_functional'],
            'device': hardware.optimizations['device'],
            'recommended_model': hardware.optimizations['recommended_model']
        }
        
        if hardware.info['cuda_functional']:
            gpu_info = hardware.get_detailed_gpu_info()
            status['hardware']['gpu'] = gpu_info['primary_gpu']
    
    if args.all or args.dependencies:
        dep_manager = SmartDependencyManager()
        missing = dep_manager.get_missing_dependencies()
        status['dependencies'] = {
            'all_installed': len(missing) == 0,
            'missing': missing
        }
    
    if args.all or args.ollama:
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.ok:
                models = response.json().get('models', [])
                status['ollama'] = {
                    'available': True,
                    'models': [m['name'] for m in models]
                }
            else:
                status['ollama'] = {'available': False}
        except Exception:
            status['ollama'] = {'available': False}
    
    if output_json:
        print(json.dumps(status, indent=2))
    else:
        print_header("📊 Status do Sistema")
        
        if 'hardware' in status:
            hw = status['hardware']
            print_colored("🖥️  Hardware:", 'cyan', bold=True)
            print(f"   CPU: {hw['cpu_cores']} cores")
            print(f"   RAM: {hw['memory_gb']:.1f} GB")
            
            if hw['cuda_functional']:
                print_colored(f"   GPU: ✅ {hw.get('gpu', {}).get('name', 'Disponível')}", 'green')
            elif hw['cuda_available']:
                print_colored("   GPU: ⚠️  CUDA detectado mas não funcional", 'yellow')
            else:
                print_colored("   GPU: ❌ Não disponível", 'red')
            
            print(f"   Device: {hw['device']}")
            print(f"   Modelo recomendado: {hw['recommended_model']}")
            print()
        
        if 'dependencies' in status:
            deps = status['dependencies']
            if deps['all_installed']:
                print_colored("📦 Dependências: ✅ Todas instaladas", 'green')
            else:
                print_colored(f"📦 Dependências: ❌ {len(deps['missing'])} ausentes", 'red')
                for dep in deps['missing']:
                    print(f"   - {dep}")
            print()
        
        if 'ollama' in status:
            ollama = status['ollama']
            if ollama['available']:
                print_colored(f"🤖 Ollama: ✅ Disponível ({len(ollama['models'])} modelos)", 'green')
            else:
                print_colored("🤖 Ollama: ❌ Não disponível", 'red')


def cmd_config(args, output_json: bool = False):
    """Comando de configuração"""
    from speech_scribe.core.config_manager import ConfigManager, get_config_manager
    
    manager = get_config_manager()
    
    if args.action == 'show':
        config_dict = manager.config.to_dict()
        if output_json:
            print(json.dumps(config_dict, indent=2))
        else:
            print_header("⚙️  Configurações Atuais")
            print(json.dumps(config_dict, indent=2))
    
    elif args.action == 'set':
        if not args.key or not args.value:
            print_error("Use: config set --key <chave> --value <valor>")
            return
        
        try:
            manager.set(args.key, args.value)
            manager.save()
            print_success(f"Configuração atualizada: {args.key} = {args.value}")
        except Exception as e:
            print_error(f"Erro: {e}")
    
    elif args.action == 'reset':
        manager.reset_to_defaults()
        print_success("Configurações resetadas para padrões")
    
    elif args.action == 'export':
        if not args.file:
            print_error("Use: config export --file <arquivo>")
            return
        manager.export_config(Path(args.file))
        print_success(f"Configurações exportadas: {args.file}")
    
    elif args.action == 'import':
        if not args.file:
            print_error("Use: config import --file <arquivo>")
            return
        manager.import_config(Path(args.file))
        print_success(f"Configurações importadas: {args.file}")


def _format_srt(segments: List[dict]) -> str:
    """Formata segmentos em formato SRT"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp_srt(seg.get('start', 0))
        end = _format_timestamp_srt(seg.get('end', 0))
        text = seg.get('text', '').strip()
        
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)


def _format_vtt(segments: List[dict]) -> str:
    """Formata segmentos em formato VTT"""
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = _format_timestamp_vtt(seg.get('start', 0))
        end = _format_timestamp_vtt(seg.get('end', 0))
        text = seg.get('text', '').strip()
        
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines)


def _format_timestamp_srt(seconds: float) -> str:
    """Formata timestamp para SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_timestamp_vtt(seconds: float) -> str:
    """Formata timestamp para VTT (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def _print_analysis_results(results: dict):
    """Imprime resultados de análise formatados"""
    if 'sentiment' in results:
        print_colored("😊 Sentimento:", 'cyan', bold=True)
        s = results['sentiment']
        print(f"   Tipo: {s.get('sentiment', 'N/A')}")
        print(f"   Score: {s.get('score', 0):.2f}")
        print()
    
    if 'keywords' in results:
        print_colored("🔑 Palavras-chave:", 'cyan', bold=True)
        kw = results['keywords']
        for word, count in kw.get('top_keywords', [])[:10]:
            print(f"   • {word}: {count}")
        print()
    
    if 'summary' in results:
        print_colored("📄 Resumo:", 'cyan', bold=True)
        print(f"   {results['summary'].get('summary', 'N/A')}")
        print()
    
    if 'topics' in results:
        print_colored("🎯 Tópicos:", 'cyan', bold=True)
        t = results['topics']
        print(f"   Principal: {t.get('main_topic', 'N/A')}")
        print()


def cmd_batch(args, output_json: bool = False):
    """Comando de processamento em lote - salva tudo em um único arquivo"""
    from speech_scribe.core.config import AppConfig
    from speech_scribe.core.hardware import ModernHardwareDetector
    from speech_scribe.core.transcription import IntelligentTranscriptionEngine
    
    if not output_json:
        print_header("📦 Processamento em Lote")
    
    # Importar embutidor de legendas se necessário
    embed_subtitle = getattr(args, 'embed_subtitle', False)
    subtitle_embedder = None
    if embed_subtitle:
        try:
            from speech_scribe.core.subtitle_embedder import (
                is_video_file as _is_video, embed_subtitle_from_transcription, check_ffmpeg
            )
            if not check_ffmpeg():
                print_error("FFmpeg não encontrado. Embutir legendas desativado.")
                embed_subtitle = False
            else:
                subtitle_embedder = embed_subtitle_from_transcription
        except ImportError:
            embed_subtitle = False
    
    config = AppConfig()
    hardware = ModernHardwareDetector()
    engine = IntelligentTranscriptionEngine(config, hardware)
    
    if not output_json:
        print_info(f"Modelo: {args.model} | Idioma: {args.language} | Device: {hardware.get_device_info()}")
        print_info(f"Arquivos para processar: {len(args.files)}")
        print()
    
    # Carregar modelo uma vez para todo o lote
    import time
    if not output_json:
        print_info("Carregando modelo...")
    model = engine.load_model(args.model)
    if not model:
        print_error(f"Falha ao carregar modelo: {args.model}")
        return

    transcribe_kwargs = {
        'language': None if args.language == "auto" else args.language,
        'vad_filter': True,
        'word_timestamps': True,
        'beam_size': hardware.optimizations['beam_size'],
        'best_of': hardware.optimizations['best_of'],
        'condition_on_previous_text': False,
    }

    # Coletar transcrições bem-sucedidas e erros
    transcriptions = []  # [(path, text)]
    errors = []  # [(path, error)]
    results_json = []
    
    for file_path in args.files:
        path = Path(file_path)
        
        if not path.exists():
            errors.append((str(path), "Arquivo não encontrado"))
            if not output_json:
                print_error(f"Arquivo não encontrado: {path}")
            continue
        
        if not output_json:
            print_info(f"Processando: {path.name}")
        
        try:
            start_time = time.time()
            segments_gen, info = model.transcribe(str(path), **transcribe_kwargs)
            segments_list = list(segments_gen)
            processing_time = time.time() - start_time
            full_text = ' '.join([seg.text for seg in segments_list])

            result = {
                'text': full_text,
                'segments': [
                    {'start': seg.start, 'end': seg.end, 'text': seg.text}
                    for seg in segments_list
                ],
                'language': info.language,
                'duration': info.duration,
                'processing_time': processing_time,
                'model_used': args.model,
                'device_used': hardware.optimizations['device'],
            }
            
            if result and result.get('text'):
                text = result['text']
                transcriptions.append((str(path), text))
                
                if not output_json:
                    print_success(f"Concluído: {path.name} ({result.get('processing_time', 0):.1f}s)")
                
                # Embutir legenda se solicitado e for vídeo
                if embed_subtitle and subtitle_embedder and _is_video(str(path)):
                    if not output_json:
                        print_info(f"Embutindo legenda: {path.name}")
                    embed_result = subtitle_embedder(str(path), result, burn_in=True, keep_srt=True)
                    if embed_result.success:
                        if not output_json:
                            print_success(f"Legenda embutida: {embed_result.output_path}")
                    else:
                        if not output_json:
                            print_error(f"Erro legenda: {embed_result.error}")
                
                results_json.append({
                    'file': str(path),
                    'text_length': len(text),
                    'duration': result.get('processing_time', 0),
                    'status': 'completed'
                })
            else:
                raise Exception("Resultado vazio")
                
        except Exception as e:
            errors.append((str(path), str(e)))
            results_json.append({
                'file': str(path),
                'error': str(e),
                'status': 'failed'
            })
            if not output_json:
                print_error(f"Erro em {path.name}: {e}")
            # Continua processando os próximos arquivos
            continue
    
    # Salvar transcrições em um único arquivo consolidado
    if transcriptions:
        if args.output:
            output_path = Path(args.output)
            if output_path.is_dir():
                output_file = output_path / f"transcricoes_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                output_file = output_path
        else:
            # Salvar na pasta do primeiro arquivo
            first_dir = Path(transcriptions[0][0]).parent
            output_file = first_dir / f"transcricoes_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Montar conteúdo consolidado
        separator = "=" * 60
        parts = []
        for file_path, text in transcriptions:
            parts.append(f"Caminho: {file_path}")
            parts.append("")
            parts.append(text.strip())
            parts.append("")
            parts.append(separator)
            parts.append("")
        
        content = "\n".join(parts)
        output_file.write_text(content, encoding='utf-8')
        
        if not output_json:
            print()
            print_success(f"Transcrições salvas em arquivo único: {output_file}")
    
    # Resumo final
    if output_json:
        print(json.dumps({
            'batch_results': results_json,
            'summary': {
                'total': len(args.files),
                'completed': len(transcriptions),
                'errors': len(errors),
                'output_file': str(output_file) if transcriptions else None
            }
        }, indent=2, ensure_ascii=False))
    else:
        print()
        print_colored(f"{'='*40}", 'cyan')
        print_success(f"Total: {len(args.files)} | Sucesso: {len(transcriptions)} | Erros: {len(errors)}")
        if errors:
            print_warning("Arquivos com erro:")
            for path, error in errors:
                print_colored(f"   • {Path(path).name}: {error}", 'red')


def main():
    """Função principal da CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    output_json = args.json
    
    try:
        if args.command in ['transcribe', 't']:
            cmd_transcribe(args, output_json)
        elif args.command in ['analyze', 'a']:
            cmd_analyze(args, output_json)
        elif args.command in ['status', 's']:
            cmd_status(args, output_json)
        elif args.command in ['config', 'c']:
            cmd_config(args, output_json)
        elif args.command in ['batch', 'b']:
            cmd_batch(args, output_json)
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print_warning("\nOperação cancelada pelo usuário")
        return 130
    except Exception as e:
        if output_json:
            print(json.dumps({'error': str(e)}))
        else:
            print_error(f"Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
