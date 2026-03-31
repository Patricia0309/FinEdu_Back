# backend/routers/budgets.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import schemas, crud, models
from database import get_db
from routers.auth import get_current_student

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)

@router.post("/income-period", response_model=schemas.IncomePeriod, status_code=status.HTTP_201_CREATED)
def create_new_income_period(
    period: schemas.IncomePeriodCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    return crud.create_income_period(db=db, student_id=current_student.id, period=period)

@router.put("/income-period/{period_id}", response_model=schemas.IncomePeriod)
def update_existing_income_period(
    period_id: int,
    period_update: schemas.IncomePeriodCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    updated_period = crud.update_income_period(
        db=db,
        period_id=period_id,
        student_id=current_student.id,
        period_update=period_update
    )
    if updated_period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período de presupuesto no encontrado o no pertenece al usuario."
        )
    return updated_period

@router.get("/income-period/{period_id}", response_model=schemas.IncomePeriod)
def read_specific_income_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    db_period = crud.get_income_period_by_id(
        db=db,
        period_id=period_id,
        student_id=current_student.id
    )
    if db_period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Período de presupuesto no encontrado o no pertenece al usuario."
        )
    return db_period

@router.get("/status", response_model=Optional[schemas.BudgetStatus])
def get_budget_status(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    budget_status = crud.get_current_budget_status(db=db, student_id=current_student.id)
    if not budget_status:
        return None
    return budget_status

# --- ENDPOINT DE HISTORIAL (VERSIÓN CORRECTA) ---
@router.get("/history", response_model=List[schemas.IncomePeriodHistory])
def get_budget_history(
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(get_current_student)
):
    # 1. Obtenemos la fecha y hora actual
    now = datetime.now() # O datetime.now(timezone.utc) si tus fechas de BD tienen timezone

    # 2. Consultamos la BD
    historical_budgets = crud.get_budget_history(db=db, student_id=current_user.id)

    # 3. Construimos la lista de respuesta
    response_list = []
    
    for budget in historical_budgets:
        
        # 4. Calculamos el gasto total
        total_spent_decimal = sum(
            t.amount for t in budget.transactions if t.type == 'gasto' # 'gasto' o 'expense'
        )
        total_spent_float = float(total_spent_decimal)
        
        # 6. Calculamos el restante
        remaining = budget.total_income - total_spent_float
        
        # 7. Creamos el objeto de respuesta Pydantic
        history_item = schemas.IncomePeriodHistory(
            income_period_id=budget.income_period_id,
            start_date=budget.start_date,
            end_date=budget.end_date,
            total_income=budget.total_income,
            total_spent=total_spent_float,
            remaining_budget=remaining,
            is_active=False
        )
        response_list.append(history_item)

    # 8. Devolvemos la lista
    return response_list