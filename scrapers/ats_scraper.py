import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ATSScraper:
    def __init__(self, target_companies, role_preferences, locations):
        self.target_companies = target_companies
        self.role_preferences = [r.lower() for r in role_preferences]
        self.locations = [l.lower() for l in locations]

    def _fetch_from_greenhouse(self, company):
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json().get('jobs', []), 'greenhouse'
        except Exception as e:
            logger.warning(f"Greenhouse fetch failed for {company}: {e}")
        return [], None

    def _fetch_from_lever(self, company):
        url = f"https://api.lever.co/v0/postings/{company}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json(), 'lever'
        except Exception as e:
            logger.warning(f"Lever fetch failed for {company}: {e}")
        return [], None

    def _is_match(self, title, location):
        title = title.lower()
        location = location.lower() if location else ""
        
        # Check if role matches
        role_match = any(role in title for role in self.role_preferences)
        if not role_match:
            return False
            
        # Check if location matches
        loc_match = any(loc in location for loc in self.locations)
        if not loc_match:
            return False
            
        return True

    def _fetch_jd_text(self, url):
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Very basic text extraction
            return soup.get_text(separator='\\n', strip=True)
        except Exception as e:
            logger.error(f"Failed to fetch JD text for {url}: {e}")
            return ""

    def get_matching_jobs(self):
        logger.info("Fetching jobs from configured ATS sources...")
        all_matched_jobs = []
        
        for company in self.target_companies:
            logger.info(f"Checking {company}...")
            
            jobs, ats_type = self._fetch_from_greenhouse(company)
            if not jobs:
                jobs, ats_type = self._fetch_from_lever(company)
                
            for job in jobs:
                if ats_type == 'greenhouse':
                    title = job.get('title', '')
                    location = job.get('location', {}).get('name', '')
                    url = job.get('absolute_url', '')
                elif ats_type == 'lever':
                    title = job.get('text', '')
                    location = job.get('categories', {}).get('location', '')
                    url = job.get('hostedUrl', '')
                else:
                    continue
                    
                if self._is_match(title, location):
                    logger.info(f"Found match: {title} at {company}")
                    jd_text = self._fetch_jd_text(url)
                    all_matched_jobs.append({
                        "company": company.capitalize(),
                        "title": title,
                        "url": url,
                        "location": location,
                        "jd": jd_text
                    })
                    
        return all_matched_jobs
