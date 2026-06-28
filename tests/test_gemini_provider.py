import sys
sys.path.append('.')
from providers.llm_provider import get_llm_provider

try:
    provider = get_llm_provider("gemini")
    print("Testing gemini provider...")
    response = provider.generate("Say 'Hello world' and nothing else.")
    print("Response:", response)
except Exception as e:
    print("Error:", e)
