"""LangChain LLM client wrapper with multi-provider support."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult
from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation).

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ≈ 4 characters for English, 1 token ≈ 2 chars for Asian languages
    # Use conservative estimate
    char_count = len(text)
    # Average: 1 token per 3 characters
    return max(1, char_count // 3)


class TokenBucketTPM:
    """Token bucket rate limiter for Tokens Per Minute (TPM) control.

    Uses sliding window to track token usage over the last 60 seconds.
    Automatically waits when TPM limit is exceeded.
    """

    def __init__(self, tokens_per_minute: int) -> None:
        """Initialize TPM rate limiter.

        Args:
            tokens_per_minute: Maximum tokens allowed per minute.
        """
        self.tpm = tokens_per_minute
        self._window: deque[tuple[float, int]] = deque()  # (timestamp, tokens)
        self._lock = asyncio.Lock()
        self._window_seconds = 60.0

    def _cleanup_window(self, current_time: float) -> None:
        """Remove entries older than the sliding window.

        Args:
            current_time: Current timestamp.
        """
        cutoff = current_time - self._window_seconds
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()

    def _get_current_usage(self) -> int:
        """Get total token usage within current window.

        Returns:
            Total tokens used in the last 60 seconds.
        """
        return sum(tokens for _, tokens in self._window)

    def _get_wait_time(self, required_tokens: int) -> float:
        """Calculate wait time until tokens become available.

        Args:
            required_tokens: Number of tokens needed.

        Returns:
            Seconds to wait (0 if tokens are available).
        """
        if not self._window:
            return 0.0

        current_usage = self._get_current_usage()
        available = self.tpm - current_usage

        if required_tokens <= available:
            return 0.0

        # Find when enough tokens will expire
        tokens_to_free = required_tokens - available
        freed = 0
        current_time = time.monotonic()

        for timestamp, tokens in self._window:
            freed += tokens
            if freed >= tokens_to_free:
                # Wait until this entry expires
                wait_time = (timestamp + self._window_seconds) - current_time
                return max(0.0, wait_time + 0.1)  # Add 100ms buffer

        # Need to wait for entire window to clear
        oldest_timestamp = self._window[0][0]
        return max(0.0, (oldest_timestamp + self._window_seconds) - current_time + 0.1)

    async def acquire(self, estimated_tokens: int) -> None:
        """Acquire permission to use tokens, waiting if necessary.

        Args:
            estimated_tokens: Estimated number of tokens for the request.
        """
        async with self._lock:
            current_time = time.monotonic()
            self._cleanup_window(current_time)

            wait_time = self._get_wait_time(estimated_tokens)
            if wait_time > 0:
                current_usage = self._get_current_usage()
                logger.info(
                    "TPM limit reached (%.0f/%d). Waiting %.1f seconds...",
                    current_usage,
                    self.tpm,
                    wait_time,
                )

        # Wait outside the lock to allow other operations
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            # Re-acquire lock and re-check after waiting
            async with self._lock:
                current_time = time.monotonic()
                self._cleanup_window(current_time)

    def record_usage(self, actual_tokens: int) -> None:
        """Record actual token usage after a request completes.

        Args:
            actual_tokens: Actual number of tokens used.
        """
        # Use asyncio.run_coroutine_threadsafe if called from sync context
        # For now, we'll use a simple sync approach since callbacks are async
        current_time = time.monotonic()
        self._window.append((current_time, actual_tokens))

        current_usage = self._get_current_usage()
        logger.debug(
            "TPM usage recorded: +%d tokens (total: %d/%d)",
            actual_tokens,
            current_usage,
            self.tpm,
        )

    def get_status(self) -> dict[str, float | int]:
        """Get current TPM status.

        Returns:
            Dictionary with current usage, limit, and available tokens.
        """
        current_time = time.monotonic()
        self._cleanup_window(current_time)
        current_usage = self._get_current_usage()

        return {
            "current_tokens": current_usage,
            "limit_tokens": self.tpm,
            "available_tokens": max(0, self.tpm - current_usage),
            "utilization_percent": (current_usage / self.tpm) * 100
            if self.tpm > 0
            else 0,
        }


class TokenUsageCallback(AsyncCallbackHandler):
    """Callback handler to track token usage."""

    def __init__(
        self,
        usage_callback: object | None = None,
        enable_estimation: bool = True,
        tpm_limiter: TokenBucketTPM | None = None,
    ) -> None:
        """Initialize token usage callback.

        Args:
            usage_callback: Optional callback function(input_tokens, output_tokens, total_tokens)
            enable_estimation: Enable token estimation if provider doesn't report usage
            tpm_limiter: Optional TPM rate limiter to record usage to
        """
        super().__init__()
        self.usage_callback = usage_callback
        self.enable_estimation = enable_estimation
        self._tpm_limiter = tpm_limiter
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self._last_prompt = ""

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Track token usage when LLM call completes.

        Args:
            response: LLM response with usage metadata
            **kwargs: Additional arguments
        """
        input_tokens = 0
        output_tokens = 0
        total = 0

        # Debug: Log response structure
        logger.debug(
            "LLM response - llm_output keys: %s, generations count: %d",
            list(response.llm_output.keys()) if response.llm_output else "None",
            len(response.generations) if response.generations else 0,
        )

        # Try multiple locations for token usage data
        # Method 1: Check ALL generations for usage_metadata (Google, newer LangChain)
        # 모든 generation을 순회하며 토큰 합산 - Google Gemini는 이 방식 사용
        found_tokens = False
        if response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "message") and hasattr(
                        gen.message, "usage_metadata"
                    ):
                        usage_metadata = gen.message.usage_metadata
                        if usage_metadata:
                            # Google uses "input_tokens" and "output_tokens"
                            input_tokens += usage_metadata.get(
                                "input_tokens", 0
                            ) or usage_metadata.get("prompt_tokens", 0)
                            output_tokens += usage_metadata.get(
                                "output_tokens", 0
                            ) or usage_metadata.get("completion_tokens", 0)
                            found_tokens = True

        if found_tokens:
            total = input_tokens + output_tokens

        # Method 2: response.llm_output["token_usage"] (OpenAI, Anthropic)
        elif response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0) or usage.get(
                "output_tokens", 0
            )
            total = usage.get("total_tokens", input_tokens + output_tokens)

        # Method 3: response.llm_output["usage"] (some providers)
        elif response.llm_output and "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0) or usage.get(
                "output_tokens", 0
            )
            total = usage.get("total_tokens", input_tokens + output_tokens)

        # If we got token data, update counters
        if total > 0 or input_tokens > 0 or output_tokens > 0:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_tokens += total

            # Record to TPM limiter for rate limiting
            if self._tpm_limiter is not None and total > 0:
                self._tpm_limiter.record_usage(total)

            logger.debug(
                "Token usage: +%d input, +%d output, +%d total (%d)",
                input_tokens,
                output_tokens,
                total,
                self.total_tokens,
            )

            if self.usage_callback:
                try:
                    self.usage_callback(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total,
                        cumulative_input=self.total_input_tokens,
                        cumulative_output=self.total_output_tokens,
                        cumulative_total=self.total_tokens,
                    )
                except Exception as e:
                    logger.warning("Token usage callback failed: %s", e)
        elif self.enable_estimation and self._last_prompt:
            # Fallback: Estimate tokens if provider doesn't report (e.g., Ollama)
            input_tokens = estimate_tokens(self._last_prompt)

            # Estimate output tokens from response
            if response.generations and len(response.generations) > 0:
                gen = response.generations[0]
                if len(gen) > 0:
                    response_text = str(
                        gen[0].text if hasattr(gen[0], "text") else gen[0]
                    )
                    output_tokens = estimate_tokens(response_text)

            total = input_tokens + output_tokens

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_tokens += total

            # Record to TPM limiter for rate limiting (estimated)
            if self._tpm_limiter is not None and total > 0:
                self._tpm_limiter.record_usage(total)

            logger.debug(
                "Token usage (estimated): +%d input, +%d output, +%d total (累積: %d)",
                input_tokens,
                output_tokens,
                total,
                self.total_tokens,
            )

            if self.usage_callback:
                try:
                    self.usage_callback(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total,
                        cumulative_input=self.total_input_tokens,
                        cumulative_output=self.total_output_tokens,
                        cumulative_total=self.total_tokens,
                    )
                except Exception as e:
                    logger.warning("Token usage callback failed: %s", e)
        else:
            # Log for debugging - no token usage found
            logger.debug("No token usage data found in LLM response")

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        """Store prompt for token estimation.

        Args:
            serialized: Serialized LLM
            prompts: Input prompts
            **kwargs: Additional arguments
        """
        if prompts:
            self._last_prompt = "\n".join(prompts)

    def reset(self) -> None:
        """Reset cumulative token counts."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMConfig(BaseModel):
    """Configuration for LLM client."""

    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "qwen2.5:14b"
    temperature: float = 0.1
    max_tokens: int | None = None
    base_url: str | None = None  # For Ollama custom URL
    api_key: str | None = None  # For cloud providers

    # Concurrency settings
    max_concurrent: int = 15
    timeout: float = 120.0

    # Rate limiting settings
    # requests_per_minute: None or 0 = no rate limiting
    requests_per_minute: int | None = None
    # tokens_per_minute: None or 0 = no rate limiting (e.g., 4_000_000 for 4M TPM)
    tokens_per_minute: int | None = None


class LLMClient:
    """Unified LLM client supporting multiple providers.

    Provides async methods for chat completion and structured output
    with concurrency control via semaphore.
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        token_usage_callback: object | None = None,
    ) -> None:
        """Initialize the LLM client.

        Args:
            config: LLM configuration. Uses defaults if not provided.
            token_usage_callback: Optional callback for token usage tracking
        """
        self.config = config or LLMConfig()
        self._llm: BaseChatModel | None = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self.token_callback = TokenUsageCallback(
            token_usage_callback, tpm_limiter=self._create_tpm_limiter()
        )
        self._rate_limiter = self._create_rate_limiter()
        self._tpm_limiter = self.token_callback._tpm_limiter

        rpm_info = (
            f", rpm={self.config.requests_per_minute}"
            if self.config.requests_per_minute
            else ""
        )
        tpm_info = (
            f", tpm={self.config.tokens_per_minute:,}"
            if self.config.tokens_per_minute
            else ""
        )
        logger.info(
            "Initializing LLM client: provider=%s, model=%s, max_concurrent=%d%s%s",
            self.config.provider,
            self.config.model,
            self.config.max_concurrent,
            rpm_info,
            tpm_info,
        )

    def _create_tpm_limiter(self) -> TokenBucketTPM | None:
        """Create TPM rate limiter if configured.

        Returns:
            TokenBucketTPM or None if not configured.
        """
        tpm = self.config.tokens_per_minute
        if tpm is None or tpm <= 0:
            return None

        logger.info("TPM limiter enabled: %d tokens/minute", tpm)
        return TokenBucketTPM(tpm)

    def _create_rate_limiter(self) -> object | None:
        """Create rate limiter if configured.

        Returns:
            InMemoryRateLimiter or None if not configured.
        """
        rpm = self.config.requests_per_minute
        if rpm is None or rpm <= 0:
            return None

        from langchain_core.rate_limiters import InMemoryRateLimiter

        # Convert RPM to requests per second
        requests_per_second = rpm / 60.0

        rate_limiter = InMemoryRateLimiter(
            requests_per_second=requests_per_second,
            check_every_n_seconds=0.1,  # Check every 100ms
            max_bucket_size=max(10, rpm // 6),  # Allow some burst capacity
        )

        logger.info(
            "Rate limiter enabled: %d RPM (%.2f req/s)",
            rpm,
            requests_per_second,
        )

        return rate_limiter

    @property
    def llm(self) -> BaseChatModel:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _create_llm(self) -> BaseChatModel:
        """Create the appropriate LLM instance based on provider.

        Returns:
            LangChain chat model instance.

        Raises:
            ValueError: If provider is not supported.
        """
        llm: BaseChatModel

        if self.config.provider == LLMProvider.OLLAMA:
            from langchain_ollama import ChatOllama

            kwargs: dict[str, object] = {
                "model": self.config.model,
                "temperature": self.config.temperature,
            }
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            if self.config.max_tokens:
                kwargs["num_predict"] = self.config.max_tokens
            if self._rate_limiter:
                kwargs["rate_limiter"] = self._rate_limiter

            llm = ChatOllama(**kwargs)

        elif self.config.provider == LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI

            kwargs = {
                "model": self.config.model,
                "temperature": self.config.temperature,
            }
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.max_tokens:
                kwargs["max_tokens"] = self.config.max_tokens
            if self._rate_limiter:
                kwargs["rate_limiter"] = self._rate_limiter

            llm = ChatOpenAI(**kwargs)

        elif self.config.provider == LLMProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic

            kwargs = {
                "model": self.config.model,
                "temperature": self.config.temperature,
            }
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.max_tokens:
                kwargs["max_tokens"] = self.config.max_tokens
            if self._rate_limiter:
                kwargs["rate_limiter"] = self._rate_limiter

            llm = ChatAnthropic(**kwargs)

        elif self.config.provider == LLMProvider.GOOGLE:
            from langchain_google_genai import ChatGoogleGenerativeAI

            kwargs = {
                "model": self.config.model,
                "temperature": self.config.temperature,
            }
            if self.config.api_key:
                kwargs["google_api_key"] = self.config.api_key
            if self.config.max_tokens:
                kwargs["max_output_tokens"] = self.config.max_tokens
            if self._rate_limiter:
                kwargs["rate_limiter"] = self._rate_limiter

            llm = ChatGoogleGenerativeAI(**kwargs)

        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

        return llm

    async def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Send a chat message and get a response.

        Args:
            prompt: User message.
            system_prompt: Optional system message.

        Returns:
            Assistant response text.
        """
        messages: list[SystemMessage | HumanMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Estimate tokens for TPM rate limiting
        if self._tpm_limiter is not None:
            total_text = prompt + (system_prompt or "")
            estimated_tokens = (
                estimate_tokens(total_text) * 2
            )  # Input + output estimate
            await self._tpm_limiter.acquire(estimated_tokens)

        async with self._semaphore:
            logger.debug("Sending chat request (prompt length: %d)", len(prompt))
            response = await self.llm.ainvoke(
                messages, config={"callbacks": [self.token_callback]}
            )
            content = response.content
            if isinstance(content, str):
                return content
            # Handle list of content blocks (some providers)
            return str(content)

    async def chat_batch(
        self,
        prompts: Sequence[str],
        system_prompt: str | None = None,
    ) -> list[str]:
        """Send multiple chat messages concurrently.

        Args:
            prompts: List of user messages.
            system_prompt: Optional system message for all.

        Returns:
            List of assistant responses.
        """
        tasks = [self.chat(prompt, system_prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    async def structured_output(
        self,
        prompt: str,
        output_schema: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Get structured output matching a Pydantic schema.

        Args:
            prompt: User message.
            output_schema: Pydantic model class for output.
            system_prompt: Optional system message.

        Returns:
            Parsed output matching the schema.
        """
        messages: list[SystemMessage | HumanMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Estimate tokens for TPM rate limiting
        if self._tpm_limiter is not None:
            total_text = prompt + (system_prompt or "")
            estimated_tokens = (
                estimate_tokens(total_text) * 2
            )  # Input + output estimate
            await self._tpm_limiter.acquire(estimated_tokens)

        async with self._semaphore:
            logger.debug(
                "Sending structured output request (schema: %s)",
                output_schema.__name__,
            )
            structured_llm = self.llm.with_structured_output(output_schema)
            response = await structured_llm.ainvoke(
                messages, config={"callbacks": [self.token_callback]}
            )

            if isinstance(response, output_schema):
                return response

            # Some providers return dict instead of model
            if isinstance(response, dict):
                return output_schema.model_validate(response)

            raise TypeError(
                f"Unexpected response type: {type(response)}. "
                f"Expected {output_schema.__name__}"
            )

    async def structured_output_batch(
        self,
        prompts: Sequence[str],
        output_schema: type[T],
        system_prompt: str | None = None,
    ) -> list[T]:
        """Get structured outputs for multiple prompts concurrently.

        Args:
            prompts: List of user messages.
            output_schema: Pydantic model class for outputs.
            system_prompt: Optional system message for all.

        Returns:
            List of parsed outputs matching the schema.
        """
        tasks = [
            self.structured_output(prompt, output_schema, system_prompt)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)

    def update_config(self, **kwargs: object) -> None:
        """Update configuration and reset LLM instance.

        Args:
            **kwargs: Configuration parameters to update.
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Reset LLM to apply new config
        self._llm = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        logger.info("LLM config updated: %s", kwargs)

    def get_token_usage(self) -> dict[str, int]:
        """Get cumulative token usage statistics.

        Returns:
            Dictionary with input_tokens, output_tokens, and total_tokens
        """
        return {
            "input_tokens": self.token_callback.total_input_tokens,
            "output_tokens": self.token_callback.total_output_tokens,
            "total_tokens": self.token_callback.total_tokens,
        }

    def get_tpm_status(self) -> dict[str, float | int] | None:
        """Get current TPM rate limiter status.

        Returns:
            Dictionary with current_tokens, limit_tokens, available_tokens,
            utilization_percent, or None if TPM limiter is not enabled.
        """
        if self._tpm_limiter is None:
            return None
        return self._tpm_limiter.get_status()

    def reset_token_usage(self) -> None:
        """Reset token usage statistics."""
        self.token_callback.reset()
