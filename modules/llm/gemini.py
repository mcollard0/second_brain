import os
import json
from typing import List, Dict, Any
from .base import LLMProvider
from google import genai
from google.genai import types

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-3-flash-preview"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generates a response using the new google-genai SDK.
        """
        try:
            # Prepare configuration
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
            
            # Prepare contents
            # The new SDK accepts a list of Content objects or dicts
            gemini_contents = []
            for msg in messages:
                # Map roles: user -> user, assistant -> model
                role = "user" if msg["role"] == "user" else "model"
                gemini_contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                )

            # Generate content asynchronously
            # Note: `client.aio` is the async client accessor in the new SDK
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=gemini_contents,
                config=config
            )
            
            # Parse JSON response
            return json.loads(response.text)

        except Exception as e:
            print(f"Error generating response from Gemini: {e}")
            return {
                "voice_output": {"text": "I'm having trouble retrieving a response from Gemini."},
                "data_management": {"will_capture": False}
            }
