import os

# Rutas base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, '..', 'dataset')

# Subdirectorios
RAW_DIR = os.path.join(DATASET_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATASET_DIR, 'processed')
ANNOTATIONS_FILE = os.path.join(DATASET_DIR, 'annotations.csv')

# Subdirectorios dentro de processed
CLEAN_DIR = os.path.join(PROCESSED_DIR, 'limpios')
FRAUD_N1_DIR = os.path.join(PROCESSED_DIR, 'fraudulentos', 'nivel1')
FRAUD_N2_DIR = os.path.join(PROCESSED_DIR, 'fraudulentos', 'nivel2')

# Configuración de generación
NUM_SAMPLES = 800  # Total de pares a generar
TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

# Formatos
IMAGE_SIZE = (800, 600)  # Tamaño de las imágenes generadas
IMAGE_FORMAT = 'PNG'

# Semilla para reproducibilidad
RANDOM_SEED = 42

# Crear directorios si no existen
for dir_path in [RAW_DIR, PROCESSED_DIR, CLEAN_DIR, FRAUD_N1_DIR, FRAUD_N2_DIR]:
    os.makedirs(dir_path, exist_ok=True)
    os.makedirs(os.path.join(RAW_DIR, 'nominas'), exist_ok=True)
    os.makedirs(os.path.join(RAW_DIR, 'dnis'), exist_ok=True)
