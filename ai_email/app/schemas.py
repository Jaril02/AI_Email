from pydantic import BaseModel

class EmailRequest(BaseModel):
    text: str