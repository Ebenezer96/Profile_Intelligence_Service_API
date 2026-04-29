# Profile Intelligence Platform (Stage 3)

## Overview

The **Profile Intelligence Platform** is a full-stack system that transforms raw name input into enriched profile intelligence using multiple external APIs. It provides secure access via GitHub OAuth, supports role-based permissions, and exposes functionality through three interfaces:

* REST API (Backend)
* CLI Tool
* Web Portal

The system maintains a single backend source of truth while supporting multiple client interfaces.

---

## System Architecture

```text
                ┌───────────────┐
                │   GitHub OAuth│
                └──────┬────────┘
                       │
        ┌──────────────▼──────────────┐
        │        Django Backend        │
        │  (DRF + JWT + RBAC + APIs)  │
        └──────┬──────────┬───────────┘
               │          │
        ┌──────▼───┐  ┌───▼────────┐
        │   CLI     │  │ Web Portal │
        │ (Typer)   │  │ (React)    │
        └───────────┘  └────────────┘
```

---

## Authentication Flow

### 1. CLI / API Flow (JWT)

1. User logs in via GitHub OAuth
2. Backend returns:

   * access_token (short-lived)
   * refresh_token (long-lived)
3. CLI stores tokens in:

   ```text
   ~/.insighta/credentials.json
   ```
4. CLI sends requests with:

   ```text
   Authorization: Bearer <token>
   ```

---

### 2. Web Portal Flow (Secure Cookies)

1. User clicks login
2. Redirects to GitHub
3. GitHub returns `code`
4. Backend:

   * exchanges code for access token
   * creates JWT tokens
   * stores them in HTTP-only cookies

```text
access_token → HttpOnly cookie
refresh_token → HttpOnly cookie
```

5. Frontend makes requests using:

```js
axios.get(url, { withCredentials: true })
```

---

## Token Handling Strategy

* Access token expires in **15 minutes**
* Refresh token used to generate new access tokens
* CLI implements **automatic token refresh**
* Web portal uses cookies (no local storage)

---

## Role-Based Access Control

| Role    | Permissions           |
| ------- | --------------------- |
| analyst | View profiles, search |
| admin   | View, search, export  |

Enforced via custom DRF permission classes.

---

## API Endpoints

### Profiles

```text
GET /api/v1/profiles/
GET /api/v1/profiles/search/
GET /api/v1/profiles/export/
```

---

### Authentication

```text
GET /api/v1/auth/github/login/
POST /api/v1/auth/token/refresh/
```

---

### Web Auth (Cookies)

```text
GET /api/v1/web/auth/github/login/
GET /api/v1/web/auth/github/callback/
GET /api/v1/web/auth/me/
POST /api/v1/web/auth/logout/
```

---

## Natural Language Parsing

The search endpoint converts human queries into structured filters.

Example:

```text
"female adult in nigeria"
```

Parsed into:

```json
{
  "gender": "female",
  "age_group": "adult",
  "country_id": "NG"
}
```

This is handled in:

```text
services.py → parse_natural_language_query()
```

---

## CLI Usage

### Install

```bash
pip install -e .
```

### Commands

```bash
insighta login
insighta profiles
insighta search "female adult in nigeria"
insighta export
insighta refresh
insighta logout
```

---

## Web Portal Features

* GitHub login
* Profile dashboard
* Search functionality
* CSV export
* Logout

Uses secure cookie-based authentication.

---

## Rate Limiting

```text
100 requests per user per day
```

---

## Request Logging

Logs include:

```text
method, endpoint, status, user, IP, duration
```

---

## Setup Instructions

### Backend

```bash
git clone <repo>
cd backend_wizard_stage2
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

### CLI

```bash
cd insighta-cli
pip install -e .
```

---

### Web Portal

```bash
cd insighta-web
npm install
npm run dev
```

---

## Project Structure

```text
backend_wizard_stage2/
insighta-cli/
insighta-web/
```

---

## Features Summary

* GitHub OAuth authentication
* JWT + Cookie-based auth
* Role-based access control
* CLI + Web integration
* Natural language search
* CSV export
* Rate limiting
* Request logging


## Author

Ebenezer Amakato
