"""
Multi-provider LLM service supporting Ollama, OpenAI, and Groq.
Allows switching between local (Ollama) and cloud (OpenAI/Groq) providers.
"""
import logging
from typing import List
from abc import ABC, abstractmethod
import httpx
import asyncio
import config

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str,
        is_validation: bool = False
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available."""
        pass
    
    def _build_troubleshooting_prompt(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str
    ) -> str:
        """Build a troubleshooting prompt."""
        context_text = "\n\n".join([
            f"[{i+1}] {chunk}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        return f"""You are an industrial maintenance expert. Provide DETAILED troubleshooting steps from the manual context below.

CONTEXT FROM MANUAL:
{context_text}

QUESTION: {question}

INSTRUCTIONS:
- Provide AT LEAST 5-8 detailed troubleshooting steps
- Include safety warnings if mentioned in context
- Specify tools or parts needed
- Explain what to check and why
- Use numbered steps format
- Be thorough and complete

DETAILED ANSWER:"""


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider - handles concurrency natively."""
    
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.model = config.OPENAI_MODEL
        self.timeout = config.OPENAI_TIMEOUT
        self.base_url = "https://api.openai.com/v1"
        logger.info(f"OpenAI provider initialized (model: {self.model})")
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str,
        is_validation: bool = False
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            # Build prompt
            if is_validation:
                prompt = question
            else:
                prompt = self._build_troubleshooting_prompt(question, context_chunks, manual_id)
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful industrial maintenance assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            logger.info(f"Sending request to OpenAI ({self.model})...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            logger.info(f"OpenAI response received ({len(answer)} chars)")
            return answer
        
        except httpx.TimeoutException:
            logger.error("OpenAI request timed out")
            return "Request timed out. Please try again."
        
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                return "OpenAI API key is invalid. Please check config.py"
            return f"OpenAI API error: {e.response.status_code}"
        
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check OpenAI API availability."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False


class GroqProvider(BaseLLMProvider):
    """Groq provider - extremely fast inference with Llama models."""
    
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.model = config.GROQ_MODEL
        self.timeout = config.GROQ_TIMEOUT
        self.base_url = "https://api.groq.com/openai/v1"
        logger.info(f"Groq provider initialized (model: {self.model})")
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str,
        is_validation: bool = False
    ) -> str:
        """Generate response using Groq API."""
        try:
            if is_validation:
                prompt = question
            else:
                prompt = self._build_troubleshooting_prompt(question, context_chunks, manual_id)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful industrial maintenance assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            logger.info(f"Sending request to Groq ({self.model})...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            logger.info(f"Groq response received ({len(answer)} chars)")
            return answer
        
        except httpx.TimeoutException:
            logger.error("Groq request timed out")
            return "Request timed out. Please try again."
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq HTTP error: {e.response.status_code}")
            if e.response.status_code == 401:
                return "Groq API key is invalid. Please check config.py"
            return f"Groq API error: {e.response.status_code}"
        
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check Groq API availability."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Groq health check failed: {e}")
            return False


class OllamaProvider(BaseLLMProvider):
    """Ollama provider - local, free, but sequential processing."""
    
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        logger.info(f"Ollama provider initialized (model: {self.model})")
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str,
        is_validation: bool = False
    ) -> str:
        """Generate response using Ollama."""
        try:
            if is_validation:
                prompt = question
            else:
                prompt = self._build_troubleshooting_prompt(question, context_chunks, manual_id)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1500,  # Increased for more detailed steps
                    "num_ctx": 1024,  # Reduced to free memory for concurrent users
                    "repeat_penalty": 1.1  # Reduced to allow more detailed explanation
                }
            }
            
            logger.info(f"Sending request to Ollama ({self.model})...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "").strip()
            logger.info(f"Ollama response received ({len(answer)} chars)")
            return answer if answer else "No response generated"
        
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return "Ollama timed out. Try a smaller model or increase timeout."
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            return "Ollama service unavailable. Please ensure it's running."
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Ollama error: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check Ollama availability."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


class OllamaMultiProvider(BaseLLMProvider):
    """Multiple Ollama instances with load balancing - local + concurrent."""
    
    def __init__(self):
        self.instances = config.OLLAMA_INSTANCES
        self.timeout = config.OLLAMA_TIMEOUT
        self.current_index = 0
        self.instance_locks = [asyncio.Lock() for _ in self.instances]
        logger.info(f"OllamaMulti provider initialized with {len(self.instances)} instances")
        for i, inst in enumerate(self.instances):
            logger.info(f"  Instance {i+1}: {inst['url']} (model: {inst['model']})")
    
    async def _send_to_instance(self, instance_idx: int, prompt: str) -> str:
        """Send request to a specific Ollama instance."""
        instance = self.instances[instance_idx]
        
        payload = {
            "model": instance["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 400,
                "num_ctx": 2048,
                "repeat_penalty": 1.2
            }
        }
        
        async with self.instance_locks[instance_idx]:
            logger.info(f"Sending to instance {instance_idx+1} ({instance['url']})...")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{instance['url']}/api/generate",
                    json=payload
                )
                response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "").strip()
            logger.info(f"Instance {instance_idx+1} responded ({len(answer)} chars)")
            return answer
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        manual_id: str,
        is_validation: bool = False
    ) -> str:
        """Generate response using round-robin load balancing across instances."""
        try:
            if is_validation:
                prompt = question
            else:
                prompt = self._build_troubleshooting_prompt(question, context_chunks, manual_id)
            
            # Round-robin: try instances in order
            for attempt in range(len(self.instances)):
                instance_idx = (self.current_index + attempt) % len(self.instances)
                
                try:
                    answer = await self._send_to_instance(instance_idx, prompt)
                    # Update index for next request
                    self.current_index = (instance_idx + 1) % len(self.instances)
                    return answer if answer else "No response generated"
                
                except Exception as e:
                    logger.warning(f"Instance {instance_idx+1} failed: {e}")
                    continue
            
            # All instances failed
            return "All Ollama instances unavailable. Please check services."
        
        except Exception as e:
            logger.error(f"OllamaMulti error: {e}")
            return f"Error: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check if at least one instance is available."""
        for instance in self.instances:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{instance['url']}/api/tags")
                    if response.status_code == 200:
                        return True
            except Exception:
                continue
        return False


# Global LLM service instance
_llm_service = None


def get_llm_service() -> BaseLLMProvider:
    """Get or create the LLM service based on configured provider."""
    global _llm_service
    if _llm_service is None:
        provider = config.LLM_PROVIDER.lower()
        
        if provider == "openai":
            _llm_service = OpenAIProvider()
        elif provider == "groq":
            _llm_service = GroqProvider()
        elif provider == "ollama-multi":
            _llm_service = OllamaMultiProvider()
        elif provider == "ollama":
            _llm_service = OllamaProvider()
        else:
            logger.warning(f"Unknown provider '{provider}', defaulting to Ollama")
            _llm_service = OllamaProvider()
        
        logger.info(f"LLM service initialized: {provider}")
    
    return _llm_service
