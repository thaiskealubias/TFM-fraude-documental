"""
Genera 200 pares de documentos (nómina + DNI) con fraudes de Nivel 1
LOS CAMBIOS SE VEN EN LAS IMÁGENES
"""

import os
import random
import pandas as pd
import shutil
from datetime import datetime
from config import FRAUD_N1_DIR, RAW_DIR, RANDOM_SEED
from utils import generate_nif, generate_ssn, generate_amount, fake
from generate_nominas_n1 import create_nomina_image
from generate_dnis_n1 import create_dni_image

random.seed(RANDOM_SEED)

# Mapeo a tipo de incoherencia global
FRAUD_TO_INCOHERENCE = {
    'importe_sospechoso': 'importe_sospechoso',
    'nif': 'nif_no_coincide',
    'nif_invalido': 'nif_no_coincide',
    'nombre': 'nombre_no_coincide',
    'dni_caducado': 'dni_caducado',
    'fecha_nacimiento': 'fecha_nacimiento_incoherente',
}

def aplicar_fraude_nomina(datos_base, tipo_fraude):
    """Aplica fraude SOLO al campo específico, manteniendo el resto coherente"""
    datos = datos_base.copy()
    
    if tipo_fraude == 'nombre':
        partes = datos_base['worker_name'].split()
        datos['worker_name'] = f"FRAUDE_{partes[0] if partes else 'Nombre'}"
        
    elif tipo_fraude == 'nif':
        datos['nif'] = generate_nif()
        
    elif tipo_fraude == 'nif_invalido':
        numeros = random.randint(10000000, 99999999)
        letras = 'TRWAGMYFPDXBNJZSQVHLCKE'
        letra_correcta = letras[numeros % 23]
        letras_posibles = [l for l in letras if l != letra_correcta]
        letra_incorrecta = random.choice(letras_posibles)
        datos['nif'] = f"{numeros}{letra_incorrecta}"
        
    elif tipo_fraude == 'importe_sospechoso':
        opcion = random.choice(['muy_bajo', 'muy_alto'])
        if opcion == 'muy_bajo':
            datos['amount'] = round(random.uniform(0, 299), 2)
        else:
            datos['amount'] = round(random.uniform(15001, 50000), 2)
    
    return datos

def aplicar_fraude_dni(datos_base, tipo_fraude):
    """Aplica fraude SOLO al campo específico, manteniendo el resto coherente"""
    datos = datos_base.copy()
    
    if tipo_fraude == 'nombre':
        partes = datos_base['full_name'].split()
        datos['full_name'] = f"FRAUDE_{partes[0] if partes else 'Nombre'}"
        
    elif tipo_fraude == 'nif':
        datos['nif'] = generate_nif()
        
    elif tipo_fraude == 'nif_invalido':
        numeros = random.randint(10000000, 99999999)
        letras = 'TRWAGMYFPDXBNJZSQVHLCKE'
        letra_correcta = letras[numeros % 23]
        letras_posibles = [l for l in letras if l != letra_correcta]
        letra_incorrecta = random.choice(letras_posibles)
        datos['nif'] = f"{numeros}{letra_incorrecta}"
        
    elif tipo_fraude == 'fecha_nacimiento':
        year_actual = datetime.now().year
        opcion = random.choice(['menor_16', 'mayor_67', 'futuro'])
        if opcion == 'menor_16':
            año = year_actual - random.randint(5, 15)
        elif opcion == 'mayor_67':
            año = year_actual - random.randint(68, 90)
        else:
            año = year_actual + random.randint(1, 10)
        datos['birth_date'] = f"01/01/{año}"
        
    elif tipo_fraude == 'dni_caducado':
        datos['force_caducado'] = True
    
    return datos

def generar_par_fraudulento(par_id, tipo_incoherencia):
    """
    Genera UN par con un tipo específico de incoherencia
    
    IMPORTANTE: Los datos BASE son comunes para ambos documentos.
    Solo se modifican los campos que CAUSAN la incoherencia.
    """
    
    # === DATOS BASE (coherentes para ambos documentos) ===
    birth_year = random.randint(1960, 2005)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    birth_date = datetime(birth_year, birth_month, birth_day)
    birth_date_str = birth_date.strftime('%d/%m/%Y')
    
    base_data = {
        'full_name': fake.name(),
        'nif': generate_nif(),
        'birth_date': birth_date_str,
        'ssn': generate_ssn(),
        'amount': generate_amount(),
        'force_caducado': False
    }
    
    # Inicializar datos para cada documento (copia de base)
    nomina_data = {
        'worker_name': base_data['full_name'],
        'nif': base_data['nif'],
        'ssn': base_data['ssn'],
        'amount': base_data['amount'],
        'date': fake.date_between(start_date='-1y', end_date='today').strftime('%d/%m/%Y')
    }
    
    dni_data = {
        'full_name': base_data['full_name'],
        'nif': base_data['nif'],
        'birth_date': base_data['birth_date'],
        'force_caducado': False
    }
    
    fraud_nomina_type = None
    fraud_dni_type = None
    
    # === APLICAR FRAUDE SEGÚN EL TIPO DE INCOHERENCIA ===
    if tipo_incoherencia == 'nombre_no_coincide':
        quien = random.choice(['nomina', 'dni'])
        if quien == 'nomina':
            fraud_nomina_type = 'nombre'
            nomina_data = aplicar_fraude_nomina(nomina_data, 'nombre')
        else:
            fraud_dni_type = 'nombre'
            dni_data = aplicar_fraude_dni(dni_data, 'nombre')
    
    elif tipo_incoherencia == 'nif_no_coincide':
        quien = random.choice(['nomina', 'dni'])
        tipo_nif = random.choice(['nif', 'nif_invalido'])
        if quien == 'nomina':
            fraud_nomina_type = tipo_nif
            nomina_data = aplicar_fraude_nomina(nomina_data, tipo_nif)
        else:
            fraud_dni_type = tipo_nif
            dni_data = aplicar_fraude_dni(dni_data, tipo_nif)
    
    elif tipo_incoherencia == 'importe_sospechoso':
        fraud_nomina_type = 'importe_sospechoso'
        nomina_data = aplicar_fraude_nomina(nomina_data, 'importe_sospechoso')
    
    elif tipo_incoherencia == 'dni_caducado':
        fraud_dni_type = 'dni_caducado'
        dni_data = aplicar_fraude_dni(dni_data, 'dni_caducado')
    
    elif tipo_incoherencia == 'fecha_nacimiento_incoherente':
        fraud_dni_type = 'fecha_nacimiento'
        dni_data = aplicar_fraude_dni(dni_data, 'fecha_nacimiento')
    
    # === GENERAR LAS IMÁGENES ===
    os.makedirs(os.path.join(RAW_DIR, 'nominas_temp'), exist_ok=True)
    os.makedirs(os.path.join(RAW_DIR, 'dnis_temp'), exist_ok=True)
    
    nomina_path = os.path.join(RAW_DIR, 'nominas_temp', f'nomina_{par_id}.png')
    dni_path = os.path.join(RAW_DIR, 'dnis_temp', f'dni_{par_id}.png')
    
    # Crear nómina
    from generate_nominas import NOMINA_STYLES
    style_idx = random.randint(0, len(NOMINA_STYLES) - 1)
    
    create_nomina_image(
        nomina_data['worker_name'],
        nomina_data['nif'],
        nomina_data['ssn'],
        nomina_data['amount'],
        nomina_data['date'],
        nomina_path,
        style_idx
    )
    
    # Crear DNI (pasando el flag force_caducado)
    create_dni_image(
        dni_data['full_name'],
        dni_data['nif'],
        dni_data['birth_date'],
        dni_path,
        force_caducado=dni_data.get('force_caducado', False)  # ← MODIFICADO
    )
    
    # === COPIAR A DIRECTORIO FINAL ===
    par_dir = os.path.join(FRAUD_N1_DIR, f'fraud_n1_{par_id:04d}')
    os.makedirs(par_dir, exist_ok=True)
    
    nomina_destino = os.path.join(par_dir, 'nomina.png')
    dni_destino = os.path.join(par_dir, 'dni.png')
    
    shutil.copy2(nomina_path, nomina_destino)
    shutil.copy2(dni_path, dni_destino)
    
    # Limpiar temporales
    os.remove(nomina_path)
    os.remove(dni_path)
    
    return {
        'id_par': f'fraud_n1_{par_id:04d}',
        'nomina_path': nomina_destino,
        'dni_path': dni_destino,
        'nomina_fraud': fraud_nomina_type is not None,
        'dni_fraud': fraud_dni_type is not None,
        'tipo_incoherencia': tipo_incoherencia,
        'tipo_fraude_nomina': fraud_nomina_type,
        'tipo_fraude_dni': fraud_dni_type,
        'worker_name_nomina': nomina_data['worker_name'],
        'nif_nomina': nomina_data['nif'],
        'importe_nomina': nomina_data['amount'],
        'nombre_dni': dni_data['full_name'],
        'nif_dni': dni_data['nif'],
        'fecha_nacimiento_dni': dni_data['birth_date'],
        'etiqueta': 'fraude_n1'
    }

def generate_fraud_n1_pairs(num_pairs=200):
    """
    Genera EXACTAMENTE num_pairs pares fraudulentos N1
    """
    
    print(f"\n=== Generando {num_pairs} pares con fraude N1 ===")
    print("✓ Los documentos BASE son coherentes (mismo nombre, mismo NIF)")
    print("✓ Solo se modifican los campos que causan el fraude")
    print("✓ EXCLUIDO: ssn_invalido")
    
    os.makedirs(FRAUD_N1_DIR, exist_ok=True)
    
    # Distribución balanceada de tipos de fraude (SIN SSN)
    distribucion = {
        'nombre_no_coincide': 45,           # 45 pares
        'nif_no_coincide': 45,              # 45 pares
        'importe_sospechoso': 40,           # 40 pares
        'dni_caducado': 35,                 # 35 pares
        'fecha_nacimiento_incoherente': 35, # 35 pares
    }
    # Total: 200
    
    all_pairs = []
    par_id = 1
    
    for tipo_incoherencia, cantidad in distribucion.items():
        print(f"Generando {cantidad} pares de tipo: {tipo_incoherencia}")
        
        for _ in range(cantidad):
            par = generar_par_fraudulento(par_id, tipo_incoherencia)
            all_pairs.append(par)
            par_id += 1
    
    print(f"\n✓ Generados {len(all_pairs)} pares con fraude N1")
    
    # Guardar anotaciones
    df = pd.DataFrame(all_pairs)
    df.to_csv(os.path.join(FRAUD_N1_DIR, 'annotations_fraud_n1.csv'), index=False)
    
    # Estadísticas
    print("\n=== Distribución de incoherencias generadas ===")
    print(df['tipo_incoherencia'].value_counts())
    
    # Verificación de coherencia
    print("\n=== VERIFICACIÓN DE COHERENCIA ===")
    
    # Pares sin fraude de nombre
    no_nombre = df[df['tipo_incoherencia'] != 'nombre_no_coincide']
    if len(no_nombre) > 0:
        nombre_match = sum(no_nombre['worker_name_nomina'] == no_nombre['nombre_dni'])
        print(f"✓ Pares sin fraude de nombre: {len(no_nombre)}")
        print(f"  - Nombres coincidentes: {nombre_match}/{len(no_nombre)} (100% requerido)")
        assert nombre_match == len(no_nombre), "ERROR: Nombres no coinciden"
    
    # Pares sin fraude de NIF
    no_nif = df[df['tipo_incoherencia'] != 'nif_no_coincide']
    if len(no_nif) > 0:
        nif_match = sum(no_nif['nif_nomina'] == no_nif['nif_dni'])
        print(f"✓ Pares sin fraude de NIF: {len(no_nif)}")
        print(f"  - NIFs coincidentes: {nif_match}/{len(no_nif)} (100% requerido)")
        assert nif_match == len(no_nif), "ERROR: NIFs no coinciden"
    
    print("\n✓ VALIDACIÓN COMPLETA")
    
    return all_pairs

if __name__ == '__main__':
    # Limpiar carpeta anterior
    import shutil
    if os.path.exists(FRAUD_N1_DIR):
        print(f"Limpiando {FRAUD_N1_DIR}...")
        shutil.rmtree(FRAUD_N1_DIR)
    
    # Generar 200 pares fraudulentos
    pairs = generate_fraud_n1_pairs(200)
    
    # Resumen final
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Total pares generados: {len(pairs)}")
    print(f"Ubicación: {FRAUD_N1_DIR}/")
    print(f"Anotaciones: {FRAUD_N1_DIR}/annotations_fraud_n1.csv")