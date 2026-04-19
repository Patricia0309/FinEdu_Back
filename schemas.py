# backend/schemas.py
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List
import re  # <-- ¡CORRECCIÓN 1: IMPORTACIÓN AÑADIDA!

# =============================================================================
# ESQUEMAS DE CATEGORÍA
# =============================================================================
class CategoryBase(BaseModel):
    name: str
class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# =============================================================================
# ESQUEMAS DE ESTUDIANTE
# =============================================================================
class StudentBase(BaseModel):
    display_name: str
    email: str
class StudentCreate(StudentBase):
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator('password')
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if not re.search(r"\d", value): # 're' ahora está definido
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", value): # 're' ahora está definido
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
class FCMTokenUpdate(BaseModel):
    fcm_token: str

# =============================================================================
# ESQUEMAS DE TRANSACCIÓN
# =============================================================================
class TransactionBase(BaseModel):
    amount: float
    type: str # 'income' o 'gasto'
    note: Optional[str] = None
    income_period_id: int
    
    # --- CAMBIO AQUÍ ---
    # La categoría es opcional (para los ingresos)
    category_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    ts: Optional[datetime] = None
    pass # Hereda los campos de TransactionBase

class Transaction(TransactionBase):
    id: int
    ts: datetime
    student_id: int
    # La categoría devuelta también puede ser nula
    category: Optional[Category] = None 

    class Config:
        from_attributes = True

# =============================================================================
# ESQUEMAS DE PRESUPUESTO
# =============================================================================
class IncomePeriodCreate(BaseModel):
    total_income: float  # <-- ¡CORRECCIÓN 2: DE 'amount' A 'total_income'!
    start_date: datetime
    end_date: datetime

    @model_validator(mode='after')
    def check_dates(self) -> 'IncomePeriodCreate':
        if self.start_date >= self.end_date:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de término.")
        return self
    

class IncomePeriod(IncomePeriodCreate):
    income_period_id: int
    is_active: bool
    student_id: int
    class Config:
        from_attributes = True
class IncomePeriodHistory(BaseModel):
    income_period_id: int
    start_date: datetime
    end_date: datetime
    total_income: float
    total_spent: float
    remaining_budget: float
    is_active: bool = False
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
class BudgetPeriodSummary(BaseModel):
    start_date: datetime
    end_date: datetime
    budgeted_amount: float
    total_spent: float
    class Config:
        from_attributes = True
class BudgetTendencyResponse(BaseModel):
    current_period: Optional[BudgetPeriodSummary] = None
    previous_period: Optional[BudgetPeriodSummary] = None
    comparison: Optional[dict] = None

# =============================================================================
# ESQUEMAS DE ANALYTICS
# =============================================================================
class AssociationRuleResponse(BaseModel):
    antecedents: List[str]
    consequents: List[str]
    support: float
    confidence: float
    lift: float
    class Config:
        from_attributes = True
class Recommendation(BaseModel):
    type: str
    title: str
    body: str
class ProfileResponse(BaseModel):
    profile: str
    justification: str
    recommendation: str
    # --- CAMPOS NUEVOS PARA LA BARRA DE PROGRESO ---
    is_calculating: bool = False
    current_count: int = 0
    goal: int = 15

# =============================================================================
# ESQUEMA DE TOKEN DE AUTENTICACIÓN
# =============================================================================
class Token(BaseModel):
    access_token: str
    token_type: str

# --- ESQUEMA PARA MICROCONTENIDOS ---
class MicrocontentResponse(BaseModel):
    id: int
    title: str
    body: str
    tag: str

    class Config:
        from_attributes = True

# Esquema para solicitar la recuperación
class PasswordRecoveryRequest(BaseModel):
    email: str

# Esquema para confirmar el cambio con el token
class PasswordResetConfirmOTP(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)

class CategorySpendingDetail(BaseModel):
    category_name: str
    total_spent: float
    percentage: float  # (Gasto en esta categoría / Presupuesto Total) * 100
    
class CategorySpendingResponse(BaseModel):
    income_period_id: int
    total_budget: float
    categories: List[CategorySpendingDetail]


class BudgetHistoryDetailResponse(BaseModel):
    income_period_id: int
    total_income: float
    total_spent: float
    remaining_budget: float
    start_date: datetime
    end_date: datetime
    # Lista de cuánto se gastó por categoría en ese entonces
    categories: List[CategorySpendingDetail]