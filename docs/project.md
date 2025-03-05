# Mini-Auth API

Une alternative simplifiée à Supabase axée sur l'authentification et la gestion des utilisateurs.

## Objectif

Créer une API backend qui permet aux développeurs de gérer l'authentification et les utilisateurs de leurs applications, avec des limites strictes (100 requêtes/minute, 100 utilisateurs maximum).

## Architecture

### Structure des Dossiers

```
/backend
│── /app
│   │── /api                 # Routeurs FastAPI
│   │   │── /v1
│   │   │   │── auth.py      # Authentification (OAuth2, JWT)
│   │   │   │── projects.py  # Gestion des projets
│   │   │   │── users.py     # Gestion des utilisateurs
│   │── /core                # Configuration principale
│   │   │── config.py        # Paramètres de l'application
│   │   │── database.py      # Connexion à PostgreSQL
│   │   │── security.py      # Gestion des tokens
│   │── /models              # Modèles SQLAlchemy
│   │── /schemas             # Schémas Pydantic
│   │── /services            # Logique métier
│   │── /middlewares         # Middlewares (rate limiting)
│   │── main.py              # Point d'entrée
```

### Fonctionnalités Principales

1. **Authentification des Administrateurs**
   - Login/Register avec email/mot de passe
   - JWT pour l'authentification
   - Gestion des sessions

2. **Gestion des Projets**
   - Création de projets par admin
   - Génération de clés API par projet
   - Limites de ressources par projet

3. **Gestion des Utilisateurs**
   - Création d'utilisateurs par projet
   - Authentification des utilisateurs
   - Gestion des sessions utilisateurs

### Limites et Quotas

- 100 requêtes par minute par projet
- 100 utilisateurs maximum par projet
- Stockage limité par projet

### Technologies Utilisées

- FastAPI (Python)
- PostgreSQL (Base de données)
- Redis (Rate limiting)
- JWT (Authentification)
- SQLAlchemy (ORM)

## Workflow

1. L'administrateur crée un compte et se connecte
2. Il crée un projet et reçoit une clé API
3. Il peut créer des utilisateurs dans son projet
4. Les utilisateurs peuvent s'authentifier via l'API
5. Les requêtes sont limitées à 100/minute
6. Le nombre d'utilisateurs est limité à 100

## Sécurité

- Authentification JWT pour les admins
- Clés API pour les projets
- Rate limiting avec Redis
- Protection contre les attaques courantes
- Validation des données avec Pydantic

## API Endpoints

### Authentification
- POST /auth/register
- POST /auth/login
- POST /auth/logout

### Projets
- POST /projects
- GET /projects
- GET /projects/{id}
- DELETE /projects/{id}

### Utilisateurs
- POST /projects/{id}/users
- GET /projects/{id}/users
- DELETE /projects/{id}/users/{user_id}
