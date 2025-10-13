# backend/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import models
import crud
from routers import students, auth, transactions # <-- 1. Importa el router de transacciones

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

# 2. Incluye todos los routers
app.include_router(students.router)
app.include_router(auth.router)
app.include_router(transactions.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "¡Bienvenido a la API de FinEdu!"}