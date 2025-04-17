import sys
from pathlib import Path

# Détermine le chemin racine du projet (parent du dossier 'vercel_handler')
project_root = Path(__file__).resolve().parent.parent

# Détermine le chemin vers le dossier 'src'
src_dir = project_root / "src"

# Ajoute le dossier 'src' au début de sys.path
# Cela permet à Python de trouver les modules comme 'main', 'core', 'api.v1' (qui est src.api.v1)
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Importe l'application FastAPI depuis src/main.py
try:
    # Comme 'src' est maintenant dans le path, on peut importer 'main' directement.
    # 'main' pourra ensuite importer 'core', 'api.v1' etc. car ils sont dans 'src'.
    from main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis src/main.py.")
    print(f"PYTHONPATH actuel: {sys.path}")
    print(f"Erreur originale: {e}")
    raise e

# Vercel recherchera la variable 'app' dans ce fichier (vercel_handler/index.py)
# Elle est maintenant disponible grâce à l'importation ci-dessus. 