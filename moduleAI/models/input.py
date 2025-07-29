from pydantic import BaseModel


class IdeaInput(BaseModel):
    user_id: int
    text: str
