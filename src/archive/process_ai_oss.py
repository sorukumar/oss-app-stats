import json
import os
from datetime import datetime, timedelta

RAW_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "data", "ai_oss_raw.json")
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "data", "ai_oss.json")

def process_data():
    with open(RAW_FILE, "r") as f:
        raw_data = json.load(f)
        
    processed_data = {}
    
    for repo_name, repo_data in raw_data.items():
        releases = repo_data.get("releases", [])
        if not releases:
            continue
            
        # Find Launch Date (first release > 10k downloads)
        launch_date_str = None
        for r in releases:
            if r["downloads"] > 10000:
                launch_date_str = r["published_at"]
                break
                
        if not launch_date_str:
            print(f"No >10k release found for {repo_name}, skipping.")
            continue
            
        launch_date = datetime.strptime(launch_date_str, "%Y-%m-%dT%H:%M:%SZ")
        end_date = launch_date + timedelta(days=60)
        
        # Calculate daily cumulative metrics for first 60 days
        normalized_series = []
        cumulative_downloads = 0
        cumulative_releases = 0
        
        # We need to map releases to their 'day since launch'
        for day_offset in range(61):
            current_day_end = launch_date + timedelta(days=day_offset + 1)
            
            # Find releases that happened up to this day
            # Since we iterate day by day, we just need to sum up what happened before current_day_end
            # To be precise, we reset and sum to avoid double counting
            cum_dl = 0
            cum_rel = 0
            for r in releases:
                r_date = datetime.strptime(r["published_at"], "%Y-%m-%dT%H:%M:%SZ")
                if launch_date <= r_date < current_day_end:
                    cum_dl += r["downloads"]
                    cum_rel += 1
            
            normalized_series.append({
                "day": day_offset,
                "cumulative_downloads": cum_dl,
                "cumulative_releases": cum_rel
            })
            
        # Calculate Median Gaps for different time horizons
        median_gaps = {}
        for days in range(1, 61):
            horizon_end = launch_date + timedelta(days=days)
            valid_dates = []
            for r in releases:
                r_date = datetime.strptime(r["published_at"], "%Y-%m-%dT%H:%M:%SZ")
                if launch_date <= r_date < horizon_end and not r.get("is_prerelease", False):
                    valid_dates.append(r_date)
                    
            valid_dates.sort()
            
            gap_hours = 0
            if len(valid_dates) > 1:
                gaps = [(valid_dates[i+1] - valid_dates[i]).total_seconds() / 3600 for i in range(len(valid_dates)-1)]
                gaps.sort()
                gap_hours = round(gaps[len(gaps)//2], 1)
            median_gaps[str(days)] = gap_hours
            
        processed_data[repo_name] = {
            "stars": repo_data["stars"],
            "forks": repo_data["forks"],
            "total_releases": repo_data["total_releases"],
            "launch_date": launch_date_str,
            "first_60_days": normalized_series,
            "median_gaps": median_gaps
        }
        
    with open(OUT_FILE, "w") as f:
        json.dump(processed_data, f, indent=2)
        
    print(f"Saved processed data to {OUT_FILE}")

if __name__ == "__main__":
    process_data()
