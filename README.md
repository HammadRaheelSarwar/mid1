# mid1

## Deploy Backend To Railway

This repo is now ready for Railway deployment as a Python web service.

### 1) Push this repo to GitHub
Railway deploys cleanly from a GitHub repo.

### 2) Create a Railway project
1. Open Railway.
2. Click `New Project`.
3. Choose `Deploy from GitHub repo`.
4. Select this repository.

### 3) Set required environment variables in Railway
In Railway project settings, add:
- `GOOGLE_API_KEY` = your key
- Any other variables you keep in `my_agent/.env`

Do not commit secrets to Git.

### 4) Deploy
Railway will install from `requirements.txt` and start using `Procfile`:
- `web: gunicorn backend_api:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0`

### 5) Verify
After deployment, open your Railway URL and test:
- `GET /`
- `POST /api/session`
- `POST /api/chat`
