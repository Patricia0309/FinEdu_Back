from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from security import get_password_hash
from sqlalchemy import func 
from datetime import datetime, timezone

def get_student_by_email(db: Session, email: str):
    return db.query(models.Student).filter(models.Student.email == email).first()

def create_student(db: Session, student: schemas.StudentCreate):
    hashed_password = get_password_hash(student.password)
    db_student = models.Student(email=student.email, display_name=student.display_name, hashed_password=hashed_password)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student_favorite_categories(db: Session, student_id: int, category_ids: List[int]):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return None
    new_categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
    student.favorite_categories = new_categories
    db.commit()
    db.refresh(student)
    return student

def update_student_fcm_token(db: Session, student_id: int, fcm_token: str):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student:
        db_student.fcm_token = fcm_token
        db.commit()
        db.refresh(db_student)
    return db_student

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_initial_categories(db: Session):
    if db.query(models.Category).count() == 0:
        print("Creando categorías iniciales...")
        initial_categories = [
            models.Category(name="Hogar y Servicios"), models.Category(name="Educación"),
            models.Category(name="Salud y Bienestar"), models.Category(name="Deudas y Obligaciones"),
            models.Category(name="Alimentación"), models.Category(name="Transporte"),
            models.Category(name="Compras y Cuidado personal"), models.Category(name="Ocio y Vida Social"),
            models.Category(name="Ahorro e Inversión"), models.Category(name="Gastos Hormiga")
        ]
        db.add_all(initial_categories)
        db.commit()
        print(f"{len(initial_categories)} categorías creadas.")
    else:
        print("Categorías ya pobladas.")

def create_student_transaction(db: Session, transaction: schemas.TransactionCreate, student_id: int):
    # 1. Convierte el schema de Pydantic a un diccionario
    data_dict = transaction.model_dump(exclude_unset=True) # Excluye campos no enviados

    # 2. Renombra la llave 'date' (del frontend) a 'ts' (del modelo DB)
    if 'date' in data_dict:
        data_dict['ts'] = data_dict.pop('date')
    
    # 3. Crea el objeto del modelo usando el diccionario corregido
    db_transaction = models.Transaction(**data_dict, student_id=student_id)
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_student_transactions(db: Session, student_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.student_id == student_id).offset(skip).limit(limit).all()

def create_income_period(db: Session, student_id: int, period: schemas.IncomePeriodCreate):
    # Desactivamos cualquier otro período activo para este usuario
    db.query(models.IncomePeriod).filter(models.IncomePeriod.student_id == student_id).update({"is_active": False})
    
    db_period = models.IncomePeriod(
        **period.model_dump(),
        student_id=student_id,
        is_active=True
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period

def get_current_budget_status(db: Session, student_id: int):
    """
    Busca el período de ingresos activo para un estudiante,
    calcula el gasto total y el saldo restante.
    """
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.is_active == True
    ).first()

    if not active_period:
        return None # No hay período activo

    # Calcula el gasto total durante el período activo (resultado puede ser Decimal o None)
    total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto', # Usa 'gasto' como acordamos
        models.Transaction.ts >= active_period.start_date,
        models.Transaction.ts <= active_period.end_date
    ).scalar()

    # --- CORRECCIÓN AQUÍ ---
    # Convertimos el resultado Decimal (o None) a float, default 0.0 si es None
    total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0

    # Ahora ambos son floats, la resta funcionará
    remaining_budget = float(active_period.amount) - total_spent
    # --- FIN CORRECCIÓN ---

    # Calcula los días restantes
    now = datetime.now(timezone.utc)
    end_date_aware = active_period.end_date
    if end_date_aware.tzinfo is None:
         end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)

    days_left = (end_date_aware - now).days if end_date_aware > now else 0

    return schemas.BudgetStatus(
        income_period_id=active_period.id,
        total_income=float(active_period.amount),
        start_date=active_period.start_date,
        end_date=active_period.end_date,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        days_left=days_left,
        is_active=active_period.is_active
    )

def get_income_period_by_id(db: Session, period_id: int, student_id: int):
    """
    Obtiene un período de ingresos específico por su ID,
    verificando que pertenezca al estudiante.
    """
    return db.query(models.IncomePeriod).filter(
        models.IncomePeriod.id == period_id,
        models.IncomePeriod.student_id == student_id # Security check!
    ).first()

def update_income_period(db: Session, period_id: int, student_id: int, period_update: schemas.IncomePeriodCreate):
    """
    Actualiza un período de ingresos específico para un estudiante.
    Verifica que el estudiante sea el propietario del período.
    """
    db_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.id == period_id,
        models.IncomePeriod.student_id == student_id # Security check!
    ).first()

    if not db_period:
        return None # Not found or doesn't belong to the user

    # Update fields from the request data
    db_period.amount = period_update.amount
    db_period.start_date = period_update.start_date
    db_period.end_date = period_update.end_date
    # We probably don't want to reactivate it here, just edit details
    # db_period.is_active = True 

    db.commit()
    db.refresh(db_period)
    return db_period