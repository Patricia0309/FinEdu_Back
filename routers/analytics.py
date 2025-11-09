# backend/routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas, crud
from database import get_db
from routers.auth import get_current_student
# Importamos las funciones desde 'profiling'
from analytics.profiling import (
    train_and_cluster_students, 
    get_student_features, 
    PROFILE_MAP,
    run_apriori_analysis,
    generate_recommendations,
    create_demo_data
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/profile", response_model=schemas.ProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    user_metrics = get_student_features(db, student_id=current_student.id)
    results_df = train_and_cluster_students(db)

    if results_df is None or results_df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suficientes datos de usuarios en el sistema para generar perfiles.")
    
    user_result = results_df[results_df['student_id'] == current_student.id]
    
    if user_result.empty or user_metrics is None:
        profile_data = PROFILE_MAP[4]
        return schemas.ProfileResponse(
            profile=profile_data["profile"],
            justification="Aún estás empezando. Sigue registrando gastos para que podamos encontrar tus patrones.",
            recommendation=profile_data["recommendation"]
        )

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

@router.get("/rules", response_model=List[schemas.AssociationRuleResponse], summary="Obtiene las reglas de asociación (Apriori)")
def get_apriori_rules(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    rules = crud.get_association_rules(db)
    return rules

@router.post("/run-apriori-demo", response_model=List[schemas.AssociationRuleResponse], summary="[DEMO] Ejecuta Apriori con datos de prueba")
def run_apriori_analysis_demo(db: Session = Depends(get_db)):
    create_demo_data(db) # Llama a la función desde profiling
    found_rules = run_apriori_analysis(db) # Llama a la función desde profiling
    return found_rules

@router.get("/recommendations", response_model=List[schemas.Recommendation], summary="Obtiene recomendaciones personalizadas")
def get_recommendations_for_user(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    recommendations = generate_recommendations(db=db, student_id=current_student.id)
    if not recommendations:
        return [
            schemas.Recommendation(
                type="general",
                title="¡Sigue así!",
                body="Continúa registrando tus gastos para recibir análisis y consejos personalizados."
            )
        ]
    return recommendations

@router.get("/me/rules", response_model=List[schemas.AssociationRuleResponse], summary="Obtiene las 10 reglas más sobresalientes que el usuario ha 'activado'")
def get_my_triggered_rules(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Obtiene una lista de las 10 reglas de asociación más fuertes
    que el comportamiento reciente del usuario (últimos 30 días) ha activado.
    """
    rules = crud.get_triggered_rules(db=db, student_id=current_student.id)
    return rules[:10]

@router.get("/tendency", response_model=schemas.BudgetTendencyResponse, summary="Compara el presupuesto actual con el anterior")
def get_spending_tendency(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Compara el gasto del período de presupuesto activo actual
    con el gasto del período completado más reciente.
    """
    tendency_data = crud.get_budget_tendency(db=db, student_id=current_student.id)
    if not tendency_data.current_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un período de presupuesto activo. Por favor, crea uno."
        )
    return tendency_data