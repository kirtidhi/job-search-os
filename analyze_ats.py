import json
import requests
import concurrent.futures

with open('config.json', 'r') as f:
    config = json.load(f)

companies = [c.lower().replace(" ", "").replace("&", "").replace("-", "").replace(".", "") for c in config['target_companies']]

# From ats_landscape.md we know greenhouse/lever are ~32.
# Let's just check all for Workday and iCIMS.

def check_workday(company):
    for wd in ['wd1', 'wd3', 'wd5']:
        url = f"https://{company}.{wd}.myworkdayjobs.com/"
        try:
            res = requests.head(url, timeout=3, allow_redirects=True)
            if res.status_code in [200, 301, 302]:
                return f"Workday ({wd})"
        except:
            pass
    return None

def check_icims(company):
    urls = [
        f"https://careers-{company}.icims.com/",
        f"https://{company}.icims.com/"
    ]
    for url in urls:
        try:
            res = requests.head(url, timeout=3, allow_redirects=True)
            if res.status_code in [200, 301, 302]:
                return "iCIMS"
        except:
            pass
    return None

def analyze(company):
    wd = check_workday(company)
    if wd: return (company, wd)
    icims = check_icims(company)
    if icims: return (company, icims)
    return (company, "Unknown/Paid API")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(analyze, companies))

wd_count = sum(1 for c, r in results if 'Workday' in r)
icims_count = sum(1 for c, r in results if 'iCIMS' in r)
unknown_count = sum(1 for c, r in results if 'Unknown' in r)

print(f"Workday: {wd_count}")
print(f"iCIMS: {icims_count}")
print(f"Unknown (Fallback to Paid API): {unknown_count}")
