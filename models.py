# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, NUMERIC, TIMESTAMP, Table, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Tabla de asociación para Categorías Favoritas
student_favorite_category_association = Table(
    "student_favorite_category",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("category.id"), primary_key=True),
)

class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fcm_token = Column(String, nullable=True, index=True)

    income_periods = relationship("IncomePeriod", back_populates="owner")
    transactions = relationship("Transaction", back_populates="owner")
    favorite_categories = relationship("Category", secondary=student_favorite_category_association)

class IncomePeriod(Base):
    __tablename__ = "income_periods"
    
    # El ID se llama 'income_period_id'
    income_period_id = Column(Integer, primary_key=True, index=True)
    # El monto se llama 'total_income'
    total_income = Column(Float, nullable=False) 
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True) # Columna para saber si está activo
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)

    owner = relationship("Student", back_populates="income_periods")
    transactions = relationship("Transaction", back_populates="income_period")

class Transaction(Base):
    __tablename__ = "transaction"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(NUMERIC(12, 2), nullable=False)
    type = Column(Text, nullable=False) # 'income' o 'gasto'
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now())
    note = Column(String, nullable=True)
    
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    
    # Llave foránea que conecta con el período de presupuesto
    income_period_id = Column(Integer, ForeignKey("income_periods.income_period_id"), nullable=False)

    owner = relationship("Student", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    income_period = relationship("IncomePeriod", back_populates="transactions")

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    transactions = relationship("Transaction", back_populates="category")

class AssociationRule(Base):
    __tablename__ = "association_rule"
    id = Column(Integer, primary_key=True, index=True)
    antecedents = Column(ARRAY(String), nullable=False)
    consequents = Column(ARRAY(String), nullable=False)
    support = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    lift = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())