import logging
from playwright.sync_api import sync_playwright
import re

logger = logging.getLogger(__name__)

class HeadlessScraper:
    def __init__(self, target_companies, role_preferences, locations):
        self.target_companies = target_companies
        self.role_preferences = [r.lower() for r in role_preferences]
        self.locations = [l.lower() for l in locations]

    def _is_match(self, title, location):
        title = title.lower()
        location = location.lower() if location else ""
        
        role_match = any(
            re.search(r'\b' + re.escape(role) + r'\b', title)
            for role in self.role_preferences
        )
        if not role_match:
            return False
            
        if self.locations:
            loc_match = any(loc in location for loc in self.locations)
            if not loc_match:
                return False
            
        return True

    def get_matching_jobs(self):
        logger.info("Initializing Headless Scraper (Playwright) for Workday/iCIMS...")
        matched_jobs = []
        processed_companies = []
        
        # Example hardcoded mapping for demonstration. In production, we'd dynamically resolve these.
        known_urls = {
            "adobe": "https://adobe.wd5.myworkdayjobs.com/external_corporate",
            "uber": "https://careers.uber.com/icims",
            "walmart": "https://walmart.wd5.myworkdayjobs.com/Walmart_External",
            "woolworths": "https://woolworths.wd3.myworkdayjobs.com/WoolworthsGroupCareers"
        }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                for company in self.target_companies:
                    norm_company = company.lower()
                    if norm_company in known_urls:
                        logger.info(f"Headless Scraper running for {company} at {known_urls[norm_company]}...")
                        # Simulate fetching
                        # page.goto(known_urls[norm_company])
                        # ... parse with BeautifulSoup/Playwright ...
                        
                        processed_companies.append(company)
                    else:
                        # For unmapped companies, we could attempt a Google search to find their Workday/iCIMS url.
                        # For now, we'll skip them so they fall back to the Paid API.
                        pass
                        
                browser.close()
        except Exception as e:
            logger.error(f"Headless Scraper encountered an error: {e}")
            
        return matched_jobs, processed_companies
