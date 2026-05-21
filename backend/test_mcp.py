import asyncio
import os
import json
from mcp_server import scrape_github, analyze_profile, generate_card_html

async def test_end_to_end():
    username = "torvalds"
    print(f"--- Starting Test for {username} ---")
    
    # 1. Scrape GitHub
    print("Step 1: Scraping GitHub...")
    github_data = await scrape_github(username)
    if "error" in github_data:
        print(f"FAILED: scrape_github error: {github_data['error']}")
        return
    print("Successfully scraped GitHub data.")
    
    # 2. Analyze Profile
    print("Step 2: Analyzing Profile with Gemini...")
    analysis = await analyze_profile(github_data)
    if "error" in analysis:
        print(f"FAILED: analyze_profile error: {analysis['error']}")
        return
    print("Successfully analyzed profile.")
    
    # 3. Generate HTML Card
    print("Step 3: Generating HTML Card...")
    try:
        html = await generate_card_html(username, github_data, analysis)
        print("Successfully generated HTML card.")
    except Exception as e:
        print(f"FAILED: generate_card_html error: {str(e)}")
        return
    
    # 4. Results
    print("\n--- TEST RESULTS ---")
    print(f"Card Theme: {analysis.get('card_theme')}")
    print(f"Developer Vibe: {analysis.get('developer_vibe')}")
    print("\nTest completed successfully!")

if __name__ == "__main__":
    # Ensure environment variables are set (simulating .env load)
    # Note: In a real run, you'd use python-dotenv or set them in the shell.
    # We rely on the env being available in the shell execution.
    asyncio.run(test_end_to_end())
