import importlib.util
from typing import List

class SmartDependencyManager:
    """Gerenciador inteligente de dependências com cache"""
    
    def __init__(self):
        self.cache = {}
        self.required_deps = {
            'faster_whisper': 'faster-whisper',
            'torch': 'torch',
            'librosa': 'librosa',
            'requests': 'requests',
            'numpy': 'numpy',
            'PyQt6': 'PyQt6',
            'psutil': 'psutil',
            'dotenv': 'python-dotenv',
            'yaml': 'PyYAML',
            'deep_translator': 'deep-translator',
            'docx': 'python-docx',
            'pyannote.audio': 'pyannote.audio'
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
            "# Speech Scribe Pro V3 - Dependencias",
            "# Instale com: pip install -r requirements.txt",
            "#",
            "# Se voce precisar de uma build especifica do PyTorch (CUDA/ROCm),",
            "# instale-a antes deste arquivo. Exemplo:",
            "# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128",
            "",
            "# Dependencias principais",
            "torch",
            "faster-whisper",
            "librosa",
            "numpy",
            "PyQt6",
            "requests",
            "psutil",
            "python-dotenv",
            "PyYAML",
            "",
            "# Recursos integrados",
            "deep-translator",
            "python-docx",
            "pyannote.audio",
            "",
            "# Testes e smoke tests",
            "pytest",
            "pytest-qt",
            "",
            "# Streaming e microfone",
            "pyaudio"
        ]
        return "\n".join(reqs)
