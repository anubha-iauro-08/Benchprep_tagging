import importlib
from typing import Any
import logging
from config.config import Settings

logger = logging.getLogger(__name__)


class GeneratorModelHandler:
    """
    Handler for generating responses using different generator models.

    This handler provides a consistent interface for creating and using
    various generator models, abstracting away platform-specific details.
    """

    def __init__(self, config: Settings) -> None:
        """
        Initialize an instance with a generator model configuration.

        Creates a generator model instance using the provided configuration dictionary.
        The actual model initialization is delegated to the `generator_handler` method.

        Attributes:
            generator_model (LLMGeneratorBase | bool):
                The initialized generator model instance created by `generator_handler`.
                If initialization fails, this will be False.
        """
        self.generator_model = self.generator_handler(config)

    def generator_handler(self, config: Settings) -> Any:
        """
        Create and return an appropriate generator model based on platform configuration.

        This method dynamically imports and instantiates a generator model class based on
        the platform specified in the configuration. It constructs the import path using
        the platform name and model API information from the config.

        Returns:
            Any:
                An instantiated generator model object if successful.
            bool:
                False if any error occurs during model creation.
        """
        platform = config.llm.platform
        platform_config = getattr(config.generator, platform)
        generator_name = platform_config.model_api

        full_import_path = (
            f"{platform}_generator"
        )
        generator_module = importlib.import_module(full_import_path)
        generator_class = getattr(generator_module, generator_name)

        logger.debug("Successfully imported generator class: %s", generator_class)
        return generator_class(config)

    def generate_response(self, prompt: str) -> Any:
        """
        Generate a response for the provided prompt using the initialized generator model.

        Args:
            prompt (str):
                The prompt string for which to generate a response.

        Returns:
            Any:
                The generated response from the selected model.

        Raises:
            Exception:
                If response generation fails due to an error in the underlying model.
        """
        if not self.generator_model:
            error_msg = "No valid generator model is initialized."
            logger.error(error_msg)
            raise Exception(error_msg)

        return self.generator_model.generate_response(prompt)

    def get_model(self) -> Any:
        """
        Retrieve the underlying LangChain-compatible model instance.

        Returns:
            Any:
                The underlying generator model object, or False if initialization failed.
        """
        return getattr(self.generator_model, "generator_model", False)