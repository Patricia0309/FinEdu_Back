# backend/routers/auth.py

from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from email_utils import send_otp_email
# LA LÍNEA CLAVE A CORREGIR:
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, selectinload
from jose import JWTError, jwt

import crud
import models
import schemas
import security
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

@router.post("/auth/recover-password")
def recover_password(request: schemas.PasswordRecoveryRequest, db: Session = Depends(get_db)):
    user = crud.get_student_by_email(db, email=request.email)
    if not user:
        # Mantenemos el mensaje genérico por seguridad
        return {"msg": "Si el correo existe, recibirás un código."}

    # 1. Generamos el código de 6 dígitos
    otp_code = security.generate_otp_code()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=10)

    # 2. Guardamos en la base de datos
    db.query(models.PasswordResetCode).filter(models.PasswordResetCode.email == user.email).delete()
    
    new_reset_code = models.PasswordResetCode(
        email=user.email,
        code=otp_code,
        expires_at=expiration
    )
    db.add(new_reset_code)
    db.commit()

    # 3. 🚀 MANDAR EL CORREO REAL
    # Aquí es donde ocurre la magia. Usamos el correo del usuario y el código generado.
    exito_envio = send_otp_email(user.email, otp_code)
    
    if not exito_envio:
        # Si el servidor de correos falla, le avisamos al sistema
        raise HTTPException(
            status_code=500, 
            detail="No se pudo enviar el correo de recuperación. Intenta más tarde."
        )

    # Mantenemos el print solo para que tú sigas viendo qué pasa en la consola
    print(f"\n🔢 CÓDIGO ENVIADO A {user.email}: [{otp_code}]")
    print(f"Válido hasta: {expiration}\n")

    return {"msg": "Código enviado exitosamente al correo."}

@router.post("/auth/reset-password")
def reset_password(data: schemas.PasswordResetConfirmOTP, db: Session = Depends(get_db)):
    # Buscamos el código en la base de datos
    db_code = db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.email == data.email,
        models.PasswordResetCode.code == data.code
    ).first()

    # Validamos si existe y si no ha expirado
    if not db_code or db_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")

    user = crud.get_student_by_email(db, email=data.email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Todo bien: cambiamos contraseña y borramos el código usado
    user.hashed_password = security.get_password_hash(data.new_password)
    db.delete(db_code) # El código solo sirve una vez
    db.commit()

    return {"msg": "Contraseña actualizada exitosamente"}