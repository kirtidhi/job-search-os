import logging
import os
from providers.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class StrategyGenerator:
    def __init__(self, llm_provider="openai"):
        self.llm = get_llm_provider(llm_provider)

    def generate(self, job, research_data, output_dir, base_resume=""):
        logger.info(f"Generating Cover Letter and Prototype Strategy for {job.get('title')}")
        
        prompt = f"Job Description:\n{job.get('jd', '')[:6000]}\n\nCompany Research:\n{research_data.get('strategy')}\n\nCandidate Resume:\n{base_resume[:3000]}"
        
        # 1. Playbook
        playbook_sys = (
            "You are an expert career strategist. "
            "Given a Job Description and Company Research, output a markdown document containing "
            "an 'Interview Prototype Recommendation' (a specific project to build to impress them)."
        )
        playbook_doc = self.llm.generate(prompt, system_prompt=playbook_sys)
        playbook_path = os.path.join(output_dir, "playbook.md")
        with open(playbook_path, "w") as f:
            f.write(playbook_doc)
            
        # 2. Cover Letter
        cl_sys = (
            "You are an expert career strategist. "
            "Given a Job Description and Company Research, output a highly tailored 'Cover Letter' "
            "that references their strategic initiatives."
        )
        cl_doc = self.llm.generate(prompt, system_prompt=cl_sys)
        cl_path = os.path.join(output_dir, "cover_letter.md")
        with open(cl_path, "w") as f:
            f.write(cl_doc)
            
        return {
            "playbook": playbook_path,
            "cover_letter": cl_path
        }
