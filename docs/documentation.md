# Mini Auth API Documentation

## 1. Introduction

Mini Auth is a FastAPI-based authentication and authorization service designed to manage users and projects. It provides distinct authentication flows for platform administrators/project owners and for end-users belonging to specific projects (clients).

Key features include:
*   Platform user registration and login (cookie-based JWT).
*   Project creation and management (CRUD).
*   Project API key generation and management.
*   Project member management (inviting, removing, roles).
*   Client (end-user) registration and login scoped to a project (API key header + response body JWT).

## 2. Authentication

The API uses JSON Web Tokens (JWT) for authentication, but employs different mechanisms depending on the user type.

### 2.1. Platform Authentication

*   **Target Users:** Administrators or project owners managing the platform and projects.
*   **Mechanism:** Uses email and password for login. JWT Access and Refresh tokens are stored in secure, HttpOnly cookies (`access_token`, `refresh_token`).
*   **Endpoints:** Primarily interacts with `/api/v1/auth`, `/api/v1/users`, and `/api/v1/projects`.
*   **Authorization:** Subsequent requests are authenticated automatically via the cookies sent by the browser.

### 2.2. Client Authentication

*   **Target Users:** End-users belonging to a specific application/project managed by Mini Auth.
*   **Mechanism:**
    *   Requires a valid `X-Project-Api-Key` header identifying the project for registration and login.
    *   Uses email and password for registration/login within that project scope.
    *   JWT Access and Refresh tokens are **returned in the response body** upon successful login. Clients are responsible for securely storing and using these tokens.
*   **Endpoints:** Primarily interacts with `/api/v1/client/auth`.
*   **Authorization:** Subsequent requests requiring client authentication must include the `Authorization: Bearer <access_token>` header.

## 3. API Endpoints

All endpoints are prefixed with `/api/v1`.

### 3.1. Platform Authentication (`/auth`)

These endpoints manage platform user sessions.

*   **`POST /auth/register`**
    *   **Description:** Registers a new platform user (owner/admin).
    *   **Auth:** None.
    *   **Request Body:** `UserCreate` schema (email, full_name, password, confirm_password).
    *   **Response Body:** `UserRead` schema (user details without password).
*   **`POST /auth/login`**
    *   **Description:** Logs in a platform user. Sets `access_token` and `refresh_token` cookies.
    *   **Auth:** None.
    *   **Request Body:** `OAuth2PasswordRequestForm` (username=email, password).
    *   **Response Body:** `Token` schema (access_token, refresh_token, token_type).
*   **`POST /auth/refresh`**
    *   **Description:** Refreshes the access token using the `refresh_token` cookie. Sets a new `access_token` cookie.
    *   **Auth:** Valid `refresh_token` cookie.
    *   **Request Body:** None.
    *   **Response Body:** `Token` schema (new access_token, original refresh_token).
*   **`POST /auth/logout`**
    *   **Description:** Logs out the current platform user. Clears auth cookies. Optionally revokes the provided refresh token if available.
    *   **Auth:** Valid `access_token` cookie (optional, needed if not providing refresh token). Valid `refresh_token` cookie (optional, used for revocation).
    *   **Request Body:** None (logic likely needs adjustment to reliably get refresh token from cookie).
    *   **Response Body:** `{"detail": "Successfully logged out"}`.
*   **`POST /auth/logout-all`**
    *   **Description:** Logs out the current platform user from all devices by revoking all their refresh tokens. Clears auth cookies.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** None.
    *   **Response Body:** `{"detail": "Successfully logged out from all devices"}`.

### 3.2. Platform User Management (`/users`)

These endpoints manage platform user accounts.

*   **`GET /users/me`**
    *   **Description:** Gets the profile information of the currently logged-in platform user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** None.
    *   **Response Body:** `UserRead` schema.
*   **`PUT /users/me`**
    *   **Description:** Updates the profile information (full name, email, password) of the currently logged-in platform user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** `UserUpdate` schema.
    *   **Response Body:** `UserRead` schema (updated user).
*   **`POST /users/me/change-password`**
    *   **Description:** Changes the password for the currently logged-in platform user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** `{"current_password": "...", "new_password": "..."}` (Form data likely).
    *   **Response Body:** `{"detail": "Password successfully updated"}`.
*   **`GET /users/{user_id}`**
    *   **Description:** Gets profile information for a specific platform user by their ID.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** None.
    *   **Response Body:** `UserRead` schema.

### 3.3. Project Management (`/projects`)

These endpoints manage projects, their API keys, and members. Platform authentication is required.

*   **`POST /projects`**
    *   **Description:** Creates a new project owned by the current user. Automatically creates a default API key.
    *   **Auth:** Valid `access_token` cookie.
    *   **Request Body:** `ProjectCreate` schema (name, description).
    *   **Response Body:** `Project` schema (full project details including initial API key).
*   **`GET /projects`**
    *   **Description:** Lists projects owned by the current user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100).
    *   **Response Body:** `ProjectList` schema.
*   **`GET /projects/{project_id}`**
    *   **Description:** Gets details of a specific project owned by the current user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Path Params:** `project_id` (string).
    *   **Response Body:** `Project` schema.
*   **`PUT /projects/{project_id}`**
    *   **Description:** Updates details of a specific project owned by the current user.
    *   **Auth:** Valid `access_token` cookie.
    *   **Path Params:** `project_id` (string).
    *   **Request Body:** `ProjectUpdate` schema (name, description).
    *   **Response Body:** `Project` schema (updated project).
*   **`DELETE /projects/{project_id}`**
    *   **Description:** Deletes a specific project owned by the current user (and associated keys/members).
    *   **Auth:** Valid `access_token` cookie.
    *   **Path Params:** `project_id` (string).
    *   **Response Body:** `{"detail": "Project successfully deleted"}`.

#### 3.3.1. Project API Keys (`/projects/{project_id}/api-keys`)

*   **`POST /projects/{project_id}/api-keys`**
    *   **Description:** Creates a new API key for the specified project.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string).
    *   **Request Body:** `ProjectApiKeyCreate` schema (name).
    *   **Response Body:** `ProjectApiKey` schema (including the generated key).
*   **`GET /projects/{project_id}/api-keys`**
    *   **Description:** Lists API keys for the specified project.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string).
    *   **Query Params:** `include_inactive` (bool, default False).
    *   **Response Body:** List of `ProjectApiKey` schemas.
*   **`DELETE /projects/{project_id}/api-keys/{key_id}`**
    *   **Description:** Deactivates (soft delete) an API key.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string), `key_id` (string).
    *   **Response Body:** `204 No Content`.

#### 3.3.2. Project Members (`/projects/{project_id}/members`)

*   **`POST /projects/{project_id}/members`**
    *   **Description:** Adds a registered platform user as a member to the project.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string).
    *   **Request Body:** `ProjectMemberCreate` schema (user_id, role ['member', 'admin']).
    *   **Response Body:** `ProjectMember` schema.
*   **`GET /projects/{project_id}/members`**
    *   **Description:** Lists members of the specified project.
    *   **Auth:** Valid `access_token` cookie (must own or be a member of the project).
    *   **Path Params:** `project_id` (string).
    *   **Response Body:** List of `ProjectMember` schemas.
*   **`DELETE /projects/{project_id}/members/{user_id}`**
    *   **Description:** Removes a member from the project. Cannot remove the owner.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string), `user_id` (string).
    *   **Response Body:** `{"detail": "Member successfully removed"}`.
*   **`PUT /projects/{project_id}/members/{user_id}/role`**
    *   **Description:** Updates the role of a project member. Cannot change the owner's role.
    *   **Auth:** Valid `access_token` cookie (must own project).
    *   **Path Params:** `project_id` (string), `user_id` (string).
    *   **Request Body:** `{"role": "member"}` or `{"role": "admin"}` (likely form data or simple JSON).
    *   **Response Body:** `ProjectMember` schema (updated member).

### 3.4. Client Authentication (`/client/auth`)

These endpoints manage end-users belonging to a specific project.

*   **`POST /client/auth/register`**
    *   **Description:** Registers a new end-user for the project identified by the API key.
    *   **Auth:** Valid `X-Project-Api-Key` header.
    *   **Request Body:** `UserCreate` schema (email, full_name, password, confirm_password).
    *   **Response Body:** `UserRead` schema (user details without password).
    *   **Headers:** Requires `X-Project-Api-Key: <your_project_api_key>`.
*   **`POST /client/auth/login`**
    *   **Description:** Logs in an end-user for the project identified by the API key. Returns JWTs in the response body.
    *   **Auth:** Valid `X-Project-Api-Key` header.
    *   **Request Body:** `ClientLogin` schema (email, password).
    *   **Response Body:** `Token` schema (access_token, refresh_token, token_type).
    *   **Headers:** Requires `X-Project-Api-Key: <your_project_api_key>`.

### 3.5 Future Client Endpoints (Potential)

Endpoints for client-side token refresh, logout, and user profile management (`/client/auth/refresh`, `/client/auth/logout`, `/client/user/me`) might be added, requiring `Authorization: Bearer <client_access_token>`.

## 4. Core Models

*   **`User`:** Represents both platform users (`project_id` is `None`) and client end-users (`project_id` is set). Contains email, password hash, etc. Platform users have a unique email globally, while client users have a unique email *within* their project.
*   **`Project`:** Represents a client application or service managed by Mini Auth. Has an owner, members, and API keys.
*   **`ProjectApiKey`:** An API key associated with a `Project`. Used to identify the project in client authentication requests. Can be active or inactive.
*   **`ProjectMember`:** Links a platform `User` to a `Project` with a specific role (`member` or `admin`).
*   **`RefreshToken`:** Stores JWT refresh tokens associated with a `User`. Used for session persistence and token revocation.

## 5. Headers

*   **`Authorization: Bearer <token>`:** Used to send JWT access tokens for authenticated requests (primarily for client-side operations after login, potentially for some platform operations if not using cookies).
*   **`X-Project-Api-Key: <key>`:** Used to identify the target project when registering or logging in client end-users via `/client/auth` endpoints.

## 6. Schemas

Request bodies and response bodies are validated using Pydantic schemas defined in the `src/schemas/` directory (e.g., `UserCreate`, `Project`, `Token`). Refer to these for exact field names and types.

## 7. Error Handling

The API uses standard HTTP status codes:
*   `200 OK`, `201 Created`, `204 No Content`: Success.
*   `400 Bad Request`: Invalid input data (e.g., weak password, missing fields, passwords don't match).
*   `401 Unauthorized`: Missing, invalid, or expired token/cookie; incorrect password. Often includes `WWW-Authenticate: Bearer` header.
*   `403 Forbidden`: Authentication successful, but insufficient permissions (e.g., invalid API key, trying to modify a project not owned by the user).
*   `404 Not Found`: Resource not found (e.g., project, user, API key).
*   `422 Unprocessable Entity`: Input data has the correct type but invalid values (FastAPI validation error). 