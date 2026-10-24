# BrandGuardAI

## Overview
BrandGuardAI is a prototype that reviews brand-related content and flags potentially risky or unsupported claims before publication.

## Features
- Reviews text submitted by the user.
- Flags selected risky phrases and guarantee-related claims.
- Shows issue severity, explanation, and a suggested fix.
- Keeps human review essential.

## Technology Stack
- HTML for the user interface
- Python and FastAPI for the backend
- Rule-based content checking

## How to Run Locally
1. Install Python.
2. Install dependencies: `python -m pip install fastapi "uvicorn[standard]"`
3. Start the backend: `python -m uvicorn app:app --reload`
4. Open the frontend `index.html` using a local web server.

## Limitations
This is an early rule-based prototype, not a fully AI-powered verification system. It does not independently verify claims against official brand guidelines or external evidence. Human review is required.

## Future Improvements
- Add configurable brand guidelines.
- Improve claim detection and evidence references.
- Add review history and exportable reports.
