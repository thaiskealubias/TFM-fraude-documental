"""
Organiza el dataset para CNN combinando:
- Nóminas limpias (de processed/limpios)
- Nóminas con fraude N2 (de processed/fraudulentos/nivel2)
"""

import os
import random
import shutil

RANDOM_SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

BASE_DIR = r'C:\Users\Lenovo\Documents\TFM'
LIMPIOS_DIR = os.path.join(BASE_DIR, 'dataset', 'processed', 'limpios')
N2_DIR = os.path.join(BASE_DIR, 'dataset', 'processed', 'fraudulentos', 'nivel2')
OUTPUT_DIR = os.path.join(BASE_DIR, 'dataset_cnn')

random.seed(RANDOM_SEED)

def split_list(data, train_ratio, val_ratio):
    random.shuffle(data)
    n = len(data)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    return data[:train_end], data[train_end:val_end], data[val_end:]

def encontrar_nominas_limpias():
    """Recorre processed/limpios y recoge todas las nóminas"""
    nominas = []
    if not os.path.exists(LIMPIOS_DIR):
        print(f"Error: No existe {LIMPIOS_DIR}")
        return nominas
    
    for par_dir in os.listdir(LIMPIOS_DIR):
        if par_dir.startswith('pair_'):
            nomina_path = os.path.join(LIMPIOS_DIR, par_dir, 'nomina.png')
            if os.path.exists(nomina_path):
                nominas.append(nomina_path)
    return nominas

def encontrar_nominas_fraude_n2():
    """Recorre processed/fraudulentos/nivel2 y recoge todas las nóminas"""
    nominas = []
    if not os.path.exists(N2_DIR):
        print(f"Error: No existe {N2_DIR}")
        return nominas
    
    for par_dir in os.listdir(N2_DIR):
        if par_dir.startswith('fraud_n2_'):
            nomina_path = os.path.join(N2_DIR, par_dir, 'nomina.png')
            if os.path.exists(nomina_path):
                nominas.append(nomina_path)
    return nominas

# Crear directorios
for split in ['train', 'val', 'test']:
    for clase in ['limpia', 'fraude']:
        os.makedirs(os.path.join(OUTPUT_DIR, split, clase), exist_ok=True)

print("=== Organizando dataset para CNN ===\n")

# Recopilar nóminas
print("Buscando nóminas limpias...")
nominas_limpias = encontrar_nominas_limpias()
print(f"  Encontradas: {len(nominas_limpias)}")

print("Buscando nóminas con fraude N2...")
nominas_fraude = encontrar_nominas_fraude_n2()
print(f"  Encontradas: {len(nominas_fraude)}")

if len(nominas_limpias) == 0 or len(nominas_fraude) == 0:
    print("\nError: Faltan imágenes. Verifica las rutas.")
    print(f"Limpias: {LIMPIOS_DIR}")
    print(f"Fraude N2: {N2_DIR}")
    raise SystemExit

# Dividir
limpia_train, limpia_val, limpia_test = split_list(nominas_limpias, TRAIN_RATIO, VAL_RATIO)
fraude_train, fraude_val, fraude_test = split_list(nominas_fraude, TRAIN_RATIO, VAL_RATIO)

def copiar(lista, split_name, clase):
    for i, src in enumerate(lista):
        ext = os.path.splitext(src)[1]
        dst = os.path.join(OUTPUT_DIR, split_name, clase, f"{clase}_{i+1:04d}{ext}")
        shutil.copy2(src, dst)

print("\n=== Copiando imágenes ===")
copiar(limpia_train, 'train', 'limpia')
copiar(limpia_val, 'val', 'limpia')
copiar(limpia_test, 'test', 'limpia')
copiar(fraude_train, 'train', 'fraude')
copiar(fraude_val, 'val', 'fraude')
copiar(fraude_test, 'test', 'fraude')

print("\n=== Distribución final ===")
print(f"Train: {len(limpia_train)} limpias + {len(fraude_train)} fraude = {len(limpia_train)+len(fraude_train)}")
print(f"Val:   {len(limpia_val)} limpias + {len(fraude_val)} fraude = {len(limpia_val)+len(fraude_val)}")
print(f"Test:  {len(limpia_test)} limpias + {len(fraude_test)} fraude = {len(limpia_test)+len(fraude_test)}")
print(f"\n✓ Dataset organizado en: {OUTPUT_DIR}")
