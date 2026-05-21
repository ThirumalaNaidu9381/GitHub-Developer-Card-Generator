# GitHub Card Generator

A production-ready proof-of-concept for generating beautiful GitHub developer cards from a username.

This project combines a Python FastAPI backend with Google ADK tooling and a lightweight React frontend served through Nginx. A GitHub username is transformed into a rich HTML developer card via profile scraping, AI-powered analysis, and card generation.

---

## Project Highlights

- Backend built with `FastAPI` and `uvicorn`
- GitHub profile scraping using `httpx`
- AI analysis using Google Gemini via `google-genai`
- Agent orchestration through `google-adk` and `mcp`
- Frontend served by `nginx` with runtime backend URL injection
- Generated cards are stored as static HTML files under `backend/static/cards/`

---

## Architecture Overview

- `backend/`
  - `main.py`: API service exposing `/generate`, `/card/{username}`, `/health`, and `/`.
  - `agent.py`: Defines the Gemini-based agent and required function tools.
  - `mcp_server.py`: Implements the GitHub scraper, AI analysis, HTML card generator, and file saver.
  - `requirements.txt`: Python dependencies for the backend.
  - `static/cards/`: Stores generated HTML card files.
- `frontend/`
  - `index.html`: React-powered UI that captures GitHub usernames and displays results.
  - `Dockerfile`: Builds the Nginx container and copies the frontend template.
  - `docker-entrypoint.sh`: Injects `BACKEND_URL` into the HTML template at container startup.
- `docker-compose.yml`: Orchestrates the backend and frontend services.

---

## Requirements

- Docker
- Docker Compose
- `.env` file at repository root containing:
  - `GEMINI_API_KEY` for Google Gemini
  - `GITHUB_TOKEN` for GitHub API rate limit safety (optional but recommended)

---

## Getting Started

From the repository root:

```sh
docker-compose up --build
```

Open the app in your browser:

- Frontend: `http://localhost`
- Backend API: `http://localhost:8080`

---

## Application Flow

1. The frontend captures a GitHub username.
2. The frontend sends a POST request to `POST /generate`.
3. Backend starts an ADK runner session and calls the agent.
4. The agent executes:
   - `scrape_github` to fetch profile metadata and repos
   - `analyze_profile` to derive personality, skills, and theme
   - `generate_card_html` to build the static HTML card
   - `save_card` to persist the card under `backend/static/cards/`
5. The response returns the saved card URL and analysis output.

---

## API Reference

### `POST /generate`

Request body:

```json
{
  "username": "octocat"
}
```

Response includes:

- `username`
- `message`
- `card_url`

### `GET /card/{username}`

Returns the generated static HTML card if it exists.

### `GET /health`

Returns a simple health response:

```json
{ "status": "healthy" }
```

---

## Local Backend Development

Run the backend directly without Docker:

```sh
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080
```

Then use the frontend with `BACKEND_URL=http://localhost:8080`.

---

## Notes

- Generated cards are saved in `backend/static/cards/`.
- The frontend uses environment injection to set `BACKEND_URL` at runtime.
- If `GEMINI_API_KEY` is missing, AI analysis returns an error from `mcp_server.py`.

---

## Repository Layout

```text
github-card-generator/
├── backend/
│   ├── agent.py
│   ├── Dockerfile
│   ├── main.py
│   ├── mcp_server.py
│   ├── requirements.txt
│   └── static/
│       └── cards/
├── frontend/
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   └── index.html
├── docker-compose.yml
└── README.md
```

---

## Dependencies

Backend dependencies are defined in `backend/requirements.txt` and include:

- `fastapi`
- `uvicorn`
- `mcp`
- `google-adk`
- `google-genai`
- `httpx`
- `jinja2`
- `python-dotenv`

---

## Output

<img width="988" height="298" alt="image" src="https://github.com/user-attachments/assets/292800f5-71ae-4408-a599-1809a488f8d7" />

<img width="757" height="712" alt="image" src="https://github.com/user-attachments/assets/651421c5-c922-4b56-9eea-ef728d543c84" />


