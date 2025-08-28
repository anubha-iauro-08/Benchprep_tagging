from enum import Enum
from pydantic import BaseModel, ConfigDict

class OpenAIGeneratorModelApiEnum(str, Enum):
    openai_model = 'OpenAIModel'

class OpenAIGeneratorModelNameEnum(str, Enum):
    gpt_4o = 'gpt-4o'

class OpenAIGenerator(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    model_api: OpenAIGeneratorModelApiEnum = OpenAIGeneratorModelApiEnum.openai_model
    model_name: OpenAIGeneratorModelNameEnum = OpenAIGeneratorModelNameEnum.gpt_4o
    temperature: float = 0.1
    max_tokens: int = 2000

class GeneratorSettings(BaseModel):
    openai: OpenAIGenerator
