# Mini-Auth : Clone SupaBase Authentication System

## Vue d'ensemble

Mini-Auth est une API d'authentification inspirée de SupaBase qui gère trois niveaux distincts d'authentification :

1. **Authentification de l'API** (Niveau Système)
2. **Authentification Dashboard** (Niveau Administrateur)
3. **Authentification Projet** (Niveau Utilisateur Final)

## 1. Authentification de l'API

### Objectif
Sécuriser l'API elle-même contre les accès non autorisés.

### Méthodes de protection
- **CORS Protection** : Restriction des origines autorisées à accéder à l'API
- **Token d'API** : Authentification par token pour chaque requête
- **Middleware de Sécurité** : Validation des requêtes entrantes

### Fonctionnement
- Chaque requête doit inclure un token valide dans les headers d'autorisation
- Vérification des origines des requêtes via CORS
- Blocage automatique des requêtes non conformes

## 2. Authentification Dashboard

### Objectif
Gérer l'accès des utilisateurs principaux de la plateforme (administrateurs de projets).

### Caractéristiques
- Interface dashboard dédiée
- Authentification email/mot de passe
- Génération de token JWT pour les sessions
- Possibilité future d'ajouter d'autres méthodes d'authentification (OAuth, SSO, etc.)

### Fonctionnalités
- Création de compte
- Connexion/Déconnexion
- Gestion de profil
- Création et gestion de projets
- Génération et gestion des clés API pour les projets

## 3. Authentification Projet

### Objectif
Permettre aux projets créés par les utilisateurs du dashboard de gérer leur propre système d'authentification.

### Caractéristiques
- Système d'authentification isolé par projet
- Base d'utilisateurs indépendante pour chaque projet
- Clé API unique par projet

### Fonctionnement
1. L'administrateur crée un projet dans le dashboard
2. Il reçoit une clé API unique pour ce projet
3. Il intègre cette clé dans son application
4. Les utilisateurs finaux peuvent créer des comptes et s'authentifier dans le contexte de ce projet spécifique

### Isolation
- Les utilisateurs d'un projet sont isolés des autres projets
- Pas d'accès au dashboard principal
- Authentication limitée au contexte du projet

## Architecture Technique

```
┌─────────────────┐
│     API         │ ← Niveau 1 : Protection globale
├─────────────────┤
│   Dashboard     │ ← Niveau 2 : Administrateurs
├─────────────────┤
│    Projets      │ ← Niveau 3 : Utilisateurs finaux
└─────────────────┘
```

## Flux d'authentification

1. **Niveau API**
   - Validation CORS
   - Vérification du token API
   - Middleware de sécurité

2. **Niveau Dashboard**
   - Login email/password
   - Génération JWT
   - Session management

3. **Niveau Projet**
   - Authentification via clé API du projet
   - Gestion utilisateurs locale au projet
   - Tokens spécifiques au projet

## Sécurité

- Tokens JWT pour toutes les authentifications
- Hachage sécurisé des mots de passe
- Validation stricte des origines
- Isolation complète entre les projets
- Rate limiting et protection contre les attaques 