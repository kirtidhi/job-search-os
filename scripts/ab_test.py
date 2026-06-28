import json
import logging
from dotenv import load_dotenv
load_dotenv()

from scrapers.ats_scraper import ATSScraper
from providers.llm_provider import get_llm_provider

with open('config.json', 'r') as f:
    config = json.load(f)

logging.basicConfig(level=logging.INFO)

# Let's test on a few high-signal companies for speed and visibility
test_companies = ["Adyen", "Airbnb", "Anthropic", "Stripe"]

scraper = ATSScraper(
    target_companies=test_companies,
    role_preferences=config.get("roles", []),
    locations=config.get("locations", [])
)

jobs = scraper.get_matching_jobs()
print(f"Fetched {len(jobs)} jobs for A/B testing...")

with open(config.get("base_resume_path", "base_resume.html"), "r") as f:
    base_resume = f.read()

llm = get_llm_provider("gemini")

def score_job_a(job, non_negotiables, resume):
    prompt = f"""
You are an expert technical recruiter analyzing a job description against a candidate's non-negotiables and resume.

JOB TITLE: {job.get('title')}
COMPANY: {job.get('company')}
LOCATION: {job.get('location')}

JOB DESCRIPTION:
{job.get('jd', '')[:4000]}

CANDIDATE'S NON-NEGOTIABLES:
{json.dumps(non_negotiables, indent=2)}

CANDIDATE'S RESUME:
{resume[:4000]}

Analyze the job description and evaluate how well it matches the candidate's non-negotiables AND their resume background.
Provide a fit score between 0.0 and 1.0 (where 1.0 is a perfect fit, and 0.0 is a terrible fit).
Output your response as raw JSON matching this schema exactly:
{{
  "fit_score": 0.8,
  "reason": "Brief explanation of why it fits or fails",
  "meets_all_non_negotiables": true
}}
"""
    response = llm.generate(prompt)
    if "```json" in response: response = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response: response = response.split("```")[1].split("```")[0].strip()
    return json.loads(response)

def score_job_b(job, non_negotiables, resume):
    prompt = f"""
You are an expert technical recruiter analyzing a job description against a candidate's non-negotiables and resume.

Instead of just doing keyword matching, extract the underlying Semantic Profile of the candidate and the job.

CANDIDATE'S RESUME:
{resume[:4000]}

Based on the resume, the candidate is a Product Manager / Solutions Architect specializing in:
- Domain: Payments, FinTech, Identity, AdTech, B2B Enterprise APIs
- Archetype: Product Manager, Pre-Sales, Solutions Architecture

JOB DESCRIPTION TO ANALYZE:
JOB TITLE: {job.get('title')}
COMPANY: {job.get('company')}
LOCATION: {job.get('location')}
{job.get('jd', '')[:4000]}

CANDIDATE'S NON-NEGOTIABLES:
{json.dumps(non_negotiables, indent=2)}

INSTRUCTIONS:
1. Compare the Job's Domain (e.g. B2C Travel, B2B Payments, Core Infrastructure) to the Candidate's Domain.
2. Compare the Job's Archetype (e.g. Hands-on Software Engineer vs Product Manager vs Architect) to the Candidate's Archetype.
3. If there is a massive Domain mismatch (e.g. B2C Travel vs B2B Payments) OR an Archetype mismatch (e.g. SWE vs PM), the fit score should drop drastically (below 0.6).
4. Provide a fit score between 0.0 and 1.0.

Output your response as raw JSON matching this schema exactly:
{{
  "fit_score": 0.8,
  "reason": "Brief explanation focused on Domain and Archetype alignment",
  "meets_all_non_negotiables": true
}}
"""
    response = llm.generate(prompt)
    if "```json" in response: response = response.split("```json")[1].split("```")[0].strip()
    elif "```" in response: response = response.split("```")[1].split("```")[0].strip()
    return json.loads(response)

# Run the test
results = []
for job in jobs[:10]: # Limit to 10 for speed
    print(f"Scoring: {job.get('company')} - {job.get('title')}")
    try:
        res_a = score_job_a(job, config.get("non_negotiables", []), base_resume)
        res_b = score_job_b(job, config.get("non_negotiables", []), base_resume)
        
        results.append({
            "title": job.get("title"),
            "company": job.get("company"),
            "score_a": res_a.get("fit_score"),
            "reason_a": res_a.get("reason"),
            "score_b": res_b.get("fit_score"),
            "reason_b": res_b.get("reason")
        })
    except Exception as e:
        print(f"Error scoring {job.get('title')}: {e}")

# Save results
md_content = "# Semantic Scorer A/B Test Results\n\n"
md_content += "| Company | Job Title | Part A (Current) Score | Part B (Semantic) Score |\n"
md_content += "|---|---|---|---|\n"

for r in results:
    md_content += f"| {r['company']} | {r['title']} | {r['score_a']} | {r['score_b']} |\n"

md_content += "\n## Detailed Reasons\n\n"
for r in results:
    md_content += f"### {r['company']} - {r['title']}\n"
    md_content += f"**Part A Score:** {r['score_a']}\n"
    md_content += f"**Part A Reason:** {r['reason_a']}\n\n"
    md_content += f"**Part B Score:** {r['score_b']}\n"
    md_content += f"**Part B Reason:** {r['reason_b']}\n\n"
    md_content += "---\n\n"

with open("ab_test_results.md", "w") as f:
    f.write(md_content)

print("A/B test completed. Results saved to ab_test_results.md")
