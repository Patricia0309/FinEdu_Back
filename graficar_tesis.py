import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
# IMPORTANTE: Asegúrate de que estas rutas sean correctas según tu carpeta
from database import SessionLocal 
from analytics.profiling import train_and_cluster_students

def generar_grafica_tesis_pro():
    db = SessionLocal()
    df = train_and_cluster_students(db)
    db.close()

    if df is not None and not df.empty:
        plt.figure(figsize=(14, 8))
        sns.set_style("whitegrid")
        
        counts = df['profile_name'].value_counts()
        df['legend_label'] = df['profile_name'].apply(lambda x: f"{x} (n={counts[x]})")

        # Scatter Plot
        sns.scatterplot(
            data=df, x='savings_rate', y='discretionary_ratio',
            hue='legend_label', s=200, alpha=0.6, edgecolor='black', palette='viridis'
        )

        # Centroides
        centroids = df.groupby('profile_name')[['savings_rate', 'discretionary_ratio']].mean()
        plt.scatter(
            centroids['savings_rate'], centroids['discretionary_ratio'],
            marker='X', s=500, color='red', label='Centroides',
            edgecolor='white', linewidth=2, zorder=10
        )

        # Etiquetas de centroides
        for name, row in centroids.iterrows():
            plt.text(row['savings_rate'], row['discretionary_ratio'] + 0.02, 
                     name, fontsize=10, fontweight='bold', ha='center')

        score = df['global_silhouette'].iloc[0]
        plt.title(f'Análisis de Perfiles FinEdu\n(Silhouette Score: {score:.2f})', fontsize=16, pad=20)
        plt.xlabel('Tasa de Ahorro')
        plt.ylabel('Gasto Discrecional')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.savefig("resultado_clusters_tesis_VALIDADO.png", dpi=300, bbox_inches='tight')
        print(f"✅ Gráfica generada con éxito.")

if __name__ == "__main__":
    generar_grafica_tesis_pro()