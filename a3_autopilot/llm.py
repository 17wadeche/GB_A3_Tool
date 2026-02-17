from __future__ import annotations
import os
from typing import Protocol
class Summarizer(Protocol):
    def summarize(self, text: str) -> str: ...
class RuleBasedSummarizer:
    def summarize(self, text: str) -> str:
        return text[:220] + ("..." if len(text) > 220 else "")
class OptionalLLMSummarizer:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._fallback = RuleBasedSummarizer()
    def summarize(self, text: str) -> str:
        return self._fallback.summarize(text)