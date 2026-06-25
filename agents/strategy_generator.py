import logging
from providers.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class StrategyGenerator:
    def __init__(self, llm_provider="openai"):
        self.llm = get_llm_provider(llm_provider)

    def generate(self, job, research_data):
        logger.info(f"Generating Cover Letter and Prototype Strategy for {job.get('title')}")
        
        system_prompt = (
            "You are an expert career strategist. "
            "Given a Job Description and Company Research, output a markdown document containing: "
            "1. An 'Interview Prototype Recommendation' (a specific project to build to impress them). "
            "2. A highly tailored 'Cover Letter' that references their strategic initiatives."
        )
        
        prompt = f"Job Description:\n{job.get('jd')}\n\nCompany Research:\n{research_data.get('strategy')}"
        
        strategy_doc = self.llm.generate(prompt, system_prompt=system_prompt)
        
        filename = f"strategy_{job.get('title').replace(' ', '_')}.md"
        with open(filename, "w") as f:
            f.write(strategy_doc)
            
        return {"content": strategy_doc, "filename": filename}
