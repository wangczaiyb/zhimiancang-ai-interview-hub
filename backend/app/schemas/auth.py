from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    account: str  # email or phone
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    account_type: str
    role_codes: List[str]
    user_id: int
    name: str
    avatar_url: Optional[str] = None
    company_id: Optional[int] = None

class RegisterPersonalRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="用户真实姓名")
    phone: Optional[str] = None
    email: EmailStr
    password: str
    confirm_password: str
    agreed: bool

class RegisterEnterpriseRequest(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: EmailStr
    password: str
    industry: str = "互联网/软件"
    city: str = "北京"

class OnboardingRequest(BaseModel):
    profile_type: str = "STUDENT"  # STUDENT, GRADUATE, EXPERIENCED
    name: str
    gender: Optional[str] = "保密"
    education: str
    school: str
    major: str
    graduation_year: int
    target_job_title: str
    target_cities: str
    salary_min: int = 15
    salary_max: int = 25
    job_status: str = "LOOKING"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserInfoOut(BaseModel):
    id: int
    email: str
    phone: Optional[str] = None
    account_type: str
    status: str
    roles: List[str]
    name: str
    avatar_url: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    profile_type: Optional[str] = None
    target_job_title: Optional[str] = None
