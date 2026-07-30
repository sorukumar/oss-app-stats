#!/usr/bin/env python3
"""
Fetch stargazers history for block/buzz to track top-of-funnel discovery.
Saves data to docs/data/buzz_stars.json.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Try to load token from .env
token = os.environ.get('GITHUB_TOKEN', '')
if not token:
    try:
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        token = line.split('=', 1)[1].strip()
    except Exception:
        pass

if not token:
    print("Error: GITHUB_TOKEN is required for fetching stargazers due to rate limits.")
    sys.exit(1)

OUTPUT_FILE = Path(__file__).parent.parent / "docs" / "data" / "buzz_stars.json"

def fetch_stargazers(owner: str, repo: str) -> list:
    all_stars = []
    page = 1
    
    print(f"Fetching stargazers for {owner}/{repo}...")
    
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/stargazers?per_page=100&page={page}"
        headers = {
            'Accept': 'application/vnd.github.v3.star+json',
            'User-Agent': 'oss-app-stats/1.0',
            'Authorization': f'Bearer {token}'
        }
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                remaining = resp.headers.get('X-RateLimit-Remaining', '?')
                data = json.loads(resp.read().decode())
                
                if not data:
                    break
                
                all_stars.extend(data)
                print(f"  ✓ Page {page} ({len(data)} stars) | Limit remaining: {remaining}")
                
                if len(data) < 100:
                    break
                    
                page += 1
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP Error {e.code}: {e.reason}")
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            break
            
    return all_stars

def process_stars(raw_stars: list) -> dict:
    """Group stars by week and compute cumulative totals."""
    weekly_data = {}
    
    # Ensure sorted chronologically
    # starred_at is ISO 8601 string
    sorted_stars = sorted(raw_stars, key=lambda x: x.get('starred_at', ''))
    
    cumulative = 0
    for star in sorted_stars:
        starred_at = star.get('starred_at')
        if not starred_at:
            continue
            
        cumulative += 1
        
        d = datetime.fromisoformat(starred_at.replace('Z', '+00:00'))
        # ISO week grouping (similar to fetch_releases.py)
        year, week, _ = d.isocalendar()
        key = f"{year}-W{str(week).zfill(2)}"
        
        if key not in weekly_data:
            weekly_data[key] = {
                'new_stars': 0,
                'cumulative': cumulative,
                'date': starred_at
            }
        
        weekly_data[key]['new_stars'] += 1
        # Update cumulative to the latest in that week
        weekly_data[key]['cumulative'] = cumulative
        
    # Convert to array
    weekly_array = []
    for k, v in sorted(weekly_data.items()):
        weekly_array.append({
            'label': k,
            'date': v['date'],
            'new_stars': v['new_stars'],
            'cumulative': v['cumulative']
        })
        
    return {
        'total_stars': len(raw_stars),
        'weekly_growth': weekly_array,
        'fetched_at': datetime.now(timezone.utc).isoformat()
    }

def main():
    stars = fetch_stargazers('block', 'buzz')
    if not stars:
        print("No stars fetched or error occurred.")
        return
        
    print(f"Total stars fetched: {len(stars)}")
    
    processed_data = process_stars(stars)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(processed_data, f, indent=2)
        
    print(f"✓ Saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
