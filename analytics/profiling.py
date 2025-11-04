import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import models
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import crud

ESSENTIAL_CATEGORIES = {
    "Hogar y Servicios", "Educación", "Salud y Bienestar",
    "Deudas y Obligaciones", "Alimentación", "Transporte"
}

PROFILE_MAP = {
    0: {
        "profile": "El Urbanita Social",
        # Cambiamos "description" por "recommendation"
        "recommendation": "Enfócate en crear tu primer fondo de emergencia. Empieza automatizando un ahorro semanal equivalente a 'dos salidas por café'. Pequeños pasos construyen tu seguridad sin sacrificar toda la diversión."
    },
    1: {
        "profile": "El Guardián del Futuro",
        "recommendation": "¡Felicidades por tu increíble disciplina! Tu siguiente nivel es hacer que tu dinero trabaje para ti. Explora nuestras guías sobre inversiones de bajo riesgo para que tu futuro sea, además de seguro, más próspero."
    },
    2: {
        "profile": "El Arquitecto Financiero",
        "recommendation": "Has dominado las bases del juego financiero. ¿Estás listo para el siguiente nivel? Te retamos a optimizar una de tus categorías de gasto un 5% este mes e invertir esa diferencia en tu meta a largo plazo."
    },
    3: {
        "profile": "El Coleccionista de Experiencias",
        "recommendation": "Nos encanta que inviertas en ti. Para que puedas seguir explorando el mundo sin preocupaciones, crea dos metas de ahorro paralelas: una para tu próxima aventura y otra, más pequeña pero constante, para tu fondo de emergencia."
    },
    4: {
        "profile": "El Explorador Financiero",
        "recommendation": "¡Bienvenido a tu viaje financiero! Tu primer y más poderoso paso es simple: registra absolutamente todos tus gastos durante dos semanas. No juzgues, solo observa. Este mapa te revelará exactamente dónde estás."
    }
}

def get_student_features(db: Session, student_id: int, period_days: int = 60):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    transactions = db.query(models.Transaction).filter(
        models.Transaction.student_id == student_id, models.Transaction.ts >= start_date
    ).all()
    if len(transactions) < 15:
        return None
    total_income = sum(t.amount for t in transactions if t.type == 'income') or 1
    total_expense = sum(t.amount for t in transactions if t.type == 'expense') or 0
    savings_rate = (total_income - total_expense) / total_income
    discretionary_expense = sum(t.amount for t in transactions if t.type == 'expense' and t.category.name not in ESSENTIAL_CATEGORIES)
    discretionary_ratio = discretionary_expense / total_expense if total_expense > 0 else 0
    return {
        "savings_rate": savings_rate,
        "discretionary_ratio": discretionary_ratio,
        "transaction_count": len(transactions),
        "avg_expense_amount": (total_expense / len([t for t in transactions if t.type == 'expense'])) if any(t.type == 'expense' for t in transactions) else 0
    }

def train_and_cluster_students(db: Session):
    students = db.query(models.Student).all()
    feature_list = []
    for student in students:
        features = get_student_features(db, student.id)
        if features:
            features["student_id"] = student.id
            feature_list.append(features)
    if len(feature_list) < 5:
        return None
    df = pd.DataFrame(feature_list)
    df_features = df.drop(columns=["student_id"])
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_features)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init='auto')
    df['cluster'] = kmeans.fit_predict(scaled_features)
    df['profile_name'] = df['cluster'].map(lambda x: PROFILE_MAP.get(x, PROFILE_MAP[4])['profile'])
    df['profile_desc'] = df['cluster'].map(lambda x: PROFILE_MAP.get(x, PROFILE_MAP[4])['recommendation'])
    return df

def run_apriori_analysis(db: Session):
    """
    Ejecuta el análisis Apriori completo sobre los datos de transacciones.
    """
    
    # 1. Obtener las "cestas" de transacciones
    # Analizaremos los últimos 90 días de datos
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=90)
    baskets = crud.get_transaction_baskets(db, start_date=start_date, end_date=end_date)

    if len(baskets) < 10:
        print("LOG: No hay suficientes cestas de datos para ejecutar Apriori.")
        return []

    # 2. Transformar datos para mlxtend (One-Hot Encoding)
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    # 3. Ejecutar Apriori para encontrar itemsets frecuentes
    # min_support=0.1 significa que el patrón debe aparecer en al menos el 10% de las cestas
    frequent_itemsets = apriori(df, min_support=0.1, use_colnames=True)

    if frequent_itemsets.empty:
        print("LOG: No se encontraron itemsets frecuentes.")
        return []

    # 4. Generar las reglas de asociación
    # min_threshold=0.5 significa que la confianza debe ser de al menos 50%
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)

    # Filtramos reglas que sean útiles (ej. lift > 1 significa que la regla es significativa)
    rules = rules[rules['lift'] > 1]
    
    if rules.empty:
        print("LOG: No se encontraron reglas de asociación significativas.")
        return []

    # 5. Guardar las reglas en la base de datos
    saved_rules = crud.save_association_rules(db, rules)
    
    return saved_rules