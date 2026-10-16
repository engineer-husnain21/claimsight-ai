from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


class RegisterRequest(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(char.isalpha() for char in value)
        has_digit = any(char.isdigit() for char in value)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one digit.")
        return value
