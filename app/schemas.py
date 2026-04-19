from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    objective: str = Field(..., min_length=3, max_length=2000)


class EnhanceRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=5000)


class PreviewRequest(BaseModel):
    message_template: str = Field(..., min_length=3, max_length=5000)
    limit: int = Field(default=5, ge=1, le=50)


class SendRequest(BaseModel):
    message_template: str = Field(..., min_length=3, max_length=5000)
    subject: str = Field(..., min_length=1, max_length=255)
