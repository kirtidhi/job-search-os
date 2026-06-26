import json
import logging
from providers.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

class FitScorer:
    def __init__(self, llm_provider='openai'):
        self.llm = get_llm_provider(llm_provider)

    def score_fit(self, job: dict, non_negotiables: list, base_resume: str) -> dict:
        prompt = f"""
You are an expert technical recruiter analyzing a job description against a candidate's non-negotiables and resume.

JOB TITLE: {job.get('title')}
COMPANY: {job.get('company')}
LOCATION: {job.get('location')}

JOB DESCRIPTION:
{job.get('jd')[:4000]}

CANDIDATE'S NON-NEGOTIABLES:
{json.dumps(non_negotiables, indent=2)}

CANDIDATE'S RESUME:
{base_resume[:4000]}

Analyze the job description and evaluate how well it matches the candidate's non-negotiables AND their resume background.
Provide a fit score between 0.0 and 1.0 (where 1.0 is a perfect fit, and 0.0 is a terrible fit).
Output your response as raw JSON matching this schema exactly:
{{
  "fit_score": 0.8,
  "reason": "Brief explanation of why it fits or fails",
  "meets_all_non_negotiables": true
}}
"""
        try:
            response = self.llm.generate(prompt)
            # Simple JSON cleanup in case LLM wraps in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            return {
                "score": float(result.get("fit_score", 0.0)),
                "reason": result.get("reason", ""),
                "meets_all": result.get("meets_all_non_negotiables", False)
            }
        except Exception as e:
            logger.error(f"Error scoring fit for {job.get('title')}: {e}")
            return {"score": 0.0, "reason": f"Error during scoring: {e}", "meets_all": False}
