# backend/routers/auth.py

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
# LA LÍNEA CLAVE A CORREGIR:
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, selectinload
from jose import JWTError, jwt

import crud
import models
import schemas
from database import get_db
from security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

router = APIRouter(tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = crud.get_student_by_email(db, email=form_data.username)
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.email, "student_id": student.id}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        student_id: int = payload.get("student_id")
        if email is None or student_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    student = db.query(models.Student).options(
    selectinload(models.Student.favorite_categories)
    ).filter(models.Student.id == student_id).first()

    if student is None:
        raise credentials_exception
    return student