# backend/routers/students.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import crud
import schemas
from database import get_db
from routers.auth import get_current_student
import models

# Creamos un router. Podemos darle un prefijo y etiquetas.
# prefix="/students": Todas las rutas en este archivo empezarán con /students
# tags=["Students"]: Agrupa estas rutas bajo la etiqueta "Students" en los docs.
router = APIRouter(
    prefix="/students",
    tags=["Students"]
)

# NOTA: La ruta ahora es "/" porque el prefijo "/students" ya está incluido.
# La URL final seguirá siendo POST /students/
@router.post("/", response_model=schemas.Student, status_code=status.HTTP_201_CREATED)
def create_student_endpoint(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo estudiante en la base de datos.
    - **display_name**: Nombre visible del estudiante.
    - **email**: Email del estudiante (opcional y debe ser único).
    """
    try:
        new_student = crud.create_student(db=db, student=student)
        return new_student
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

@router.get("/me", response_model=schemas.Student)
async def read_students_me(current_student: models.Student = Depends(get_current_student)):
    """
    Devuelve la información del estudiante actualmente autenticado.
    Requiere un token de acceso válido.
    """
    return current_student