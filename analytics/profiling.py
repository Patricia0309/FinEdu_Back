import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import models

ESSENTIAL_CATEGORIES = {
    "Hogar y Servicios", "Educación", "Salud y Bienestar",
    "Deudas y Obligaciones", "Alimentación", "Transporte"
}

PROFILE_MAP = {
    0: {"profile": "El Urbanita Social", "description": "Enfócate en crear tu primer fondo de emergencia..."},
    1: {"profile": "El Guardián del Futuro", "description": "¡Felicidades por tu increíble disciplina!..."},
    2: {"profile": "El Arquitecto Financiero", "description": "Has dominado las bases del juego financiero..."},
    3: {"profile": "El Coleccionista de Experiencias", "description": "Nos encanta que inviertas en ti..."},
    4: {"profile": "El Explorador Financiero", "description": "¡Bienvenido a tu viaje financiero!..."},
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
    df['profile_desc'] = df['cluster'].map(lambda x: PROFILE_MAP.get(x, PROFILE_MAP[4])['description'])
    return df