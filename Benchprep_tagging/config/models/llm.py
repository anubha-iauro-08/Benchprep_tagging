from enum import Enum
from pydantic import BaseModel, ConfigDict

class LLMPlatformEnum(str, Enum):
    openai = 'openai'

class LLMSettings(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    platform: LLMPlatformEnum = LLMPlatformEnum.openai
    api_key: str
