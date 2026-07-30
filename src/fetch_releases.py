#!/usr/bin/env python3
"""
OSS App Stats — Data Fetcher Pipeline

Fetches release data from GitHub API and Crates.io for tracked projects and saves
structured JSON files for the static frontend to consume.

Usage:
    python fetch_releases.py                   # Fetch all projects
    python fetch_releases.py block/buzz        # Fetch single project
    python fetch_releases.py --category "Block Open Source"  # Fetch category

Environment Variables:
    GITHUB_TOKEN - Optional. Personal access token for higher rate limits.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Load .env file manually (avoids python-dotenv dependency)
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, val = line.strip().split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"\'')

# ─── Configuration ───────────────────────────────────────────────────────────

PROJECTS = [
    {
        "category": "Core Infrastructure",
        "repos": [
            {"owner": "bitcoin", "repo": "bitcoin", "name": "Bitcoin Core"},
            {"owner": "btcpayserver", "repo": "btcpayserver", "name": "BTCPay Server"},
            {"owner": "mempool", "repo": "mempool", "name": "Mempool.space"},
            {"owner": "joinmarket-webui", "repo": "joinmarket-webui", "name": "Jam"},
            {"owner": "RoboSats", "repo": "robosats", "name": "RoboSats"},
        ]
    },
    {
        "category": "Wallets",
        "repos": [
            {"owner": "sparrowwallet", "repo": "sparrow", "name": "Sparrow Wallet"},
            {"owner": "spesmilo", "repo": "electrum", "name": "Electrum"},
            {"owner": "BlueWallet", "repo": "BlueWallet", "name": "BlueWallet"},
            {"owner": "Blockstream", "repo": "green_android", "name": "Green Wallet"},
            {"owner": "nunchuk-io", "repo": "nunchuk-desktop", "name": "Nunchuk"},
            {"owner": "WalletWasabi", "repo": "WalletWasabi", "name": "Wasabi Wallet"},
            {"owner": "ZeusLN", "repo": "zeus", "name": "Zeus"},
            {"owner": "ACINQ", "repo": "phoenix", "name": "Phoenix"},
            {"owner": "MutinyWallet", "repo": "mutiny-web", "name": "Mutiny Wallet"},
            {"owner": "hsjoberg", "repo": "blixt-wallet", "name": "Blixt"},
            {"owner": "breez", "repo": "breezmobile", "name": "Breez"},
            {"owner": "bitkey", "repo": "bitkey", "name": "Bitkey"},
        ]
    },
    {
        "category": "Lightning",
        "repos": [
            {"owner": "lightningnetwork", "repo": "lnd", "name": "LND"},
            {"owner": "ElementsProject", "repo": "lightning", "name": "Core Lightning"},
            {"owner": "ACINQ", "repo": "eclair", "name": "Eclair"},
            {"owner": "lightningdevkit", "repo": "rust-lightning", "name": "LDK", "source": "crates", "crate_name": "lightning"},
            {"owner": "lnbits", "repo": "lnbits", "name": "LNBits"},
            {"owner": "fedimint", "repo": "fedimint", "name": "Fedimint"},
            {"owner": "cashubtc", "repo": "nutshell", "name": "Cashu"},
            {"owner": "getAlby", "repo": "lightning-browser-extension", "name": "Alby"},
        ]
    },
    {
        "category": "Exchanges",
        "repos": [
            {"owner": "bisq-network", "repo": "bisq", "name": "Bisq"},
        ]
    },
    {
        "category": "Libraries & Tools",
        "repos": [
            {"owner": "bitcoinj", "repo": "bitcoinj", "name": "bitcoinj"},
            {"owner": "rust-bitcoin", "repo": "rust-bitcoin", "name": "rust-bitcoin", "source": "crates", "crate_name": "bitcoin"},
            {"owner": "bitcoindevkit", "repo": "bdk", "name": "BDK", "source": "crates", "crate_name": "bdk"},
        ]
    },
]

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "data"

# ─── Platform Classification ────────────────────────────────────────────────

PLATFORM_RULES = [
    # Windows
    (lambda n: any(ext in n.lower() for ext in ['.exe', '.msi', '.msix']), 'Windows'),
    (lambda n: 'win64' in n.lower() or 'win32' in n.lower() or 'windows' in n.lower(), 'Windows'),
    # macOS
    (lambda n: any(ext in n.lower() for ext in ['.dmg', '.pkg']), 'macOS'),
    (lambda n: 'darwin' in n.lower() or 'macos' in n.lower() or 'osx' in n.lower(), 'macOS'),
    (lambda n: 'apple' in n.lower(), 'macOS'),
    # Linux
    (lambda n: any(ext in n.lower() for ext in ['.deb', '.rpm', '.appimage', '.snap', '.flatpak']), 'Linux'),
    (lambda n: 'linux' in n.lower(), 'Linux'),
    (lambda n: any(arch in n.lower() for arch in ['x86_64', 'amd64', 'aarch64', 'arm64', 'armv7']), 'Linux'),
    # Source
    (lambda n: any(ext in n.lower() for ext in ['.tar.gz', '.tar.xz', '.tar.bz2', '.zip']) and 'src' in n.lower(), 'Source'),
    (lambda n: 'source' in n.lower(), 'Source'),
    # Verification / Signatures
    (lambda n: any(ext in n.lower() for ext in ['.sig', '.asc', '.sha256', '.sha256sums', '.checksums', '.gpg']), 'Signatures'),
    (lambda n: 'SHASUMS' in n or 'SHA256' in n, 'Signatures'),
]

def classify_platform(asset_name: str) -> str:
    """Classify a release asset into a platform category."""
    for rule, platform in PLATFORM_RULES:
        if rule(asset_name):
            return platform
    return 'Other'


# ─── Data Fetchers ─────────────────────────────────────────────────────────

def github_api_get(url: str) -> dict | list:
    """Make an authenticated (if token available) GET request to GitHub API."""
    token = os.environ.get('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'oss-app-stats/1.0',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            remaining = resp.headers.get('X-RateLimit-Remaining', '?')
            print(f"  ← {resp.status} (rate limit remaining: {remaining})")
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.reason}")
        if e.code == 403:
            print("    → Rate limited. Set GITHUB_TOKEN env var for higher limits.")
        return []

def fetch_github_project(project: dict) -> dict:
    """Fetch and process data for a single GitHub project."""
    owner, repo, name = project['owner'], project['repo'], project['name']
    
    # Fetch Repo Info
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    print(f"  → GET {repo_url}")
    repo_info = github_api_get(repo_url)
    if not repo_info:
        print(f"  ✗ Could not fetch repo info for {owner}/{repo}")
        return None

    # Fetch Releases (Paginated)
    all_releases = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=100&page={page}"
        print(f"  → GET {url}")
        releases = github_api_get(url)
        
        if isinstance(releases, dict):
            if page == 1: return None
            break
        if not releases:
            break
            
        all_releases.extend(releases)
        if len(releases) < 100:
            break
        page += 1
        
    print(f"  ✓ Found {len(all_releases)} releases")
    return process_github_releases(all_releases, repo_info, project)

def fetch_crates_project(project: dict) -> dict:
    """Fetch and process data for a single Crates.io project."""
    crate_name = project['crate_name']
    url = f"https://crates.io/api/v1/crates/{crate_name}"
    
    headers = {'User-Agent': 'oss-app-stats/1.0'}
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

    # Fetch GitHub stats if owner/repo are provided
    github_stars = 0
    github_forks = 0
    github_issues = 0
    github_description = crate.get('description', '')
    if project.get('owner') and project.get('repo'):
        repo_url = f"https://api.github.com/repos/{project['owner']}/{project['repo']}"
        print(f"  → GET {repo_url} (for crates.io stats)")
        repo_info = github_api_get(repo_url)
        if repo_info and isinstance(repo_info, dict):
            github_stars = repo_info.get('stargazers_count', 0)
            github_forks = repo_info.get('forks_count', 0)
            github_issues = repo_info.get('open_issues_count', 0)
            if repo_info.get('description'):
                github_description = repo_info.get('description')

    return {
        'project': {
            'owner': project['owner'],
            'repo': project['repo'],
            'name': project['name'],
            'full_name': f"{project['owner']}/{project['repo']}",
            'description': github_description,
            'stars': github_stars, # Fetched from GitHub if available
            'forks': github_forks,
            'open_issues': github_issues,
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
        'deep_dive': enrich_project_data({'releases': processed_releases})
    }


# ─── Data Processing ────────────────────────────────────────────────────────

def process_github_releases(releases: list[dict], repo_info: dict, project: dict) -> dict:
    """Transform raw API data into our analytics schema."""
    now = datetime.now(timezone.utc)
    processed_releases = []
    total_downloads = 0
    rolling_downloads = 0
    platform_totals = {}

    for rel in releases:
        if not rel.get('tag_name'):
            continue
        
        tag_lower = rel['tag_name'].lower()
        is_rolling = 'latest' in tag_lower

        published = rel.get('published_at') or rel.get('created_at', '')
        assets = []
        release_downloads = 0

        for asset in rel.get('assets', []):
            dl_count = asset.get('download_count', 0)
            platform = classify_platform(asset['name'])
            if not is_rolling:
                assets.append({
                    'name': asset['name'],
                    'size_bytes': asset.get('size', 0),
                    'download_count': dl_count,
                    'platform': platform,
                    'content_type': asset.get('content_type', ''),
                })
            release_downloads += dl_count
            platform_totals[platform] = platform_totals.get(platform, 0) + dl_count

        total_downloads += release_downloads

        if is_rolling:
            rolling_downloads += release_downloads
            continue

        processed_releases.append({
            'tag': rel['tag_name'],
            'name': rel.get('name', rel['tag_name']),
            'published_at': published,
            'is_prerelease': rel.get('prerelease', False),
            'is_draft': rel.get('draft', False),
            'raw_downloads': release_downloads,
            'total_downloads': release_downloads,
            'asset_count': len(assets),
            'assets': assets,
            'body_excerpt': (rel.get('body') or '')[:500],
            'html_url': rel.get('html_url', ''),
            'author': (rel.get('author') or {}).get('login', ''),
        })

    # Sort by published date descending
    processed_releases.sort(
        key=lambda r: r['published_at'] if r['published_at'] else '',
        reverse=True
    )

    # Compute release cadence
    dates = [
        datetime.fromisoformat(r['published_at'].replace('Z', '+00:00'))
        for r in processed_releases
        if r['published_at'] and not r['is_prerelease']
    ]
    cadence_days = None
    if len(dates) >= 2:
        deltas = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
        cadence_days = round(sum(deltas) / len(deltas), 1)

    # Days since latest release
    days_since_latest = None
    if processed_releases and processed_releases[0]['published_at']:
        latest_date = datetime.fromisoformat(
            processed_releases[0]['published_at'].replace('Z', '+00:00')
        )
        days_since_latest = (now - latest_date).days

    data = {
        'project': {
            'owner': project['owner'],
            'repo': project['repo'],
            'name': project['name'],
            'full_name': f"{project['owner']}/{project['repo']}",
            'description': repo_info.get('description', ''),
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'open_issues': repo_info.get('open_issues_count', 0),
            'language': repo_info.get('language', ''),
            'license': (repo_info.get('license') or {}).get('spdx_id', ''),
            'homepage': repo_info.get('homepage', ''),
            'html_url': repo_info.get('html_url', f"https://github.com/{project['owner']}/{project['repo']}"),
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
            'platform_breakdown': platform_totals,
        },
        'releases': processed_releases,
        'fetched_at': now.isoformat(),
    }
    
    data['deep_dive'] = enrich_project_data(data)
    
    return data

def enrich_project_data(data: dict) -> dict:
    """Computes advanced metrics for frontend dashboards."""
    releases = data.get('releases', [])
    if not releases:
        return {}
        
    deep_dive = {}
    
    # Timeline
    sorted_asc = list(reversed(releases))
    first_release = sorted_asc[0]
    latest_release = sorted_asc[-1]
    
    if first_release.get('published_at') and latest_release.get('published_at'):
        first_date = datetime.fromisoformat(first_release['published_at'].replace('Z', '+00:00'))
        latest_date = datetime.fromisoformat(latest_release['published_at'].replace('Z', '+00:00'))
        days_since_launch = max(1, (latest_date - first_date).days)
        deep_dive['days_since_launch'] = days_since_launch
    
    # DAU Proxy & Cadence
    recent_stable = [r for r in releases if not r['is_prerelease']][:12]
    deep_dive['recent_stable_releases'] = recent_stable
    
    dates = [datetime.fromisoformat(r['published_at'].replace('Z', '+00:00')) for r in recent_stable if r.get('published_at')]
    gaps = [(dates[i] - dates[i+1]).total_seconds() / 3600 for i in range(len(dates)-1)]
    
    avg_gap_hours = sum(gaps) / len(gaps) if gaps else 0
    median_gap_hours = sorted(gaps)[len(gaps)//2] if gaps else 0
    
    deep_dive['velocity'] = {
        'avg_gap_hours': round(avg_gap_hours, 1),
        'median_gap_hours': round(median_gap_hours, 1),
    }
    
    return deep_dive


# ─── Main ────────────────────────────────────────────────────────────────────

def fetch_project(project: dict) -> dict:
    name = project['name']
    owner = project['owner']
    repo = project['repo']
    
    print(f"\n{'='*60}")
    print(f"Fetching: {name} ({owner}/{repo})")
    print(f"{'='*60}")
    
    if project.get('source') == 'crates':
        return fetch_crates_project(project)
    else:
        return fetch_github_project(project)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Parse CLI arguments
    filter_repo = None
    filter_category = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--category' and len(sys.argv) > 2:
            filter_category = sys.argv[2]
        else:
            filter_repo = sys.argv[1]  # e.g. "block/buzz"

    all_projects = []
    for category in PROJECTS:
        if filter_category and category['category'] != filter_category:
            continue
        for project in category['repos']:
            full_name = f"{project['owner']}/{project['repo']}"
            if filter_repo and full_name != filter_repo:
                continue
            all_projects.append({**project, 'category': category['category']})

    if not all_projects:
        print(f"No matching projects found for filter: {filter_repo or filter_category}")
        sys.exit(1)

    results = []
    for project in all_projects:
        data = fetch_project(project)
        if data:
            data['category'] = project['category']
            results.append(data)

            # Save individual project file
            filename = f"{project['owner']}_{project['repo']}.json"
            filepath = OUTPUT_DIR / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ Saved → {filepath}")

    # Save combined index
    index = {
        'projects': [],
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_projects': len(results),
    }

    for data in results:
        index['projects'].append({
            'full_name': data['project']['full_name'],
            'name': data['project']['name'],
            'category': data['category'],
            'file': f"{data['project']['owner']}_{data['project']['repo']}.json",
            'total_downloads': data['summary']['total_downloads'],
            'total_releases': data['summary']['total_releases'],
            'latest_version': data['summary']['latest_version'],
            'latest_date': data['summary']['latest_date'],
            'days_since_latest': data['summary']['days_since_latest'],
            'stars': data['project']['stars'],
            'language': data['project']['language'],
            'description': data['project']['description'],
        })

    index_path = OUTPUT_DIR / 'index.json'
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    print(f"\n{'='*60}")
    print(f"✓ Index saved → {index_path}")
    print(f"  {len(results)} projects processed")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
