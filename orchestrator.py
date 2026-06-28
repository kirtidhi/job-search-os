import sys
import os
import json
import time
import schedule
import logging
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pipeline modules
from scrapers.ats_scraper import ATSScraper
from agents.resume_tailor import ResumeTailor
from agents.company_researcher import CompanyResearcher
from agents.strategy_generator import StrategyGenerator
from agents.fit_scorer import FitScorer
from utils.workspace_sync import WorkspaceManager
from utils.state_manager import StateManager

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
        
        # Load user config
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logger.critical("config.json not found. Create it from config.example.json and restart.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.critical(f"config.json is malformed: {e}. Fix the JSON syntax and restart.")
            sys.exit(1)
            
        self.non_negotiables = config.get("non_negotiables", [])
        self.fit_threshold = config.get("fit_threshold", 0.6)

        logger.info(f"Initializing JobSearchOS with LLM Provider: {self.llm_provider.upper()}")
        
        # Initialize Modules
        self.scraper = ATSScraper(
            target_companies=config.get("target_companies", []),
            role_preferences=config.get("roles", []),
            locations=config.get("locations", [])
        )
        self.resume_tailor = ResumeTailor(self.base_resume_path, llm_provider=self.llm_provider)
        self.researcher = CompanyResearcher(llm_provider=self.llm_provider)
        self.strategy_gen = StrategyGenerator(llm_provider=self.llm_provider)
        self.fit_scorer = FitScorer(llm_provider=self.llm_provider)
        self.workspace = WorkspaceManager(self.tracker_sheet_id)
        self.state_manager = StateManager()

    def run_daily_pipeline(self, step="all"):
        logger.info(f"=== Starting Job Search OS Pipeline (Step: {step}) ===")
        
        try:
            with open(self.base_resume_path, 'r') as f:
                base_resume_content = f.read()
        except FileNotFoundError:
            logger.critical(f"Base resume not found at '{self.base_resume_path}'. Set BASE_RESUME_PATH and restart.")
            return
            
        roles_to_process = []
        pending_roles_file = "pending_roles.json"

        if step in ["all", "interim"]:
            # 1. Ingestion & Filtering
            jobs = self.scraper.get_matching_jobs()
            if not jobs:
                logger.info("No new matching jobs found today.")
                logger.info("=== Pipeline Completed ===")
                return
                
            companies_found = len(set(job.get('company') for job in jobs))
            logger.info(f"Interim Stage: Found {len(jobs)} roles across {companies_found} companies.")

            roles_to_process = []
            filtered_out_roles = []
                
            for job in jobs:
                try:
                    # 1.5 State Store Check
                    if not self.state_manager.is_new_role(job.get('url')):
                        logger.info(f"Skipping already processed role: {job.get('title')} at {job.get('company')}")
                        continue
                        
                    logger.info(f"Processing Role: {job.get('title')} at {job.get('company')}")
                    
                    # 1.6 Semantic Fit Scoring
                    fit_data = self.fit_scorer.score_fit(job, self.non_negotiables, base_resume_content)
                    logger.info(f"Fit Score: {fit_data['score']} - {fit_data['reason']}")
                    
                    if fit_data['score'] < self.fit_threshold:
                        logger.info(f"Role rejected due to low fit score (< {self.fit_threshold}).")
                        self.state_manager.mark_seen(job.get('url'), job.get('company'), job.get('title'), fit_data['score'], 'REJECTED')
                        filtered_out_roles.append({"job": job, "fit_data": fit_data})
                        continue
                    
                    roles_to_process.append({"job": job, "fit_data": fit_data})
                except Exception as e:
                    logger.error(f"Error scoring {job.get('title')}: {str(e)}")
                    
            # --- INTERIM REPORT ---
            report_content = f"# Interim Pipeline Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report_content += f"**Total Roles Found:** {len(jobs)}\n"
            report_content += f"**Companies Searched:** {companies_found}\n"
            
            # Add ATS processing breakdown
            from scrapers.ats_scraper import ATSScraper
            total_companies = len(self.scraper.target_companies)
            report_content += f"\n## ATS Processing Breakdown\n"
            report_content += f"We processed {total_companies} companies across our pipeline tiers.\n"
            report_content += f"- **Tier 1 (API - Greenhouse/Lever):** ~25-30 companies.\n"
            report_content += f"- **Tier 2A (Headless - Workday/iCIMS):** Attempted for companies not supported by APIs.\n"
            report_content += f"- **Tier 2B (Paid API Fallback):** Processed the remaining proprietary platforms.\n\n"
            report_content += f"> **Notice regarding Paid API Quota:** We will use the free API quota first (e.g. 100 free searches). If we need to run it extensively again, we might ask you to provide an API key for the commercial scraper.\n\n"

            report_content += f"**Roles Proceeding to Generation:** {len(roles_to_process)}\n"
            report_content += f"**Roles Filtered Out:** {len(filtered_out_roles)}\n\n"
            
            non_negotiable_failures = [r for r in filtered_out_roles if not r['fit_data'].get('meets_all', True)]
            if non_negotiable_failures:
                report_content += "## Filtered Due to Non-Negotiables\n"
                for r in non_negotiable_failures:
                    report_content += f"- **{r['job'].get('company')} - {r['job'].get('title')}**: {r['fit_data'].get('reason')}\n"
                report_content += "\n"

            other_failures = [r for r in filtered_out_roles if r['fit_data'].get('meets_all', True)]
            if other_failures:
                report_content += "## Filtered Due to Low Fit Score (Domain/Archetype)\n"
                for r in other_failures:
                    report_content += f"- **{r['job'].get('company')} - {r['job'].get('title')}**: {r['fit_data'].get('reason')}\n"
                report_content += "\n"

            with open("interim_report.md", "w") as f:
                f.write(report_content)
            
            logger.info(f"Interim report generated: interim_report.md. Proceeding to asset generation for {len(roles_to_process)} roles.")

            # --- INTERIM APPROVAL STAGE ---
            with open(pending_roles_file, "w") as f:
                json.dump(roles_to_process, f, indent=2)
                
            logger.info(f"Saved pending roles to {pending_roles_file}.")
            logger.info("ACTION REQUIRED: Please review interim_report.md.")
            
            if step == "interim":
                logger.info("Step 'interim' completed. Exiting. Run with '--step generate' to resume.")
                return
                
            # Pause for user approval if running 'all' interactively
            if sys.stdin.isatty():
                user_input = input("\nPress Enter to approve and proceed to Stage 2 (Asset Generation), or type 'cancel' to stop: ")
                if user_input.strip().lower() == 'cancel':
                    logger.info("Pipeline cancelled by user.")
                    return
            else:
                logger.info("Running in non-interactive mode. Proceeding automatically to generation...")
            
    if step in ["all", "generate"]:
        # Re-load roles after potential user modifications
        try:
            with open(pending_roles_file, "r") as f:
                roles_to_process = json.load(f)
            logger.info(f"Resuming with {len(roles_to_process)} roles for generation.")
        except Exception as e:
            logger.error(f"Could not load {pending_roles_file}: {e}. Aborting generation.")
            return

        # --- ASSET GENERATION ---
        for item in roles_to_process:
            job = item["job"]
            fit_data = item["fit_data"]
            try:
                # 1.7 Create Output Directory
                title_safe = re.sub(r'[^\w\-]', '_', job.get('title', 'unknown'))
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = os.path.join("output", f"{job.get('company', 'unknown')}_{title_safe}_{timestamp}")
                os.makedirs(output_dir, exist_ok=True)
                
                # 2. Core Asset Tailoring
                tailored_resume = self.resume_tailor.tailor(job, output_dir)
                
                # 3. Deep Company Research
                research_data = self.researcher.research(job.get('company'))
                
                # 4. Strategic Generation
                strategy_docs = self.strategy_gen.generate(job, research_data, output_dir, base_resume_content)
                
                # 5. Workspace Sync
                self.workspace.sync(job, tailored_resume['filename'], strategy_docs['playbook'], strategy_docs['cover_letter'], fit_data)
                
                # Mark as processed in state
                self.state_manager.mark_seen(job.get('url'), job.get('company'), job.get('title'), fit_data['score'], 'PROCESSED')
                
                logger.info(f"Successfully processed {job.get('title')} at {job.get('company')}")
                
            except Exception as e:
                logger.error(f"Error processing {job.get('title')}: {str(e)}")
                
        logger.info("=== Pipeline Completed ===")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JobSearchOS Orchestrator")
    parser.add_argument("--step", choices=["all", "interim", "generate"], default="all", help="Which step to run")
    parser.add_argument("--scheduled", action="store_true", help="Run in scheduled background mode")
    args = parser.parse_args()

    os_instance = JobSearchOS()
    
    if args.scheduled:
        logger.info("Running initial startup execution...")
        os_instance.run_daily_pipeline(step="all")
        
        # Schedule the job to run every day at 9:00 AM
        schedule.every().day.at("09:00").do(os_instance.run_daily_pipeline, step="all")
        
        logger.info("Job Search OS is now scheduled and running in the background.")
        logger.info("Waiting for next execution time...")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        os_instance.run_daily_pipeline(step=args.step)

if __name__ == "__main__":
    main()
