import sys
from pathlib import Path

# Détermine le chemin racine du projet (parent du dossier 'api')
project_root = Path(__file__).resolve().parent.parent

# Détermine le chemin vers le dossier 'src'
src_dir = project_root / "src"

# Ajoute le dossier racine ET le dossier 'src' au début de sys.path
# Mettre la racine en premier permet de résoudre 'api.v1'
# Mettre src ensuite permet de résoudre les imports internes comme 'core.config'
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_dir) not in sys.path:
    sys.path.insert(1, str(src_dir)) # Insérer en 2ème position

# Importe l'application FastAPI depuis src/main.py
# Python devrait maintenant pouvoir trouver 'main' via src_dir
# et 'main' devrait pouvoir trouver 'api.v1' via project_root
try:
    # L'importation doit être relative au PYTHONPATH
    # Comme 'src' est dans le path, on importe 'main'
    from main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis src/main.py.")
    print(f"PYTHONPATH actuel: {sys.path}")
    print(f"Erreur originale: {e}")
    # Renvoyer l'erreur pour que Vercel l'affiche
    raise e

# Vercel recherchera la variable 'app' dans ce fichier (api/index.py)
# Elle est maintenant disponible grâce à l'importation ci-dessus. 