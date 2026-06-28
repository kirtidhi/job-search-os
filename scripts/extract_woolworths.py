from playwright.sync_api import sync_playwright
import time
import json

urls = [
    "https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92248?source=LinkedIn",
    "https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92524?source=LinkedIn"
]

def extract():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for url in urls:
            page = browser.new_page()
            print(f"Navigating to {url}")
            page.goto(url)
            time.sleep(5)  # Wait for JS
            
            title_el = page.query_selector("h1")
            title = title_el.inner_text() if title_el else "Unknown Title"
            
            # The job description is usually in an element with class jobDescription or article
            desc_el = page.query_selector(".job-description") or page.query_selector(".job-details") or page.query_selector("article")
            if not desc_el:
                desc_el = page.query_selector("body")
                
            desc = desc_el.inner_text() if desc_el else "No description"
            
            results.append({
                "url": url,
                "company": "Woolworths",
                "title": title,
                "description": desc
            })
            page.close()
        browser.close()
    
    with open("woolworths_jobs.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved to woolworths_jobs.json")

if __name__ == "__main__":
    extract()
