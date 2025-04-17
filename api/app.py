# api/app.py - Point d'entrée pour Vercel

# Importe l'application FastAPI depuis le package src
try:
    from src.main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis src.main.")
    import sys
    print(f"PYTHONPATH actuel: {sys.path}")
    print(f"Erreur originale: {e}")
    raise e

# La variable 'app' est maintenant disponible pour Vercel 