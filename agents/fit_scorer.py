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

Instead of just doing keyword matching, extract the underlying Semantic Profile of the candidate and the job.

CANDIDATE'S RESUME:
{base_resume[:4000]}

JOB DESCRIPTION TO ANALYZE:
JOB TITLE: {job.get('title')}
COMPANY: {job.get('company')}
LOCATION: {job.get('location')}
{job.get('jd', '')[:4000]}

CANDIDATE'S NON-NEGOTIABLES:
{json.dumps(non_negotiables, indent=2)}

INSTRUCTIONS:
1. First, extract the candidate's Domain and Archetype from the resume above.
2. Compare the Job's Domain (e.g. B2C Travel, B2B Payments, Core Infrastructure) to the Candidate's Domain.
3. Compare the Job's Archetype (e.g. Hands-on Software Engineer vs Product Manager vs Architect) to the Candidate's Archetype.
4. If there is a massive Domain mismatch (e.g. B2C Travel vs B2B Payments) OR an Archetype mismatch (e.g. SWE vs PM), the fit score should drop drastically (below 0.6).
5. Provide a fit score between 0.0 and 1.0.
6. CRITICAL RULE: If the job violates ANY of the Candidate's Non-Negotiables (including location or language requirements), you MUST set "meets_all_non_negotiables" to false AND set "fit_score" to exactly 0.0, regardless of how good the Domain or Archetype match is.

Output your response as raw JSON matching this schema exactly:
{{
  "fit_score": 0.8,
  "reason": "Brief explanation focused on Domain, Archetype alignment, and Non-Negotiables.",
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
