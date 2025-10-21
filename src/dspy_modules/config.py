import dspy
import logging
from functools import lru_cache

from src.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_dspy_lm():
    settings = get_settings()

    logger.info(f"Initializing DSPy LM with model: {settings.OPENAI_MODEL}")
    lm = dspy.LM(
        model=f"openai/{settings.OPENAI_MODEL}",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=2000,
    )

    logger.info("DSPy LM instance created successfully")
    return lm


def configure_dspy():
    if dspy.settings.lm is not None:
        logger.info("DSPy already configured, using existing LM")
        return dspy.settings.lm

    logger.info("Configuring DSPy...")
    lm = get_dspy_lm()
    dspy.configure(lm=lm)

    if dspy.settings.lm is None:
        logger.error("DSPy configuration failed - LM is still None")
        raise RuntimeError("Failed to configure DSPy language model")

    logger.info(f"DSPy configured successfully with {type(lm).__name__}")
    return lm


def is_dspy_configured() -> bool:
    return dspy.settings.lm is not None
