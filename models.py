# backend/models.py

from sqlalchemy import Column, Integer, String, TIMESTAMP, NUMERIC, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# --- TABLA DE CATEGORÍAS ---
class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    # Esta relación no crea una columna, solo ayuda a SQLAlchemy a entender
    # que una categoría puede tener muchas transacciones.
    transactions = relationship("Transaction", back_populates="category")


# --- TABLA DE TRANSACCIONES ---
class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(NUMERIC(12, 2), nullable=False) # Para guardar dinero con 2 decimales
    type = Column(Text, nullable=False) # 'expense' o 'income'
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now()) # Timestamp con zona horaria
    
    # --- Claves Foráneas (Foreign Keys) que conectan las tablas ---
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)

    # --- Relaciones de SQLAlchemy ---
    # Esto le enseña a SQLAlchemy cómo navegar entre los objetos en nuestro código Python.
    # Por ejemplo, podremos hacer `mi_transaccion.owner` para ver el estudiante.
    owner = relationship("Student")
    category = relationship("Category", back_populates="transactions")


# --- TABLA DE ESTUDIANTES (la que ya teníamos) ---
# Le añadiremos una relación para poder acceder fácilmente a las transacciones de un estudiante
class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    display_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Esta relación nos permitirá hacer algo como `mi_estudiante.transactions`
    # para obtener una lista de todas sus transacciones.
    transactions = relationship("Transaction", back_populates="owner")