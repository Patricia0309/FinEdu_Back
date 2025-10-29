from sqlalchemy import Column, Integer, String, TIMESTAMP, NUMERIC, ForeignKey, Text, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

student_favorite_category_association = Table(
    "student_favorite_category",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("category.id"), primary_key=True),
)

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(NUMERIC(12, 2), nullable=False)
    type = Column(Text, nullable=False)
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now())
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    owner = relationship("Student", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    fcm_token = Column(String, nullable=True, index=True)
    transactions = relationship("Transaction", back_populates="owner")
    favorite_categories = relationship("Category", secondary=student_favorite_category_association)
    income_periods = relationship("IncomePeriod", back_populates="student")

class IncomePeriod(Base):
    __tablename__ = "income_period"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(NUMERIC(12, 2), nullable=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    student = relationship("Student", back_populates="income_periods")