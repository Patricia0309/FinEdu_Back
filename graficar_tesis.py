import matplotlib.pyplot as plt
import seaborn as sns

def generar_grafica_tesis_pro():
    db = SessionLocal()[cite: 3]
    df = train_and_cluster_students(db)[cite: 1]
    db.close()[cite: 3]

    if df is not None and not df.empty:
        plt.figure(figsize=(14, 8))
        sns.set_style("whitegrid")
        
        # Conteo de usuarios por cluster para la leyenda
        counts = df['profile_name'].value_counts()
        df['legend_label'] = df['profile_name'].apply(lambda x: f"{x} (n={counts[x]})")

        # Scatter Plot principal
        scatter = sns.scatterplot(
            data=df, x='savings_rate', y='discretionary_ratio',
            hue='legend_label', style='legend_label',
            s=200, alpha=0.6, edgecolor='black', palette='viridis'
        )

        # --- CENTROIDES CON ETIQUETAS ---
        centroids = df.groupby('profile_name')[['savings_rate', 'discretionary_ratio']].mean()
        plt.scatter(
            centroids['savings_rate'], centroids['discretionary_ratio'],
            marker='X', s=500, color='red', label='Centroides (Núcleo)',
            edgecolor='white', linewidth=2, zorder=10
        )

        # Añadir texto a cada centroide para identificar el perfil
        for name, row in centroids.iterrows():
            plt.text(
                row['savings_rate'], row['discretionary_ratio'] + 0.02, 
                name, fontsize=10, fontweight='bold', ha='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
            )

        # Información estadística en la gráfica
        score = df['global_silhouette'].iloc[0]
        plt.title(f'Segmentación de Comportamiento Financiero\n(Optimización K-Means | Silhouette: {score:.2f})', 
                  fontsize=16, pad=20, fontweight='bold')
        
        plt.xlabel('Tasa de Ahorro (Balance Neto / Ingresos Totales)', fontsize=12)
        plt.ylabel('Proporción de Gasto Discrecional', fontsize=12)
        plt.legend(title='Clusters y Población', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.savefig("resultado_clusters_tesis_VALIDADO.png", dpi=300, bbox_inches='tight')[cite: 1]
        print(f"✅ Gráfica generada con K={df['profile_id'].max()} y score {score:.2f}")