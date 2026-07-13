"""
Pipeline multimodal para detección de fraude documental
Combina:
- Nivel 1: OCR + reglas (inconsistencias lógicas)
- Nivel 2: CNN (alteraciones visuales en fuente)
"""

import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import re
import easyocr
from datetime import datetime

class FraudDetectorN1:
    """Módulo OCR + Reglas para Nivel 1"""
    
    def __init__(self, gpu=False):
        self.reader = easyocr.Reader(['es', 'en'], gpu=gpu)
    
    def calcular_letra_nif(self, numeros):
        letras = 'TRWAGMYFPDXBNJZSQVHLCKE'
        return letras[numeros % 23]
    
    def validar_nif(self, nif):
        if not nif or len(nif) != 9:
            return False
        try:
            numeros = int(nif[:8])
            letra = nif[8].upper()
            return letra == self.calcular_letra_nif(numeros)
        except:
            return False
    
    def validar_ssn(self, ssn):
        if not ssn:
            return False
        patron = r'^\d{2}\s\d{7}$'
        return re.match(patron, ssn) is not None
    
    def extraer_campos_nomina(self, textos):
        campos = {'nombre': None, 'nif': None, 'ssn': None, 'importe': None, 'fecha': None}
        for i, texto in enumerate(textos):
            nif_match = re.search(r'\b(\d{8}[A-Z])\b', texto.upper())
            if nif_match:
                campos['nif'] = nif_match.group(1)
            ssn_match = re.search(r'\b(\d{2}\s\d{7})\b', texto)
            if ssn_match:
                campos['ssn'] = ssn_match.group(1)
            fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
            if fecha_match:
                campos['fecha'] = fecha_match.group(1)
            if 'Nombre:' in texto:
                partes = texto.split('Nombre:')
                if len(partes) > 1:
                    campos['nombre'] = partes[1].strip()
            if 'TOTAL NETO' in texto.upper():
                if i + 1 < len(textos):
                    siguiente = textos[i + 1]
                    importe_match = re.search(r'(\d+(?:\.\d+)?)', siguiente)
                    if importe_match:
                        try:
                            campos['importe'] = float(importe_match.group(1))
                        except:
                            pass
        return campos
    
    def extraer_campos_dni(self, textos):
        campos = {'nombre': None, 'nif': None, 'fecha_nacimiento': None, 'fecha_validez': None}
        for i, texto in enumerate(textos):
            if i == 4:
                nif_match = re.search(r'\b(\d{8}[A-Z])\b', texto.upper())
                if nif_match:
                    campos['nif'] = nif_match.group(1)
            if i == 8:
                campos['nombre'] = texto
            if i == 9:
                fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
                if fecha_match:
                    campos['fecha_validez'] = fecha_match.group(1)
            if i == 12:
                fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
                if fecha_match:
                    campos['fecha_nacimiento'] = fecha_match.group(1)
        return campos
    
    def detectar(self, ruta_nomina, ruta_dni):
        resultados_nomina = self.reader.readtext(ruta_nomina)
        textos_nomina = [texto for (_, texto, _) in resultados_nomina]
        resultados_dni = self.reader.readtext(ruta_dni)
        textos_dni = [texto for (_, texto, _) in resultados_dni]
        
        campos_nomina = self.extraer_campos_nomina(textos_nomina)
        campos_dni = self.extraer_campos_dni(textos_dni)
        
        anomalias = []
        
        # Regla 1: Nombre
        if campos_nomina['nombre'] and campos_dni['nombre']:
            if campos_nomina['nombre'].lower().strip() != campos_dni['nombre'].lower().strip():
                anomalias.append("Nombre no coincide")
        
        # Regla 2: NIF
        if campos_nomina['nif'] and campos_dni['nif']:
            if campos_nomina['nif'] != campos_dni['nif']:
                anomalias.append("NIF no coincide")
        
        # Regla 3: Importe
        if campos_nomina['importe']:
            importe = campos_nomina['importe']
            if importe < 300 or importe > 15000:
                anomalias.append(f"Importe sospechoso: {importe}€")
        
        # Regla 4: SSN
        if campos_nomina['ssn'] and not self.validar_ssn(campos_nomina['ssn']):
            anomalias.append(f"SSN inválido: {campos_nomina['ssn']}")
        
        # Regla 5: DNI caducado
        if campos_dni['fecha_validez']:
            try:
                fecha_validez = datetime.strptime(campos_dni['fecha_validez'], '%d/%m/%Y')
                if fecha_validez < datetime.now():
                    anomalias.append(f"DNI caducado ({campos_dni['fecha_validez']})")
            except:
                pass
        
        # Regla 6: Edad
        # Se ejecuta siempre que exista fecha de nacimiento del DNI
        if campos_dni['fecha_nacimiento']:
            try:
                fecha_nac = datetime.strptime(campos_dni['fecha_nacimiento'], '%d/%m/%Y')
                
                # Determinar año de referencia (nómina o actual)
                if campos_nomina['fecha']:
                    año_referencia = int(campos_nomina['fecha'].split('/')[2])
                    fecha_referencia = datetime.strptime(campos_nomina['fecha'], '%d/%m/%Y')
                else:
                    año_referencia = datetime.now().year
                    fecha_referencia = datetime.now()
                
                # Calcular edad
                edad = año_referencia - fecha_nac.year - ((fecha_referencia.month, fecha_referencia.day) < (fecha_nac.month, fecha_nac.day))
                
                if edad < 16 or edad > 67:
                    anomalias.append(f"REGLA 6 - Edad incoherente: {edad} años (fecha nacimiento: {campos_dni['fecha_nacimiento']})")
                
                # Si hay fecha de nómina, verificar que no sea anterior al nacimiento
                if campos_nomina['fecha']:
                    fecha_nomina = datetime.strptime(campos_nomina['fecha'], '%d/%m/%Y')
                    if fecha_nomina < fecha_nac:
                        anomalias.append(f"REGLA 6 - Nómina anterior a fecha de nacimiento")
            except:
                pass
        
        # Regla 7: NIF inválido
        if campos_nomina['nif'] and not self.validar_nif(campos_nomina['nif']):
            anomalias.append(f"NIF nómina inválido: {campos_nomina['nif']}")
        if campos_dni['nif'] and not self.validar_nif(campos_dni['nif']):
            anomalias.append(f"NIF DNI inválido: {campos_dni['nif']}")
        
        veredicto = "FRAUDE_N1" if len(anomalias) > 0 else "VALIDO_N1"
        return veredicto, anomalias, campos_nomina, campos_dni


class FraudDetectorN2:
    """Módulo CNN para Nivel 2 (detección de cambio de fuente)"""
    
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.classes = ['fraude', 'limpia']
        
        # Crear modelo con misma arquitectura
        self.model = models.resnet18(weights=None)
        num_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 2)
        )
        
        # Cargar pesos entrenados
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        
        # Transformaciones
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
    
    def detectar(self, ruta_nomina):
        """Predice si una nómina es limpia o fraudulenta"""
        img = Image.open(ruta_nomina).convert('RGB')
        img_tensor = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confianza, pred = torch.max(probs, 1)
        
        clase = self.classes[pred.item()]
        confianza = confianza.item() * 100
        
        veredicto = "VALIDO_N2" if clase == 'limpia' else "FRAUDE_N2"
        return veredicto, clase, confianza


class PipelineMultimodal:
    """Pipeline que combina N1 y N2 para emitir veredicto final"""
    
    def __init__(self, model_path_cnn, gpu_ocr=False):
        self.detector_n1 = FraudDetectorN1(gpu=gpu_ocr)
        self.detector_n2 = FraudDetectorN2(model_path_cnn)
    
    def procesar(self, ruta_nomina, ruta_dni):
        """
        Procesa un par de documentos y emite veredicto final
        Retorna: (veredicto_final, explicacion, detalles_n1, detalles_n2)
        """
        # Nivel 1: OCR + Reglas
        veredicto_n1, anomalias_n1, campos_nomina, campos_dni = self.detector_n1.detectar(ruta_nomina, ruta_dni)
        
        # Nivel 2: CNN solo en nómina
        veredicto_n2, clase_n2, confianza_n2 = self.detector_n2.detectar(ruta_nomina)
        
        # Combinación multimodal
        if veredicto_n1 == "FRAUDE_N1":
            veredicto_final = "FRAUDE"
            explicacion = f"Fraude detectado por Nivel 1: {', '.join(anomalias_n1)}"
        elif veredicto_n2 == "FRAUDE_N2":
            veredicto_final = "FRAUDE"
            explicacion = f"Fraude detectado por Nivel 2: alteración visual en la nómina (fuente distinta, confianza {confianza_n2:.1f}%)"
        else:
            veredicto_final = "VALIDO"
            explicacion = "No se detectaron anomalías en ninguno de los dos niveles"
        
        return {
            'veredicto_final': veredicto_final,
            'explicacion': explicacion,
            'nivel1': {
                'veredicto': veredicto_n1,
                'anomalias': anomalias_n1,
                'campos_nomina': campos_nomina,
                'campos_dni': campos_dni
            },
            'nivel2': {
                'veredicto': veredicto_n2,
                'clase': clase_n2,
                'confianza': confianza_n2
            }
        }


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == '__main__':
    # Rutas (ajústalas)
    MODELO_CNN = r'C:\Users\Lenovo\Documents\TFM\mejor_modelo_cnn.pth'
    RUTA_NOMINA = r'C:\Users\Lenovo\Documents\TFM\dataset\processed\limpios\pair_0001\nomina.png'
    RUTA_DNI = r'C:\Users\Lenovo\Documents\TFM\dataset\processed\limpios\pair_0001\dni.png'
    
    # Inicializar pipeline
    print("Inicializando pipeline multimodal...")
    pipeline = PipelineMultimodal(MODELO_CNN, gpu_ocr=False)
    
    # Procesar
    print("\n=== PROCESANDO DOCUMENTOS ===\n")
    resultado = pipeline.procesar(RUTA_NOMINA, RUTA_DNI)
    
    print(f"Veredicto final: {resultado['veredicto_final']}")
    print(f"Explicación: {resultado['explicacion']}")
    
    print("\n=== DETALLE NIVEL 1 ===")
    print(f"  Veredicto: {resultado['nivel1']['veredicto']}")
    if resultado['nivel1']['anomalias']:
        print(f"  Anomalías: {resultado['nivel1']['anomalias']}")
    print(f"  Campos nómina: {resultado['nivel1']['campos_nomina']}")
    print(f"  Campos DNI: {resultado['nivel1']['campos_dni']}")
    
    print("\n=== DETALLE NIVEL 2 ===")
    print(f"  Veredicto: {resultado['nivel2']['veredicto']}")
    print(f"  Clase: {resultado['nivel2']['clase']}")
    print(f"  Confianza: {resultado['nivel2']['confianza']:.1f}%")