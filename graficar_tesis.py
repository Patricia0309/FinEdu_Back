# FinEdu_Back/graficar_tesis.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from database import SessionLocal
from analytics.profiling import train_and_cluster_students

def generar_grafica_clusters():
    # 1. Conexión a la BD
    db = SessionLocal()
    print("LOG: Extrayendo datos de la base de datos...")
    
    # 2. Llamamos a tu lógica de K-Means
    df = train_and_cluster_students(db)
    db.close()

    if df is not None and not df.empty:
        print(f"LOG: Graficando {len(df)} usuarios encontrados...")
        
        # 3. Configuración visual
        plt.figure(figsize=(10, 6))
        sns.set_context("talk")
        
        # Creamos el Scatter Plot
        # Eje X: Tasa de ahorro | Eje Y: Gasto discrecional
        scatter = sns.scatterplot(
            data=df,
            x='savings_rate',
            y='discretionary_ratio',
            hue='profile_name',
            palette='deep',
            s=150,
            edgecolor='black',
            alpha=0.7
        )

        # 4. Etiquetas profesionales para la tesis
        plt.title('Visualización de Perfiles Financieros (K-Means)', pad=20)
        plt.xlabel('Tasa de Ahorro (Income vs Expense)')
        plt.ylabel('Proporción de Gasto Discrecional')
        plt.legend(title='Clusters Identificados', bbox_to_anchor=(1, 1))
        
        # 5. Guardar el archivo
        nombre_archivo = "resultado_clusters_tesis.png"
        plt.savefig(nombre_archivo, bbox_inches='tight', dpi=300)
        print(f"✅ ¡ÉXITO! Tu gráfica se guardó como: {nombre_archivo}")
        plt.show()
    else:
        print("❌ ERROR: No hay suficientes usuarios (mínimo 5) para generar clusters.")

if __name__ == "__main__":
    generar_grafica_clusters()