import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from main import app 