"""
Crea un subconjunto de prueba con pares limpios, fraude N1 y fraude N2.
No incluye pares mixtos.
Estructura de salida lista para usar con el pipeline multimodal.
"""

import os
import random
import shutil
import pandas as pd

# ============================================
# CONFIGURACIÓN
# ============================================

BASE_DIR = r'C:\Users\Lenovo\Documents\TFM'

# Directorios de origen
LIMPIO_DIR = os.path.join(BASE_DIR, 'dataset', 'processed', 'limpios')
N1_DIR = os.path.join(BASE_DIR, 'dataset', 'processed', 'fraudulentos', 'nivel1')
N2_DIR = os.path.join(BASE_DIR, 'dataset', 'processed', 'fraudulentos', 'nivel2')

# Directorio de destino para el test
TEST_DIR = os.path.join(BASE_DIR, 'dataset_test')
TEST_LIMPIO_DIR = os.path.join(TEST_DIR, 'limpios')
TEST_N1_DIR = os.path.join(TEST_DIR, 'fraude_n1')
TEST_N2_DIR = os.path.join(TEST_DIR, 'fraude_n2')

# Configuración de muestras
NUM_LIMPIOS = 50
NUM_N1 = 50
NUM_N2 = 50

# Semilla para reproducibilidad
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ============================================
# FUNCIONES
# ============================================

def limpiar_carpeta(directorio):
    """Elimina y recrea un directorio para empezar desde cero."""
    if os.path.exists(directorio):
        shutil.rmtree(directorio)
    os.makedirs(directorio, exist_ok=True)

def listar_pares(directorio, prefijo):
    """Lista las subcarpetas que contienen los pares."""
    pares = []
    if not os.path.exists(directorio):
        return pares
    for item in os.listdir(directorio):
        if item.startswith(prefijo):
            ruta = os.path.join(directorio, item)
            if os.path.isdir(ruta):
                pares.append(ruta)
    return sorted(pares)

def copiar_par(origen, destino, id_par, clase):
    """Copia un par (nomina.png, dni.png) a una nueva ubicación."""
    os.makedirs(destino, exist_ok=True)
    
    nomina_origen = os.path.join(origen, 'nomina.png')
    dni_origen = os.path.join(origen, 'dni.png')
    
    nomina_destino = os.path.join(destino, f'{clase}_{id_par:04d}_nomina.png')
    dni_destino = os.path.join(destino, f'{clase}_{id_par:04d}_dni.png')
    
    shutil.copy2(nomina_origen, nomina_destino)
    shutil.copy2(dni_origen, dni_destino)
    
    return nomina_destino, dni_destino

# ============================================
# CREACIÓN DEL DATASET DE TEST
# ============================================

print("=== CREANDO DATASET DE TEST ===\n")

# Limpiar carpetas de destino
limpiar_carpeta(TEST_LIMPIO_DIR)
limpiar_carpeta(TEST_N1_DIR)
limpiar_carpeta(TEST_N2_DIR)
print("Carpetas de destino limpias.\n")

# 1. Pares LIMPIOS
print(f"Seleccionando {NUM_LIMPIOS} pares limpios...")
pares_limpios = listar_pares(LIMPIO_DIR, 'pair_')
pares_limpios_seleccionados = random.sample(pares_limpios, min(NUM_LIMPIOS, len(pares_limpios)))
print(f"  Encontrados: {len(pares_limpios)} | Seleccionados: {len(pares_limpios_seleccionados)}")

for i, origen in enumerate(pares_limpios_seleccionados):
    copiar_par(origen, TEST_LIMPIO_DIR, i+1, 'limpio')

# 2. Pares FRAUDE N1
print(f"\nSeleccionando {NUM_N1} pares de fraude N1...")
pares_n1 = listar_pares(N1_DIR, 'fraud_n1_')
pares_n1_seleccionados = random.sample(pares_n1, min(NUM_N1, len(pares_n1)))
print(f"  Encontrados: {len(pares_n1)} | Seleccionados: {len(pares_n1_seleccionados)}")

for i, origen in enumerate(pares_n1_seleccionados):
    copiar_par(origen, TEST_N1_DIR, i+1, 'fraude_n1')

# 3. Pares FRAUDE N2
print(f"\nSeleccionando {NUM_N2} pares de fraude N2...")
pares_n2 = listar_pares(N2_DIR, 'fraud_n2_')
pares_n2_seleccionados = random.sample(pares_n2, min(NUM_N2, len(pares_n2)))
print(f"  Encontrados: {len(pares_n2)} | Seleccionados: {len(pares_n2_seleccionados)}")

for i, origen in enumerate(pares_n2_seleccionados):
    copiar_par(origen, TEST_N2_DIR, i+1, 'fraude_n2')

# ============================================
# CREAR ANOTACIONES GLOBALES (opcional)
# ============================================

print("\n=== CREANDO ANOTACIONES ===\n")

anotaciones = []

# Limpios
for i in range(len(pares_limpios_seleccionados)):
    anotaciones.append({
        'id': f'limpio_{i+1:04d}',
        'tipo': 'limpio',
        'ruta': TEST_LIMPIO_DIR,
        'nomina': f'limpio_{i+1:04d}_nomina.png',
        'dni': f'limpio_{i+1:04d}_dni.png'
    })

# N1
for i in range(len(pares_n1_seleccionados)):
    anotaciones.append({
        'id': f'fraude_n1_{i+1:04d}',
        'tipo': 'fraude_n1',
        'ruta': TEST_N1_DIR,
        'nomina': f'fraude_n1_{i+1:04d}_nomina.png',
        'dni': f'fraude_n1_{i+1:04d}_dni.png'
    })

# N2
for i in range(len(pares_n2_seleccionados)):
    anotaciones.append({
        'id': f'fraude_n2_{i+1:04d}',
        'tipo': 'fraude_n2',
        'ruta': TEST_N2_DIR,
        'nomina': f'fraude_n2_{i+1:04d}_nomina.png',
        'dni': f'fraude_n2_{i+1:04d}_dni.png'
    })

# Guardar CSV
df = pd.DataFrame(anotaciones)
csv_path = os.path.join(TEST_DIR, 'anotaciones.csv')
df.to_csv(csv_path, index=False)
print(f"Anotaciones guardadas en: {csv_path}")

# ============================================
# ESTADÍSTICAS FINALES
# ============================================

print("\n=== DATASET DE TEST CREADO ===\n")
print(f"Limpios:    {len(pares_limpios_seleccionados)} pares")
print(f"Fraude N1:  {len(pares_n1_seleccionados)} pares")
print(f"Fraude N2:  {len(pares_n2_seleccionados)} pares")
print(f"\nTotal:      {len(anotaciones)} pares")
print(f"\nDirectorio principal: {TEST_DIR}")