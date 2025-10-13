# backend/crud.py

from sqlalchemy.orm import Session
import models, schemas
from security import get_password_hash 

def create_student(db: Session, student: schemas.StudentCreate):
    # 2. Hasheamos la contraseña antes de guardarla
    hashed_password = get_password_hash(student.password)
    
    db_student = models.Student(
        email=student.email,
        display_name=student.display_name,
        hashed_password=hashed_password 
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_student_by_email(db: Session, email: str):
    """Busca y devuelve un estudiante por su email."""
    return db.query(models.Student).filter(models.Student.email == email).first()

# --- FUNCIONES PARA CATEGORÍAS ---

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de todas las categorías."""
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_initial_categories(db: Session):
    """Crea las categorías iniciales si la tabla está vacía."""
    # Primero, comprueba si ya existen categorías
    if db.query(models.Category).count() == 0:
        print("Base de datos de categorías vacía, creando categorías iniciales...")
        
        initial_categories = [
            models.Category(name="Alimentación"),
            models.Category(name="Transporte"),
            models.Category(name="Alojamiento"),
            models.Category(name="Ocio"),
            models.Category(name="Educación"),
            models.Category(name="Salud"),
            models.Category(name="Ropa y Accesorios"),
            models.Category(name="Ingresos"),
            models.Category(name="Otros")
        ]
        
        db.add_all(initial_categories)
        db.commit()
        print("Categorías iniciales creadas.")
    else:
        print("La base de datos de categorías ya está poblada.")


# --- FUNCIÓN PARA CREAR TRANSACCIONES ---

def create_student_transaction(db: Session, transaction: schemas.TransactionCreate, student_id: int):
    """Crea una nueva transacción asociada a un estudiante."""
    # Creamos un objeto del modelo SQLAlchemy a partir de los datos del esquema
    db_transaction = models.Transaction(
        amount=transaction.amount,
        type=transaction.type,
        category_id=transaction.category_id,
        student_id=student_id  # <-- El ID del estudiante se pasa de forma segura
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_student_transactions(db: Session, student_id: int, skip: int = 0, limit: int = 100):
    """Obtiene una lista de las transacciones de un estudiante específico."""
    return db.query(models.Transaction).filter(models.Transaction.student_id == student_id).offset(skip).limit(limit).all()

