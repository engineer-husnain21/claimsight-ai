from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user_role import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
