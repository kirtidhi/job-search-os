import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
from dotenv import load_dotenv

load_dotenv()

from agents.resume_tailor import ResumeTailor
from agents.company_researcher import CompanyResearcher
from agents.strategy_generator import StrategyGenerator
from agents.fit_scorer import FitScorer

urls = [
    ("https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92248?source=LinkedIn", "Product Manager, Platform Capabilities"),
    ("https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92524?source=LinkedIn", "Senior Product Manager, Platform Capabilities") # Assuming the second title based on standard conventions, but we will extract the real one
]

def get_job_info(url, default_title):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        time.sleep(10)
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        
        title_el = soup.find('title')
        title = title_el.get_text() if title_el else default_title
        title = title.split('-')[0].strip()
        
        article = soup.find('article')
        if article:
            desc = article.get_text(separator='\n', strip=True)
        else:
            desc = soup.get_text(separator='\n', strip=True)
            
        page.close()
        browser.close()
        
        return {
            "title": title,
            "company": "Woolworths",
            "url": url,
            "description": desc
        }

def process():
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    base_resume_path = os.getenv("BASE_RESUME_PATH", "base_resume.html")
    
    with open(base_resume_path, 'r') as f:
        base_resume_content = f.read()
        
    resume_tailor = ResumeTailor(base_resume_path, llm_provider=llm_provider)
    researcher = CompanyResearcher(llm_provider=llm_provider)
    strategy_gen = StrategyGenerator(llm_provider=llm_provider)
    
    for url, default_title in urls:
        print(f"Fetching {url}")
        job = get_job_info(url, default_title)
        
        title_safe = re.sub(r'[^\w\-]', '_', job.get('title', 'unknown'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join("output", f"{job.get('company', 'unknown')}_{title_safe}_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processing {job['title']} at {job['company']}")
        
        tailored_resume = resume_tailor.tailor(job, output_dir)
        print(f"Tailored resume saved to {tailored_resume['filename']}")
        
        research_data = researcher.research(job.get('company'))
        
        strategy_docs = strategy_gen.generate(job, research_data, output_dir, base_resume_content)
        print(f"Strategy and Cover Letter generated in {output_dir}")
        print("-" * 50)

if __name__ == "__main__":
    process()
