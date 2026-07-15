from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import random
from datetime import datetime, timedelta
from config import RAW_DIR, IMAGE_SIZE
from utils import generate_nif, fake, save_image

# Configurar semillas para reproducibilidad
random.seed(42)

# Tamaño específico para DNI (más alargado, como un DNI real)
DNI_SIZE = (550, 350)  # Ancho x Alto (formato tarjeta)

# Colores realistas
DNI_COLORS = {
    'background': '#FDF5E6',  # Beige claro más natural
    'border': '#8B7355',       # Marrón suave
    'text_dark': '#2C2C2C',    # Gris oscuro
    'text_light': '#666666',    # Gris medio
    'accent': '#C41E3A'         # Rojo para elementos destacados
}

def get_validity_date(birth_date_str):
    """
    Determina la fecha de validez del DNI según normativa española:
    - Menores de 30 años: 5 años
    - Entre 30 y 70 años: 10 años
    - Mayores de 70 años: indefinido
    """
    birth_date = datetime.strptime(birth_date_str, '%d/%m/%Y')
    today = datetime.now()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age >= 70:
        return "INDEFINIDA"
    elif age < 30:
        years_valid = 5
    else:
        years_valid = 10
    
    # Fecha de caducidad (siempre posterior a 2026)
    expiry_date = today.replace(year=today.year + years_valid)
    
    # Asegurar que sea posterior a 2026
    if expiry_date.year <= 2026:
        expiry_date = expiry_date.replace(year=2027)
    
    return expiry_date.strftime('%d/%m/%Y')

def add_realistic_details(img, draw, fonts):
    """Añade detalles realistas al DNI"""
    
    # Fondo con degradado sutil
    for i in range(DNI_SIZE[1]):
        color_intensity = 245 + int(10 * (i / DNI_SIZE[1]))
        draw.line([(0, i), (DNI_SIZE[0], i)], fill=(color_intensity, color_intensity, 220))
    
    # Borde exterior
    draw.rectangle([(5, 5), (DNI_SIZE[0] - 5, DNI_SIZE[1] - 5)], 
                   outline=DNI_COLORS['border'], width=2)
    
    # Sello simulado (círculo semitransparente)
    seal_center = (DNI_SIZE[0] - 80, DNI_SIZE[1] - 80)
    draw.ellipse([(seal_center[0] - 40, seal_center[1] - 40),
                  (seal_center[0] + 40, seal_center[1] + 40)],
                 outline='#C0C0C0', width=2)
    draw.text((seal_center[0] - 25, seal_center[1] - 8), 
              "ESPAÑA", fill='#C0C0C0', font=fonts['small'])

def create_dni_image(full_name, nif, birth_date_str, filename):
    """
    Crea una imagen de DNI realista
    """
    # Crear imagen con tamaño de tarjeta
    img = Image.new('RGB', DNI_SIZE, color=DNI_COLORS['background'])
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar fuentes profesionales
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_normal = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 12)
        font_bold = ImageFont.truetype("arialbd.ttf", 18)  # Negrita si existe
    except:
        try:
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
            font_normal = ImageFont.truetype("DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("DejaVuSans.ttf", 12)
            font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        except:
            font_title = ImageFont.load_default()
            font_normal = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
    
    fonts = {
        'title': font_title,
        'normal': font_normal,
        'small': font_small,
        'bold': font_bold
    }
    
    # Añadir detalles realistas
    add_realistic_details(img, draw, fonts)
    
    # Logo simulado (escudo)
    draw.text((25, 25), "◉", fill=DNI_COLORS['accent'], font=font_title)
    draw.text((45, 28), "GOBIERNO DE ESPAÑA", fill=DNI_COLORS['text_dark'], font=font_small)
    draw.text((45, 42), "MINISTERIO DEL INTERIOR", fill=DNI_COLORS['text_light'], font=font_small)
    
    # Título
    draw.text((25, 75), "DOCUMENTO NACIONAL DE IDENTIDAD", fill=DNI_COLORS['text_dark'], font=font_bold)
    
    # Línea decorativa
    draw.line([(25, 100), (DNI_SIZE[0] - 25, 100)], fill=DNI_COLORS['border'], width=1)
    
    # Número de documento (destacado)
    draw.text((25, 120), "NÚMERO", fill=DNI_COLORS['text_light'], font=font_small)
    draw.text((25, 140), nif, fill=DNI_COLORS['accent'], font=font_title)
    
    # Línea divisoria vertical (simulando zonas del DNI)
    draw.line([(DNI_SIZE[0] - 180, 115), (DNI_SIZE[0] - 180, DNI_SIZE[1] - 30)], 
              fill=DNI_COLORS['border'], width=1)
    
    # Zona de datos (parte izquierda)
    y_offset = 180
    
    # Nombre completo
    draw.text((25, y_offset), "APELLIDOS Y NOMBRE", fill=DNI_COLORS['text_light'], font=font_small)
    # Formatear nombre para que quepa
    display_name = full_name.upper()
    if len(display_name) > 35:
        display_name = display_name[:32] + "..."
    draw.text((25, y_offset + 18), display_name, fill=DNI_COLORS['text_dark'], font=font_normal)
    y_offset += 55
    
    # Fecha de nacimiento
    draw.text((25, y_offset), "FECHA DE NACIMIENTO", fill=DNI_COLORS['text_light'], font=font_small)
    draw.text((25, y_offset + 18), birth_date_str, fill=DNI_COLORS['text_dark'], font=font_normal)
    y_offset += 45
    
    # Nacionalidad
    draw.text((25, y_offset), "NACIONALIDAD", fill=DNI_COLORS['text_light'], font=font_small)
    draw.text((25, y_offset + 18), "ESPAÑOLA", fill=DNI_COLORS['text_dark'], font=font_normal)
    
    # Zona de validez (parte derecha)
    validity_date = get_validity_date(birth_date_str)
    
    # Fecha de validez
    draw.text((DNI_SIZE[0] - 165, 180), "FECHA DE VALIDEZ", fill=DNI_COLORS['text_light'], font=font_small)
    
    if validity_date == "INDEFINIDA":
        draw.text((DNI_SIZE[0] - 165, 198), validity_date, fill='#006400', font=font_bold)  # Verde para indefinido
    else:
        draw.text((DNI_SIZE[0] - 165, 198), validity_date, fill=DNI_COLORS['text_dark'], font=font_normal)
    
    # Número de soporte (simulado)
    support_number = f"ES{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
    draw.text((DNI_SIZE[0] - 165, 230), "SOPORTE", fill=DNI_COLORS['text_light'], font=font_small)
    draw.text((DNI_SIZE[0] - 165, 248), support_number, fill=DNI_COLORS['text_light'], font=font_small)
    
    # Firma simulada
    draw.text((DNI_SIZE[0] - 165, 280), "FIRMA DEL TITULAR", fill=DNI_COLORS['text_light'], font=font_small)
    
    # Firma manuscrita simulada
    signature_points = []
    sig_start_x = DNI_SIZE[0] - 165
    sig_start_y = 300
    for j in range(20):
        x = sig_start_x + j * 6
        y = sig_start_y + random.randint(-5, 5)
        signature_points.append((x, y))
    
    if len(signature_points) > 1:
        for j in range(len(signature_points) - 1):
            draw.line([signature_points[j], signature_points[j + 1]], 
                     fill=DNI_COLORS['text_dark'], width=1)
    
    # Aplicar variaciones sutiles
    if random.random() < 0.3:
        # Ligero desenfoque (simula impresión no perfecta)
        blur_radius = random.uniform(0.2, 0.5)
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    if random.random() < 0.4:
        # Pequeña rotación
        angle = random.uniform(-1.5, 1.5)
        img = img.rotate(angle, expand=False, fillcolor=DNI_COLORS['background'])
    
    save_image(img, filename)
    return filename

def generate_batch_dnis(n):
    """
    Genera n DNIs sintéticos realistas
    
    Returns:
        list: Lista de diccionarios con los datos generados
    """
    results = []
    
    print("Generando DNIs...")
    for i in range(n):
        # Generar fecha de nacimiento entre 1960 y 2005
        birth_year = random.randint(1960, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # Evitamos problemas con febrero
        birth_date = datetime(birth_year, birth_month, birth_day)
        birth_date_str = birth_date.strftime('%d/%m/%Y')
        
        full_name = fake.name()
        nif = generate_nif()
        
        filename = os.path.join(RAW_DIR, 'dnis', f'dni_{i+1:04d}.png')
        
        create_dni_image(full_name, nif, birth_date_str, filename)
        
        # Calcular edad para validación
        today = datetime.now()
        age = today.year - birth_year - ((today.month, today.day) < (birth_month, birth_day))
        
        results.append({
            'id': f'dni_{i+1:04d}',
            'path': filename,
            'full_name': full_name,
            'nif': nif,
            'birth_date': birth_date_str,
            'age': age
        })
        
        if (i + 1) % 50 == 0:
            print(f"Generados {i+1} DNIs...")
    
    return results

if __name__ == '__main__':
    print("Generando DNIs sintéticos realistas...")
    print(f"Tamaño de imagen: {DNI_SIZE[0]}x{DNI_SIZE[1]} píxeles")
    print("- Formato tarjeta (más alargado)")
    print("- Sellos y elementos de seguridad simulados")
    print("- Fechas de validez según normativa (5/10 años o indefinido)")
    print("- Fechas nacimiento entre 1960-2005")
    
    os.makedirs(os.path.join(RAW_DIR, 'dnis'), exist_ok=True)
    
    dnis = generate_batch_dnis(10)
    
    # Estadísticas de edades
    ages = [d['age'] for d in dnis]
    print(f"\n=== Estadísticas de edad ===")
    print(f"Edad mínima: {min(ages)} años")
    print(f"Edad máxima: {max(ages)} años")
    print(f"Edad media: {sum(ages)/len(ages):.1f} años")
    
    print(f"\n✓ Generados {len(dnis)} DNIs en {RAW_DIR}/dnis/")
