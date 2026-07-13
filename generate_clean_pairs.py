import pandas as pd
import random
import os
import shutil
from config import CLEAN_DIR, RAW_DIR, NUM_SAMPLES, RANDOM_SEED
from utils import save_image, load_annotation_file
from generate_nominas import generate_batch_nominas
from generate_dnis import generate_batch_dnis

random.seed(RANDOM_SEED)

def generate_clean_pairs(n):
    """
    Genera n pares limpios (nómina + DNI) con datos coherentes
    
    Cada par consiste en una nómina y un DNI que pertenecen a la misma persona
    """
    print(f"Generando {n} pares limpios...")
    
    # Generar documentos base
    nominas = generate_batch_nominas(n)
    dnis = generate_batch_dnis(n)
    
    # Emparejar por índice (misma persona)
    pairs = []
    annotations = load_annotation_file()
    
    for i in range(n):
        nomina = nominas[i]
        dni = dnis[i]
        
        # Para pares limpios, los datos deben coincidir
        # Ajustamos el DNI para que coincida con la nómina
        dni['full_name'] = nomina['worker_name']
        dni['nif'] = nomina['nif']
        
        # Regenerar imagen del DNI con los datos corregidos
        from generate_dnis import create_dni_image
        dni_path = os.path.join(RAW_DIR, 'dnis', f'dni_{i+1:04d}_clean.png')
        create_dni_image(dni['full_name'], dni['nif'], dni['birth_date'], dni_path)
        
        # Copiar o mover a processed/limpios
        clean_pair_dir = os.path.join(CLEAN_DIR, f'pair_{i+1:04d}')
        os.makedirs(clean_pair_dir, exist_ok=True)
        
        nomina_clean_path = os.path.join(clean_pair_dir, 'nomina.png')
        dni_clean_path = os.path.join(clean_pair_dir, 'dni.png')
        
        shutil.copy2(nomina['path'], nomina_clean_path)
        shutil.copy2(dni_path, dni_clean_path)
        
        # Guardar anotación
        pairs.append({
            'id_nomina': nomina['id'],
            'id_dni': dni['id'],
            'nomina_path': nomina_clean_path,
            'dni_path': dni_clean_path,
            'tipo_fraude': 'clean',
            'campos_afectados': '',
            'etiqueta': 'valido',
            'split': ''  # Se asignará después
        })
    
    print(f"Generados {len(pairs)} pares limpios")
    return pairs

if __name__ == '__main__':
    pairs = generate_clean_pairs(400)  # Generamos 400 pares limpios
    
    # Guardar anotaciones
    df = pd.DataFrame(pairs)
    from config import ANNOTATIONS_FILE
    df.to_csv(ANNOTATIONS_FILE, index=False)
    print(f"Anotaciones guardadas en {ANNOTATIONS_FILE}")