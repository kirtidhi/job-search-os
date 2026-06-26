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
    def __init__(self, api_key: str = None, model: str = "gemini-3.1-pro"):
        from google import genai
        from google.genai import types
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

def get_llm_provider(provider_name: str, **kwargs) -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_name == "anthropic" or provider_name == "claude":
        return AnthropicProvider(**kwargs)
    elif provider_name == "gemini" or provider_name == "google":
        return GeminiProvider(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
