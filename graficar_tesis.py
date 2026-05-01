import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from database import SessionLocal
from analytics.profiling import train_and_cluster_students

def generar_grafica_tesis_pro():
    print("--- Iniciando proceso de graficación ---")
    db = SessionLocal()
    df = train_and_cluster_students(db)
    db.close()

    if df is not None and not df.empty:
        plt.figure(figsize=(14, 8))
        sns.set_style("whitegrid")
        
        # Leyendas con conteo de usuarios
        counts = df['profile_name'].value_counts()
        df['legend_label'] = df['profile_name'].apply(lambda x: f"{x} (n={counts[x]})")

        # Puntos de estudiantes
        sns.scatterplot(
            data=df, x='savings_rate', y='discretionary_ratio',
            hue='legend_label', s=250, alpha=0.6, edgecolor='black', palette='viridis'
        )

        # Centroides (Las X rojas)
        centroids = df.groupby('profile_name')[['savings_rate', 'discretionary_ratio']].mean()
        plt.scatter(
            centroids['savings_rate'], centroids['discretionary_ratio'],
            marker='X', s=600, color='red', label='Centroides (Núcleo)',
            edgecolor='white', linewidth=2, zorder=10
        )

        # Etiquetas en los centroides
        for name, row in centroids.iterrows():
            plt.text(row['savings_rate'], row['discretionary_ratio'] + 0.02, 
                     name, fontsize=10, fontweight='bold', ha='center',
                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        score = df['global_silhouette'].iloc[0]
        plt.title(f'Segmentación de Comportamiento Financiero FinEdu\n(Validación Silhouette: {score:.2f})', 
                  fontsize=16, pad=20, fontweight='bold')
        plt.xlabel('Tasa de Ahorro (Balance/Ingresos)', fontsize=12)
        plt.ylabel('Proporción de Gasto Discrecional', fontsize=12)
        plt.legend(title='Perfiles Identificados', bbox_to_anchor=(1.05, 1), loc='upper left')

        nombre_archivo = "resultado_clusters_tesis_FINAL.png"
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"--- ✅ PROCESO COMPLETADO: Imagen guardada como {nombre_archivo} ---")
    else:
        print("--- ❌ ERROR: No se pudo generar la gráfica por falta de datos ---")

if __name__ == "__main__":
    generar_grafica_tesis_pro()