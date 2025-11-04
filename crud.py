# backend/crud.py
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from security import get_password_hash
from sqlalchemy import func 
from datetime import datetime, timezone, timedelta
import random

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
            models.Category(name="Ingresos"), # Añadida para la demo
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
    # Asumimos que el frontend envía 'income_period_id'
    db_transaction = models.Transaction(
        **transaction.model_dump(), 
        student_id=student_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_student_transactions(db: Session, student_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.student_id == student_id).order_by(models.Transaction.ts.desc()).offset(skip).limit(limit).all()

def create_income_period(db: Session, student_id: int, period: schemas.IncomePeriodCreate):
    """
    Crea un nuevo período de presupuesto y calcula si debe estar activo.
    Si está activo, desactiva los demás.
    """
    
    # 1. Calcular el estado 'is_active' basado en las fechas
    now = datetime.now(timezone.utc)
    
    # Asegurarnos de que las fechas del input tengan timezone (asumimos UTC si no)
    start_date_aware = period.start_date.replace(tzinfo=timezone.utc) if period.start_date.tzinfo is None else period.start_date
    end_date_aware = period.end_date.replace(tzinfo=timezone.utc) if period.end_date.tzinfo is None else period.end_date

    is_now_active = (start_date_aware <= now) and (now <= end_date_aware)

    # 2. Si este nuevo período está activo, desactivamos los demás
    if is_now_active:
        db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == student_id,
            models.IncomePeriod.is_active == True
        ).update({"is_active": False})
    
    # 3. Crear el objeto de la base de datos
    db_period = models.IncomePeriod(
        **period.model_dump(),
        student_id=student_id,
        is_active=is_now_active # <-- Usamos el valor calculado
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period

def get_current_budget_status(db: Session, student_id: int):
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.is_active == True
    ).first()

    if not active_period:
        return None 

    total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.income_period_id == active_period.income_period_id # Filtro por ID de período
    ).scalar()
    
    total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0

    # CORRECCIÓN DE NOMBRE:
    remaining_budget = float(active_period.total_income) - total_spent

    now = datetime.now(timezone.utc)
    end_date_aware = active_period.end_date
    if end_date_aware.tzinfo is None:
         end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)
         
    days_left = (end_date_aware - now).days if end_date_aware > now else 0

    return schemas.BudgetStatus(
        income_period_id=active_period.income_period_id, # Nombre de ID corregido
        total_income=float(active_period.total_income), # Nombre de campo corregido
        start_date=active_period.start_date,
        end_date=active_period.end_date,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        days_left=days_left,
        is_active=active_period.is_active
    )

def get_income_period_by_id(db: Session, period_id: int, student_id: int):
    return db.query(models.IncomePeriod).filter(
        models.IncomePeriod.income_period_id == period_id, # Nombre de ID corregido
        models.IncomePeriod.student_id == student_id
    ).first()

def update_income_period(db: Session, period_id: int, student_id: int, period_update: schemas.IncomePeriodCreate):
    db_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.income_period_id == period_id, # Nombre de ID corregido
        models.IncomePeriod.student_id == student_id
    ).first()

    if not db_period:
        return None

    # CORRECCIÓN DE NOMBRE:
    db_period.total_income = period_update.total_income
    db_period.start_date = period_update.start_date
    db_period.end_date = period_update.end_date

    db.commit()
    db.refresh(db_period)
    return db_period

def get_budget_history(db: Session, student_id: int, days_history: int = 60):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_history)
    history = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.end_date <= end_date
    ).order_by(models.IncomePeriod.start_date.desc()).all()
    return history

def get_association_rules(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.AssociationRule).order_by(
        models.AssociationRule.lift.desc()
    ).offset(skip).limit(limit).all()

# --- DEMO DATA Y RECOMENDACIONES (Movidas a profiling.py) ---
# (La función 'create_demo_data' y 'generate_recommendations' 
# deben estar en 'analytics/profiling.py' para evitar errores de importación)

def get_triggered_rules(db: Session, student_id: int):
    """
    Compara las reglas de Apriori con los gastos recientes de un usuario
    y devuelve las reglas que el usuario ha "activado".
    """
    
    # 1. Obtener todas las reglas fuertes del sistema
    rules = get_association_rules(db, limit=50) # Obtenemos las 50 reglas más fuertes
    
    # 2. Obtener las categorías en las que ha gastado el usuario recientemente (ej. últimos 30 días)
    recent_transactions = db.query(models.Transaction.category_id).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= (datetime.now(timezone.utc) - timedelta(days=30))
    ).distinct().all()
    
    recent_category_ids = {t[0] for t in recent_transactions}
    recent_categories_db = db.query(models.Category).filter(models.Category.id.in_(recent_category_ids)).all()
    recent_category_names = {c.name for c in recent_categories_db}
    
    # 3. Filtrar las reglas que el usuario ha activado
    triggered_rules = []
    for rule in rules:
        antecedent_set = set(rule.antecedents)
        consequent_set = set(rule.consequents)
        
        # Si el usuario ha gastado en AMBAS partes de la regla...
        if antecedent_set.issubset(recent_category_names) and consequent_set.issubset(recent_category_names):
            # ... entonces esta regla es "relevante" para él.
            triggered_rules.append(rule)
            
    return triggered_rules