import sys
from pathlib import Path

# Détermine le chemin racine du projet (parent du dossier 'api')
project_root = Path(__file__).resolve().parent.parent

# Détermine le chemin vers le dossier 'src'
src_dir = project_root / "src"

# Ajoute le dossier 'src' au début de sys.path si ce n'est pas déjà fait
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Importe l'application FastAPI depuis le module main (qui est maintenant directement accessible)
try:
    from main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis main.py (dans src).")
    print(f"PYTHONPATH actuel: {sys.path}")
    print(f"Erreur originale: {e}")
    # Renvoyer l'erreur pour que Vercel l'affiche
    raise e

# Vercel recherchera la variable 'app' dans ce fichier (api/index.py)
# Elle est maintenant disponible grâce à l'importation ci-dessus. 