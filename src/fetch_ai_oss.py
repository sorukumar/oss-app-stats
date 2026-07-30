import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"} if GITHUB_TOKEN else {}

REPOS = [
    "ollama/ollama",
    "openclaw/openclaw",
    "NousResearch/hermes-agent",
    "block/goose",
    "block/buzz"
]

def fetch_repo_data(repo_name):
    print(f"Fetching repo info for {repo_name}...")
    repo_resp = requests.get(f"https://api.github.com/repos/{repo_name}", headers=HEADERS)
    if repo_resp.status_code != 200:
        print(f"Error fetching repo {repo_name}: {repo_resp.text}")
        return None
    repo_info = repo_resp.json()
    
    # Fetch all releases handling pagination
    print(f"Fetching releases for {repo_name}...")
    releases = []
    page = 1
    while True:
        rel_resp = requests.get(
            f"https://api.github.com/repos/{repo_name}/releases", 
            headers=HEADERS,
            params={"per_page": 100, "page": page}
        )
        if rel_resp.status_code != 200:
            break
        page_releases = rel_resp.json()
        if not page_releases:
            break
        for r in page_releases:
            # sum downloads across all assets
            total_downloads = sum(asset.get("download_count", 0) for asset in r.get("assets", []))
            releases.append({
                "tag": r.get("tag_name"),
                "published_at": r.get("published_at"),
                "is_prerelease": r.get("prerelease"),
                "downloads": total_downloads,
                "asset_count": len(r.get("assets", []))
            })
        if len(page_releases) < 100:
            break
        page += 1
        
    return {
        "repo": repo_name,
        "stars": repo_info.get("stargazers_count"),
        "forks": repo_info.get("forks_count"),
        "created_at": repo_info.get("created_at"),
        "total_releases": len(releases),
        "releases": sorted(releases, key=lambda x: x["published_at"])
    }

def main():
    results = {}
    for repo in REPOS:
        data = fetch_repo_data(repo)
        if data:
            results[repo] = data
            
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "ai_oss_raw.json")
    # Ensure directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved raw data to {out_path}")

if __name__ == "__main__":
    main()
