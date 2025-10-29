# backend/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import firebase_admin
from firebase_admin import credentials
import models
import crud
# LA LÍNEA CLAVE A CORREGIR:
from routers import students, auth, transactions, analytics, budgets

# --- INICIALIZACIÓN DE FIREBASE ---
# Carga las credenciales desde el archivo JSON
cred = credentials.Certificate("firebase-credentials.json") 
# Inicializa la app de Firebase
firebase_admin.initialize_app(cred)
# --- FIN INICIALIZACIÓN ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y sembrando la base de datos...")
    db = SessionLocal()
    try:
        crud.create_initial_categories(db)
    finally:
        db.close()
    yield
    print("Apagando aplicación...")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinEdu API",
    description="La API para el proyecto de tesis FinEdu.",
    version="0.1.0",
    lifespan=lifespan
)

# Incluimos todos los routers
app.include_router(students.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(analytics.router) 
app.include_router(budgets.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "¡Bienvenido a la API de FinEdu!"}