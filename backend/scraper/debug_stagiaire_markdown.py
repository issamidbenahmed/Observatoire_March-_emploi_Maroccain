import os
import requests
import json

FIRECRAWL_API_KEY = "fc-a805e220aa514494980e52aa76950c8b"
API_URL = "https://api.firecrawl.dev/v0/scrape"

def debug_stagiaire():
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": "https://www.stagiaire.ma/offres-stages/1",
        "formats": ["markdown"],
    }
    
    print(f"🔥 Scraping stagiaire.ma for debug...")
    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        markdown = data['data'].get('markdown', '')
        
        with open("debug_stagiaire.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print("✅ Markdown saved to debug_stagiaire.md")
        # Print a snippet
        print("\nSnippet:")
        print(markdown[:1000])
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_stagiaire()
