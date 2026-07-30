import json
import os
from datetime import datetime

with open("docs/data/ai_oss_raw.json", "r") as f:
    data = json.load(f)

markdown = "# AI OSS Raw Data Analysis\n\n"
markdown += "Here is a high-level summary of the raw data we pulled. We can use this to decide how to normalize the 'Launch Date' for each project.\n\n"

for repo, info in data.items():
    markdown += f"## {repo}\n"
    markdown += f"- **Stars**: {info['stars']:,}\n"
    markdown += f"- **Total Releases**: {info['total_releases']}\n"
    
    releases = info.get("releases", [])
    if not releases:
        markdown += "- No releases found.\n\n"
        continue
        
    first_rel = releases[0]
    last_rel = releases[-1]
    
    markdown += f"- **First Release**: {first_rel['tag']} on {first_rel['published_at'][:10]}\n"
    markdown += f"- **Latest Release**: {last_rel['tag']} on {last_rel['published_at'][:10]}\n"
    
    # Find first v1.0.0 or non-0.0.x
    stable_found = False
    for r in releases:
        tag = r['tag'].lower()
        if 'alpha' not in tag and 'beta' not in tag and 'rc' not in tag and 'pre' not in tag:
            # check if it's considered "stable" like v1.x or at least v0.1 for ollama since ollama never hit v1
            pass
            
    markdown += "\n### First 5 Releases\n"
    markdown += "| Tag | Date | Downloads | Is Prerelease |\n"
    markdown += "|---|---|---|---|\n"
    for r in releases[:5]:
        markdown += f"| {r['tag']} | {r['published_at'][:10]} | {r['downloads']:,} | {r['is_prerelease']} |\n"
    
    markdown += "\n### Notable Milestone Releases\n"
    markdown += "| Tag | Date | Downloads | Note |\n"
    markdown += "|---|---|---|---|\n"
    # Find first release with > 10,000 downloads
    for r in releases:
        if r['downloads'] > 10000:
            markdown += f"| {r['tag']} | {r['published_at'][:10]} | {r['downloads']:,} | First >10k downloads |\n"
            break
            
    # Find first release with > 100,000 downloads
    for r in releases:
        if r['downloads'] > 100000:
            markdown += f"| {r['tag']} | {r['published_at'][:10]} | {r['downloads']:,} | First >100k downloads |\n"
            break
            
    markdown += "\n---\n\n"

# Write to artifact
artifact_path = "/Users/saurabhkumar/.gemini/antigravity-ide/brain/3c3a89b6-f72e-45b3-bacd-11d036f98581/ai_oss_raw_summary.md"
with open(artifact_path, "w") as f:
    f.write(markdown)
    
print(f"Summary written to {artifact_path}")
