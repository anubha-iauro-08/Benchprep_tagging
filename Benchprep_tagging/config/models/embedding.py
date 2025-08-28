from enum import Enum
from pydantic import BaseModel, ConfigDict

class OpenAIModelApiEnum(str, Enum):
    openai_embedding = 'OpenAIEmbedding'

class OpenAIModelNameEnum(str, Enum):
    text_embedding_3_large = 'text-embedding-3-large'

class OpenAIEmbedding(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    model_api: OpenAIModelApiEnum = OpenAIModelApiEnum.openai_embedding
    model_name: OpenAIModelNameEnum = OpenAIModelNameEnum.text_embedding_3_large

class EmbeddingSettings(BaseModel):
    openai: OpenAIEmbedding
