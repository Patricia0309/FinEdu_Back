import matplotlib.pyplot as plt
import seaborn as sns
from database import SessionLocal
from analytics.profiling import train_and_cluster_students

def generar_grafica_tesis_final():
    db = SessionLocal()
    df = train_and_cluster_students(db)
    db.close()

    if df is not None and not df.empty:
        plt.figure(figsize=(12, 7))
        sns.set_style("whitegrid")
        
        # Conteo para la leyenda
        counts = df['profile_name'].value_counts()
        df['label'] = df['profile_name'].apply(lambda x: f"{x} (n={counts[x]})")

        # Dibujar puntos
        sns.scatterplot(
            data=df, x='savings_rate', y='discretionary_ratio',
            hue='label', s=250, alpha=0.7, edgecolor='black', palette='Set1'
        )

        # Dibujar Centroides (Las X rojas)
        centroids = df.groupby('profile_name')[['savings_rate', 'discretionary_ratio']].mean()
        plt.scatter(
            centroids['savings_rate'], centroids['discretionary_ratio'],
            marker='X', s=500, color='red', label='Centroides',
            edgecolor='white', linewidth=2, zorder=10
        )

        score = df['global_silhouette'].iloc[0]
        plt.title(f'Segmentación de Comportamiento Financiero (N= {len(df)})\nValidación Silhouette: {score:.2f}', 
                  fontsize=14, fontweight='bold', pad=20)
        
        # Limitar los ejes para que se vea bien el "zoom"
        plt.xlim(-1.1, 1.1) 
        plt.xlabel('Tasa de Ahorro (Ahorro / Ingresos)', fontsize=11)
        plt.ylabel('Gasto Discrecional (Gasto / Total)', fontsize=11)
        
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Perfiles")
        plt.tight_layout()

        plt.savefig("resultado_TESIS_IMPECABLE.png", dpi=300)
        print("✅ ¡Gráfica perfecta generada!")

if __name__ == "__main__":
    generar_grafica_tesis_final()