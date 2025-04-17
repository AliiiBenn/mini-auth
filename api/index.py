import sys
from pathlib import Path

# Détermine le chemin racine du projet (parent du dossier 'api')
project_root = Path(__file__).resolve().parent.parent

# Détermine le chemin vers le dossier 'src'
src_dir = project_root / "src"

# Ajoute le dossier racine du projet au PYTHONPATH
# Cela permet d'importer 'src' comme un package
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importe l'application FastAPI depuis src/main.py
try:
    # Importe explicitement depuis le package src
    from src.main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis src.main.")
    print(f"PYTHONPATH actuel: {sys.path}")
    print(f"Erreur originale: {e}")
    # Renvoyer l'erreur pour que Vercel l'affiche
    raise e

# Vercel recherchera la variable 'app' dans ce fichier (api/index.py)
# Elle est maintenant disponible grâce à l'importation ci-dessus. 