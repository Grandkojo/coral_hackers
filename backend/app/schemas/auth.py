from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    organization_id: str


class AuthOrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
    organization: AuthOrganizationResponse


class MeResponse(BaseModel):
    user: AuthUserResponse
    organization: AuthOrganizationResponse
