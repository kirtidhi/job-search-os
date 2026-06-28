import logging
from playwright.sync_api import sync_playwright
import re

logger = logging.getLogger(__name__)

from scrapers.base_scraper import BaseScraper

class HeadlessScraper(BaseScraper):
    def __init__(self, target_companies, role_preferences, locations):
        super().__init__(target_companies, role_preferences, locations)



    def _search_for_careers_url(self, page, company):
        """Use Playwright to search DuckDuckGo for the company's careers site."""
        import urllib.parse
        try:
            logger.info(f"Searching web for {company} careers URL...")
            page.goto(f"https://html.duckduckgo.com/html/?q={company}+careers+myworkdayjobs+OR+icims")
            
            # Extract links from DuckDuckGo HTML results
            results = page.query_selector_all("a.result__url")
            for result in results:
                url = result.get_attribute("href")
                if url:
                    # DuckDuckGo wraps links in a redirect
                    if "uddg=" in url:
                        parsed = urllib.parse.urlparse(url)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if "uddg" in qs:
                            url = qs["uddg"][0]
                            
                    if "myworkdayjobs.com" in url or "icims.com" in url:
                        logger.info(f"Found ATS URL via web search: {url}")
                        return url
                        
            logger.info(f"Could not find Workday/iCIMS URL via web search for {company}.")
            return None
        except Exception as e:
            logger.error(f"Web search failed for {company}: {e}")
            return None

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
                try:
                    page = browser.new_page()
                    
                    for company in self.target_companies:
                        norm_company = company.lower()
                        target_url = known_urls.get(norm_company)
                        
                        if not target_url:
                            # Attempt web search if not mapped
                            target_url = self._search_for_careers_url(page, company)
                            
                        if target_url:
                            logger.info(f"Headless Scraper running for {company} at {target_url}...")
                            # Simulate fetching and parsing the ATS page
                            try:
                                page.goto(target_url, wait_until="domcontentloaded")
                                # ... parse with BeautifulSoup/Playwright ...
                                # If successful, mark as processed so it doesn't fall to Paid API
                                # processed_companies.append(company) # Commented out so it falls through to Paid API
                            except Exception as e:
                                logger.error(f"Failed to scrape {target_url}: {e}")
                        else:
                            logger.info(f"Skipping {company} - will fallback to Paid API.")
                finally:
                    browser.close()
        except Exception as e:
            logger.error(f"Headless Scraper encountered an error: {e}")
            
        return matched_jobs, processed_companies
