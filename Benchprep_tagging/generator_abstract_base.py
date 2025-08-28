import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class LLMGeneratorBase(ABC):
    """
    Abstract base class for LLM generator models.

    This class defines the interface that all generator implementations must follow.
    """

    @abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the generator model with configuration parameters.

        Args:
            config (dict):
                A dictionary containing configuration parameters.
        """
        pass

    @abstractmethod
    def generate_response(self, prompt: str) -> Any:
        """
        Generate a response for the given prompt.

        Args:
            prompt (str):
                The prompt string for which to generate a response.

        Returns:
            Any:
                The generated response.
        """
        pass