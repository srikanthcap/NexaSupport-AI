# =============================================================
# NexaSupport AI — LLM Client
# =============================================================
# PURPOSE:
#   A thin, provider-agnostic wrapper around LLM APIs.
#   Currently supports Google Gemini. Designed to easily add OpenAI.
#
# CONCEPT — Why a wrapper?
#   Each LLM provider has its own SDK, method names, and response formats.
#   By wrapping them here, the rest of the system (pipeline.py, agent, etc.)
#   never needs to care which provider is being used — they just call:
#       response = llm.generate(prompt)
#   This is the "strategy pattern" — swap the strategy (LLM provider)
#   without changing the code that uses it.
#
# HOW IT FITS:
#   prompt_builder.py → [this file] → pipeline.py → API response
# =============================================================

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from loguru import logger

from app.config import settings


@dataclass
class LLMResponse:
    """
    A standardized response from any LLM provider.
    
    Attributes:
        text          : The generated answer text.
        model         : The model name that was used.
        provider      : 'gemini' or 'openai'.
        prompt_tokens : Approximate input token count (if available).
        output_tokens : Approximate output token count (if available).
        finish_reason : Why generation stopped ('stop', 'max_tokens', etc.).
    """
    text: str
    model: str
    provider: str
    prompt_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"


class LLMClient:
    """
    Provider-agnostic LLM client.
    
    Selects the backend (Gemini or OpenAI) based on settings.LLM_PROVIDER.
    
    Usage:
        client = LLMClient()
        response = client.generate("What is Error 809 in VPN?")
        print(response.text)
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._client = None
        self._model = None
        self._init_client()

    def _init_client(self):
        """Initialize the LLM client for the configured provider."""
        if self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{self.provider}'. "
                "Choose 'gemini' or 'openai' in your .env file."
            )

    def _init_gemini(self):
        """Configure Google Gemini API client."""
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing from your .env file. "
                "Get a free key at: https://aistudio.google.com/app/apikey"
            )
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            )
            
            self._client = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=generation_config,
            )
            self._model = settings.GEMINI_MODEL
            logger.info(f"✅ Gemini LLM client initialized: {self._model}")
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

    def _init_openai(self):
        """Configure OpenAI API client."""
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is missing from your .env file."
            )
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self._model = "gpt-4o-mini"  # Fast, cost-effective model
            logger.info(f"✅ OpenAI LLM client initialized: {self._model}")
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")

    def generate(self, prompt: str) -> LLMResponse:
        """
        Send a prompt to the configured LLM and return a standardized response.
        
        Args:
            prompt: The complete prompt string (built by prompt_builder.py).
        
        Returns:
            LLMResponse with the generated text and metadata.
        
        Raises:
            RuntimeError: If the API call fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Cannot generate a response for an empty prompt.")

        logger.debug(f"Sending prompt to {self.provider} ({self._model}): {len(prompt)} chars")

        if self.provider == "gemini":
            return self._generate_gemini(prompt)
        elif self.provider == "openai":
            return self._generate_openai(prompt)

    def _generate_gemini(self, prompt: str) -> LLMResponse:
        """Call Gemini API and return standardized response."""
        try:
            response = self._client.generate_content(prompt)
            
            # Extract text — Gemini may sometimes return empty responses if blocked
            if not response.parts:
                # Response was blocked by Gemini safety filters
                return LLMResponse(
                    text=(
                        "I'm unable to generate a response for this query. "
                        "Please rephrase your question or contact IT Helpdesk directly."
                    ),
                    model=self._model,
                    provider="gemini",
                    finish_reason="safety",
                )
            
            text = response.text.strip()
            
            # Extract token usage if available
            prompt_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

            logger.debug(
                f"Gemini response: {len(text)} chars, "
                f"~{prompt_tokens} prompt tokens, ~{output_tokens} output tokens"
            )

            return LLMResponse(
                text=text,
                model=self._model,
                provider="gemini",
                prompt_tokens=prompt_tokens,
                output_tokens=output_tokens,
                finish_reason="stop",
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API call failed: {e}") from e

    def _generate_openai(self, prompt: str) -> LLMResponse:
        """Call OpenAI API and return standardized response."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            
            choice = response.choices[0]
            text = choice.message.content.strip()
            
            return LLMResponse(
                text=text,
                model=self._model,
                provider="openai",
                prompt_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API call failed: {e}") from e


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """
    Return a cached singleton LLMClient instance.
    
    Initializing the LLM client involves API configuration — we only
    want to do this once per application process.
    
    Usage (anywhere in the project):
        from app.rag.llm_client import get_llm_client
        client = get_llm_client()
    """
    return LLMClient()
