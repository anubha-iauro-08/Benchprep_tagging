from enum import Enum
from pydantic import BaseModel, ConfigDict

class ChunkingTypeEnum(str, Enum):
    sectionwise = 'sectionwise'
    blockwise = 'blockwise'

class DocumentSettings(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    chunk_size: int
    chunking_type: ChunkingTypeEnum = ChunkingTypeEnum.sectionwise
    overlap_window_size: int
