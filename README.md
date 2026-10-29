# BrandGuardAI — Round 3 Upgrade

BrandGuardAI is a pre-publication brand governance prototype. It checks submitted copy against demo rules and configurable brand guidelines, compares copy with user-supplied reference passages, stores review history in SQLite, and provides JSON report downloads.

## Features
- Rule-based detection of guarantee, superiority, absolute and configured prohibited phrases.
- Configurable approved claims, prohibited phrases and approved reference text.
- Exact/substring reference matching with a transparent evidence status.
- SQLite-backed review history and saved guidelines.
- Reopen historical reviews and download JSON reports.
- Health endpoint at `/health`; interactive API docs at `/docs`.

## Technology
HTML/CSS/JavaScript frontend; Python, FastAPI, Pydantic and SQLite backend.

## Run locally
1. Install Python 3.10 or newer.
2. In this folder run `python -m pip install -r requirements.txt`.
3. Run `python -m uvicorn app:app --reload`.
4. Open `index.html` using a local web server. The included frontend is configured to use the deployed API; for local testing change `API_BASE` in `index.html` to `http://127.0.0.1:8000`.

## Deployment
- Frontend: GitHub Pages from the repository root and `main` branch.
- Backend: Render Web Service with build command `pip install -r requirements.txt` and start command `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- For persistent review history, configure a durable mounted disk and set `DATABASE_PATH` to a file on that disk (example: `/var/data/brandguardai.db`) or use a managed database. SQLite stored on an ephemeral filesystem can be lost after service replacement/redeployment.

## Limitations
This is a rule-based prototype, not an autonomous AI fact-checker. Evidence matching is exact/substring comparison against reference text supplied by the user. It does not fetch official sources or determine whether a claim is objectively true. No detected issue does not guarantee content is safe. Human verification is required.
