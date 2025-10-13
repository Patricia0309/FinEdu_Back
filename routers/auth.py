# backend/routers/auth.py

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db
from security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import models
from security import SECRET_KEY, ALGORITHM

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint de Login. Recibe un email (en el campo 'username') y una contraseña.
    Devuelve un token de acceso si las credenciales son correctas.
    """
    # 1. Busca al usuario por su email (que viene en el campo 'username' del formulario)
    student = crud.get_student_by_email(db, email=form_data.username)

    # 2. Si no existe el usuario O la contraseña es incorrecta, devuelve un error
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Si todo es correcto, crea el token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": student.email, "student_id": student.id}, 
        expires_delta=access_token_expires
    )

    # 4. Devuelve el token
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependencia para obtener el usuario actual a partir de un token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token para obtener el payload (los datos)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        student_id: int = payload.get("student_id")
        if email is None or student_id is None:
            raise credentials_exception
        # Podríamos crear un esquema Pydantic para el payload del token si quisiéramos
    except JWTError:
        raise credentials_exception
    
    # Busca al estudiante en la base de datos
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student is None:
        raise credentials_exception
    return student
