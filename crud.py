# backend/crud.py
from colorama import init
from sqlalchemy.orm import Session
from typing import List, Optional
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
    """Crea las categorías iniciales si la tabla está vacía."""
    if db.query(models.Category).count() == 0:
        print("Creando categorías iniciales...")
        initial_categories = [
            models.Category(name="Hogar y Servicios"),
            models.Category(name="Educación"),
            models.Category(name="Salud y Bienestar"),
            models.Category(name="Deudas y Obligaciones"),
            models.Category(name="Alimentación"),
            models.Category(name="Transporte"),
            models.Category(name="Compras y Cuidado personal"),
            models.Category(name="Ocio y Vida Social"),
            models.Category(name="Ahorro e Inversión"),
            models.Category(name="Gastos Hormiga")
        ]
        db.add_all(initial_categories)
        db.commit()
        print(f"{len(initial_categories)} categorías creadas.")
    else:
        print("Categorías ya pobladas.")

def create_initial_microcontent(db: Session):
    """
    Crea el contenido educativo inicial si la tabla está vacía.
    """
    if db.query(models.Microcontent).count() == 0:
        print("Creando microcontenidos educativos iniciales...")
        
        # --- TUS 20 TARJETAS DE CONTENIDO ---
        content_cards = [
            # Tag: Ahorro
            models.Microcontent(title="¿Qué es un Fondo de Emergencia?", body="Es un 'colchón' de dinero solo para imprevistos (3-6 meses de tus gastos). Es tu primer paso hacia la libertad financiera.", tag="ahorro"),
            models.Microcontent(title="El Método 50/30/20", body="Una regla simple: 50% de tu ingreso a 'Necesidades' (renta, comida), 30% a 'Deseos' (ocio, compras) y 20% a 'Ahorro y Deudas'.", tag="presupuesto"),
            models.Microcontent(title="Págate a Ti Mismo Primero", body="Antes de pagar cualquier factura o gastar en ocio, aparta un porcentaje de tu ingreso para ahorro. Trata tu ahorro como el 'gasto' más importante.", tag="ahorro"),
            models.Microcontent(title="Ahorro vs. Inversión", body="Ahorrar es guardar dinero (seguro, pero pierde valor con la inflación). Invertir es poner tu dinero a trabajar para que crezca (conlleva riesgo).", tag="inversion"),

            # Tag: Deuda
            models.Microcontent(title="El Peligro del 'Paga Mínimo'", body="Pagar solo el mínimo de tu tarjeta de crédito hace que tu deuda crezca exponencialmente por los intereses. ¡Evítalo a toda costa!", tag="deuda"),
            models.Microcontent(title="La Bola de Nieve", body="Un método para salir de deudas: paga todas tus deudas del monto más pequeño al más grande. Cada vez que liquidas una, ganas 'momentum' psicológico.", tag="deuda"),
            models.Microcontent(title="Deuda 'Buena' vs. Deuda 'Mala'", body="Deuda 'buena' es la que te ayuda a generar más valor (ej. un crédito educativo). Deuda 'mala' es la que financia gastos que pierden valor (ej. ropa, fiestas).", tag="deuda"),
            models.Microcontent(title="¿Qué es el CAT?", body="El Costo Anual Total (CAT) es el número real de lo que te cuesta un crédito (incluye intereses, comisiones, etc.). ¡Compara siempre el CAT, no solo la tasa de interés!", tag="deuda"),

            # Tag: Gastos Hormiga
            models.Microcontent(title="El Poder Oculto del Gasto Hormiga", body="Ese café de $50, el refresco de $20... parecen inofensivos. Pero $70 al día son $2,100 al mes. ¿Realmente valen la pena?", tag="gastos_hormiga"),
            models.Microcontent(title="La Regla de los 10 Minutos", body="¿Quieres hacer un gasto hormiga? Espera 10 minutos. Si después de 10 minutos sigues queriéndolo, cómpralo. La mayoría de las veces, el impulso desaparecerá.", tag="gastos_hormiga"),
            models.Microcontent(title="Prepara tu 'Kit Anti-Hormiga'", body="Lleva siempre una botella de agua reutilizable y un snack saludable en tu mochila. Esto te salvará de comprar impulsivamente en la calle.", tag="gastos_hormiga"),
            models.Microcontent(title="Ponle Nombre a tu Ahorro", body="En lugar de 'no comprar un café', piensa 'estoy ahorrando para mi próximo concierto'. Darle un objetivo a tu ahorro lo hace más fácil.", tag="gastos_hormiga"),

            # Tag: Presupuesto
            models.Microcontent(title="Tu Presupuesto no es una Cárcel", body="Un presupuesto no es para restringirte, es una herramienta para darte permiso de gastar sin culpa en las cosas que SÍ te importan.", tag="presupuesto"),
            models.Microcontent(title="El Presupuesto 'Base Cero'", body="En lugar de ajustar el presupuesto del mes pasado, empieza cada mes desde cero. Asigna cada peso de tu ingreso a una categoría (incluyendo ahorro) hasta que te queden $0.", tag="presupuesto"),
            models.Microcontent(title="Sobres Digitales", body="Asigna tu presupuesto a 'sobres' o 'apartados' digitales. Cuando el sobre de 'Ocio' se acaba, se acaba. Esto hace el gasto visible y tangible.", tag="presupuesto"),
            models.Microcontent(title="Revisa tu Presupuesto Semanalmente", body="No esperes a fin de mes. Revisa tus gastos cada domingo por 10 minutos. Es más fácil corregir el rumbo a tiempo que lamentarse después.", tag="presupuesto"),

            # Tag: Inversión
            models.Microcontent(title="El Interés Compuesto", body="Es la 'magia' de la inversión. Es el interés que ganas sobre el interés que ya ganaste. Por eso, empezar a invertir joven es la mayor ventaja.", tag="inversion"),
            models.Microcontent(title="¿Qué es CetesDirecto?", body="Es la plataforma más segura para empezar a invertir en México. Le prestas dinero al gobierno y te paga un interés. Es ideal para tu fondo de emergencia.", tag="inversion"),
            models.Microcontent(title="No Inviertas en lo que no Entiendes", body="Si suena demasiado bueno para ser verdad (criptomonedas milagrosas, Forex), probablemente lo sea. Invierte solo en instrumentos que entiendas.", tag="inversion"),
            models.Microcontent(title="Diversificar es Protegerse", body="La regla de oro: no pongas todos los huevos en la misma canasta. Distribuye tu dinero en diferentes tipos de inversión para reducir el riesgo.", tag="inversion")
        ]
        
        db.add_all(content_cards)
        db.commit()
        print(f"{len(content_cards)} microcontenidos creados.")
    else:
        print("Microcontenidos ya poblados.")

def get_microcontent(db: Session, tags: Optional[str] = None, skip: int = 0, limit: int = 100):
    """
    Obtiene una lista de microcontenidos, opcionalmente filtrados
    por una LISTA de tags.
    """
    query = db.query(models.Microcontent)
    if tags:
        query = query.filter(models.Microcontent.tag.in_(tags))
    
    return query.offset(skip).limit(limit).all()

def create_student_transaction(db: Session, transaction: schemas.TransactionCreate, student_id: int):
    transaction_data = transaction.model_dump()
    if transaction_data.get("ts") is None:
        transaction_data["ts"] = datetime.now(timezone.utc)
    # Asumimos que el frontend envía 'income_period_id'
    db_transaction = models.Transaction(
        **transaction_data, 
        student_id=student_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_student_transactions(db: Session, student_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.student_id == student_id).order_by(models.Transaction.ts.desc()).offset(skip).limit(limit).all()

def create_income_period(db: Session, student_id: int, period: schemas.IncomePeriodCreate):
    # 🚀 NORMALIZACIÓN TOTAL (Día completo)
    # Ponemos el inicio a las 00:00:00 y el fin a las 23:59:59
    clean_start = period.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    clean_end = period.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 🛡️ PASO 1: Buscar si hay choque de fechas (Overlap)
    overlapping_budget = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.start_date <= clean_end,
        models.IncomePeriod.end_date >= clean_start
    ).first()

    if overlapping_budget:
        return "overlap" 

    # 🛡️ PASO 2: Calcular si este periodo debe estar activo (USANDO LAS LIMPIAS)
    now = datetime.now(timezone.utc)
    
    # Aseguramos que las fechas limpias tengan zona horaria para comparar con 'now'
    start_aware = clean_start.replace(tzinfo=timezone.utc) if clean_start.tzinfo is None else clean_start
    end_aware = clean_end.replace(tzinfo=timezone.utc) if clean_end.tzinfo is None else clean_end

    # Ahora sí, si hoy es el día de inicio, se activa desde el primer segundo
    is_now_active = (start_aware <= now) and (now <= end_aware)

    # 🛡️ PASO 3: Si va a estar activo, desactivar cualquier otro que ande por ahí
    if is_now_active:
        db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == student_id,
            models.IncomePeriod.is_active == True
        ).update({"is_active": False})

    # 🛡️ PASO 4: Guardar con las fechas estiradas a día completo
    db_period = models.IncomePeriod(
        total_income=period.total_income,
        start_date=clean_start, 
        end_date=clean_end,     
        student_id=student_id,
        is_active=is_now_active
    )
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period

def get_current_budget_status(db: Session, student_id: int):
    now = datetime.now(timezone.utc)
    active_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.start_date <= now,
        models.IncomePeriod.end_date >= now
    ).first()

    if active_period and not active_period.is_active:
        # Desactivamos cualquier otro por seguridad
        db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == student_id,
            models.IncomePeriod.is_active == True
        ).update({"is_active": False})
        
        # Activamos el actual
        active_period.is_active = True
        db.commit()
        db.refresh(active_period)

    if not active_period:
        return None 

    total_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.income_period_id == active_period.income_period_id # Filtro por ID de período
    ).scalar()
    
    total_spent = float(total_spent_decimal) if total_spent_decimal is not None else 0.0

    # CORRECCIÓN DE NOMBRE:
    remaining_budget = float(active_period.total_income) - total_spent

    now = datetime.now(timezone.utc)
    end_date_aware = active_period.end_date
    if end_date_aware.tzinfo is None:
         end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)
         
    days_left = (end_date_aware - now).days if end_date_aware > now else 0

    return schemas.BudgetStatus(
        income_period_id=active_period.income_period_id, # Nombre de ID corregido
        total_income=float(active_period.total_income), # Nombre de campo corregido
        start_date=active_period.start_date,
        end_date=active_period.end_date,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        days_left=days_left,
        is_active=active_period.is_active
    )

def get_income_period_by_id(db: Session, period_id: int, student_id: int):
    return db.query(models.IncomePeriod).filter(
        models.IncomePeriod.income_period_id == period_id, # Nombre de ID corregido
        models.IncomePeriod.student_id == student_id
    ).first()

def realign_student_transactions(db: Session, student_id: int):
    # 1. Traemos todo
    periods = db.query(models.IncomePeriod).filter(models.IncomePeriod.student_id == student_id).all()
    transactions = db.query(models.Transaction).filter(models.Transaction.student_id == student_id).all()

    count = 0
    for t in transactions:
        # Aseguramos que la fecha de la transacción sea "consciente" (aware) de UTC
        t_ts = t.ts if t.ts.tzinfo else t.ts.replace(tzinfo=timezone.utc)
        
        for p in periods:
            # 🚀 EL TRUCO: Convertimos las fechas del periodo a UTC para comparar
            p_start = p.start_date.replace(tzinfo=timezone.utc) if p.start_date.tzinfo is None else p.start_date
            p_end = p.end_date.replace(tzinfo=timezone.utc) if p.end_date.tzinfo is None else p.end_date

            if p_start <= t_ts <= p_end:
                if t.income_period_id != p.income_period_id:
                    t.income_period_id = p.income_period_id
                    count += 1
                break 
    
    db.commit()
    return count

def update_income_period(db: Session, period_id: int, student_id: int, period_update: schemas.IncomePeriodCreate):
    # 🛡️ 1. Buscar el periodo
    db_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.income_period_id == period_id,
        models.IncomePeriod.student_id == student_id
    ).first()

    if not db_period:
        return None

    # 🛡️ 2. Normalizar fechas (Día completo)
    clean_start = period_update.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    clean_end = period_update.end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 🛡️ 3. Revisar Overlap (Ignorando el periodo actual)
    overlapping = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id,
        models.IncomePeriod.income_period_id != period_id,
        models.IncomePeriod.start_date <= clean_end,
        models.IncomePeriod.end_date >= clean_start
    ).first()

    if overlapping:
        return "overlap"

    # 🛡️ 4. Actualizar datos básicos
    db_period.total_income = period_update.total_income
    db_period.start_date = clean_start
    db_period.end_date = clean_end
    
    # Recalcular is_active
    now = datetime.now(timezone.utc)
    start_aware = clean_start.replace(tzinfo=timezone.utc) if clean_start.tzinfo is None else clean_start
    end_aware = clean_end.replace(tzinfo=timezone.utc) if clean_end.tzinfo is None else clean_end
    db_period.is_active = (start_aware <= now <= end_aware)

    db.commit() # Guardamos los cambios de fecha primero

    # 🚀 5. EL TOQUE MAESTRO: Re-alinear transacciones
    # Ahora que las fechas cambiaron, movemos los gastos a donde pertenecen
    realign_student_transactions(db, student_id=student_id)

    db.refresh(db_period)
    return db_period

# def get_budget_history(db: Session, student_id: int, days_history: int = 60):
#     end_date = datetime.now(timezone.utc)
#     start_date = end_date - timedelta(days=days_history)
#     history = db.query(models.IncomePeriod).filter(
#         models.IncomePeriod.student_id == student_id,
#         models.IncomePeriod.end_date <= end_date
#     ).order_by(models.IncomePeriod.start_date.desc()).all()
#     return history

def get_budget_history(db: Session, student_id: int):
    # 🚀 Quitamos los filtros de fecha para que veas TODO lo que hay en la BD
    # así podrás detectar qué presupuestos están chocando.
    return db.query(models.IncomePeriod).filter(
        models.IncomePeriod.student_id == student_id
    ).order_by(models.IncomePeriod.start_date.desc()).all()

def get_association_rules(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.AssociationRule).order_by(
        models.AssociationRule.lift.desc()
    ).offset(skip).limit(limit).all()

# --- DEMO DATA Y RECOMENDACIONES (Movidas a profiling.py) ---
# (La función 'create_demo_data' y 'generate_recommendations' 
# deben estar en 'analytics/profiling.py' para evitar errores de importación)

def get_triggered_rules(db: Session, student_id: int):
    """
    Compara las reglas de Apriori con los gastos recientes de un usuario
    y devuelve las reglas que el usuario ha "activado".
    """
    
    # 1. Obtener todas las reglas fuertes del sistema
    rules = get_association_rules(db, limit=50) # Obtenemos las 50 reglas más fuertes
    
    # 2. Obtener las categorías en las que ha gastado el usuario recientemente (ej. últimos 30 días)
    recent_transactions = db.query(models.Transaction.category_id).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= (datetime.now(timezone.utc) - timedelta(days=30))
    ).distinct().all()
    
    recent_category_ids = {t[0] for t in recent_transactions}
    recent_categories_db = db.query(models.Category).filter(models.Category.id.in_(recent_category_ids)).all()
    recent_category_names = {c.name for c in recent_categories_db}
    
    # 3. Filtrar las reglas que el usuario ha activado
    triggered_rules = []
    for rule in rules:
        antecedent_set = set(rule.antecedents)
        consequent_set = set(rule.consequents)
        
        # Si el usuario ha gastado en AMBAS partes de la regla...
        if antecedent_set.issubset(recent_category_names) and consequent_set.issubset(recent_category_names):
            # ... entonces esta regla es "relevante" para él.
            triggered_rules.append(rule)
            
    return triggered_rules

# backend/crud.py

def get_predictive_rule_match(db: Session, category_id: int):
    """
    Busca una regla de asociación donde la categoría recién gastada 
    sea el 'disparador' (antecedente).
    """
    # 1. Obtenemos el nombre de la categoría (porque tus reglas usan nombres)
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        return None

    # 2. Buscamos todas las reglas
    # Nota: Filtramos por un 'lift' alto para que la predicción sea de calidad
    rules = db.query(models.AssociationRule).filter(
        models.AssociationRule.lift > 1.2 
    ).all()

    for rule in rules:
        # 3. ¿La categoría que acaba de usar está en los antecedentes de esta regla?
        if category.name in rule.antecedents:
            # Si sí, devolvemos la regla para avisarle sobre los 'consequents'
            return rule
            
    return None

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
            models.Transaction.income_period_id == active_period.income_period_id
        ).scalar()
        active_spent = float(active_spent_decimal) if active_spent_decimal is not None else 0.0
        
        current_summary = schemas.BudgetPeriodSummary(
            start_date=active_period.start_date,
            end_date=active_period.end_date,
            budgeted_amount=float(active_period.total_income),
            total_spent=active_spent
        )

    # 4. Procesar el período anterior (si existe)
    if previous_period:
        prev_spent_decimal = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.student_id == student_id,
            models.Transaction.type == 'gasto',
            models.Transaction.income_period_id == previous_period.income_period_id
        ).scalar()
        prev_spent = float(prev_spent_decimal) if prev_spent_decimal is not None else 0.0
        
        previous_summary = schemas.BudgetPeriodSummary(
            start_date=previous_period.start_date,
            end_date=previous_period.end_date,
            budgeted_amount=float(previous_period.total_income),
            total_spent=prev_spent
        )

    # 5. Calcular la comparación (si tenemos ambos períodos)
    if current_summary and previous_summary and previous_summary.total_spent > 0:
        change = ((current_summary.total_spent - previous_summary.total_spent) / previous_summary.total_spent) * 100
        comparison = {"spending_change_percentage": round(change, 2)}
    elif current_summary and previous_summary:
        comparison = {"spending_change_percentage": 0.0}

    return schemas.BudgetTendencyResponse(
        current_period=current_summary,
        previous_period=previous_summary,
        comparison=comparison
    )

def get_category_spending_report(db: Session, student_id: int, period_id: int = None): 
    # 1. Decidimos qué periodo usar
    if period_id is None:
        # Si no hay ID, buscamos el que esté activo hoy
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == student_id,
            models.IncomePeriod.is_active == True
        ).first()
    else:
        # Si nos pasaron un ID, buscamos ese específicamente
        active_period = db.query(models.IncomePeriod).filter(
            models.IncomePeriod.student_id == student_id,
            models.IncomePeriod.income_period_id == period_id # 👈 Aquí debe decir period_id
        ).first()

    # Si después de buscar no encontramos nada, regresamos None
    if not active_period:
        return None

    # 2. Calculamos los gastos por categoría (Esto ya lo tenías y funciona bien)
    from sqlalchemy import func
    
    results = db.query(
        models.Category.name,
        func.sum(models.Transaction.amount).label("total")
    ).join(models.Transaction, models.Category.id == models.Transaction.category_id)\
     .filter(
        models.Transaction.income_period_id == active_period.income_period_id,
        models.Transaction.type == 'gasto'
    ).group_by(models.Category.name).all()

    category_list = []
    total_budget = float(active_period.total_income)

    for name, spent in results:
        spent_float = float(spent)
        # Calculamos el porcentaje respecto al presupuesto total
        percentage = (spent_float / total_budget) if total_budget > 0 else 0
        
        category_list.append(schemas.CategorySpendingDetail(
            category_name=name,
            total_spent=spent_float,
            percentage=round(percentage, 4) # Guardamos el decimal (0.25 = 25%)
        ))

    return schemas.CategorySpendingResponse(
        income_period_id=active_period.income_period_id,
        start_date=active_period.start_date,
        end_date=active_period.end_date,
        total_budget=total_budget,
        categories=category_list
    )

def delete_income_period(db: Session, student_id: int, period_id: int):
    # 🕵️ Buscamos el periodo asegurándonos de que pertenezca al estudiante
    db_period = db.query(models.IncomePeriod).filter(
        models.IncomePeriod.income_period_id == period_id,
        models.IncomePeriod.student_id == student_id
    ).first()

    if db_period:
        # 🗑️ Al borrar el periodo, SQLAlchemy se encargará de las transacciones 
        # (siempre y cuando tengas configurado el 'cascade delete' en tus modelos)
        db.delete(db_period)
        db.commit()
        return True
    
    return False



