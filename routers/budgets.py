# backend/routers/budgets.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import schemas, crud, models
from database import get_db
from routers.auth import get_current_student

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)

@router.post("/income-period", response_model=schemas.IncomePeriod, status_code=201)
def create_new_income_period(
    period: schemas.IncomePeriodCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Crea un nuevo período de presupuesto para el usuario autenticado.
    Esto desactivará cualquier período anterior.
    """
    return crud.create_income_period(db=db, student_id=current_student.id, period=period)

@router.get("/status", response_model=schemas.BudgetStatus)
def get_budget_status(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Obtiene el estado actual del presupuesto (período activo,
    gasto total, saldo restante) para el usuario autenticado.
    """
    status = crud.get_current_budget_status(db=db, student_id=current_student.id)
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes un período de presupuesto activo."
        )
    return status