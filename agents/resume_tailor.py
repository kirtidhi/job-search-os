import logging
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
            base_resume = "<html><body>Placeholder base resume. Please set BASE_RESUME_PATH.</body></html>"
            
        system_prompt = (
            "You are an expert technical recruiter and resume writer. "
            "Given a base HTML resume and a job description, tailor the resume. "
            "Highlight removed content in <span style='color:red;text-decoration:line-through'>red strikethrough</span> "
            "and new content in <span style='color:blue'>blue</span>. Return ONLY valid HTML."
        )
        
        prompt = f"Job Description:\n{job.get('jd')}\n\nBase Resume:\n{base_resume}"
        
        tailored_html = self.llm.generate(prompt, system_prompt=system_prompt)
        
        # Strip markdown formatting if present
        if tailored_html.startswith("```html"):
            tailored_html = tailored_html[7:-3]
            
        import os
        filename = os.path.join(output_dir, "resume.html")
        with open(filename, "w") as f:
            f.write(tailored_html)
            
        return {"content": tailored_html, "filename": filename}
