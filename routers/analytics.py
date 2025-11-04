# backend/routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List 
import models, schemas, crud
from database import get_db
from routers.auth import get_current_student
# Importamos las funciones y el mapa que necesitamos DESDE PROFILING
from analytics.profiling import (
    train_and_cluster_students, 
    get_student_features, 
    PROFILE_MAP
)
from analytics import profiling # Importa el módulo profiling para la demo

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# --- ENDPOINT DE PERFIL ACTUALIZADO ---
@router.post("/profile", response_model=schemas.ProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Calcula, justifica y devuelve el perfil financiero del usuario autenticado.
    """
    
    # 1. Obtenemos las métricas individuales (EL "POR QUÉ")
    # Llama a la función desde profiling, no desde crud
    user_metrics = get_student_features(db, student_id=current_student.id)

    # 2. Obtenemos el resultado del clustering (EL "QUIÉN")
    results_df = train_and_cluster_students(db)

    # --- Manejo de Errores ---
    if results_df is None or results_df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suficientes datos de usuarios en el sistema para generar perfiles.")
    
    user_result = results_df[results_df['student_id'] == current_student.id]
    
    if user_result.empty or user_metrics is None:
        profile_data = PROFILE_MAP[4] # Perfil "El Explorador Financiero"
        return schemas.ProfileResponse(
            profile=profile_data["profile"],
            justification="Aún estás empezando. Sigue registrando gastos para que podamos encontrar tus patrones.",
            recommendation=profile_data["recommendation"]
        )

    # --- 3. Construcción de la Respuesta ---
    profile_cluster_id = user_result.iloc[0]['cluster']
    profile_name = user_result.iloc[0]['profile_name']
    recommendation = PROFILE_MAP[profile_cluster_id]["recommendation"]
    
    savings_rate_pct = round(user_metrics['savings_rate'] * 100)
    discretionary_ratio_pct = round(user_metrics['discretionary_ratio'] * 100)

    justification = f"Te asignamos este perfil porque, según tus últimos 60 días, tu tasa de ahorro es de aprox. **{savings_rate_pct}%** y el **{discretionary_ratio_pct}%** de tus gastos se destina a categorías discrecionales (ocio, compras, etc.)."
    
    if profile_name == "El Guardián del Futuro":
        justification = f"¡Felicidades! Te identificamos como un Guardián porque tienes una excelente tasa de ahorro (aprox. **{savings_rate_pct}%**) y mantienes tus gastos discrecionales muy bajos (aprox. **{discretionary_ratio_pct}%**)."
    elif profile_name == "El Urbanita Social":
        justification = f"Te identificamos como un Urbanita Social porque tu tasa de ahorro es baja (aprox. **{savings_rate_pct}%**) y una gran parte de tus gastos se va a categorías discrecionales (aprox. **{discretionary_ratio_pct}%**)."

    return schemas.ProfileResponse(
        profile=profile_name,
        justification=justification,
        recommendation=recommendation
    )

# --- Endpoint para obtener Reglas Apriori ---
@router.get("/rules", response_model=List[schemas.AssociationRuleResponse], summary="Obtiene las reglas de asociación (Apriori)")
def get_apriori_rules(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Obtiene la lista de reglas de asociación de gastos (Apriori)
    que han sido calculadas por el sistema.
    """
    rules = crud.get_association_rules(db)
    return rules

# --- Endpoint de Demo Apriori ---
@router.post("/run-apriori-demo", response_model=List[schemas.AssociationRuleResponse], summary="[DEMO] Ejecuta Apriori con datos de prueba")
def run_apriori_analysis_demo(db: Session = Depends(get_db)):
    """
    ¡SOLO PARA DEMOSTRACIÓN!
    1. Borra datos antiguos y crea un set de datos de prueba con patrones.
    2. Ejecuta el algoritmo Apriori sobre esos datos.
    3. Guarda y devuelve las reglas encontradas.
    """
    crud.create_demo_data(db)
    found_rules = profiling.run_apriori_analysis(db)
    return found_rules

# --- Endpoint de Recomendaciones ---
@router.get("/recommendations", response_model=List[schemas.Recommendation], summary="Obtiene recomendaciones personalizadas")
def get_recommendations_for_user(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Genera y devuelve una lista de recomendaciones personalizadas
    (basadas en K-Means y Apriori) para el usuario autenticado.
    """
    recommendations = crud.generate_recommendations(db=db, student_id=current_student.id)
    
    if not recommendations:
        return [
            schemas.Recommendation(
                type="general",
                title="¡Sigue así!",
                body="Continúa registrando tus gastos para recibir análisis y consejos personalizados."
            )
        ]
        
    return recommendations