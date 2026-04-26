from typing import Annotated

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    user_id: Annotated[int, Field(ge=1, title="ID", description="ID")]
