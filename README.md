# Temperature Mind Reading — Setup Guide

## Files
- `main.py` — FastAPI backend
- `dashboard.html` — Performer dashboard (open in browser)
- `requirements.txt` — Python dependencies

---

## Backend Deployment (Render — same as your other projects)

1. Push these files to a GitHub repo
2. Create a new **Web Service** on Render
3. Set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable:
   - `ANTHROPIC_API_KEY` = your Anthropic API key

Your backend URL will be: `https://your-app-name.onrender.com`

---

## Goo Configuration

Point Goo's submit action to:

```
POST https://your-app.onrender.com/submit
Content-Type: application/json

{ "query": "What is the temperature in Tokyo" }
```

The raw query string from Goo goes directly in the `query` field.
AI extracts the place name automatically — works with any phrasing.

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/submit` | Goo sends query here |
| GET | `/poll` | Dashboard polls this |
| DELETE | `/reset` | Clear between performances |
| GET | `/health` | Sanity check |

---

## Performer Dashboard

1. Open `dashboard.html` in your browser
2. Paste your Render backend URL in the field at the top
3. URL is saved automatically between sessions
4. Hit **Test** to preview the reveal without the backend
5. Hit **Reset** before each new spectator
