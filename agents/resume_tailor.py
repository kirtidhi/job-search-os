import logging
import os
from providers.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class ResumeTailor:
    def __init__(self, base_resume_path, llm_provider="openai"):
        self.base_resume_path = base_resume_path
        self.llm = get_llm_provider(llm_provider)

    def tailor(self, job, output_dir):
        logger.info(f"Tailoring resume for {job.get('title')} at {job.get('company')}")
        
        # Load base resume
        try:
            with open(self.base_resume_path, 'r') as f:
                base_resume = f.read()
        except FileNotFoundError:
            logger.critical(f"Base resume not found at '{self.base_resume_path}'.")
            raise
            
        system_prompt = (
            "You are an expert technical recruiter and resume writer. "
            "Given a base HTML resume and a job description, tailor the resume. "
            "Highlight removed content in <span style='color:red;text-decoration:line-through'>red strikethrough</span> "
            "and new content in <span style='color:blue'>blue</span>. Return ONLY valid HTML."
        )
        
        prompt = f"Job Description:\n{job.get('jd')}\n\nBase Resume:\n{base_resume}"
        
        tailored_html = self.llm.generate(prompt, system_prompt=system_prompt)
        
        tailored_html = tailored_html.strip()
        if tailored_html.startswith("```"):
            tailored_html = tailored_html.split('\n', 1)[1]
        if tailored_html.endswith("```"):
            tailored_html = tailored_html.rsplit('\n', 1)[0]
            
        filename = os.path.join(output_dir, "resume.html")
        with open(filename, "w") as f:
            f.write(tailored_html)
            
        return {"content": tailored_html, "filename": filename}
