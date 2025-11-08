"""
Base agent class for Ollama-powered agents.
"""
import json
import requests
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from agents.config import OLLAMA_ENDPOINT


class OllamaAgent(ABC):
    """Base class for all Ollama-powered agents."""
    
    def __init__(self, model: str, role: str, temperature: float = 0.1):
        """
        Initialize an Ollama agent.
        
        Args:
            model: Ollama model name (e.g., "phi3:mini")
            role: Human-readable role description
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
        """
        self.endpoint = OLLAMA_ENDPOINT
        self.model = model
        self.role = role
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []
    
    def call_llm(self, prompt: str, format: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Call Ollama with the prompt.
        
        Args:
            prompt: User prompt to send to the LLM
            format: Optional format ("json" for JSON response)
            system_prompt: Optional override for system prompt
            
        Returns:
            Dict containing response content or parsed JSON
        """
        url = f"{self.endpoint}/api/chat"
        
        # Build messages
        messages = []
        
        # Add system prompt if provided or use default
        system = system_prompt or self.get_system_prompt()
        if system:
            messages.append({"role": "system", "content": system})
        
        # Add conversation history if maintained
        if self.should_maintain_history():
            messages.extend(self.conversation_history)
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        
        if format:
            payload["format"] = format
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # Maintain conversation history if enabled
            if self.should_maintain_history():
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": content})
            
            # Parse JSON if requested
            if format == "json":
                if not content or not content.strip():
                    raise RuntimeError(
                        f"{self.role} agent returned empty response. "
                        f"This may indicate:\n"
                        f"1. Ollama is overloaded or slow to respond\n"
                        f"2. The model is having trouble with the prompt\n"
                        f"3. Network/connection issues\n\n"
                        f"Try: Restart Ollama or use Single-Agent mode."
                    )
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            pass
                    
                    # Try to find any JSON object in the response
                    json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            pass
                    
                    raise RuntimeError(
                        f"{self.role} agent returned invalid JSON.\n\n"
                        f"Response preview:\n{content[:500]}\n\n"
                        f"Error: {e}\n\n"
                        f"This usually means the LLM is having trouble with structured output. "
                        f"Try using Single-Agent mode instead."
                    )
            
            return {"content": content}
            
        except requests.Timeout:
            raise RuntimeError(
                f"{self.role} agent timed out after 60 seconds. "
                f"Ollama may be overloaded. Try again or use Single-Agent mode."
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"{self.role} agent API call failed: {e}\n\n"
                f"Make sure Ollama is running: ollama serve"
            )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for this agent.
        Each agent must define its own specialized system prompt.
        """
        pass
    
    def should_maintain_history(self) -> bool:
        """
        Whether this agent should maintain conversation history.
        Override to True for agents that benefit from context (like orchestrator).
        """
        return False
    
    def reset_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "role": self.role,
            "model": self.model,
            "temperature": self.temperature,
            "maintains_history": self.should_maintain_history(),
            "history_length": len(self.conversation_history)
        }
