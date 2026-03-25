#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎙️ Speech Scribe Pro V3 - Entry Point
Ponto de entrada principal da aplicação
"""

import sys

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

if __name__ == "__main__":
    from speech_scribe.main import main
    sys.exit(main())
