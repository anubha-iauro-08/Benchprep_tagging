from pydantic import BaseModel

class FlagsmithSettings(BaseModel):
    api_url: str
    enabled: bool
    environment_key: str
