# main.py (à la racine) - Peut être utilisé pour exécution locale ou outils

# Importe l'application principale pour la rendre accessible si ce fichier est exécuté
try:
    from src.main import app
except ImportError:
    print("Assurez-vous que le dossier src est dans le PYTHONPATH pour exécuter ce fichier.")
    # Gérer l'erreur ou simplement passer si ce fichier n'est pas destiné à être exécuté directement
    pass 

if __name__ == "__main__":
    print("Pour lancer l'application localement, exécutez : uvicorn src.main:app --reload")
    # Ou décommentez pour lancer directement (nécessite PYTHONPATH correct)
    # import uvicorn
    # uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True) 