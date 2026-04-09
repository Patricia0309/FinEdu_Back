from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
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
    Crea una nueva transacción y activa alertas de presupuesto según el porcentaje de gasto.
    """
    
    if transaction.type == 'gasto':
        # 1. Buscar el periodo de presupuesto activo
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == current_student.id,
            models.IncomePeriod.is_active == True
        ).first()

        if active_period:
            # 2. Calcular cuánto se ha gastado HASTA AHORA (antes de esta transacción)
            total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
                models.Transaction.student_id == current_student.id,
                models.Transaction.type == 'gasto',
                models.Transaction.ts >= active_period.start_date,
                models.Transaction.ts <= active_period.end_date
            ).scalar()
            
            total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0
            budget_amount = float(active_period.total_income)
            new_total_spent = total_spent + transaction.amount
            
            # 3. Calcular porcentajes
            current_percentage = (total_spent / budget_amount) * 100 if budget_amount > 0 else 0
            new_percentage = (new_total_spent / budget_amount) * 100 if budget_amount > 0 else 0

            # --- LOGS DE DEPURACIÓN PARA DOCKER ---
            print(f"--- ANALIZANDO PRESUPUESTO (Estudiante: {current_student.id}) ---")
            print(f"Presupuesto Total: ${budget_amount}")
            print(f"Gastado antes: ${total_spent} ({current_percentage:.2f}%)")
            print(f"Gasto nuevo: ${transaction.amount}")
            print(f"Total después: ${new_total_spent} ({new_percentage:.2f}%)")

            # --- LÓGICA DE NOTIFICACIONES MEJORADA ---
            # Caso 1: Se excede el 100% por primera vez
            if new_percentage >= 100 and current_percentage < 100:
                print("⚠️ DISPARADOR: Presupuesto Excedido")
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="🚫 ¡Presupuesto Excedido!",
                    body=f"Has superado tu límite de ${budget_amount:.2f}. Total gastado: ${new_total_spent:.2f}."
                )
            
            # Caso 2: Se cruza el umbral del 90%
            elif new_percentage >= 90 and current_percentage < 90:
                print("⚠️ DISPARADOR: Alerta 90%")
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="🚨 ¡Cuidado! Presupuesto Bajo",
                    body=f"Has gastado más del 90% de tu presupuesto disponible."
                )
            
            # Caso 3: Se cruza el umbral del 50%
            elif new_percentage >= 50 and current_percentage < 50:
                print("⚠️ DISPARADOR: Alerta 50%")
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="⚠️ Mitad del Camino",
                    body=f"Ya has utilizado el {new_percentage:.0f}% de tu presupuesto mensual."
                )
            
            else:
                print("ℹ️ INFO: No se cruzó ningún umbral de notificación.")

    # 4. Guardar la transacción en la base de datos
    new_transaction = crud.create_student_transaction(
        db=db, 
        transaction=transaction, 
        student_id=current_student.id
    )
    
    return new_transaction

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions_for_current_user(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    return crud.get_student_transactions(db, student_id=current_student.id, skip=skip, limit=limit)

@router.get("/categories/", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)