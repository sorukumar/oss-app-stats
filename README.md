# 📊 OSS App Stats

**[View the Dashboard](https://sorukumar.github.io/oss-app-stats/)**

Release intelligence and download analytics for Bitcoin open source projects — wallets, Lightning implementations, core infrastructure, libraries, and Block open source projects.

---

## 🍊 The Orange Dev Suite

This project is part of the **Orange Dev Suite**, a comprehensive, open-source analytical ecosystem designed to provide forensic transparency into Bitcoin research and development:

1. **[Orange Dev Tracker](https://tracker.bitcoindatalabs.org)**: The "What" and "Where" — a dashboard focused on the architectural evolution of Bitcoin Core.
2. **[Orange Dev Network](https://network.bitcoindatalabs.org)**: The "Who" and "How" — a technical influence map of Bitcoin R&D contributors.
3. **[This Week in Bitcoin (TWIB)](https://twib.bitcoindatalabs.org)**: The "Now" — an automated weekly executive summary of Bitcoin development.
4. **[OSS App Stats](https://sorukumar.github.io/oss-app-stats/)**: The "How Much" — release analytics and adoption intelligence across the Bitcoin open source ecosystem.

---

## 📈 What We Track

| Category | Projects |
|---|---|
| **Block Open Source** | Goose, Buzz |
| **Core Infrastructure** | Bitcoin Core, BTCPay Server |
| **Wallets** | Sparrow Wallet, Electrum |
| **Lightning** | LND, Core Lightning, Eclair, LDK |
| **Libraries & Tools** | Bisq, bitcoinj, rust-bitcoin |

### Metrics

- **Download counts** per release, per platform (Windows/macOS/Linux)
- **Release cadence** — how often each project ships
- **Freshness scores** — how recently each project released
- **Platform breakdown** — which OSes each project targets
- **Cross-project comparisons** — leaderboard and charts

---

## 🛠️ How It Works

1. **Data Pipeline** (`src/fetch_releases.py`): Python script that fetches release data from the GitHub API and saves structured JSON files.
2. **Static Frontend** (`docs/`): Reads the JSON files and renders an analytics dashboard with Chart.js visualizations.
3. **Hosted on GitHub Pages** from the `docs/` directory.

### Running the Data Pipeline

```bash
# Fetch all projects
python3 src/fetch_releases.py

# Fetch a single project
python3 src/fetch_releases.py block/buzz

# Fetch a category
python3 src/fetch_releases.py --category "Block Open Source"
```

Set `GITHUB_TOKEN` environment variable for higher API rate limits (5000 req/hr vs 60 req/hr).

---

*Created by [Bitcoin Data Labs](https://bitcoindatalabs.org) as a contribution to the transparency of the Bitcoin open source ecosystem.*
