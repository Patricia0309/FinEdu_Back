import matplotlib.pyplot as plt
import seaborn as sns
from database import SessionLocal
from analytics.profiling import train_and_cluster_students

def ejecutar():
    print("--- Generando gráfica definitiva ---")
    db = SessionLocal()
    df = train_and_cluster_students(db)
    db.close()

    if df is not None and not df.empty:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='savings_rate', y='discretionary_ratio', 
                        hue='profile_name', s=200, palette='viridis')
        
        # Centroides
        centroids = df.groupby('profile_name')[['savings_rate', 'discretionary_ratio']].mean()
        plt.scatter(centroids['savings_rate'], centroids['discretionary_ratio'], 
                    marker='X', s=400, color='red', label='Centroides')

        plt.title(f"Segmentación FinEdu (Silhouette: {df['global_silhouette'].iloc[0]:.2f})")
        plt.xlim(-1.1, 1.1)
        plt.savefig("resultado_FINAL_FINAL.png")
        print("✅ ¡LOGRADO! Imagen guardada como resultado_FINAL_FINAL.png")
    else:
        print("❌ Sigue sin haber suficientes datos válidos (ingresos > 0).")

if __name__ == "__main__":
    ejecutar()