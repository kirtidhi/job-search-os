import json
from scrapers.ats_scraper import ATSScraper

with open('config.json', 'r') as f:
    config = json.load(f)

scraper = ATSScraper(
    target_companies=config.get("target_companies", []),
    role_preferences=config.get("roles", []),
    locations=config.get("locations", [])
)

jobs = scraper.get_matching_jobs()
print("Found jobs:", len(jobs))
for job in jobs:
    print(job.get('company'), job.get('title'), job.get('url'))
