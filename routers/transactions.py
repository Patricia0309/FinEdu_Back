from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
    active_period = None
    if transaction.type == 'expense':
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == current_student.id,
            models.IncomePeriod.is_active == True
        ).first()

        if active_period:
            total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
                models.Transaction.student_id == current_student.id,
                models.Transaction.type == 'gasto', # O 'expense' si corregiste
                models.Transaction.ts >= active_period.start_date,
                models.Transaction.ts <= active_period.end_date
            ).scalar()
            total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0
            
            # --- LÓGICA DE NOTIFICACIONES ---
            budget_amount = float(active_period.amount)
            new_total_spent = total_spent + transaction.amount
            
            if new_total_spent > budget_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Este gasto excede tu presupuesto. Te quedan ${budget_amount - total_spent}."
                )

            # Calcular porcentaje gastado DESPUÉS de este gasto
            spent_percentage = (new_total_spent / budget_amount) * 100

            # Umbrales (puedes ajustarlos)
            if spent_percentage >= 90 and total_spent < (budget_amount * 0.9): # Enviar solo una vez al cruzar el 90%
                send_fcm_notification(
                    student=current_student,
                    title="🚨 ¡Presupuesto Bajo!",
                    body=f"Has gastado más del 90% de tu presupuesto (${new_total_spent:.2f} de ${budget_amount:.2f})."
                )
            elif spent_percentage >= 50 and total_spent < (budget_amount * 0.5): # Enviar solo una vez al cruzar el 50%
                 send_fcm_notification(
                    student=current_student,
                    title="⚠️ Mitad de Presupuesto",
                    body=f"Ya has utilizado el {spent_percentage:.0f}% de tu presupuesto (${new_total_spent:.2f} de ${budget_amount:.2f})."
                )
            # --- FIN LÓGICA NOTIFICACIONES ---

    # Crear la transacción (movido al final)
    new_transaction = crud.create_student_transaction(db=db, transaction=transaction, student_id=current_student.id)
    
    # Si fue un ingreso y actualizó el período, podríamos notificarlo
    if transaction.type == 'income' and active_period:
        # Lógica opcional para actualizar active_period.amount si decides
        # que los ingresos extra aumenten el presupuesto y notificarlo.
        pass
        
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