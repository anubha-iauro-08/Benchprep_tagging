from pydantic_settings import BaseSettings, SettingsConfigDict
from config.models.llm import LLMSettings
from config.models.rdbms import RDBMSSettings
from config.models.vector import VectorSettings
from config.models.generator import GeneratorSettings
from config.models.embedding import EmbeddingSettings
from config.models.document import DocumentSettings
from config.models.snowflake import SnowflakeSettings
from config.models.conversation import ConversationSettings
from config.models.flagsmith import FlagsmithSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_nested_delimiter="__"
    )

    llm: LLMSettings
    rdbms: RDBMSSettings
    vector: VectorSettings
    generator: GeneratorSettings
    embedding: EmbeddingSettings
    document: DocumentSettings
    snowflake: SnowflakeSettings
    conversation: ConversationSettings
    flagsmith: FlagsmithSettings
