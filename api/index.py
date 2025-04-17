# api/index.py - Point d'entrée pour Vercel

# Importe directement l'application depuis le package src
# Vercel devrait gérer le PYTHONPATH pour que 'src' soit trouvable
try:
    from src.main import app
except ImportError as e:
    print(f"ERREUR: Impossible d'importer l'application depuis src.main.")
    # Imprime le sys.path pour le débogage dans les logs Vercel
    import sys
    print(f"PYTHONPATH actuel: {sys.path}") 
    print(f"Erreur originale: {e}")
    raise e

# La variable 'app' est maintenant disponible pour Vercel 