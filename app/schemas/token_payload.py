from pydantic import BaseModel


class TokenPayload(BaseModel):
    """Validated claims of a decoded JWT."""

    sub: str
    role: str
    type: str
    jti: str
    exp: int
