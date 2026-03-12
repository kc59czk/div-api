# Copilot / AI Agent Instructions for div-api

Short, actionable guidance to help AI coding agents be productive in this repository.

- **Big picture:** This is a small Flask-based REST API for tracking user portfolios (accounts, holdings, dividends). The HTTP service and data model are implemented in `app.py` and `schema.sql` (SQLite). The DB file lives under `instance/portfolio.db` and is created by `init_db()` which reads `schema.sql`.

- **Primary files:**
  - `app.py` — main Flask app, routes, auth, DB helpers.
  - `schema.sql` — SQLite schema for `users`, `accounts`, `holdings`, `dividends`.

- **Architecture / data flow:**
  - Requests arrive at Flask endpoints in `app.py`.
  - `get_db()` returns a per-request SQLite connection (`instance/portfolio.db`); `init_db()` creates tables from `schema.sql`.
  - Authentication is JWT-based: `generate_token(user_id)` and `token_required` decorator enforce `Authorization: Bearer <token>`.
  - User ownership is enforced by joining `accounts` to `users` and checking `user_id` in routes (see `get_user_accounts()` and various account/holding/dividend checks).

- **Key conventions & patterns (project-specific):**
  - SQLite is used for persistence; migrations are manual via `schema.sql`. Do not assume a migration tool.
  - The `instance/` folder is used for runtime artifacts (`portfolio.db`). Code calls `os.makedirs('instance', exist_ok=True)` on startup.
  - `init_db()` is intentionally a manual step (commented in `__main__`). To initialize DB, run the helper directly (example below) rather than uncommenting permanently.
  - Error responses are JSON objects `{ "error": "..." }` with appropriate HTTP status codes. Follow this pattern when adding new endpoints.
  - Passwords are hashed with `bcrypt` and stored in `users.password_hash`.
  - Input validation is explicit in routes (e.g., numeric checks for `quantity`, `price`, `amount`). Match the existing style (return JSON with status codes rather than raising exceptions).

- **Dependencies & runtime:**
  - Core packages: `flask`, `bcrypt`, `pyjwt` (imported as `jwt`), `sqlite3` (stdlib). Use the repo virtualenv at `bin/` if present: `bin/python` or activate with `source bin/activate`.
  - Environment: set `SECRET_KEY` env var for JWT in production; default fallback is `your-secret-key-change-in-prod` in `app.py`.

- **How to run locally (developer workflow):**
  - Create DB (one-off):
    - Using Python: `bin/python -c "from app import init_db; init_db()"`
    - Or temporarily uncomment `init_db()` inside `if __name__ == '__main__':` then run `bin/python app.py` once.
  - Start server (development): `bin/python app.py` (runs Flask dev server with `debug=True`).
  - To use a different Python interpreter, the repo includes a virtualenv in `bin/` — prefer that interpreter.

- **Auth / example calls:**
  - Register:
    - `curl -X POST -H 'Content-Type: application/json' -d '{"username":"u","email":"e@e","password":"pw"}' http://localhost:5000/auth/register`
  - Login (returns `access_token`):
    - `curl -X POST -H 'Content-Type: application/json' -d '{"username":"u","password":"pw"}' http://localhost:5000/auth/login`
  - Use token (example get accounts):
    - `curl -H 'Authorization: Bearer <token>' http://localhost:5000/accounts`

- **Patterns to preserve when editing:**
  - Keep `token_required` as the single place for JWT parsing and error handling — reuse it for new protected endpoints.
  - Use `g` (Flask context) for `db` and `user_id` per-request state (see `get_db()` and `token_required`).
  - When adding DB queries, prefer `db.execute(...).fetchone()` / `.fetchall()` and convert rows to dicts as in existing handlers.

- **Testing & debugging tips:**
  - No automated tests present — when adding tests, prefer small function-level tests that mock DB or use a temporary SQLite file under `instance/`.
  - For quick DB inspection: open `instance/portfolio.db` with `sqlite3 instance/portfolio.db` and run `SELECT` queries.
  - To debug JWT issues, verify `SECRET_KEY` env var and token `exp` claims.

- **Integration points & warnings:**
  - Production: `app.run(debug=True)` is fine for dev only — use a WSGI server for production and ensure `SECRET_KEY` is set and strong.
  - Be careful with `sqlite3` concurrency if you later run multiple workers — SQLite has locking characteristics; consider migrating to a client/server DB for concurrent writes.

If anything here is unclear or you want more examples (tests, sample requests, or deployment notes), tell me which area to expand. After your feedback I will iterate on this file.
