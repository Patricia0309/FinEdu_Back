# backend/analytics/profiling.py

import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import models
import schemas
import crud # crud SÍ se necesita para create_student
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import random

# --- CATEGORÍAS Y MAPA DE PERFILES ---
ESSENTIAL_CATEGORIES = {
    "Hogar y Servicios", "Educación", "Salud y Bienestar",
    "Deudas y Obligaciones", "Alimentación", "Transporte"
}
PROFILE_MAP = {
    0: {"profile": "El Urbanita Social", "recommendation": "Enfócate en crear tu primer fondo de emergencia..."},
    1: {"profile": "El Guardián del Futuro", "recommendation": "¡Felicidades por tu increíble disciplina!..."},
    2: {"profile": "El Arquitecto Financiero", "recommendation": "Has dominado las bases del juego financiero..."},
    3: {"profile": "El Coleccionista de Experiencias", "recommendation": "Nos encanta que inviertas en ti..."},
    4: {"profile": "El Explorador Financiero", "recommendation": "¡Bienvenido a tu viaje financiero!..."},
}

# --- LÓGICA K-MEANS ---
def get_student_features(db: Session, student_id: int, period_days: int = 60):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=period_days)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.student_id == student_id, models.Transaction.ts >= start_date
    ).all()
    if len(transactions) < 15:
        return None
    total_income = sum(t.amount for t in transactions if t.type == 'income') or 1
    total_expense = sum(t.amount for t in transactions if t.type == 'gasto') or 0
    savings_rate = (total_income - total_expense) / total_income
    discretionary_expense = sum(t.amount for t in transactions if t.type == 'gasto' and t.category.name not in ESSENTIAL_CATEGORIES)
    discretionary_ratio = discretionary_expense / total_expense if total_expense > 0 else 0
    return {
        "savings_rate": savings_rate,
        "discretionary_ratio": discretionary_ratio,
        "transaction_count": len(transactions),
        "avg_expense_amount": (total_expense / len([t for t in transactions if t.type == 'gasto'])) if any(t.type == 'gasto' for t in transactions) else 0
    }

def train_and_cluster_students(db: Session):
    students = db.query(models.Student).all()
    feature_list = []
    for student in students:
        features = get_student_features(db, student_id=student.id)
        if features:
            features["student_id"] = student.id
            feature_list.append(features)
    if len(feature_list) < 5:
        return None
    df = pd.DataFrame(feature_list)
    df_features = df.drop(columns=["student_id"])
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_features)
    n_clusters = min(5, len(df_features)) # Asegurarse de no tener más clusters que muestras
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    df['cluster'] = kmeans.fit_predict(scaled_features)
    df['profile_name'] = df['cluster'].map(lambda x: PROFILE_MAP.get(x, PROFILE_MAP[4])['profile'])
    df['profile_desc'] = df['cluster'].map(lambda x: PROFILE_MAP.get(x, PROFILE_MAP[4])['recommendation'])
    return df

# --- LÓGICA APRIORI (FUNCIONES MOVIDAS AQUÍ) ---

def get_transaction_baskets(db: Session, start_date: datetime, end_date: datetime):
    """Prepara los datos en formato 'cesta' para Apriori."""
    transactions = db.query(
        models.Transaction.student_id,
        models.Category.name
    ).join(models.Category).filter(
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= start_date,
        models.Transaction.ts <= end_date
    ).distinct().all()
    baskets = {}
    for student_id, category_name in transactions:
        if student_id not in baskets:
            baskets[student_id] = []
        baskets[student_id].append(category_name)
    return list(baskets.values())

def save_association_rules(db: Session, rules_df):
    """Borra las reglas antiguas y guarda las nuevas encontradas."""
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

def run_apriori_analysis(db: Session):
    """Ejecuta el análisis Apriori completo sobre los datos de transacciones."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=90)
    
    # Llama a la función local
    baskets = get_transaction_baskets(db, start_date=start_date, end_date=end_date)
    
    if len(baskets) < 10:
        print("LOG: No hay suficientes cestas de datos para ejecutar Apriori.")
        return []
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(df, min_support=0.1, use_colnames=True)
    if frequent_itemsets.empty:
        print("LOG: No se encontraron itemsets frecuentes.")
        return []
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
    rules = rules[rules['lift'] > 1]
    if rules.empty:
        print("LOG: No se encontraron reglas de asociación significativas.")
        return []
    
    # Llama a la función local
    saved_rules = save_association_rules(db, rules)
    return saved_rules

# --- LÓGICA DE RECOMENDACIONES ---
def generate_recommendations(db: Session, student_id: int):
    recommendations = []
    try:
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

    # Esta función SÍ es de crud.py, así que la llamamos con crud.
    rules = crud.get_association_rules(db, limit=10) 
    
    recent_transactions = db.query(models.Transaction.category_id).filter(
        models.Transaction.student_id == student_id,
        models.Transaction.type == 'gasto',
        models.Transaction.ts >= (datetime.now(timezone.utc) - timedelta(days=15))
    ).distinct().all()
    recent_category_ids = {t[0] for t in recent_transactions}
    recent_categories_db = db.query(models.Category).filter(models.Category.id.in_(recent_category_ids)).all()
    recent_category_names = {c.name for c in recent_categories_db}
    
    for rule in rules:
        antecedent_set = set(rule.antecedents)
        consequent_set = set(rule.consequents)
        if antecedent_set.issubset(recent_category_names) and consequent_set.issubset(recent_category_names):
            recommendations.append(
                schemas.Recommendation(
                    type="pattern",
                    title="¡Patrón Detectado!",
                    body=f"Notamos que tus gastos en [{', '.join(rule.antecedents)}] y [{', '.join(rule.consequents)}] suelen ir juntos. ¡Asegúrate de que este patrón se alinee con tus metas financieras!"
                )
            )
            break 
    return recommendations

# --- LÓGICA DE DEMO ---
def create_demo_data(db: Session):
    """
    Crea un set de usuarios y transacciones de prueba (20 usuarios x 20+ transacciones)
    con patrones tanto para K-Means como para Apriori, usando las 10 categorías existentes.
    """
    
    # 1. Limpiar datos antiguos
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
    
    # --- CORRECCIÓN AQUÍ ---
    # Usamos "Ahorro e Inversión" como placeholder para los ingresos
    cat_placeholder_for_income = next((c for c in categories if c.name == "Ahorro e Inversión"), None)
    # --- FIN DE LA CORRECCIÓN ---

    noise_categories = [
        c for c in categories 
        if c.name not in ["Transporte", "Gastos Hormiga", "Ahorro e Inversión"]
    ]

    if not all([cat_transporte, cat_hormiga, cat_placeholder_for_income, noise_categories]):
        print("ERROR: No se encontraron las categorías de demo. Asegúrate de que existan.")
        return

    # 3. Crear usuarios con patrones
    print(f"LOG: Creando 20 usuarios demo con presupuestos y transacciones...")
    
    for i in range(20): # Crear 20 usuarios
        student = crud.create_student(db, schemas.StudentCreate(
            email=f"user{i}@demo.com",
            display_name=f"Usuario Demo {i}",
            password="Password123!"
        ))
        
        total_income_demo = random.randint(3000, 6000)
        start_date_demo = datetime.now(timezone.utc) - timedelta(days=random.randint(15, 30))
        end_date_demo = start_date_demo + timedelta(days=14)
        
        demo_period = models.IncomePeriod(
            total_income=total_income_demo,
            start_date=start_date_demo,
            end_date=end_date_demo,
            student_id=student.id,
            is_active=(i == 0)
        )
        db.add(demo_period)
        db.commit() 
        db.refresh(demo_period)

        # Añadir 1 ingreso (type='income') asignado a la categoría placeholder
        db.add(models.Transaction(
            student_id=student.id, 
            amount=total_income_demo, 
            type='income', 
            category_id=cat_placeholder_for_income.id, # <-- CORREGIDO
            ts=start_date_demo, 
            income_period_id=demo_period.income_period_id
        ))
        
        # 15 usuarios (75%) tendrán el patrón (Transporte -> Gastos Hormiga)
        if i < 15:
            db.add(models.Transaction(student_id=student.id, amount=50, type='gasto', category_id=cat_transporte.id, ts=start_date_demo + timedelta(days=2), income_period_id=demo_period.income_period_id))
            db.add(models.Transaction(student_id=student.id, amount=20, type='gasto', category_id=cat_hormiga.id, ts=start_date_demo + timedelta(days=3), income_period_id=demo_period.income_period_id))
            for j in range(18): # Rellenar con 18 transacciones "ruido"
                db.add(models.Transaction(student_id=student.id, amount=random.randint(10, 200), type='gasto', category_id=random.choice(noise_categories).id, ts=start_date_demo + timedelta(days=j % 14), income_period_id=demo_period.income_period_id))
        
        # 5 usuarios (25%) tendrán 20 transacciones aleatorias
        else:
            for j in range(20):
                db.add(models.Transaction(student_id=student.id, amount=random.randint(10, 200), type='gasto', category_id=random.choice(noise_categories).id, ts=start_date_demo + timedelta(days=j % 14), income_period_id=demo_period.income_period_id))
    
    db.commit()
    print(f"LOG: Datos de prueba creados. 20 usuarios y +400 transacciones generadas.")