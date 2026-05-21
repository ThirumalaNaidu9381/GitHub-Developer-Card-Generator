import os
from google.adk.agents import llm_agent
from google.adk.tools.function_tool import FunctionTool
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

# Create direct function tools from our mcp_server functions
tools = [
    FunctionTool(scrape_github),
    FunctionTool(analyze_profile),
    FunctionTool(generate_card_html),
    FunctionTool(save_card),
]

# System instruction as requested
SYSTEM_INSTRUCTION = (
    "You are a GitHub profile analyst and dev card generator. When a user gives you a GitHub username, "
    "you ALWAYS follow this exact sequence: first call scrape_github, then analyze_profile with the result, "
    "then generate_card_html with all three inputs, then save_card. Never skip steps. Be enthusiastic about "
    "developers' work. If the profile is private or doesn't exist, say so clearly."
)

# Create the Gemini Agent using direct function tools
github_card_agent = llm_agent.LlmAgent(
    name="github_card_agent",
    model="gemini-flash-lite-latest",
    instruction=SYSTEM_INSTRUCTION,
    tools=tools
)
