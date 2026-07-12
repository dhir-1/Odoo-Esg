from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.enums import RoleEnum, StatusEnum

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[RoleEnum] = None
    user_id: Optional[int] = None

class UserRegister(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    password: str
    role: RoleEnum
    department_id: int
    designation: str
    date_joined: date
    avatar_url: Optional[str] = None

class UserSignup(BaseModel):
    """Public signup schema — no auth required, defaults to Employee role."""
    full_name: str
    email: EmailStr
    password: str
    department_id: int
    designation: Optional[str] = "Sustainability Advocate"


class EmployeeRead(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: EmailStr
    role: RoleEnum
    department_id: int
    designation: str
    date_joined: date
    xp_points: int
    points_balance: int
    status: StatusEnum
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EmployeeSearchRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: RoleEnum
    department_id: int
    department_name: Optional[str] = None
    status: StatusEnum

    model_config = ConfigDict(from_attributes=True)
