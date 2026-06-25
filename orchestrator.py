import os
import time
import schedule
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pipeline modules
from scrapers.ats_scraper import ATSScraper
from agents.resume_tailor import ResumeTailor
from agents.company_researcher import CompanyResearcher
from agents.strategy_generator import StrategyGenerator
from utils.workspace_sync import WorkspaceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JobSearchOS")


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

class JobSearchOS:
    def __init__(self):
        # Configuration
        self.tracker_sheet_id = os.getenv("TRACKER_SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
        self.base_resume_path = os.getenv("BASE_RESUME_PATH", "base_resume.html")
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        logger.info(f"Initializing JobSearchOS with LLM Provider: {self.llm_provider.upper()}")
        
        # Initialize Modules
        self.scraper = ATSScraper(
            target_companies=["Stripe", "Anthropic", "Google"],
            role_preferences=["Product Manager", "Solutions Architect", "AI Engineer"]
        )
        self.resume_tailor = ResumeTailor(self.base_resume_path, llm_provider=self.llm_provider)
        self.researcher = CompanyResearcher(llm_provider=self.llm_provider)
        self.strategy_gen = StrategyGenerator(llm_provider=self.llm_provider)
        self.workspace = WorkspaceManager(self.tracker_sheet_id)

    def run_daily_pipeline(self):
        logger.info("=== Starting Job Search OS Daily Pipeline ===")
        
        # 1. Ingestion & Filtering
        jobs = self.scraper.get_matching_jobs()
        if not jobs:
            logger.info("No new matching jobs found today.")
            logger.info("=== Pipeline Completed ===")
            return
            
        for job in jobs:
            try:
                logger.info(f"Processing Role: {job.get('title')} at {job.get('company')}")
                
                # 2. Core Asset Tailoring
                tailored_resume = self.resume_tailor.tailor(job)
                
                # 3. Deep Company Research
                research_data = self.researcher.research(job.get('company'))
                
                # 4. Strategic Generation
                strategy_doc = self.strategy_gen.generate(job, research_data)
                
                # 5. Workspace Sync
                self.workspace.sync(job, tailored_resume, strategy_doc)
                
                logger.info(f"Successfully processed {job.get('title')} at {job.get('company')}")
                
            except Exception as e:
                logger.error(f"Error processing {job.get('title')}: {str(e)}")
                
        logger.info("=== Pipeline Completed ===")


def main():
    os_instance = JobSearchOS()
    
    # Optional: Run immediately once on startup
    logger.info("Running initial startup execution...")
    os_instance.run_daily_pipeline()
    
    # Schedule the job to run every day at 9:00 AM
    schedule.every().day.at("09:00").do(os_instance.run_daily_pipeline)
    
    logger.info("Job Search OS is now scheduled and running in the background.")
    logger.info("Waiting for next execution time...")
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
