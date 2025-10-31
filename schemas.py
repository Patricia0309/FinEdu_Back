from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
import re

class CategoryBase(BaseModel):
    name: str

class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    display_name: str
    email: str

class StudentCreate(StudentBase):
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator('password')
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if not re.search(r"\d", value):
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", value):
            raise ValueError("La contraseña debe contener al menos un carácter especial.")
        return value

class Student(StudentBase):
    id: int
    created_at: datetime
    favorite_categories: List[Category] = []
    fcm_token: Optional[str] = None
    class Config:
        from_attributes = True

class StudentCategoryUpdate(BaseModel):
    category_ids: List[int]

class TransactionBase(BaseModel):
    amount: float
    type: str
    category_id: Optional[int] = None
    note: Optional[str] = None
    date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    ts: datetime
    student_id: int
    category: Optional[Category] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileResponse(BaseModel):
    profile: str
    description: str

class IncomePeriodCreate(BaseModel):
    amount: float
    start_date: datetime
    end_date: datetime

class IncomePeriod(IncomePeriodCreate):
    id: int
    is_active: bool
    student_id: int

    class Config:
        from_attributes = True

class BudgetStatus(BaseModel):
    income_period_id: int
    total_income: float
    start_date: datetime
    end_date: datetime
    total_spent: float
    remaining_budget: float
    days_left: int
    is_active: bool

class FCMTokenUpdate(BaseModel): 
    fcm_token: str