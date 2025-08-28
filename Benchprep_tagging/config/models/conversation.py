from pydantic import BaseModel

class ConversationSettings(BaseModel):
    max_messages: int = 20
    keep_recent: int = 5
