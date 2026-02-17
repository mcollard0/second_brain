import os
import json
from typing import List, Dict, Any
from .base import LLMProvider
import anthropic

class AnthropicProvider(LLMProvider):
    def __init__(self, model_name: str = "claude-3-opus-20240229"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model_name = model_name

    async def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Prepare messages (strip empty system messages if present, Anthropic handles system prompt separately)
            # Ensure "user", "assistant" roles are correct.
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                # Force JSON object generation? Not explicitly supported as a mode like OpenAI/Gemini yet, 
                # but models are good at compliance. We rely on the prompt instructing JSON.
            )
            
            content = response.content[0].text
            # Basic JSON extraction if markdown wrap is present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            return json.loads(content)

        except Exception as e:
            print(f"Error generating response from Anthropic: {e}")
            return {
                "voice_output": {"text": "I'm having trouble connecting to Anthropic."},
                "data_management": {"will_capture": False}
            }
