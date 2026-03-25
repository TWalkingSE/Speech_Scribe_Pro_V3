import importlib.util
from typing import List

class SmartDependencyManager:
    """Gerenciador inteligente de dependências com cache"""
    
    def __init__(self):
        self.cache = {}
        self.required_deps = {
            'faster_whisper': 'faster-whisper>=1.0.0',
            'torch': 'torch>=2.0.0',
            'librosa': 'librosa>=0.10.0',
            'moviepy': 'moviepy>=1.0.3',
            'requests': 'requests>=2.28.0',
            'numpy': 'numpy>=1.24.0'
        }
        
    def check_dependency(self, name: str) -> bool:
        """Verifica se uma dependência está disponível (com cache).
        Usa find_spec para evitar efeitos colaterais de importação (ex: DLL conflicts)."""
        if name in self.cache:
            return self.cache[name]
        try:
            spec = importlib.util.find_spec(name)
            found = spec is not None
            self.cache[name] = found
            return found
        except (ModuleNotFoundError, ValueError):
            self.cache[name] = False
            return False
    
    def get_missing_dependencies(self) -> List[str]:
        """Retorna lista de dependências ausentes"""
        missing = []
        for dep in self.required_deps:
            if not self.check_dependency(dep):
                missing.append(self.required_deps[dep])
        return missing
    
    def generate_requirements(self) -> str:
        """Gera arquivo requirements.txt otimizado"""
        reqs = [
            "# Speech Scribe Pro V3 - Dependências Otimizadas",
            "# Instale com: pip install -r requirements.txt\n",
            "# Dependências principais",
            "faster-whisper>=1.0.0",
            "torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu118",
            "librosa>=0.10.0",
            "moviepy>=1.0.3",
            "requests>=2.28.0",
            "numpy>=1.24.0",
            "PyQt6>=6.5.0",
            "\n# Dependências para análise avançada",
            "deep-translator>=1.11.0",
            "python-docx>=0.8.11",
            "webvtt-py>=0.4.6",
            "matplotlib>=3.6.0",
            "wordcloud>=1.9.0",
            "\n# Dependências opcionais para IA",
            "transformers>=4.30.0",
            "sentence-transformers>=2.2.0",
            "openai>=1.0.0",
            "anthropic>=0.3.0"
        ]
        return "\n".join(reqs)
