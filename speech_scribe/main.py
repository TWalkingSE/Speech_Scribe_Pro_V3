#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎙️ Speech Scribe Pro V3 - Main Entry Point
Aplicativo de transcrição de áudio/vídeo com IA avançada
"""

import sys
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# Configurar logging antes de importar outros módulos
from speech_scribe.utils.logger import setup_logger
from speech_scribe.core.config import AppConfig

# Inicializar logger
config = AppConfig()
logger = setup_logger(config.log_dir)


def main():
    """Função principal da aplicação"""
    # Importar PyQt6 aqui para dar mensagem clara se não estiver disponível
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("❌ PyQt6 não está disponível. Instale com: pip install PyQt6")
        logger.error("PyQt6 não está disponível")
        return 1

    from speech_scribe.core.dependencies import SmartDependencyManager
    from speech_scribe.gui.main_window import SpeechScribeProV3

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Verificar dependências
    dep_manager = SmartDependencyManager()
    missing = dep_manager.get_missing_dependencies()

    if missing:
        print("⚠️  Dependências ausentes:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n💡 Execute: pip install -r requirements.txt")

        # Gerar requirements.txt se não existir
        req_path = Path("requirements.txt")
        if not req_path.exists():
            req_path.write_text(dep_manager.generate_requirements())
            print("✅ Arquivo requirements.txt criado!")

    # Iniciar aplicação
    logger.info("Speech Scribe Pro V3 iniciando...")
    window = SpeechScribeProV3()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
