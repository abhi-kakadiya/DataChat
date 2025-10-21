"""DSPy configuration and LM setup."""

import dspy
from functools import lru_cache

from src.core.config import get_settings


@lru_cache()
def get_dspy_lm():
    """Get or create a cached DSPy language model instance."""
    settings = get_settings()

    lm = dspy.LM(
        model=f"openai/{settings.OPENAI_MODEL}",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=2000,
    )

    return lm


def configure_dspy():
    """Configure DSPy with the language model."""
    lm = get_dspy_lm()
    dspy.configure(lm=lm)
    return lm
