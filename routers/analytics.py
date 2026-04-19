# backend/routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
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
    # 1. Contamos cuántos GASTOS reales tiene el usuario
    user_expenses_count = db.query(models.Transaction).filter(
        models.Transaction.student_id == current_student.id,
        models.Transaction.type == 'gasto'
    ).count()

    # 2. Si tiene menos de 15, activamos el modo "Progreso"
    if user_expenses_count < 15:
        return schemas.ProfileResponse(
            profile="Perfil en proceso...",
            is_calculating=True,
            current_count=user_expenses_count,
            goal=15,
            justification=f"Estamos analizando tus hábitos. Te faltan {15 - user_expenses_count} transacciones para desbloquear tu perfil inteligente.",
            recommendation="Intenta registrar todos tus gastos, por pequeños que sean (café, copias, transporte)."
        )
    # 3. Si ya tiene 15 o más, procedemos con la lógica normal
    user_metrics = get_student_features(db, student_id=current_student.id)
    results_df = train_and_cluster_students(db)

    # Caso donde el sistema global aún no tiene 5 usuarios (mínimo para K-Means)
    if results_df is None or results_df.empty:
        return schemas.ProfileResponse(
            profile="Explorador Financiero",
            justification="Ya tienes suficientes datos, pero estamos esperando a que más compañeros se unan al análisis global para compararte.",
            recommendation="¡No te detengas! Tu constancia es el primer paso para el éxito."
        )
    user_result = results_df[results_df['student_id'] == current_student.id]
    
    # Si el usuario tiene los 15 gastos pero por alguna razón el algoritmo no lo incluyó
    if user_result.empty or user_metrics is None:
        profile_data = PROFILE_MAP[4] # Perfil "Explorador Financiero" por defecto
        return schemas.ProfileResponse(
            profile=profile_data["profile"],
            justification="Tu perfil se está terminando de procesar. ¡Vuelve en unos minutos!",
            recommendation=profile_data["recommendation"]
        )

    profile_cluster_id = user_result.iloc[0]['cluster']
    profile_name = user_result.iloc[0]['profile_name']
    recommendation = PROFILE_MAP[profile_cluster_id]["recommendation"]
    
    savings_rate_pct = round(user_metrics['savings_rate'] * 100)
    discretionary_ratio_pct = round(user_metrics['discretionary_ratio'] * 100)

    justification = f"Te asignamos este perfil porque tu tasa de ahorro es de aprox. {savings_rate_pct}% y destinas un {discretionary_ratio_pct}% a gastos no esenciales."
    
    if profile_name == "El Guardián del Futuro":
        justification = f"¡Felicidades! Eres un Guardián por tu excelente ahorro ({savings_rate_pct}%) y tu control estricto sobre gastos innecesarios."
    
    elif profile_name == "El Urbanita Social":
        justification = f"Eres un Urbanita porque priorizas las experiencias sociales. Tu gasto discrecional ({discretionary_ratio_pct}%) es alto, ¡ojo con el fondo de emergencia!"
    
    elif profile_name == "El Arquitecto Financiero":
        justification = f"Eres un Arquitecto porque mantienes un equilibrio perfecto. Tu ahorro del {savings_rate_pct}% muestra que planeas a largo plazo con maestría."
    
    elif profile_name == "El Coleccionista de Experiencias":
        justification = f"Eres un Coleccionista porque prefieres invertir en momentos actuales. Tu tasa de ahorro es moderada ({savings_rate_pct}%), pero tu flujo de gastos es constante."
    
    elif profile_name == "El Explorador Financiero":
        justification = f"Eres un Explorador porque estás descubriendo tu camino. Con un ahorro del {savings_rate_pct}%, es el momento ideal para definir metas claras."

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

@router.get("/category-spending", response_model=Optional[schemas.CategorySpendingResponse])
def get_spending_by_category(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    report = crud.get_category_spending_report(db, student_id=current_student.id)
    if not report:
        # Si no hay presupuesto activo, devolvemos null o un error 404
        return None
    return report