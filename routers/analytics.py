from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas
from database import get_db
from routers.auth import get_current_student
from analytics.profiling import train_and_cluster_students

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/profile", response_model=schemas.ProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    results_df = train_and_cluster_students(db)
    if results_df is None or results_df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suficientes datos para generar perfiles.")
    user_result = results_df[results_df['student_id'] == current_student.id]
    if user_result.empty:
        return {"profile": "El Explorador Financiero", "description": "Aún no tienes suficientes datos para un perfil. ¡Sigue registrando!"}
    return {
        "profile": user_result.iloc[0]['profile_name'],
        "description": user_result.iloc[0]['profile_desc']
    }