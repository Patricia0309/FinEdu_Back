from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone
import crud, models, schemas
from database import get_db
from routers.auth import get_current_student
from notifications import send_fcm_notification

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=schemas.Transaction, status_code=201)
def create_transaction_for_current_user(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    """
    Crea una nueva transacción y activa alertas de presupuesto según el porcentaje de gasto.
    """
    target_date = transaction.ts or datetime.now(timezone.utc)
    transaction.ts = target_date
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == current_student.id,
        models.IncomePeriod.start_date <= target_date,
        models.IncomePeriod.end_date >= target_date
    ).first()

    if not active_period:
        raise HTTPException(
            status_code=404, 
            detail="No existe un periodo de presupuesto para la fecha seleccionada."
        )
    
    transaction.income_period_id = active_period.income_period_id

    if transaction.type == 'gasto':

        total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.student_id == current_student.id,
            models.Transaction.type == 'gasto',
            models.Transaction.income_period_id == active_period.income_period_id
        ).scalar()

        total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0
        budget_amount = float(active_period.total_income)
        new_total_spent = total_spent + transaction.amount
            
        # 3. Calcular porcentajes
        current_percentage = (total_spent / budget_amount) * 100 if budget_amount > 0 else 0
        new_percentage = (new_total_spent / budget_amount) * 100 if budget_amount > 0 else 0

        # --- LOGS DE DEPURACIÓN PARA DOCKER ---
        print(f"--- ANALIZANDO PRESUPUESTO (Estudiante: {current_student.id}) ---")
        print(f"Presupuesto Total: ${budget_amount}")
        print(f"Gastado antes: ${total_spent} ({current_percentage:.2f}%)")
        print(f"Gasto nuevo: ${transaction.amount}")
        print(f"Total después: ${new_total_spent} ({new_percentage:.2f}%)")

        # --- LÓGICA DE NOTIFICACIONES MEJORADA ---
        # Caso 1: Se excede el 100% por primera vez
        if new_percentage >= 100 and current_percentage < 100:
            print("⚠️ DISPARADOR: Presupuesto Excedido")
            send_fcm_notification(
                token=current_student.fcm_token,
                title="🚫 ¡Presupuesto Excedido!",
                body=f"Has superado tu límite de ${budget_amount:.2f}."
            )
        
        # Caso 2: Se cruza el umbral del 90%
        elif new_percentage >= 90 and current_percentage < 90:
            print("⚠️ DISPARADOR: Alerta 90%")
            send_fcm_notification(
                token=current_student.fcm_token,
                title="🚨 ¡Cuidado! Presupuesto Bajo",
                body=f"Has gastado más del 90% de tu presupuesto disponible."
            )
        
        # Caso 3: Se cruza el umbral del 50%
        elif new_percentage >= 50 and current_percentage < 50:
            print("⚠️ DISPARADOR: Alerta 50%")
            send_fcm_notification(
                token=current_student.fcm_token,
                title="⚠️ Mitad del Camino",
                body=f"Ya has utilizado el {new_percentage:.0f}% de tu presupuesto mensual."
            )
        
        else:
            print("ℹ️ INFO: No se cruzó ningún umbral de notificación.")

    # 4. Guardar la transacción en la base de datos
    new_transaction = crud.create_student_transaction(
        db=db, 
        transaction=transaction, 
        student_id=current_student.id
    )

    if transaction.type == 'gasto':
        # Contamos cuántos gastos tiene el usuario ahora
        user_expenses_count = db.query(models.Transaction).filter(
            models.Transaction.student_id == current_student.id,
            models.Transaction.type == 'gasto'
        ).count()

        print(f"📊 Progreso de perfil para {current_student.display_name}: {user_expenses_count}/15")

        # Si acaba de llegar exactamente a 15
        if user_expenses_count == 15:
            print(f"🎯 HITO ALCANZADO: Enviando notificación de perfil a {current_student.id}")
            
            try:
                send_fcm_notification(
                    token=current_student.fcm_token,
                    title="🔓 ¡Perfil Inteligente Desbloqueado!",
                    body="Has registrado 15 gastos. ¡Entra ya para conocer tu perfil financiero y consejos!",
                )
            except Exception as e:
                print(f"❌ Error al enviar notificación de hito: {e}")
    
        if user_expenses_count >= 5: 
            try:
                # Buscamos si este gasto activa una predicción según tus reglas reales
                matched_rule = crud.get_predictive_rule_match(db, category_id=new_transaction.category_id)

                if matched_rule and current_student.fcm_token:
                    # Obtenemos el nombre de la categoría actual para el mensaje
                    current_cat = db.query(models.Category).get(new_transaction.category_id)
                    # Tomamos la primera predicción (consecuente) de la lista
                    proxima_compra = matched_rule.consequents[0] 
                    
                    print(f"🔮 PREDICCIÓN: Detectada regla tras gasto en {current_cat.name}")
                    
                    send_fcm_notification(
                        token=current_student.fcm_token,
                        title="🔮 Tip Predictivo FindEdu",
                        body=f"Vimos que gastaste en {current_cat.name}. Suele seguir un gasto en {proxima_compra}. ¡Cuida tu presupuesto!",
                        data={"screen": "analysis"}
                    )
            except Exception as e:
                print(f"❌ Error en lógica predictiva Apriori: {e}")

    return new_transaction

@router.get("/", response_model=List[schemas.Transaction])
def read_transactions_for_current_user(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student)
):
    return crud.get_student_transactions(db, student_id=current_student.id, skip=skip, limit=limit)

@router.get("/categories/", response_model=List[schemas.Category])
def read_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

