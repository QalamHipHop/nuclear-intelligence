
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from core.llm_engine import LLMEngine, PROVIDERS

def diagnose():
    print("🔍 Diagnosing LLM Providers...")
    
    # Print environment status
    for name, provider in PROVIDERS.items():
        key = os.getenv(provider.api_key_env)
        status = "✅ Set" if key and len(key) > 5 else "❌ Not Set"
        print(f"Provider {name:12}: {status} ({provider.api_key_env})")

    engine = LLMEngine()
    print(f"\nAvailable providers in engine: {engine._available_providers}")
    
    if not engine._available_providers:
        print("❌ No providers available. Check your .env file or environment variables.")
        return

    test_prompt = "Hello, respond with the word 'SUCCESS' if you can hear me."
    
    for provider in engine._available_providers:
        print(f"\nTesting {provider}...")
        try:
            # Force specific provider for testing
            engine._current_provider_name = None
            # We need a way to test a specific provider. 
            # Temporarily modify engine to test one by one.
            original_chain = engine._available_providers
            engine._available_providers = [provider]
            
            response = engine.chat(test_prompt, max_tokens=10)
            if response and "SUCCESS" in response.upper():
                print(f"✅ {provider} is WORKING")
            else:
                print(f"⚠️ {provider} returned unexpected response: {response}")
        except Exception as e:
            print(f"❌ {provider} FAILED: {str(e)}")
        finally:
            engine._available_providers = original_chain

if __name__ == "__main__":
    diagnose()
