# backend/routers/transactions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import crud, models, schemas
from database import get_db
from routers.auth import get_current_student

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction_for_current_user(
    transaction: schemas.TransactionCreate, 
    db: Session = Depends(get_db), 
    current_student: models.Student = Depends(get_current_student)
):
    """
    Crea una nueva transacción (gasto o ingreso) para el usuario autenticado.
    """
    return crud.create_student_transaction(db=db, transaction=transaction, student_id=current_student.id)

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions_for_current_user(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Obtiene el historial de transacciones del usuario autenticado.
    """
    transactions = crud.get_student_transactions(db, student_id=current_student.id, skip=skip, limit=limit)
    return transactions

# --- Endpoint adicional para obtener la lista de categorías ---
@router.get("/categories/", response_model=List[schemas.Category], tags=["Categories"])
def read_categories(db: Session = Depends(get_db)):
    """
    Obtiene la lista de todas las categorías de transacciones disponibles.
    """
    categories = crud.get_categories(db)
    return categories