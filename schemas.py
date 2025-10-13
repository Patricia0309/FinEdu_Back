# backend/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Propiedades base que comparten todos los esquemas de Student
class StudentBase(BaseModel):
    display_name: str
    email: str

# Esquema para la creación de un estudiante (lo que recibe la API)
class StudentCreate(StudentBase):
    password: str = Field(
        ...,
        min_length=3,
        max_length=64,  # <-- ESTA LÍNEA ES LA CLAVE
        description="La contraseña debe tener entre 8 y 64 caracteres."
    )

# Esquema para leer un estudiante (lo que devuelve la API)
class Student(StudentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Permite que Pydantic lea datos de objetos ORM

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Esquemas de Categoría ---
class CategoryBase(BaseModel):
    name: str

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# --- Esquemas de Transacción ---
class TransactionBase(BaseModel):
    amount: float # Usamos float aquí, Pydantic lo validará como número
    type: str # 'expense' o 'income'
    category_id: int

# Esquema para la creación de una transacción (lo que recibe la API)
class TransactionCreate(TransactionBase):
    pass

# Esquema para leer/devolver una transacción (lo que devuelve la API)
class Transaction(TransactionBase):
    id: int
    ts: datetime # Timestamp de la transacción
    student_id: int
    
    # Este campo anidado cargará los detalles de la categoría
    category: Category 

    class Config:
        from_attributes = True
