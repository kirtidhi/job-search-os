import logging
import json
from scrapers.ats_scraper import ATSScraper

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as f:
    config = json.load(f)

# Only use the 32 known working companies to speed up the test
working_companies = [
    "Adyen", "Airbnb", "Anthropic", "Block", "Brex", "Coinbase", 
    "Databricks", "Datadog", "Disney", "Dropbox", "Epic Games", 
    "Figma", "Gusto", "HubSpot", "IonQ", "LinkedIn", "Mercury", 
    "Mixmax", "MongoDB", "Okta", "Pinterest", "Scale AI", 
    "Stripe", "Twilio", "Unilever", "Atlassian", "KPMG", 
    "Netflix", "Oliver Wyman", "Palantir", "Plaid", "Spotify"
]

# Bypass JD fetching to make it extremely fast just to get the list
def mock_fetch(*args, **kwargs):
    return ""

ATSScraper._fetch_jd_text = mock_fetch
ATSScraper._fetch_jd_from_greenhouse_api = mock_fetch

scraper = ATSScraper(
    target_companies=working_companies,
    role_preferences=config.get("roles", []),
    locations=config.get("locations", [])
)

jobs = scraper.get_matching_jobs()
print("Found matching jobs:", len(jobs))

with open('matching_jobs.md', 'w') as f:
    f.write("# Matching Jobs from Greenhouse & Lever\n\n")
    current_company = ""
    for job in sorted(jobs, key=lambda x: (x.get('company', ''), x.get('title', ''))):
        company = job.get('company')
        if company != current_company:
            f.write(f"## {company}\n")
            current_company = company
        f.write(f"- [{job.get('title')}]({job.get('url')})\n")

