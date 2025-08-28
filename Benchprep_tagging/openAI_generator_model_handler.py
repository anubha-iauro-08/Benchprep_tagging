import logging

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from generator_abstract_base import LLMGeneratorBase
from config.config import Settings

logger = logging.getLogger(__name__)


class OpenAIModel(LLMGeneratorBase):
    """
    This class provides an interface to generate responses using
    an OpenAI-based chat model. It inherits from `LLMGeneratorBase` and
    utilizes the `ChatOpenAI` model from the LangChain OpenAI library.
    """

    def __init__(self, config: Settings) -> None:
        """
        Initialize an instance of the class with configuration parameters for an OpenAI-based chat model.

        This constructor sets up the `generator_model` attribute with an instance of
        `ChatOpenAI` initialized using the provided configuration dictionary.

        Args:
            config (dict):
                A dictionary containing the configuration details for the platform and model.
                Expected structure:
                    - "PLATFORM" (str):
                        The name of the platform (e.g., "OPENAI").
                    - "GENERATOR" (dict):
                        A nested dictionary containing generator-specific configuration.
                        - <PLATFORM> (dict):
                            Platform-specific details such as:
                                - "API_KEY" (str):
                                    The OpenAI API key.
                                - "MODEL_NAME" (str):
                                    The name of the OpenAI model to use (e.g., "gpt-4").
                                - "TEMPERATURE" (float, optional):
                                    The temperature setting for response variability.
                                    Defaults to 0.1 if not provided.
                                - "MAX_TOKENS" (int, optional):
                                    The maximum number of tokens for the generated response.
                                    Defaults to 2000 if not provided.

        Attributes:
            generator_model (ChatOpenAI):
                An instance of `ChatOpenAI` initialized based on the provided configuration.
        """
        platform_name = config.llm.platform
        platform_config = getattr(config.generator, platform_name)

        api_key = config.llm.api_key
        model_name = platform_config.model_name
        temperature = platform_config.temperature
        max_tokens = platform_config.max_tokens

        self.generator_model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    @retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(10))
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response for the provided prompt using the ChatOpenAI model.

        Args:
            prompt (str):
                The input text/prompt for which to generate a response.

        Returns:
            str:
                The generated response for the input prompt.
        """
        response = self.generator_model.invoke(prompt)
        content_usage_information = response
        return response.content
