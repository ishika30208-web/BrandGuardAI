# One-time Round 3 deployment checklist

## 1. Update GitHub files
1. Back up your existing `app.py` and `index.html`.
2. Replace repository-root `app.py`, `index.html`, `requirements.txt`, and `README.md` with the matching files from this package. Keep the repository name and `main` branch. Do not delete other project files.
3. Commit changes to `main`.
4. Wait for GitHub Pages to finish publishing the updated `index.html`.

## 2. Deploy backend on Render
1. Open the existing `BrandGuardAI-1` Web Service.
2. Confirm Build Command: `pip install -r requirements.txt`.
3. Confirm Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
4. Deploy latest commit and wait for status `Live`.
5. Open `https://brandguardai-1.onrender.com/health`; expect `status: healthy`, `storage: SQLite`, and `total_reviews`.
6. Open `https://brandguardai-1.onrender.com/docs` to inspect the API.

## 3. Configure durable storage (required before claiming restart-proof persistence)
The backend uses SQLite at `DATABASE_PATH`, default `brandguardai.db`. A file on an ephemeral filesystem may disappear after service replacement or redeployment. If the Render service/plan supports a persistent disk, mount it at `/var/data` and add environment variable `DATABASE_PATH=/var/data/brandguardai.db`. Otherwise use a managed database and migrate the app before claiming long-term persistence. Existing in-memory history from the old version will not automatically migrate.

## 4. Test the features from the public website
1. **Guidelines:** put `Made with recyclable packaging` in approved claims; put `guaranteed cure` in prohibited phrases; reference title `Packaging Policy`; reference text `Our packaging is made with recyclable materials.` Save and then Load Guidelines. Confirm values return.
2. **Prohibited phrase:** review `This product is a guaranteed cure.` A `Prohibited brand phrase` finding should appear.
3. **Evidence matching:** review the exact sentence `Our packaging is made with recyclable materials.` The Evidence Reference Check should show a match. Review a different claim and confirm no matching passage is reported. This is string matching, not independent truth verification.
4. **History:** submit at least two reviews, click Load Review History, open View Full Report, then download the JSON report.
5. **Persistence:** only after configuring durable storage, note a review ID, restart/redeploy, then check `/history` again. The same review must remain.
6. **Empty input:** clear the content box and click Review Content; an empty-input message should appear.

## Honest Round 3 claims
- Configurable guidelines: supported by editable lists and saved backend settings.
- Evidence check: exact/substring matching against supplied references; no external retrieval or AI semantic verification.
- History/export: SQLite storage and JSON export; persistence across redeployments depends on durable storage configuration.
