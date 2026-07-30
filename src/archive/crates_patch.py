import os
import sys

def patch_file():
    with open('/Users/saurabhkumar/Desktop/Work/github/oss-app-stats/src/fetch_releases.py', 'r') as f:
        content = f.read()

    new_func = """
def fetch_crates_project(project: dict) -> dict:
    crate_name = project['crate_name']
    print(f"\\n{'='*60}\\nFetching from crates.io: {crate_name}\\n{'='*60}")
    url = f"https://crates.io/api/v1/crates/{crate_name}"
    
    headers = {'User-Agent': 'oss-app-stats/1.0'}
    import urllib.request
    import json
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ✗ Failed to fetch crate {crate_name}: {e}")
        return None

    crate = data.get('crate', {})
    versions = data.get('versions', [])
    
    processed_releases = []
    total_downloads = crate.get('downloads', 0)
    
    for v in versions:
        processed_releases.append({
            'tag': v['num'],
            'name': f"{crate_name} {v['num']}",
            'published_at': v['created_at'],
            'is_prerelease': '-' in v['num'],
            'is_draft': v.get('yanked', False),
            'total_downloads': v['downloads'],
            'asset_count': 1,
            'assets': [{'name': f"{crate_name}-{v['num']}.crate", 'platform': 'Source', 'size_bytes': v.get('crate_size', 0), 'download_count': v['downloads']}],
            'body_excerpt': "",
            'html_url': f"https://crates.io/crates/{crate_name}/{v['num']}",
            'author': "crates.io"
        })
        
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # Sort
    processed_releases.sort(key=lambda r: r['published_at'] if r['published_at'] else '', reverse=True)
    
    # Cadence
    dates = [
        datetime.fromisoformat(r['published_at'].replace('Z', '+00:00'))
        for r in processed_releases
        if r['published_at'] and not r['is_prerelease']
    ]
    cadence_days = None
    if len(dates) >= 2:
        deltas = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
        cadence_days = round(sum(deltas) / len(deltas), 1)

    days_since_latest = None
    if processed_releases and processed_releases[0]['published_at']:
        latest_date = datetime.fromisoformat(
            processed_releases[0]['published_at'].replace('Z', '+00:00')
        )
        days_since_latest = (now - latest_date).days

    return {
        'project': {
            'owner': project['owner'],
            'repo': project['repo'],
            'name': project['name'],
            'full_name': f"{project['owner']}/{project['repo']}",
            'description': crate.get('description', ''),
            'stars': 0, # crates.io doesn't expose stars in this API
            'forks': 0,
            'open_issues': 0,
            'language': 'Rust',
            'license': crate.get('exact_match', False), 
            'homepage': crate.get('homepage', ''),
            'html_url': f"https://crates.io/crates/{crate_name}",
        },
        'summary': {
            'total_downloads': total_downloads,
            'total_releases': len(processed_releases),
            'stable_releases': sum(1 for r in processed_releases if not r['is_prerelease']),
            'pre_releases': sum(1 for r in processed_releases if r['is_prerelease']),
            'latest_version': processed_releases[0]['tag'] if processed_releases else None,
            'latest_date': processed_releases[0]['published_at'] if processed_releases else None,
            'days_since_latest': days_since_latest,
            'avg_cadence_days': cadence_days,
            'platform_breakdown': {'Source': total_downloads},
        },
        'releases': processed_releases,
        'fetched_at': now.isoformat(),
    }
"""

    if "def fetch_crates_project" not in content:
        content = content.replace("def fetch_project(project: dict) -> dict:", new_func + "\n\ndef fetch_project(project: dict) -> dict:")
    
    # Now modify fetch_project caller if not already modified
    fetch_project_new = """def fetch_project(project: dict) -> dict:
    if project.get('source') == 'crates':
        return fetch_crates_project(project)
    """
    if "if project.get('source') == 'crates':" not in content:
        content = content.replace("def fetch_project(project: dict) -> dict:\n    \"\"\"Fetch and process data for a single project.\"\"\"", fetch_project_new + "\n    \"\"\"Fetch and process data for a single project.\"\"\"")

    with open('/Users/saurabhkumar/Desktop/Work/github/oss-app-stats/src/fetch_releases.py', 'w') as f:
        f.write(content)

patch_file()
