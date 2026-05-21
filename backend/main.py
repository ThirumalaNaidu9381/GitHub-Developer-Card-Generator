from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# ADK Imports
from agent import github_card_agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner, types

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="GitHub Dev Card Generator API")

# 7. Add CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup paths
BASE_DIR = Path(__file__).parent
STATIC_CARDS_DIR = BASE_DIR / "static" / "cards"
STATIC_CARDS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files to serve generated cards
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 2. Sets up InMemorySessionService and InMemoryMemoryService
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# 3. Creates a Runner bound to the agent and services
runner = Runner(
    agent=github_card_agent,
    app_name="GithubDevCardGenerator",
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True
)

class CardRequest(BaseModel):
    username: str

# 4. Exposes POST /generate endpoint
@app.post("/generate")
async def generate_card(request: CardRequest):
    """Generates a GitHub dev card for the specified username using ADK Runner."""
    username = request.username
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    try:
        # Create or reuse a session by username
        session_id = f"session_{username}"
        
        # Construct message in ADK 2.0+ format
        new_message = types.Content(
            role="user", 
            parts=[types.Part(text=f"Generate a dev card for {username}")]
        )
        
        # Run the agent with the specified session
        print(f"Starting generation for user: {username}")
        
        full_text = ""
        # Use run_async which returns an AsyncGenerator of Events
        async for event in runner.run_async(
            user_id=username,
            session_id=session_id,
            new_message=new_message
        ):
            if event.message and event.message.parts:
                for part in event.message.parts:
                    if part.text:
                        full_text += part.text
        
        # Return the final card URL and the agent's full response text
        return {
            "status": "success",
            "data": {
                "username": username,
                "message": full_text,
                "card_url": f"/static/cards/{username}.html"
            }
        }
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. Exposes GET /card/{username} to serve saved cards
@app.get("/card/{username}")
async def get_card(username: str):
    file_path = STATIC_CARDS_DIR / f"{username}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Card not found")
    return FileResponse(file_path)

# 6. Exposes GET /health for Cloud Run health checks
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Serves the frontend at the root path
@app.get("/")
async def read_root():
    index_path = BASE_DIR / "static" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


if __name__ == "__main__":
    # Run with: uvicorn main:app --host 0.0.0.0 --port 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)
