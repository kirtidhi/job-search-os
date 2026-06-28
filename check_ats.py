import json
import requests
import re
from concurrent.futures import ThreadPoolExecutor

with open('config.json', 'r') as f:
    config = json.load(f)

companies = config['target_companies']

def normalize_name(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def check_ats(company):
    norm_name = normalize_name(company)
    
    # Try Greenhouse
    gh_url = f"https://boards-api.greenhouse.io/v1/boards/{norm_name}/jobs"
    try:
        r = requests.get(gh_url, timeout=5)
        if r.status_code == 200 and 'jobs' in r.json():
            return company, "Greenhouse", gh_url
    except:
        pass
        
    # Try Lever
    lever_url = f"https://api.lever.co/v0/postings/{norm_name}"
    try:
        r = requests.get(lever_url, timeout=5)
        if r.status_code == 200 and isinstance(r.json(), list):
            return company, "Lever", lever_url
    except:
        pass

    # For workday, the URL format isn't standard, but we can do a quick check via Google search or standard guessing
    # Actually, let's just return Unknown for the rest for now and we can manually check or use search for the remaining.
    return company, "Unknown / Other", ""

print("Checking ATS for companies...")
results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    for res in executor.map(check_ats, companies):
        results.append(res)

for company, ats, url in sorted(results, key=lambda x: (x[1], x[0])):
    print(f"{company}: {ats} ({url})")

with open('ats_report.json', 'w') as f:
    json.dump([{'company': c, 'ats': a, 'url': u} for c, a, u in results], f, indent=2)
