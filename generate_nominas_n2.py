"""
Versión para N2 - Copia de generate_nominas.py con soporte para cambio de fuente en TOTAL NETO
NO MODIFICA el original
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import random
import math
from datetime import datetime
from config import RAW_DIR, IMAGE_SIZE
from utils import generate_amount, generate_ssn, generate_nif, fake, save_image

random.seed(42)
CUSTOM_IMAGE_SIZE = (800, 1100)

LOGOS = {
    'moderno': "EMPRESA DEMO S.L.",
    'derecha': "DEMO CORPORATION",
    'compacto': "ED",
    'cuadros': "DEMO GROUP"
}

NOMINA_STYLES = [
    {
        'name': 'moderno',
        'title_size': 24,
        'normal_size': 16,
        'small_size': 12,
        'title_x': 50, 'title_y': 30,
        'company_x': 50, 'company_y': 80,
        'worker_x': 50, 'worker_y': 170,
        'table_x': 50, 'value_x': 350,
        'line_height': 40,
        'start_y': 420,
        'header_bg': True,
        'separator_style': 'double',
        'table_border': False,
        'total_bg': True
    },
    {
        'name': 'derecha',
        'title_size': 28,
        'normal_size': 18,
        'small_size': 13,
        'title_x': 300, 'title_y': 40,
        'company_x': 250, 'company_y': 100,
        'worker_x': 250, 'worker_y': 200,
        'table_x': 250, 'value_x': 550,
        'line_height': 42,
        'start_y': 480,
        'header_bg': False,
        'separator_style': 'dotted',
        'table_border': True,
        'total_bg': True
    },
    {
        'name': 'compacto',
        'title_size': 20,
        'normal_size': 14,
        'small_size': 10,
        'title_x': 30, 'title_y': 25,
        'company_x': 30, 'company_y': 65,
        'worker_x': 30, 'worker_y': 140,
        'table_x': 30, 'value_x': 320,
        'line_height': 32,
        'start_y': 380,
        'header_bg': False,
        'separator_style': 'line',
        'table_border': False,
        'total_bg': False
    },
    {
        'name': 'cuadros',
        'title_size': 26,
        'normal_size': 17,
        'small_size': 14,
        'title_x': 50, 'title_y': 30,
        'company_x': 50, 'company_y': 85,
        'worker_x': 50, 'worker_y': 180,
        'table_x': 50, 'value_x': 400,
        'line_height': 40,
        'start_y': 480,
        'header_bg': True,
        'separator_style': 'thick',
        'table_border': True,
        'total_bg': True,
        'box_shadow': True
    }
]

AVAILABLE_FONTS = []
font_options = [
    "arial.ttf", "Arial.ttf",
    "times.ttf", "Times.ttf", "Times New Roman.ttf",
    "cour.ttf", "Courier.ttf", "Courier New.ttf",
    "verdana.ttf", "Verdana.ttf",
    "calibri.ttf", "Calibri.ttf"
]

for font_name in font_options:
    try:
        ImageFont.truetype(font_name, 12)
        AVAILABLE_FONTS.append(font_name)
    except:
        pass

if not AVAILABLE_FONTS:
    AVAILABLE_FONTS = [None]

def get_extra_concepts(amount):
    """Genera conceptos adicionales aleatorios"""
    concepts = []
    total_extra = 0
    
    incentive_options = [
        'Bonus producción', 'Incentivo trimestral', 'Plus productividad',
        'Cumplimiento objetivos', 'Retribución variable', 'Premio asistencia',
        'Plus convenio', 'Complemento categoría', 'Antigüedad'
    ]
    
    deduction_options = [
        'Anticipo nómina', 'Préstamo personal', 'Seguro médico',
        'Aportación formación', 'Cuota sindical', 'Embargo judicial',
        'Pensión alimenticia', 'Préstamo vivienda'
    ]
    
    transport_options = [
        'Ayuda transporte', 'Plus distancia', 'Complemento transporte',
        'Dietas desplazamiento', 'Kilometraje', 'Abono transporte'
    ]
    
    night_options = [
        'Complemento nocturnidad', 'Plus horario nocturno', 'Dietas noche',
        'Plus turnicidad', 'Complemento turno', 'Horario especial'
    ]
    
    overtime_options = [
        'Horas extraordinarias', 'Exceso de jornada', 'Complemento horas',
        'Plus festivos', 'Horas festivas', 'Disponibilidad'
    ]
    
    if random.random() < 0.7:
        incentive = round(random.uniform(50, 300), 2)
        name = random.choice(incentive_options)
        concepts.append((name, incentive))
        total_extra += incentive
    
    if random.random() < 0.8:
        deduction = round(random.uniform(30, 200), 2)
        name = random.choice(deduction_options)
        concepts.append((name, -deduction))
        total_extra -= deduction
    
    if random.random() < 0.6:
        transport = round(random.uniform(40, 120), 2)
        name = random.choice(transport_options)
        concepts.append((name, transport))
        total_extra += transport
    
    if random.random() < 0.4:
        night_bonus = round(random.uniform(35, 150), 2)
        name = random.choice(night_options)
        concepts.append((name, night_bonus))
        total_extra += night_bonus
    
    if random.random() < 0.5:
        overtime = round(random.uniform(20, 200), 2)
        name = random.choice(overtime_options)
        concepts.append((name, overtime))
        total_extra += overtime
    
    if amount < 1500:
        irpf_rate = random.uniform(12, 16)
    elif amount < 2500:
        irpf_rate = random.uniform(16, 20)
    else:
        irpf_rate = random.uniform(20, 25)
    
    ss_rate = 6.35
    retencion = amount * (irpf_rate + ss_rate) / 100
    
    return concepts, total_extra, round(retencion, 2)

def draw_separator(draw, start, end, y, style_name, color='#7F8C8D'):
    if style_name == 'moderno':
        draw.line([(start, y), (end, y)], fill=color, width=1)
        draw.line([(start, y + 3), (end, y + 3)], fill=color, width=1)
    elif style_name == 'derecha':
        for x in range(start, end, 10):
            draw.line([(x, y), (x + 5, y)], fill=color, width=1)
    elif style_name == 'cuadros':
        draw.line([(start, y), (end, y)], fill=color, width=2)
    else:
        draw.line([(start, y), (end, y)], fill=color, width=1)

def add_watermark(img, style_name):
    return img

def add_variations(img, style_name):
    if random.random() < 0.5:
        angle = random.uniform(-1.5, 1.5)
        img = img.rotate(angle, expand=False, fillcolor='white')
    
    if random.random() < 0.3:
        blur_radius = random.uniform(0.2, 0.6)
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    
    if random.random() < 0.4:
        shift_x = random.randint(-3, 3)
        shift_y = random.randint(-2, 2)
        new_img = Image.new('RGB', CUSTOM_IMAGE_SIZE, color='white')
        new_img.paste(img, (shift_x, shift_y))
        img = new_img
    
    return img

def create_nomina_image_n2(worker_name, nif, ssn, amount, date_str, filename, style_idx=None, font_idx=None, n2_tipo=None):
    """
    Crea una imagen de nómina con detalles realistas
    n2_tipo: puede ser 'fuente_distinta', o None para normal
    """
    if style_idx is None:
        style_idx = random.randint(0, len(NOMINA_STYLES) - 1)
    style = NOMINA_STYLES[style_idx]
    style_name = style['name']
    
    if font_idx is None:
        font_idx = random.randint(0, len(AVAILABLE_FONTS) - 1)
    font_path = AVAILABLE_FONTS[font_idx] if font_idx < len(AVAILABLE_FONTS) else None
    
    extra_concepts, extra_total, retencion = get_extra_concepts(amount)
    
    img = Image.new('RGB', CUSTOM_IMAGE_SIZE, color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        if font_path:
            font_title = ImageFont.truetype(font_path, style['title_size'])
            font_normal = ImageFont.truetype(font_path, style['normal_size'])
            font_small = ImageFont.truetype(font_path, style['small_size'])
            font_bold = ImageFont.truetype(font_path, style['normal_size'])
        else:
            font_title = ImageFont.load_default()
            font_normal = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
    except:
        font_title = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_bold = ImageFont.load_default()
    
    if style_name == 'derecha':
        variation_x = random.randint(-3, 3)
        variation_y = random.randint(-2, 2)
    else:
        variation_x = random.randint(-5, 5)
        variation_y = random.randint(-3, 3)
    
    if style['header_bg']:
        draw.rectangle([(20, 20), (780, 140)], fill='#F5F5F5', outline=None)
    
    logo_text = LOGOS[style_name]
    draw.text((style['title_x'] + variation_x, style['title_y'] + variation_y), 
              logo_text, fill='#2C3E50', font=font_title)
    
    draw_separator(draw, style['title_x'] + variation_x - 10, 
                  style['title_x'] + variation_x + 300, 
                  style['title_y'] + variation_y + 45, style_name)
    
    y_company = style['company_y'] + variation_y
    
    invoice_num = f"NUM-{random.randint(10000, 99999)}"
    invoice_x = min(style['company_x'] + variation_x + 380, 700)
    draw.text((invoice_x, y_company), f"Nº {invoice_num}", fill='#7F8C8D', font=font_small)
    
    draw.text((style['company_x'] + variation_x, y_company), "EMPRESA DEMO S.L.", fill='#2C3E50', font=font_normal)
    draw.text((style['company_x'] + variation_x, y_company + 32), "CIF: B-12345678", fill='#34495E', font=font_small)
    draw.text((style['company_x'] + variation_x, y_company + 58), "C/ Ejemplo, 123 - Madrid", fill='#34495E', font=font_small)
    draw.text((style['company_x'] + variation_x, y_company + 84), "Tel: 912 345 678", fill='#7F8C8D', font=font_small)
    
    y_worker = style['worker_y'] + variation_y
    
    if style_name == 'cuadros':
        draw.rectangle([(style['worker_x'] + variation_x - 10, y_worker - 10),
                       (style['worker_x'] + variation_x + 430, y_worker + 130)],
                      fill='#FAFAFA', outline='#BDC3C7', width=1)
    
    draw.text((style['worker_x'] + variation_x, y_worker), "DATOS DEL TRABAJADOR", fill='#2C3E50', font=font_normal)
    
    display_name = worker_name if len(worker_name) < 30 else worker_name[:27] + "..."
    draw.text((style['worker_x'] + variation_x, y_worker + 32), f"Nombre: {display_name}", fill='black', font=font_small)
    draw.text((style['worker_x'] + variation_x, y_worker + 64), f"NIF: {nif}", fill='black', font=font_small)
    draw.text((style['worker_x'] + variation_x, y_worker + 96), f"Nº Seguridad Social: {ssn}", fill='black', font=font_small)
    
    categories = ['Administrativo', 'Técnico', 'Operario', 'Comercial', 'Directivo']
    category = random.choice(categories)
    category_x = min(style['worker_x'] + variation_x + 250, 650)
    draw.text((category_x, y_worker + 64), f"Categoría: {category}", fill='#7F8C8D', font=font_small)
    
    y_date = y_worker + 150
    draw.text((style['worker_x'] + variation_x, y_date), "DETALLES DE LA NÓMINA", fill='#2C3E50', font=font_normal)
    draw.text((style['worker_x'] + variation_x, y_date + 32), f"Fecha emisión: {date_str}", fill='black', font=font_small)
    
    try:
        day, month, year = date_str.split('/')
        period = f"{month}/{year}"
    except:
        period = date_str[:7]
    
    pay_date = datetime(int(year), int(month), min(28, int(day) + random.randint(5, 10)))
    pay_date_str = pay_date.strftime('%d/%m/%Y')
    draw.text((style['worker_x'] + variation_x, y_date + 64), f"Periodo: {period}", fill='black', font=font_small)
    
    payment_x = min(style['worker_x'] + variation_x + 200, 650)
    draw.text((payment_x, y_date + 64), f"Abono: {pay_date_str}", fill='#7F8C8D', font=font_small)
    
    payment_methods = ['Transferencia bancaria', 'Cheque', 'Efectivo']
    payment = random.choice(payment_methods)
    draw.text((payment_x, y_date + 32), f"Forma pago: {payment}", fill='#7F8C8D', font=font_small)
    
    y_pos = style['start_y'] + variation_y + 10
    num_lines = 1 + len(extra_concepts) + 4
    table_height = num_lines * style['line_height'] + 80
    
    if style_name == 'cuadros' and style.get('box_shadow', False):
        draw.rectangle([(style['table_x'] + variation_x - 8, y_pos - 30 + 3),
                       (style['value_x'] + variation_x + 90 + 3, y_pos + table_height + 3)],
                      fill='#E0E0E0', outline=None)
    
    if style['table_border']:
        draw.rectangle([(style['table_x'] + variation_x - 10, y_pos - 32),
                       (style['value_x'] + variation_x + 90, y_pos + table_height)],
                      outline='#34495E', width=1)
        if style_name == 'cuadros':
            draw.rectangle([(style['table_x'] + variation_x - 8, y_pos - 30),
                           (style['value_x'] + variation_x + 88, y_pos + table_height - 2)],
                          fill='#F8F9FA', outline=None)
    
    if style['header_bg'] and style_name != 'cuadros':
        draw.rectangle([(style['table_x'] + variation_x - 5, y_pos - 28),
                       (style['value_x'] + variation_x + 85, y_pos + 12)],
                      fill='#3498DB', outline=None)
        draw.text((style['table_x'] + variation_x, y_pos), "CONCEPTOS", fill='white', font=font_normal)
    else:
        draw.text((style['table_x'] + variation_x, y_pos), "CONCEPTOS", fill='#2C3E50', font=font_normal)
    
    y_pos += style['line_height'] + 8
    
    draw.text((style['table_x'] + variation_x, y_pos), "Salario base", fill='black', font=font_small)
    draw.text((style['value_x'] + variation_x, y_pos), f"{amount:.2f} €", fill='black', font=font_small)
    y_pos += style['line_height']
    
    for idx, (concept_name, concept_value) in enumerate(extra_concepts):
        if idx % 2 == 0 and style_name != 'compacto':
            draw.rectangle([(style['table_x'] + variation_x - 5, y_pos - 22),
                           (style['value_x'] + variation_x + 85, y_pos + 12)],
                          fill='#F8F9FA', outline=None)
        
        draw.text((style['table_x'] + variation_x, y_pos), concept_name, fill='black', font=font_small)
        value_str = f"{concept_value:.2f} €" if concept_value >= 0 else f"- {abs(concept_value):.2f} €"
        draw.text((style['value_x'] + variation_x, y_pos), value_str, fill='black', font=font_small)
        y_pos += style['line_height']
    
    y_pos += 10
    draw_separator(draw, style['table_x'] + variation_x, style['value_x'] + variation_x + 80, y_pos, style_name)
    y_pos += 20
    
    total_bruto = amount + extra_total
    draw.text((style['table_x'] + variation_x, y_pos), "Total bruto", fill='#2C3E50', font=font_small)
    draw.text((style['value_x'] + variation_x, y_pos), f"{total_bruto:.2f} €", fill='black', font=font_normal)
    y_pos += style['line_height']
    
    draw.text((style['table_x'] + variation_x, y_pos), "Retenciones (IRPF + SS)", fill='#7F8C8D', font=font_small)
    draw.text((style['value_x'] + variation_x, y_pos), f"- {retencion:.2f} €", fill='black', font=font_small)
    y_pos += style['line_height'] + 12
    
    line_end_x = style['value_x'] + variation_x + 130
    draw_separator(draw, style['table_x'] + variation_x - 5, line_end_x, y_pos, 
                  'cuadros' if style_name == 'cuadros' else 'moderno', '#2C3E50')
    y_pos += style['line_height']
    
    total_neto = total_bruto - retencion
    total_neto_str = f"{total_neto:.2f} €"
    value_width = max(120, len(total_neto_str) * (style['title_size'] // 2))
    
    if style['total_bg']:
        draw.rectangle([(style['table_x'] + variation_x - 8, y_pos - 24),
                       (style['value_x'] + variation_x + value_width, y_pos + 18)],
                      fill='#F0F0F0', outline='#BDC3C7', width=1)
    
    draw.text((style['table_x'] + variation_x, y_pos), "TOTAL NETO", fill='#2C3E50', font=font_bold)
    
    # ============================================
    # APLICAR FRAUDE N2: CAMBIO DE FUENTE
    # ============================================
    
    if n2_tipo == 'fuente_distinta':
        # Obtener lista de fuentes alternativas (excluyendo la original)
        fuentes_alternativas = [f for f in AVAILABLE_FONTS if f != font_path and f is not None]
        
        # Si no hay alternativas, usar fuentes predefinidas
        if not fuentes_alternativas:
            fuentes_alternativas = ["cour.ttf", "Courier New.ttf", "times.ttf", "verdana.ttf", "calibri.ttf"]
        
        # Elegir fuente aleatoria
        fuente_fraude = random.choice(fuentes_alternativas)
        
        try:
            font_neto = ImageFont.truetype(fuente_fraude, style['title_size'])
        except:
            font_neto = font_title
        
        draw.text((style['value_x'] + variation_x, y_pos), total_neto_str, fill='black', font=font_neto)
    else:
        # Normal
        draw.text((style['value_x'] + variation_x, y_pos), total_neto_str, fill='black', font=font_title)
    
    y_footer = CUSTOM_IMAGE_SIZE[1] - 70
    draw_separator(draw, 50, 750, y_footer, 'compacto', '#BDC3C7')
    legal_text = "Documento no válido como justificante bancario. Liquidación de haberes."
    draw.text((50, y_footer + 15), legal_text, fill='#95A5A6', font=font_small)
    
    if random.random() < 0.6:
        sign_date = datetime.now().strftime('%d/%m/%Y')
        draw.text((600, y_footer + 15), f"Fdo.: La empresa", fill='#7F8C8D', font=font_small)
        draw.text((600, y_footer + 35), sign_date, fill='#95A5A6', font=font_small)
    
    img = add_watermark(img, style_name)
    img = add_variations(img, style_name)
    
    save_image(img, filename)
    return filename, style_name, font_path

def generate_batch_nominas_n2(n, n2_tipo=None):
    """Genera n nóminas sintéticas con estilos variados
       n2_tipo: None (normal), 'fuente_distinta'
    """
    results = []
    
    styles_per_image = [i % len(NOMINA_STYLES) for i in range(n)]
    random.shuffle(styles_per_image)
    
    print(f"Generando {n} nóminas...")
    if n2_tipo:
        print(f"  Aplicando fraude N2: {n2_tipo}")
    
    for i in range(n):
        worker_name = fake.name()
        nif = generate_nif()
        ssn = generate_ssn()
        amount = generate_amount()
        date = fake.date_between(start_date='-1y', end_date='today')
        date_str = date.strftime('%d/%m/%Y')
        
        filename = os.path.join(RAW_DIR, 'nominas', f'nomina_n2_{i+1:04d}.png')
        style_idx = styles_per_image[i]
        
        create_nomina_image_n2(worker_name, nif, ssn, amount, date_str, filename, 
                               style_idx=style_idx, n2_tipo=n2_tipo)
        
        results.append({
            'id': f'nomina_n2_{i+1:04d}',
            'path': filename,
            'worker_name': worker_name,
            'nif': nif,
            'ssn': ssn,
            'amount': amount,
            'date': date_str,
            'style': NOMINA_STYLES[style_idx]['name'],
            'n2_tipo': n2_tipo
        })
        
        if (i + 1) % 50 == 0:
            print(f"Generadas {i+1} nóminas...")
    
    return results

if __name__ == '__main__':
    print("Generando nóminas con soporte N2...")
    os.makedirs(os.path.join(RAW_DIR, 'nominas'), exist_ok=True)
    
    # Probar con 5 nóminas
    nominas = generate_batch_nominas_n2(5, n2_tipo='fuente_distinta')
    print(f"✓ Generadas {len(nominas)} nóminas con fuente distinta")