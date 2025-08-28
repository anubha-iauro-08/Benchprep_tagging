from pydantic import BaseModel

class SnowflakeSettings(BaseModel):
    role: str
    warehouse: str
    database: str
    schema_target: str
    batch_size: int = 100
    client_session_keep_alive: bool
    key_file_path: str
    key_file_password: str
    account: str
    user: str
