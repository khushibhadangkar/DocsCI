"""AI-assisted release notes summarization and claim verification module."""

from docsci.ai.client import GeminiClient, MockLLMClient, get_llm_client, load_prompt_template
from docsci.ai.verifier import generate_draft_markdown, split_into_claims, verify_claims

__all__ = [
    "GeminiClient",
    "MockLLMClient",
    "get_llm_client",
    "load_prompt_template",
    "split_into_claims",
    "verify_claims",
    "generate_draft_markdown",
]
