"""
Evaluación completa del pipeline multimodal sobre el dataset de test.
Calcula matriz de confusión y métricas globales.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# Añadir directorio actual al path para importar pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar pipeline multimodal
from pipeline_multimodal import PipelineMultimodal

# ============================================
# CONFIGURACIÓN
# ============================================

BASE_DIR = r'C:\Users\Lenovo\Documents\TFM'
TEST_DIR = os.path.join(BASE_DIR, 'dataset_test')
MODELO_PATH = os.path.join(BASE_DIR, 'mejor_modelo_cnn.pth')

# Cargar anotaciones
anotaciones_path = os.path.join(TEST_DIR, 'anotaciones.csv')
df = pd.read_csv(anotaciones_path)

print("=== EVALUACIÓN DEL PIPELINE MULTIMODAL ===\n")
print(f"Total pares a evaluar: {len(df)}")
print(f"  - Limpios: {len(df[df['tipo'] == 'limpio'])}")
print(f"  - Fraude N1: {len(df[df['tipo'] == 'fraude_n1'])}")
print(f"  - Fraude N2: {len(df[df['tipo'] == 'fraude_n2'])}")
print(f"\nModelo CNN: {MODELO_PATH}")
print(f"Dataset test: {TEST_DIR}\n")

# ============================================
# INICIALIZAR PIPELINE
# ============================================

print("Inicializando pipeline multimodal...")
pipeline = PipelineMultimodal(MODELO_PATH, gpu_ocr=False)
print("✅ Pipeline listo\n")

# ============================================
# EVALUACIÓN
# ============================================

resultados = []

print("Ejecutando evaluación...\n")

for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando pares"):
    ruta_nomina = os.path.join(row['ruta'], row['nomina'])
    ruta_dni = os.path.join(row['ruta'], row['dni'])
    
    # Ejecutar pipeline
    try:
        resultado = pipeline.procesar(ruta_nomina, ruta_dni)
        
        # Determinar si el pipeline detectó fraude
        veredicto_final = resultado['veredicto_final']
        pipeline_detecto_fraude = 1 if veredicto_final == "FRAUDE" else 0
        
        # Determinar si realmente hay fraude (según el tipo)
        if row['tipo'] == 'limpio':
            realidad_es_fraude = 0
        else:
            realidad_es_fraude = 1
        
        # Registrar resultado
        resultados.append({
            'id': row['id'],
            'tipo_real': row['tipo'],
            'realidad_es_fraude': realidad_es_fraude,
            'pipeline_detecto_fraude': pipeline_detecto_fraude,
            'veredicto_final': veredicto_final,
            'explicacion': resultado['explicacion'],
            'nivel1_veredicto': resultado['nivel1']['veredicto'],
            'nivel1_anomalias': str(resultado['nivel1']['anomalias']),
            'nivel2_veredicto': resultado['nivel2']['veredicto'],
            'nivel2_confianza': resultado['nivel2']['confianza']
        })
        
    except Exception as e:
        print(f"Error en {row['id']}: {e}")
        resultados.append({
            'id': row['id'],
            'tipo_real': row['tipo'],
            'realidad_es_fraude': 1 if row['tipo'] != 'limpio' else 0,
            'pipeline_detecto_fraude': -1,
            'veredicto_final': 'ERROR',
            'explicacion': str(e),
            'nivel1_veredicto': 'ERROR',
            'nivel1_anomalias': '',
            'nivel2_veredicto': 'ERROR',
            'nivel2_confianza': 0
        })

# ============================================
# CÁLCULO DE MÉTRICAS
# ============================================

df_resultados = pd.DataFrame(resultados)

# Filtrar solo los que no dieron error
df_ok = df_resultados[df_resultados['pipeline_detecto_fraude'] != -1]

print("\n" + "="*50)
print("=== RESULTADOS DE LA EVALUACIÓN ===")
print("="*50 + "\n")

# Matriz de confusión global
from sklearn.metrics import confusion_matrix, classification_report

y_true = df_ok['realidad_es_fraude']
y_pred = df_ok['pipeline_detecto_fraude']

cm = confusion_matrix(y_true, y_pred)

print("=== MATRIZ DE CONFUSIÓN GLOBAL ===")
print(f"\n                 Predicho")
print(f"               No Fraude  Fraude")
print(f"Real No Fraude     {cm[0,0]:4d}      {cm[0,1]:4d}")
print(f"Real Fraude        {cm[1,0]:4d}      {cm[1,1]:4d}\n")

# Métricas por clase
print("=== MÉTRICAS POR CLASE ===")
print(classification_report(y_true, y_pred, target_names=['No Fraude', 'Fraude']))

# Exactitud global
exactitud_global = (cm[0,0] + cm[1,1]) / cm.sum() * 100
print(f"\n=== EXACTITUD GLOBAL ===")
print(f"Exactitud: {exactitud_global:.2f}%\n")

# ============================================
# RESULTADOS POR TIPO DE PAR
# ============================================

print("=== RESULTADOS POR TIPO DE PAR ===")

for tipo in ['limpio', 'fraude_n1', 'fraude_n2']:
    subtabla = df_ok[df_ok['tipo_real'] == tipo]
    if len(subtabla) > 0:
        aciertos = (subtabla['realidad_es_fraude'] == subtabla['pipeline_detecto_fraude']).sum()
        print(f"\n{tipo.upper()}: {aciertos}/{len(subtabla)} aciertos ({aciertos/len(subtabla)*100:.1f}%)")
        
        # Mostrar algunos errores como ejemplo
        errores = subtabla[subtabla['realidad_es_fraude'] != subtabla['pipeline_detecto_fraude']]
        if len(errores) > 0:
            print(f"  Errores ({len(errores)}):")
            for _, err in errores.head(3).iterrows():
                print(f"    - {err['id']}: {err['explicacion'][:100]}...")

# ============================================
# GUARDAR RESULTADOS
# ============================================

output_path = os.path.join(TEST_DIR, f'resultados_evaluacion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
df_resultados.to_csv(output_path, index=False)
print(f"\n\n✅ Resultados guardados en: {output_path}")

# Resumen final
print("\n" + "="*50)
print("=== RESUMEN FINAL ===")
print(f"Total pares evaluados: {len(df_ok)}/{len(df)}")
print(f"Exactitud global: {exactitud_global:.2f}%")
print(f"Matriz de confusión:")
print(f"  Verdaderos Negativos (limpios bien clasificados): {cm[0,0]}")
print(f"  Falsos Positivos (limpios marcados como fraude): {cm[0,1]}")
print(f"  Falsos Negativos (fraudes no detectados): {cm[1,0]}")
print(f"  Verdaderos Positivos (fraudes bien detectados): {cm[1,1]}")
print("="*50)
