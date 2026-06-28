from playwright.sync_api import sync_playwright
import time
import json

urls = [
    "https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92248?source=LinkedIn"
]

def extract():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for url in urls:
            page = browser.new_page()
            print(f"Navigating to {url}")
            page.goto(url, wait_until='networkidle')
            time.sleep(10)  # Wait extra for JS
            
            with open("woolworths_page.html", "w") as f:
                f.write(page.content())
                
            page.close()
        browser.close()

if __name__ == "__main__":
    extract()
