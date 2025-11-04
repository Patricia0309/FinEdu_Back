from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from security import get_password_hash
from sqlalchemy import func 
from datetime import datetime, timezone, timedelta
import random

def get_student_by_email(db: Session, email: str):
    return db.query(models.Student).filter(models.Student.email == email).first()

def create_student(db: Session, student: schemas.StudentCreate):
    hashed_password = get_password_hash(student.password)
    db_student = models.Student(email=student.email, display_name=student.display_name, hashed_password=hashed_password)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student_favorite_categories(db: Session, student_id: int, category_ids: List[int]):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return None
    new_categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
    student.favorite_categories = new_categories
    db.commit()
    db.refresh(student)
    return student

def update_student_fcm_token(db: Session, student_id: int, fcm_token: str):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if db_student:
        db_student.fcm_token = fcm_token
        db.commit()
        db.refresh(db_student)
    return db_student

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_initial_categories(db: Session):
    if db.query(models.Category).count() == 0:
        print("Creando categorías iniciales...")
        initial_categories = [
            models.Category(name="Hogar y Servicios"), models.Category(name="Educación"),
            models.Category(name="Salud y Bienestar"), models.Category(name="Deudas y Obligaciones"),
            models.Category(name="Alimentación"), models.Category(name="Transporte"),
            models.Category(name="Compras y Cuidado personal"), models.Category(name="Ocio y Vida Social"),
            models.Category(name="Ahorro e Inversión"), models.Category(name="Gastos Hormiga")
        ]
        db.add_all(initial_categories)
        db.commit()
        print(f"{len(initial_categories)} categorías creadas.")
    else:
        print("Categorías ya pobladas.")

def create_student_transaction(db: Session, transaction: schemas.TransactionCreate, student_id: int):
    # 1. Convierte el schema de Pydantic a un diccionario
    data_dict = transaction.model_dump(exclude_unset=True) # Excluye campos no enviados

    # 2. Renombra la llave 'date' (del frontend) a 'ts' (del modelo DB)
    if 'date' in data_dict:
        data_dict['ts'] = data_dict.pop('date')
    
    # 3. Crea el objeto del modelo usando el diccionario corregido
    db_transaction = models.Transaction(**data_dict, student_id=student_id)
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_student_transactions(db: Session, student_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.student_id == student_id).offset(skip).limit(limit).all()

def create_income_period(db: Session, student_id: int, period: schemas.IncomePeriodCreate):
    # Desactivamos cualquier otro período activo para este usuario
    db.query(models.IncomePeriod).filter(models.IncomePeriod.student_id == student_id).update({"is_active": False})
    
    db_period = models.IncomePeriod(
        **period.model_dump(),
        student_id=student_id,
        is_active=True
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period

def get_current_budget_status(db: Session, student_id: int):
    """
    Busca el período de ingresos activo para un estudiante,
    calcula el gasto total y el saldo restante.
    """
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.is_active == True
    ).first()

    if not active_period:
        return None # No hay período activo

    # Calcula el gasto total durante el período activo (resultado puede ser Decimal o None)
    total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto', # Usa 'gasto' como acordamos
        models.Transaction.ts >= active_period.start_date,
        models.Transaction.ts <= active_period.end_date
    ).scalar()

    # --- CORRECCIÓN AQUÍ ---
    # Convertimos el resultado Decimal (o None) a float, default 0.0 si es None
    total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0

    # Ahora ambos son floats, la resta funcionará
    remaining_budget = float(active_period.amount) - total_spent
    # --- FIN CORRECCIÓN ---

    # Calcula los días restantes
    now = datetime.now(timezone.utc)
    end_date_aware = active_period.end_date
    if end_date_aware.tzinfo is None:
         end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)

    days_left = (end_date_aware - now).days if end_date_aware > now else 0

    return schemas.BudgetStatus(
        income_period_id=active_period.id,
        total_income=float(active_period.amount),
        start_date=active_period.start_date,
        end_date=active_period.end_date,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        days_left=days_left,
        is_active=active_period.is_active
    )

def get_income_period_by_id(db: Session, period_id: int, student_id: int):
    """
    Obtiene un período de ingresos específico por su ID,
    verificando que pertenezca al estudiante.
    """
    return db.query(models.IncomePeriod).filter(
        models.IncomePeriod.id == period_id,
        models.IncomePeriod.student_id == student_id # Security check!
    ).first()

def update_income_period(db: Session, period_id: int, student_id: int, period_update: schemas.IncomePeriodCreate):
    """
    Actualiza un período de ingresos específico para un estudiante.
    Verifica que el estudiante sea el propietario del período.
    """
    db_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.id == period_id,
        models.IncomePeriod.student_id == student_id # Security check!
    ).first()

    if not db_period:
        return None # Not found or doesn't belong to the user

    # Update fields from the request data
    db_period.amount = period_update.amount
    db_period.start_date = period_update.start_date
    db_period.end_date = period_update.end_date
    # We probably don't want to reactivate it here, just edit details
    # db_period.is_active = True 

    db.commit()
    db.refresh(db_period)
    return db_period

def create_demo_data(db: Session):
    """
    Crea un set de usuarios y transacciones de prueba (20 usuarios x 20+ transacciones)
    con patrones tanto para K-Means como para Apriori, usando las 10 categorías existentes.
    """
    
    # 1. Limpiar datos antiguos EN EL ORDEN CORRECTO
    print("LOG: Limpiando datos antiguos de la demo...")
    db.query(models.AssociationRule).delete()
    db.query(models.Transaction).delete()
    db.query(models.IncomePeriod).delete()
    db.execute(models.student_favorite_category_association.delete())
    db.query(models.Student).delete()
    db.commit()
    print("LOG: Datos antiguos limpiados.")

    # 2. Obtener IDs de categorías clave
    categories = db.query(models.Category).all()
    
    cat_transporte = next((c for c in categories if c.name == "Transporte"), None)
    cat_hormiga = next((c for c in categories if c.name == "Gastos Hormiga"), None)
    
    # Usaremos "Ahorro e Inversión" como placeholder para los ingresos
    cat_placeholder_for_income = next((c for c in categories if c.name == "Ahorro e Inversión"), None)

    # Categorías de "ruido" (todas excepto las de patrones)
    noise_categories = [
        c for c in categories 
        if c.name not in ["Transporte", "Gastos Hormiga"]
    ]

    if not all([cat_transporte, cat_hormiga, cat_placeholder_for_income, noise_categories]):
        print("ERROR: No se encontraron las categorías de demo. Asegúrate de que existan.")
        return

    # 3. Crear usuarios con patrones (20 transacciones CADA UNO)
    print(f"LOG: Creando 20 usuarios demo con +20 transacciones cada uno...")
    
    for i in range(20): # Crear 20 usuarios
        student = create_student(db, schemas.StudentCreate(
            email=f"user{i}@demo.com",
            display_name=f"Usuario Demo {i}",
            password="Password123!"
        ))
        
        # Añadir 2 ingresos (type='income') asignados a la categoría placeholder
        # K-Means solo mira el 'type', no la categoría del ingreso.
        db.add(models.Transaction(student_id=student.id, amount=random.randint(1500, 3000), type='income', category_id=cat_placeholder_for_income.id, ts=datetime.now(timezone.utc) - timedelta(days=15)))
        db.add(models.Transaction(student_id=student.id, amount=random.randint(1500, 3000), type='income', category_id=cat_placeholder_for_income.id, ts=datetime.now(timezone.utc) - timedelta(days=1)))

        # 15 usuarios (75%) tendrán el patrón (Transporte -> Gastos Hormiga)
        if i < 15:
            db.add(models.Transaction(student_id=student.id, amount=50, type='gasto', category_id=cat_transporte.id, ts=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))))
            db.add(models.Transaction(student_id=student.id, amount=20, type='gasto', category_id=cat_hormiga.id, ts=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))))
            for _ in range(18): # Rellenar con 18 transacciones "ruido"
                db.add(models.Transaction(student_id=student.id, amount=random.randint(10, 500), type='gasto', category_id=random.choice(noise_categories).id, ts=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))))
        
        # 5 usuarios (25%) tendrán 20 transacciones aleatorias
        else:
            for _ in range(20):
                db.add(models.Transaction(student_id=student.id, amount=random.randint(10, 500), type='gasto', category_id=random.choice(noise_categories).id, ts=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))))
    
    db.commit()
    print(f"LOG: Datos de prueba creados. 20 usuarios y +400 transacciones generadas.")

def get_transaction_baskets(db: Session, start_date: datetime, end_date: datetime):
    """Prepara los datos en formato 'cesta' para Apriori."""
    
    # Obtenemos transacciones agrupadas por estudiante y categoría
    transactions = db.query(
        models.Transaction.student_id,
        models.Category.name
    ).join(models.Category).filter(
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= start_date,
        models.Transaction.ts <= end_date
    ).distinct().all()

    # Agrupamos las categorías en 'cestas' por estudiante
    baskets = {}
    for student_id, category_name in transactions:
        if student_id not in baskets:
            baskets[student_id] = []
        baskets[student_id].append(category_name)
    
    # Devolvemos solo la lista de cestas (lista de listas)
    return list(baskets.values())

def save_association_rules(db: Session, rules_df):
    """Borra las reglas antiguas y guarda las nuevas encontradas."""
    
    # Borrar reglas viejas
    db.query(models.AssociationRule).delete()
    
    new_rules = []
    for _, row in rules_df.iterrows():
        new_rule = models.AssociationRule(
            antecedents=list(row['antecedents']),
            consequents=list(row['consequents']),
            support=row['support'],
            confidence=row['confidence'],
            lift=row['lift']
        )
        new_rules.append(new_rule)
        
    db.add_all(new_rules)
    db.commit()
    print(f"LOG: {len(new_rules)} nuevas reglas de asociación guardadas.")
    return new_rules

def get_association_rules(db: Session, skip: int = 0, limit: int = 20):
    """
    Obtiene las reglas de asociación guardadas en la base de datos.
    """
    return db.query(models.AssociationRule).order_by(
        models.AssociationRule.lift.desc() # Ordena por 'lift' para mostrar las más fuertes primero
    ).offset(skip).limit(limit).all()

def generate_recommendations(db: Session, student_id: int):
    """
    Genera una lista de recomendaciones personalizadas para un estudiante.
    """
    recommendations = []
    
    # --- 1. Recomendación de Perfil (K-Means) ---
    try:
        from analytics.profiling import train_and_cluster_students
        
        results_df = train_and_cluster_students(db)
        if results_df is not None and not results_df.empty:
            user_result = results_df[results_df['student_id'] == student_id]
            if not user_result.empty:
                profile_name = user_result.iloc[0]['profile_name']
                profile_desc = user_result.iloc[0]['profile_desc']
                
                recommendations.append(
                    schemas.Recommendation(
                        type="profile",
                        title=f"Tu Perfil: {profile_name}",
                        body=profile_desc
                    )
                )
    except Exception as e:
        print(f"Error al generar recomendación K-Means (ignorado por ahora): {e}")

    # --- 2. Recomendación de Patrón (Apriori) ---
    
    rules = get_association_rules(db, limit=10)
    
    recent_transactions = db.query(models.Transaction.category_id).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= (datetime.now(timezone.utc) - timedelta(days=15))
    ).distinct().all()
    
    recent_category_ids = {t[0] for t in recent_transactions}
    recent_categories_db = db.query(models.Category).filter(models.Category.id.in_(recent_category_ids)).all()
    recent_category_names = {c.name for c in recent_categories_db}
    
    # --- LÓGICA CORREGIDA AQUÍ ---
    for rule in rules:
        antecedent_set = set(rule.antecedents)
        consequent_set = set(rule.consequents)
        
        # Si el usuario ha gastado en AMBAS partes de la regla...
        if antecedent_set.issubset(recent_category_names) and consequent_set.issubset(recent_category_names):
            
            # ¡Encontramos un patrón existente para comentar!
            recommendations.append(
                schemas.Recommendation(
                    type="pattern",
                    title="¡Patrón Detectado!",
                    body=f"Notamos que tus gastos en [{', '.join(rule.antecedents)}] y [{', '.join(rule.consequents)}] suelen ir juntos. ¡Asegúrate de que este patrón se alinee con tus metas financieras!"
                )
            )
            # Damos solo una recomendación de patrón para no abrumar
            break 
    # --- FIN DE LA CORRECCIÓN ---

    return recommendations

def get_budget_history(db: Session, student_id: int, days_history: int = 60):
    """
    Obtiene el historial de períodos de presupuesto de un estudiante
    que terminaron en los últimos 'days_history' días.
    """
    # Define el rango de fechas para buscar
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_history)

    # Busca períodos que terminaron (end_date) dentro de esta ventana de tiempo
    history = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.end_date >= start_date,
        models.IncomePeriod.end_date <= end_date
    ).order_by(models.IncomePeriod.start_date.desc()).all() # Ordena del más nuevo al más viejo
    
    return history

def get_budget_tendency(db: Session, student_id: int):
    """
    Compara el período de presupuesto activo actual con el período completado
    más reciente para el análisis de tendencias.
    """
    
    # 1. Obtener el período activo
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.is_active == True
    ).first()

    # 2. Obtener el período anterior más reciente
    # Buscamos el período (que no sea el activo) que terminó más recientemente.
    previous_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.is_active == False,
        models.IncomePeriod.end_date <= datetime.now(timezone.utc)
    ).order_by(models.IncomePeriod.end_date.desc()).first()

    current_summary = None
    previous_summary = None
    comparison = {}

    # 3. Procesar el período activo (si existe)
    if active_period:
        active_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.student_id == student_id,
            models.Transaction.type == 'gasto',
            models.Transaction.ts.between(active_period.start_date, active_period.end_date)
        ).scalar()
        active_spent = float(active_spent_decimal) if active_spent_decimal is not None else 0.0
        
        current_summary = schemas.BudgetPeriodSummary(
            start_date=active_period.start_date,
            end_date=active_period.end_date,
            budgeted_amount=float(active_period.amount),
            total_spent=active_spent
        )

    # 4. Procesar el período anterior (si existe)
    if previous_period:
        prev_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.student_id == student_id,
            models.Transaction.type == 'gasto',
            models.Transaction.ts.between(previous_period.start_date, previous_period.end_date)
        ).scalar()
        prev_spent = float(prev_spent_decimal) if prev_spent_decimal is not None else 0.0
        
        previous_summary = schemas.BudgetPeriodSummary(
            start_date=previous_period.start_date,
            end_date=previous_period.end_date,
            budgeted_amount=float(previous_period.amount),
            total_spent=prev_spent
        )

    # 5. Calcular la comparación (si tenemos ambos períodos)
    if current_summary and previous_summary and previous_summary.total_spent > 0:
        change = ((current_summary.total_spent - previous_summary.total_spent) / previous_summary.total_spent) * 100
        comparison = {"spending_change_percentage": round(change, 2)}
    elif current_summary and previous_summary:
        comparison = {"spending_change_percentage": 0.0} # No se puede dividir por cero

    return schemas.BudgetTendencyResponse(
        current_period=current_summary,
        previous_period=previous_summary,
        comparison=comparison
    )

