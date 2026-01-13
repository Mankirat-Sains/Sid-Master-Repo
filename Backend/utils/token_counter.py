"""
Token counting utilities with optional tiktoken support and safe fallbacks.
"""
from typing import Any, Dict, List, Union

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class TokenCounter:
    """Counts tokens for strings, message lists, or arbitrary dicts."""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to common encoding
                self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None

    def count_tokens(self, text: Union[str, List[Any], Dict[str, Any]]) -> int:
        """Count tokens for supported input types."""
        if isinstance(text, list):
            return sum(self.count_tokens(item) for item in text)

        if isinstance(text, dict):
            total = 0
            for value in text.values():
                total += self.count_tokens(value)
            return total

        if isinstance(text, str):
            if self.encoding:
                return len(self.encoding.encode(text))
            # Fallback: rough average of 4 chars per token
            return max(1, len(text) // 4) if text else 0

        return 0


_default_counter = TokenCounter()


def count_tokens(text: Union[str, List[Any], Dict[str, Any]], model: str = None) -> int:
    """Convenience wrapper to count tokens with an optional model override."""
    if model and model != _default_counter.model:
        return TokenCounter(model).count_tokens(text)
    return _default_counter.count_tokens(text)

