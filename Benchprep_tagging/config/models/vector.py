from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class OpensearchSettings(BaseModel):
    hosts: List[str]
    use_ssl: bool
    verify_certs: bool
    ssl_show_warn: bool
    username: str
    password: str
    default_index_name: str = 'default_index_name'

class AwsOpensearchSettings(BaseModel):
    url: str
    service: str
    region: str
    use_ssl: bool
    verify_certs: bool
    ssl_show_warn: bool
    bulk_size: int
    access_key: str
    secret_access_key: str
    default_index_name: str = 'default_aws_opensearch_index'

class VectorDatabaseTypeEnum(str, Enum):
    opensearch = 'opensearch'
    awsopensearch = 'awsopensearch'

class VectorSettings(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    database_type: VectorDatabaseTypeEnum = VectorDatabaseTypeEnum.opensearch
    opensearch: Optional[OpensearchSettings] = None
    awsopensearch: Optional[AwsOpensearchSettings] = None
