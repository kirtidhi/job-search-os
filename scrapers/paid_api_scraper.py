import logging
import os
import requests
import re

logger = logging.getLogger(__name__)

class PaidAPIScraper:
    def __init__(self, target_companies, role_preferences, locations):
        self.target_companies = target_companies
        self.role_preferences = [r.lower() for r in role_preferences]
        self.locations = [l.lower() for l in locations]
        self.api_key = os.getenv("SERPAPI_API_KEY")

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
        logger.info(f"Initializing Paid API Scraper for {len(self.target_companies)} remaining companies...")
        matched_jobs = []
        
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY is not set. Paid API Scraper will return no results.")
            return matched_jobs
            
        for company in self.target_companies:
            logger.info(f"Paid API Scraper attempting to fetch jobs for: {company}")
            for role in self.role_preferences:
                try:
                    params = {
                        "engine": "google_jobs",
                        "q": f"{role} at {company}",
                        "hl": "en",
                        "api_key": self.api_key
                    }
                    response = requests.get("https://serpapi.com/search", params=params, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        jobs_results = data.get("jobs_results", [])
                        for job in jobs_results:
                            title = job.get("title", "")
                            location = job.get("location", "")
                            company_name = job.get("company_name", company)
                            
                            # Google Jobs usually has a link in job.get("share_link") or applying links
                            apply_options = job.get("apply_options", [])
                            url = apply_options[0].get("link") if apply_options else job.get("share_link", "")
                            
                            jd = job.get("description", "")
                            
                            if self._is_match(title, location):
                                matched_jobs.append({
                                    "company": company_name,
                                    "title": title,
                                    "location": location,
                                    "url": url,
                                    "jd": jd
                                })
                    else:
                        logger.error(f"SerpApi returned status code {response.status_code} for {company}")
                except Exception as e:
                    logger.error(f"Paid API Scraper failed for {company}: {e}")
            
        return matched_jobs
