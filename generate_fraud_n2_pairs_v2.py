"""
Genera pares para Nivel 2: nómina con fraude de fuente + DNI limpio
VERSIÓN CORREGIDA: El DNI se genera CON LOS DATOS DE LA NÓMINA (coherente)
"""

import os
import random
import pandas as pd
import shutil
from datetime import datetime
from config import FRAUD_N2_DIR, RAW_DIR, RANDOM_SEED
from generate_nominas_n2 import generate_batch_nominas_n2
from generate_dnis import create_dni_image
from utils import generate_nif

random.seed(RANDOM_SEED)

def generate_fraud_n2_pairs(num_pairs=400):
    """
    Genera num_pairs pares con nómina fraudulenta (fuente distinta) y DNI limpio
    El DNI se genera a partir de los mismos datos que la nómina (coherente)
    """
    print(f"\n=== Generando {num_pairs} pares con fraude N2 (cambio de fuente) ===\n")
    
    # Limpiar carpeta anterior
    if os.path.exists(FRAUD_N2_DIR):
        shutil.rmtree(FRAUD_N2_DIR)
    os.makedirs(FRAUD_N2_DIR, exist_ok=True)
    
    # Crear carpeta temporal para DNIs generados ad-hoc
    temp_dni_dir = os.path.join(RAW_DIR, 'dnis_temp_n2')
    os.makedirs(temp_dni_dir, exist_ok=True)
    
    # Generar nóminas CON fraude (fuente distinta)
    print("1. Generando nóminas con cambio de fuente...")
    nominas = generate_batch_nominas_n2(num_pairs, n2_tipo='fuente_distinta')
    
    all_pairs = []
    
    print("\n2. Generando DNIs coherentes con cada nómina...")
    for i, nomina in enumerate(nominas):
        # DATOS COHERENTES con la nómina
        full_name = nomina['worker_name']
        nif = nomina['nif']
        
        # Generar fecha de nacimiento coherente (entre 1960 y 2005)
        birth_year = random.randint(1960, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = datetime(birth_year, birth_month, birth_day)
        birth_date_str = birth_date.strftime('%d/%m/%Y')
        
        # Generar imagen del DNI con los datos correctos
        dni_filename = os.path.join(temp_dni_dir, f'dni_coherente_{i+1:04d}.png')
        create_dni_image(full_name, nif, birth_date_str, dni_filename)
        
        # Crear directorio del par
        par_dir = os.path.join(FRAUD_N2_DIR, f'fraud_n2_{i+1:04d}')
        os.makedirs(par_dir, exist_ok=True)
        
        # Copiar imágenes
        nomina_destino = os.path.join(par_dir, 'nomina.png')
        dni_destino = os.path.join(par_dir, 'dni.png')
        
        shutil.copy2(nomina['path'], nomina_destino)
        shutil.copy2(dni_filename, dni_destino)
        
        all_pairs.append({
            'id_par': f'fraud_n2_{i+1:04d}',
            'nomina_path': nomina_destino,
            'dni_path': dni_destino,
            'nomina_fraud': True,
            'dni_fraud': False,
            'tipo_fraude': 'fuente_distinta',
            'documento_afectado': 'nomina',
            'campo_afectado': 'total_neto',
            'worker_name_nomina': nomina['worker_name'],
            'nif_nomina': nomina['nif'],
            'importe_nomina': nomina['amount'],
            'nombre_dni': full_name,
            'nif_dni': nif,
            'fecha_nacimiento_dni': birth_date_str,
            'etiqueta': 'fraude_n2'
        })
        
        if (i + 1) % 100 == 0:
            print(f"  Procesados {i+1}/{num_pairs} pares...")
    
    # Limpiar temporales
    shutil.rmtree(temp_dni_dir)
    
    # Guardar anotaciones
    df = pd.DataFrame(all_pairs)
    df.to_csv(os.path.join(FRAUD_N2_DIR, 'annotations_fraud_n2.csv'), index=False)
    
    print(f"\n✓ Generados {len(all_pairs)} pares con fraude N2")
    print(f"  - Directorio: {FRAUD_N2_DIR}")
    
    # Verificación de coherencia
    print("\n=== VERIFICACIÓN DE COHERENCIA ===")
    nombres_coinciden = sum(df['worker_name_nomina'] == df['nombre_dni'])
    nifs_coinciden = sum(df['nif_nomina'] == df['nif_dni'])
    
    print(f"  - Nombres coincidentes: {nombres_coinciden}/{len(df)} (100% requerido)")
    print(f"  - NIFs coincidentes: {nifs_coinciden}/{len(df)} (100% requerido)")
    
    if nombres_coinciden == len(df) and nifs_coinciden == len(df):
        print("\n✓ VALIDACIÓN CORRECTA: Todos los DNIs son coherentes con sus nóminas")
        print("✓ El ÚNICO fraude es el cambio de fuente en el TOTAL NETO de la nómina")
    else:
        print("\n⚠️ ERROR: Hay incoherencias en los datos")
    
    return all_pairs

if __name__ == '__main__':
    pairs = generate_fraud_n2_pairs(400)
    
    # Mostrar ejemplo
    print("\n=== EJEMPLO DE UN PAR GENERADO ===")
    ejemplo = pairs[0]
    print(f"  Nómina: {ejemplo['worker_name_nomina']} - {ejemplo['nif_nomina']}")
    print(f"  DNI:    {ejemplo['nombre_dni']} - {ejemplo['nif_dni']}")
    print(f"  Coinciden: {ejemplo['worker_name_nomina'] == ejemplo['nombre_dni']}")
    print(f"  Fraude N2 aplicado: {ejemplo['tipo_fraude']} en {ejemplo['documento_afectado']}")