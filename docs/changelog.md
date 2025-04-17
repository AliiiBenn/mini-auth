# Changelog

## [0.1.0] - Initial Release

### Base de données
- Mise en place de SQLAlchemy avec support asynchrone (AsyncSession)
- Configuration de la base de données SQLite avec aiosqlite
- Implémentation du système de migration (Alembic)
- Configuration de `expire_on_commit=False` pour une meilleure gestion des sessions asynchrones

### Modèles
#### Project
- Implémentation du modèle `Project` avec les champs :
  - `id`: UUID v4 unique
  - `name`: Nom du projet (max 50 caractères)
  - `description`: Description optionnelle (max 200 caractères)
  - `created_at`: Date de création automatique
  - `updated_at`: Date de mise à jour automatique
  - `is_active`: État d'activation du projet

#### ProjectApiKey
- Implémentation du modèle `ProjectApiKey` avec les champs :
  - `id`: UUID v4 unique
  - `project_id`: Clé étrangère vers Project
  - `key`: Clé API unique (64 caractères)
  - `name`: Nom de la clé (max 50 caractères)
  - `created_at`: Date de création automatique
  - `last_used_at`: Dernière utilisation (nullable)
  - `is_active`: État d'activation de la clé
- Relation bidirectionnelle avec Project (cascade delete)

### API Endpoints
#### Dashboard API (v1)
- Implémentation des routes CRUD pour les projets :
  - `POST /api/v1/dashboard/projects`: Création d'un projet
  - `GET /api/v1/dashboard/projects`: Liste des projets avec pagination
  - `GET /api/v1/dashboard/projects/{project_id}`: Détails d'un projet
  - `PUT /api/v1/dashboard/projects/{project_id}`: Mise à jour d'un projet
  - `DELETE /api/v1/dashboard/projects/{project_id}`: Suppression d'un projet

### Sécurité
- Middleware d'authentification pour le dashboard
- Système de génération de clés API sécurisées
- Protection des routes avec token Bearer
- Validation des données avec Pydantic

### Optimisations
- Eager loading des relations avec `selectinload`
- Gestion optimisée des sessions asynchrones
- Prévention des problèmes de lazy loading avec AsyncAttrs
- Conversion sécurisée des modèles SQLAlchemy vers Pydantic

### Schémas Pydantic
- `ProjectCreate`: Validation de la création de projet
- `ProjectUpdate`: Validation de la mise à jour de projet
- `Project`: Schéma complet de projet avec relations
- `ProjectApiKey`: Schéma de clé API
- `ProjectList`: Schéma de pagination pour la liste des projets

### Documentation
- Documentation des modèles dans `docs/project.md`
- Documentation des endpoints API
- Changelog détaillé

### Améliorations Techniques
- Gestion correcte des greenlets dans les opérations asynchrones
- Optimisation des requêtes avec eager loading
- Gestion propre des transactions asynchrones
- Conversion sécurisée des modèles vers dictionnaires 