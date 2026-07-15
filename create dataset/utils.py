import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from faker import Faker
import pandas as pd

fake = Faker('es_ES')  # Datos en español
Faker.seed(42)
random.seed(42)
np.random.seed(42)

def generate_nif():
    """Genera un NIF español válido (8 números + letra)"""
    letters = 'TRWAGMYFPDXBNJZSQVHLCKE'
    numbers = random.randint(10000000, 99999999)
    letter = letters[numbers % 23]
    return f"{numbers}{letter}"

def generate_ssn():
    """Genera un número de Seguridad Social español simulado"""
    # Formato: XX XXXXXXX (provincia + número)
    province = f"{random.randint(1, 52):02d}"
    number = f"{random.randint(1000000, 9999999)}"
    return f"{province} {number}"

def generate_amount():
    """Genera un importe de nómina realista (800-5000€)"""
    return round(random.uniform(800, 5000), 2)

def generate_date(start_year=1970, end_year=2000):
    """Genera una fecha de nacimiento aleatoria"""
    return fake.date_of_birth(minimum_age=18, maximum_age=65)

def save_image(image, path):
    """Guarda una imagen PIL en la ruta especificada"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, format='PNG')

def load_annotation_file():
    """Carga el archivo de anotaciones si existe, si no crea uno vacío"""
    from config import ANNOTATIONS_FILE
    if os.path.exists(ANNOTATIONS_FILE):
        return pd.read_csv(ANNOTATIONS_FILE)
    else:
        return pd.DataFrame(columns=[
            'id_nomina', 'id_dni', 'nomina_path', 'dni_path',
            'tipo_fraude', 'campos_afectados', 'etiqueta', 'split'
        ])
