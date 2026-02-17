from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generates a response from the LLM based on the system prompt and conversation history.
        
        Args:
            system_prompt: The system instruction.
            messages: A list of message dictionaries (e.g., [{"role": "user", "content": "..."}]).
            
        Returns:
            A dictionary parsed from the JSON response.
        """
        pass
