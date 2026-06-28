import os
import sys
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from orchestrator import JobSearchOS

def fetch_woolworths_job(url):
    print(f"Fetching {url}")
    # Fake user agent to ensure the ATS allows scraping
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Extract title
    title_element = soup.find('h1') or soup.find('title')
    title = title_element.get_text(strip=True) if title_element else "Woolworths Group Job"
    if '|' in title:
         title = title.split('|')[0].strip()
         
    # Extract location if possible (optional)
    
    # Extract jd
    jd_text = soup.get_text(separator='\n', strip=True)
    
    return {
        "company": "Woolworths Group",
        "title": title,
        "url": url,
        "location": "Australia",
        "jd": jd_text
    }

def process_manual_jobs():
    urls = [
        "https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92248?source=LinkedIn",
        "https://careers.woolworthsgroup.com.au/en_GB/apply/JobDetail/92524?source=LinkedIn"
    ]
    
    os_instance = JobSearchOS()
    
    with open(os_instance.base_resume_path, 'r') as f:
        base_resume_content = f.read()

    for url in urls:
        print(f"Processing manual URL: {url}")
        try:
            job = fetch_woolworths_job(url)
            
            # Step 1: Fit Scoring
            fit_data = os_instance.fit_scorer.score_fit(job, os_instance.non_negotiables, base_resume_content)
            print(f"Fit Score: {fit_data['score']} - {fit_data['reason']}")
            
            title_safe = re.sub(r'[^\w\-]', '_', job.get('title', 'unknown'))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join("output", f"WoolworthsGroup_{title_safe}_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 2: Tailor Resume
            print("Tailoring resume...")
            tailored_resume = os_instance.resume_tailor.tailor(job, output_dir)
            
            # Step 3: Research
            print("Researching company...")
            research_data = os_instance.researcher.research(job.get('company'))
            
            # Step 4: Strategy Gen
            print("Generating strategy...")
            strategy_docs = os_instance.strategy_gen.generate(job, research_data, output_dir, base_resume_content)
            
            # Step 5: Workspace Sync
            print("Syncing to workspace...")
            os_instance.workspace.sync(
                job, 
                tailored_resume['filename'], 
                strategy_docs['playbook'], 
                strategy_docs['cover_letter'], 
                fit_data
            )
            
            # Step 6: Update State Manager
            os_instance.state_manager.mark_seen(job.get('url'), job.get('company'), job.get('title'), fit_data['score'], 'PROCESSED')
            
            print(f"Successfully processed {url}\n")
        except Exception as e:
            print(f"Failed to process {url}: {e}")

if __name__ == "__main__":
    process_manual_jobs()
