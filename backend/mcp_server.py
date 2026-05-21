import os
import httpx
import json
from mcp.server.fastmcp import FastMCP
from google import genai
from jinja2 import Template
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("GithubDevCardServer")

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
STATIC_DIR = Path(__file__).parent / "static" / "cards"

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """Calls the GitHub REST API and returns profile and top repo data."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    async with httpx.AsyncClient() as http_client:
        # Fetch User Profile
        profile_res = await http_client.get(f"https://api.github.com/users/{username}", headers=headers)
        if profile_res.status_code != 200:
            return {"error": f"User {username} not found or API error."}
        
        user_data = profile_res.json()
        
        # Fetch Repos (sorted by stars)
        repos_res = await http_client.get(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30", headers=headers)
        repos_data = repos_res.json() if repos_res.status_code == 200 else []
        
        # Extract Top 6 Repos
        top_repos = []
        languages = {}
        for repo in repos_data:
            if not repo["fork"]:
                if len(top_repos) < 6:
                    top_repos.append({
                        "name": repo["name"],
                        "stars": repo["stargazers_count"],
                        "language": repo["language"],
                        "description": repo["description"]
                    })
                
                lang = repo["language"]
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
        
        # Sort languages
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "name": user_data.get("name") or user_data.get("login"),
            "avatar_url": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_repos": top_repos,
            "languages": [l[0] for l in sorted_langs[:5]]
        }

@mcp.tool()
async def analyze_profile(github_data: dict) -> dict:
    """Analyzes GitHub data using Gemini to generate personality and theme."""
    if not client:
        return {"error": "GEMINI_API_KEY not configured."}
    
    prompt = f"""
    Analyze this GitHub developer profile data and return a JSON object.
    Data: {json.dumps(github_data)}
    
    Required JSON format:
    {{
        "developer_vibe": "A one-sentence personality description.",
        "top_skills": ["skill1", "skill2", "skill3"],
        "fun_fact": "A clever observation inferred from their repos or bio.",
        "card_theme": "one of: 'hacker', 'builder', 'researcher', 'designer', 'open-source-hero'"
    }}
    """
    
    models_to_try = [
        "gemini-2.0-flash-lite-preview-02-05", 
        "gemini-2.0-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-1.5-flash", 
        "gemini-flash-latest"
    ]
    last_error = None

    for model_id in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
        except Exception as e:
            last_error = str(e)
            print(f"Model {model_id} failed: {last_error}")
            continue
    
    return {"error": f"All models failed. Last error: {last_error}"}

@mcp.tool()
async def generate_card_html(username: str, github_data: dict, analysis: dict) -> str:
    """Generates a self-contained HTML string for a beautiful dev card."""
    theme_colors = {
        "hacker": {"bg": "#0d1117", "text": "#58a6ff", "card": "#161b22", "border": "#30363d"},
        "builder": {"bg": "#f6f8fa", "text": "#24292e", "card": "#ffffff", "border": "#d1d5da"},
        "researcher": {"bg": "#f0f5ff", "text": "#0969da", "card": "#ffffff", "border": "#afcffa"},
        "designer": {"bg": "#fff5f5", "text": "#cf222e", "card": "#ffffff", "border": "#ffcfcf"},
        "open-source-hero": {"bg": "#fdf8ec", "text": "#9a6700", "card": "#ffffff", "border": "#f1e05a"}
    }
    
    theme = analysis.get("card_theme", "builder")
    colors = theme_colors.get(theme, theme_colors["builder"])
    
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: {{ colors.bg }}; color: {{ colors.text }}; padding: 20px; }
            .card { background: {{ colors.card }}; border: 1px solid {{ colors.border }}; border-radius: 10px; padding: 24px; max-width: 450px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
            .header { display: flex; align-items: center; margin-bottom: 16px; }
            .avatar { width: 80px; height: 80px; border-radius: 50%; border: 2px solid {{ colors.text }}; margin-right: 16px; }
            .name { font-size: 24px; font-weight: bold; margin: 0; }
            .vibe { font-style: italic; margin: 8px 0; color: #666; }
            .stats { display: flex; gap: 16px; margin: 16px 0; font-size: 14px; }
            .badge { background: {{ colors.text }}; color: {{ colors.card }}; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .repos { margin-top: 16px; }
            .repo-item { border-top: 1px solid {{ colors.border }}; padding: 8px 0; }
            .repo-name { font-weight: bold; font-size: 14px; }
            .repo-desc { font-size: 12px; opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <img class="avatar" src="{{ github_data.avatar_url }}" alt="avatar">
                <div>
                    <p class="name">{{ github_data.name }}</p>
                    <div style="display: flex; gap: 5px; margin-top: 5px;">
                        {% for skill in analysis.top_skills %}
                        <span class="badge">{{ skill }}</span>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <p class="vibe">"{{ analysis.developer_vibe }}"</p>
            <div class="stats">
                <span><strong>{{ github_data.public_repos }}</strong> Repos</span>
                <span><strong>{{ github_data.followers }}</strong> Followers</span>
            </div>
            <p style="font-size: 12px;"><strong>Fact:</strong> {{ analysis.fun_fact }}</p>
            <div class="repos">
                <p style="font-weight: bold; margin-bottom: 8px;">Top Repositories</p>
                {% for repo in github_data.top_repos[:3] %}
                <div class="repo-item">
                    <div class="repo-name">{{ repo.name }} ⭐ {{ repo.stars }}</div>
                    <div class="repo-desc">{{ repo.description or "No description" }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(template_str)
    return template.render(github_data=github_data, analysis=analysis, colors=colors)

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Saves the HTML card to the static directory and returns the path."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    file_path = STATIC_DIR / f"{username}.html"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
