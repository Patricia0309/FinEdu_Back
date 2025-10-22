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

@router.get("/income-period/{period_id}", response_model=schemas.IncomePeriod)
def read_specific_income_period(
    period_id: int, # Get the ID from the URL path
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Obtiene un período de presupuesto específico por ID para el usuario autenticado.
    """
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

@router.put("/income-period/{period_id}", response_model=schemas.IncomePeriod)
def update_existing_income_period(
    period_id: int, # Get the ID from the URL path
    period_update: schemas.IncomePeriodCreate, # Get the new data from the body
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Actualiza un período de presupuesto existente para el usuario autenticado.
    """
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