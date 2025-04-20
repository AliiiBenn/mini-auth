# Mini-Auth: Multi-Layered Authentication System

## Overview

Mini-Auth is an authentication API designed to provide a comprehensive user management system for multiple projects, mimicking core functionalities of Supabase Auth. It aims to provide a self-hostable solution for developers needing project-scoped user authentication.

The system comprises:

1.  A central **API** handling all logic.
2.  A **Dashboard** (e.g., a React/Next.js application) for platform administrators/developers to manage projects.
3.  A **Client Library** (e.g., TypeScript) for developers to integrate into their end-user applications, enabling user signup, login, and management *within* a specific project.

## Architecture & User Types

```
┌──────────────────┐      ┌────────────────────────┐      ┌───────────────────────┐
│    Dashboard     │───►│    Mini-Auth API       │◄───│ Client Applications │
│ (React/Next.js)  │      │      (FastAPI)         │      │  (Using TS Library) │
└──────────────────┘      └────────────────────────┘      └───────────────────────┘
       │                         ▲      │      ▲                         │
 Uses  │ Platform User JWT       │      │      │ Uses PROJECT_API_KEY    │
       │                         │      │      │                         │
       ▼                         │      │      │                         ▼
┌──────────────────┐             │      │      │                  ┌──────────────────┐
│ Platform User    │             │      │      │                  │ Project End-User │
│ (Manages Projects)│             │      │      │                  │ (Uses Client App)│
└──────────────────┘             ▼      ▼      ▼                  └──────────────────┘
                        ┌────────────────────────┐
                        │ Database (SQLAlchemy)  │
                        └────────────────────────┘
```

There are two distinct types of users:

1.  **Platform Users:** These are the developers or administrators who register on the Mini-Auth platform itself via the Dashboard. They create and manage `Projects`. They authenticate using standard email/password login, receiving JWTs.
2.  **Project End-Users:** These are the users of the applications *built by* Platform Users. They sign up and log in to a specific `Project` via the Client Library integrated into the end application. Their identity and data are scoped to that specific project.

## Authentication Layers

Mini-Auth employs two primary authentication mechanisms for different purposes:

1.  **Platform User JWT**
    *   **Mechanism:** Standard JSON Web Tokens (Access & Refresh) obtained after a Platform User logs in via the Dashboard. Sent via Cookies or `Authorization: Bearer` header.
    *   **Scope:**
        *   `/api/v1/auth/*` (Platform User registration, login, logout, refresh)
        *   `/api/v1/users/me` (Platform User profile)
        *   `/api/v1/projects/*` (Platform User managing their own projects - CRUD, API Key Management, Member Listing/Management)
    *   **Purpose:** Authenticates the Platform User performing actions related to their account or the projects they own via the Dashboard frontend. Verified by the `get_current_user` dependency.

2.  **Project API Key (`PROJECT_API_KEY`)**
    *   **Mechanism:** Unique key generated per project. Sent by the Client Library, typically via a custom header like `X-API-Key` or potentially `Authorization: Bearer`.
    *   **Scope:**
        *   **(Future)** `/api/v1/client/auth/*` (Routes for Project End-User signup, login, password reset, etc., specific to the project identified by the key).
        *   **(Potentially)** Specific project member management routes if distinct client library permissions are needed.
    *   **Purpose:** Authenticates the *Client Application* acting on behalf of a specific `Project`. It authorizes operations on the Project End-Users belonging to that project. Verified by specific route logic or a dedicated dependency.

**Note:** Access restriction to ensure only the dashboard frontend can *initiate* login/registration is primarily handled by **CORS configuration** on the API server, limiting allowed origins, potentially combined with CSRF protection and rate limiting, rather than a separate API key.

## Components

### 1. API (FastAPI)

*   Provides all endpoints for the different authentication layers.
*   Handles database interactions (SQLAlchemy).
*   Manages JWT creation and validation.
*   Enforces authorization based on the authentication method used (JWT or Project API Key).
*   Uses CORS to restrict browser access to allowed origins (primarily the dashboard frontend domain).

### 2. Dashboard

*   **Functionalities:** Allows Platform Users to register, log in, create/manage their projects, view project details, generate/view/manage `PROJECT_API_KEY`s, and manage Project End-Users for their projects.
*   **Authentication towards API:** Uses the Platform User's JWT for all operations after login (managing profile, projects, project API keys, project members, etc.).

### 3. Client Library (TypeScript - To Be Developed)

*   **Installation:** `npm install mini-auth-client` (Example)
*   **Initialization:** Requires the `PROJECT_API_KEY`.
```typescript
    import { MiniAuthClient } from 'mini-auth-client'; // Hypothetical

    const authClient = new MiniAuthClient({
        apiUrl: 'YOUR_MINI_AUTH_API_URL',
        projectApiKey: 'YOUR_PROJECT_API_KEY'
});
```
*   **Usage:** Provides methods for Project End-User authentication:
```typescript
    // Register a new user for this project
    const { user, error } = await authClient.signUp({
        email: 'end-user@example.com',
    password: 'secure_password'
});

    // Sign in an end-user for this project
    const { session, error } = await authClient.signIn({
        email: 'end-user@example.com',
    password: 'secure_password'
});

    // Get current end-user (if logged in via library)
    const currentUser = authClient.getUser();
    ```
*   **Authentication towards API:** Sends the `PROJECT_API_KEY` with every request to identify the project context.

## Security Considerations

*   **User Scoping:** Project End-Users *must* be strictly scoped to their respective projects. Database queries and logic need to enforce this.
*   **API Key Security:** `PROJECT_API_KEY` grants significant permissions within a project; treat it securely.
*   **Secret Management:** `JWT_SECRET_KEY`, database credentials must be managed securely (environment variables, secrets manager), not hardcoded.
*   **CORS Configuration:** Must be strict to only allow the dashboard domain for JWT-based routes.
*   **Password Hashing:** Uses `bcrypt` via `passlib`.
*   **Rate Limiting:** Essential to implement on authentication endpoints (both Platform User and Project End-User) to prevent brute-force attacks.
*   **CSRF Protection:** Recommended for dashboard frontend interactions.
*   **Input Validation:** Pydantic provides base validation; ensure sensitive inputs are further scrutinized.

## Database Structure (Conceptual - Needs Refinement)

*   Need to decide if `users` table holds Platform Users, Project End-Users, or both. Supabase clones often scope users *within* projects.
*   If users are project-scoped, the `users` table would likely need a `project_id` foreign key.
*   `projects` table stores project metadata and `owner_id` (linking to the Platform User).
*   `project_api_keys` table links keys to projects.
*   `refresh_tokens` table for managing Platform User refresh tokens (Project End-User token management might be handled differently or in the same table with scoping).
*   `project_members` table might be simplified or removed if users are directly linked to projects.

```sql
-- Platform Users (Example - May merge or separate from Project End-Users)
CREATE TABLE platform_users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    -- other platform-specific fields
    created_at TIMESTAMP
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    owner_id UUID REFERENCES platform_users(id), -- Platform User who owns it
    created_at TIMESTAMP
);

-- Project API Keys
CREATE TABLE project_api_keys (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    key VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    last_used_at TIMESTAMP NULL
);

-- Project End-Users (Example - Scoped to Project)
CREATE TABLE project_users (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    email VARCHAR(255), -- May need UNIQUE constraint *per project*
    hashed_password VARCHAR(255),
    -- other end-user specific fields (email_confirmed, etc.)
    created_at TIMESTAMP,
    UNIQUE (project_id, email) -- Example constraint
);

-- Refresh Tokens (Example - Needs scoping if handling both user types)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    token VARCHAR(255) UNIQUE,
    user_id UUID, -- Needs FK to correct user table (platform or project)
    -- user_type VARCHAR(20), -- Discriminator if using one table
    project_id UUID NULL, -- If scoping tokens to projects
    expires_at TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE
);
```

## API Endpoints (Summary & Required Authentication)

*   **Platform User Routes (Platform User JWT)**
    *   `POST /api/v1/auth/register`
    *   `POST /api/v1/auth/login`
    *   `POST /api/v1/auth/refresh`
    *   `POST /api/v1/auth/logout`
    *   `POST /api/v1/auth/logout-all`
    *   `GET /api/v1/users/me`
    *   `PUT /api/v1/users/me`
    *   `POST /api/v1/users/me/change-password`
    *   `POST /api/v1/projects` (Create project for logged-in user)
    *   `GET /api/v1/projects` (List projects for logged-in user)
    *   `GET /api/v1/projects/{project_id}` (Get owned project)
    *   `PUT /api/v1/projects/{project_id}` (Update owned project)
    *   `DELETE /api/v1/projects/{project_id}` (Delete owned project)
    *   `GET /api/v1/projects/{project_id}/api-keys` (List API keys for owned project)
    *   `POST /api/v1/projects/{project_id}/api-keys` (Create API key for owned project)
    *   `DELETE /api/v1/projects/{project_id}/api-keys/{key_id}` (Deactivate API key for owned project)
    *   `POST /api/v1/projects/{project_id}/members` (Add member link to owned project)
    *   `GET /api/v1/projects/{project_id}/members` (List members for owned project)
    *   `DELETE /api/v1/projects/{project_id}/members/{user_id}` (Remove member link from owned project)
    *   `PUT /api/v1/projects/{project_id}/members/{user_id}/role` (Update member role in owned project)

*   **Client Library / Project End-User Routes (`PROJECT_API_KEY`)**
    *   **(Future) POST /api/v1/client/auth/signup` (Register Project End-User)
    *   **(Future) POST /api/v1/client/auth/login` (Login Project End-User)
    *   **(Future) POST /api/v1/client/auth/refresh` (Refresh Project End-User token)
    *   **(Future) GET /api/v1/client/auth/user` (Get logged-in Project End-User info)
    *   **(Future) POST /api/v1/client/auth/reset-password` (Request password reset for Project End-User)
    *   *(etc. for email confirmation, password updates)*