from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import crud, models, schemas
from database import get_db
from routers.auth import get_current_student

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=schemas.Student, status_code=status.HTTP_201_CREATED)
def create_student_endpoint(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    try:
        new_student = crud.create_student(db=db, student=student)
        return new_student
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado.")

@router.get("/me", response_model=schemas.Student)
async def read_students_me(current_student: models.Student = Depends(get_current_student)):
    """
    Devuelve la información del estudiante actualmente autenticado.
    """
    print("Categorías favoritas ANTES de retornar:", current_student.favorite_categories) 
    return current_student

@router.put("/me/categories", response_model=schemas.Student)
def set_student_favorite_categories(
    categories_update: schemas.StudentCategoryUpdate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    updated_student = crud.update_student_favorite_categories(
        db=db, student_id=current_student.id, category_ids=categories_update.category_ids
    )
    return updated_student