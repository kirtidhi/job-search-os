import os
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-5.5"):
        import openai
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "claude-opus-4-8"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        if system_prompt:
            kwargs["system"] = system_prompt
            
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-pro-latest"):
        from google import genai
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        return response.text

class MockProvider(LLMProvider):
    def __init__(self, **kwargs):
        pass
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if "fit_score" in prompt or "non-negotiables" in prompt.lower():
            return '{"fit_score": 0.9, "reason": "Mock fit.", "meets_all_non_negotiables": true}'
            
        if system_prompt and "JSON" in system_prompt:
            return '{"fit_score": 0.9, "reason": "Perfect mock fit.", "meets_all_non_negotiables": true}'
        
        if system_prompt and "HTML" in system_prompt:
            return "<html><body><h1>Mock Tailored Resume</h1></body></html>"
            
        if system_prompt and "Interview Prototype" in system_prompt:
            return "# Mock Playbook\nThis is a mock strategy playbook."
            
        if system_prompt and "Cover Letter" in system_prompt:
            return "# Mock Cover Letter\nThis is a mock cover letter."
            
        # fallback
        return '{"strategy": "Mock strategy research"}'

def get_llm_provider(provider_name: str, **kwargs) -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_name == "anthropic" or provider_name == "claude":
        return AnthropicProvider(**kwargs)
    elif provider_name == "gemini" or provider_name == "google":
        return GeminiProvider(**kwargs)
    elif provider_name == "mock":
        return MockProvider(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
