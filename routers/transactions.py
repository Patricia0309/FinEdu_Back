from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import get_db
from routers.auth import get_current_student

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction_for_current_user(
    transaction: schemas.TransactionCreate, 
    db: Session = Depends(get_db), 
    current_student: models.Student = Depends(get_current_student)
):
    # --- LÓGICA DE PRESUPUESTO INTELIGENTE ---
    if transaction.type == 'expense':
        # 1. Buscar el período de ingreso activo
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == current_student.id,
            models.IncomePeriod.is_active == True
        ).first()

        if active_period:
            # 2. Calcular el gasto total en ese período
            total_spent = db.query(func.sum(models.Transaction.amount)).filter(
                models.Transaction.student_id == current_student.id,
                models.Transaction.type == 'expense',
                models.Transaction.ts >= active_period.start_date,
                models.Transaction.ts <= active_period.end_date
            ).scalar() or 0

            # 3. Verificar si el nuevo gasto excede el presupuesto
            if (total_spent + transaction.amount) > active_period.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Este gasto excede tu presupuesto. Te quedan ${active_period.amount - total_spent}."
                )
            
            # (Aquí iría la lógica para enviar notificaciones de 50%, 10%, etc.)
            print("LOG: Verificación de presupuesto pasada.")
    
    # Si pasa todas las verificaciones (o si es un ingreso), crea la transacción
    return crud.create_student_transaction(db=db, transaction=transaction, student_id=current_student.id)

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions_for_current_user(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    return crud.get_student_transactions(db, student_id=current_student.id, skip=skip, limit=limit)

@router.get("/categories/", response_model=List[schemas.Category], tags=["Categories"])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)