import os
import json
from typing import List, Dict, Any
from .base import LLMProvider
from openai import AsyncOpenAI

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Combine system prompt with messages? Or use 'developer' role for o1 models?
            # Standard gpt-4 expects 'system' role.
            
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=full_messages,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            print(f"Error generating response from OpenAI: {e}")
            return {
                "voice_output": {"text": "I'm having trouble connecting to OpenAI."},
                "data_management": {"will_capture": False}
            }
