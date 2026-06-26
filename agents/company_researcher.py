import logging
from providers.llm_provider import get_llm_provider
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

logger = logging.getLogger(__name__)

class CompanyResearcher:
    def __init__(self, llm_provider="openai"):
        self.llm = get_llm_provider(llm_provider)

    def research(self, company_name):
        logger.info(f"Conducting strategic research on {company_name}")
        
        search_results = ""
        if DDGS:
            try:
                results = DDGS().text(f"{company_name} recent news strategic initiatives product launches", max_results=5)
                for r in results:
                    search_results += f"Title: {r.get('title')}\nSnippet: {r.get('body')}\n\n"
            except Exception as e:
                logger.warning(f"Live search failed: {e}")
                search_results = "Live search failed. Rely on training data."
        else:
            search_results = "Live search disabled (duckduckgo-search not installed)."

        system_prompt = (
            "You are a top-tier corporate strategist. "
            "Provide a concise summary of the most recent strategic initiatives, product launches, "
            "and market focus for the given company based on the provided search results."
        )
        
        prompt = f"Company: {company_name}\n\nRecent Search Results:\n{search_results}\n\nProvide strategic research summary."
        
        strategy = self.llm.generate(prompt, system_prompt=system_prompt)
        
        return {"strategy": strategy}
