# backend/routers/transactions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import crud, models, schemas
from database import get_db
from routers.auth import get_current_student
from notifications import send_fcm_notification

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction_for_current_user(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Crea una nueva transacción (gasto o ingreso) para el usuario autenticado.
    Verifica el presupuesto y envía notificaciones si es necesario.
    """
    
    if transaction.type == 'gasto':
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == current_student.id,
            models.IncomePeriod.is_active == True
        ).first()

        if active_period:
            total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
                models.Transaction.student_id == current_student.id,
                models.Transaction.type == 'gasto',
                models.Transaction.ts >= active_period.start_date,
                models.Transaction.ts <= active_period.end_date
            ).scalar()
            total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0
            
            budget_amount = float(active_period.amount)
            new_total_spent = total_spent + transaction.amount
            
            # --- LÓGICA DE NOTIFICACIONES CORREGIDA ---
            
            current_percentage = (total_spent / budget_amount) * 100 if budget_amount > 0 else 0
            new_percentage = (new_total_spent / budget_amount) * 100 if budget_amount > 0 else 0

            # 1. Si el nuevo total es >= 100%, envía esta notificación SIEMPRE.
            if new_percentage >= 100:
                # (Solo la enviamos si el gasto anterior era menor a 100 para no spamear,
                # pero si quieres spamear, quita la segunda condición)
                if current_percentage < 100: # <-- ESTO ES RECOMENDADO PARA EVITAR SPAM
                    send_fcm_notification(
                        token=current_student.fcm_token,
                        title="🚫 ¡Presupuesto Excedido!",
                        body=f"Has excedido tu presupuesto. Este gasto de ${transaction.amount} se registrará como Gasto Extra."
                    )
            
            # 2. Si (si no) el gasto HACE que se cruce el 90% (y aún no se había cruzado)
            elif current_percentage <= 90 and new_percentage >= 90:
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="🚨 ¡Presupuesto Bajo!",
                    body=f"Has gastado más del 90% de tu presupuesto (${new_total_spent:.2f} de ${budget_amount:.2f})."
                )
            
            # 3. Si (si no) el gasto HACE que se cruce el 50% (y aún no se había cruzado)
            elif current_percentage <= 50 and new_percentage >= 50:
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="⚠️ Mitad de Presupuesto",
                    body=f"Ya has utilizado el {new_percentage:.0f}% de tu presupuesto (${new_total_spent:.2f} de ${budget_amount:.2f})."
                )
            
            print("LOG: Verificación de presupuesto y notificaciones completada.")
    
    # Siempre crea la transacción (incluso si excede el presupuesto)
    new_transaction = crud.create_student_transaction(db=db, transaction=transaction, student_id=current_student.id)
    
    return new_transaction

# --- Endpoints GET (sin cambios) ---

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions_for_current_user(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    return crud.get_student_transactions(db, student_id=current_student.id, skip=skip, limit=limit)

@router.get("/categories/", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)