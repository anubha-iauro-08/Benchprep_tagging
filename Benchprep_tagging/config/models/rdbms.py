from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RDBMSClassNameEnum(str, Enum):
    state_db_connector = 'StateDBConnector'

class RDBMSSettings(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    class_name: RDBMSClassNameEnum = RDBMSClassNameEnum.state_db_connector
    name: str = 'postgres'
    username: str = 'postgres'
    host: str = 'postgres'
    port: str = '5432'
    database_name: str = 'ai_tutor_development'
    max_size: int = 20
    autocommit: bool = True
    password: str = 'postgres'
    prepare_threshold: Optional[int] = None
