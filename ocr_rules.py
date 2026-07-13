"""
Módulo OCR + Reglas para detección de fraude Nivel 1
Implementa las 7 reglas definidas en la memoria
"""

import re
import easyocr
from PIL import Image
from datetime import datetime

class FraudDetectorN1:
    def __init__(self, gpu=False):
        """
        Inicializa el detector con EasyOCR
        Args:
            gpu: Si es True, usa GPU (más rápido). Default False.
        """
        self.reader = easyocr.Reader(['es', 'en'], gpu=gpu)
    
    def calcular_letra_nif(self, numeros):
        """Calcula la letra correcta para un NIF de 8 dígitos"""
        letras = 'TRWAGMYFPDXBNJZSQVHLCKE'
        return letras[numeros % 23]
    
    def validar_nif(self, nif):
        """Verifica si un NIF es válido (8 números + letra correcta)"""
        if not nif or len(nif) != 9:
            return False
        try:
            numeros = int(nif[:8])
            letra = nif[8].upper()
            return letra == self.calcular_letra_nif(numeros)
        except:
            return False
    
    def validar_ssn(self, ssn):
        """Verifica formato de Seguridad Social: XX XXXXXXX"""
        if not ssn:
            return False
        patron = r'^\d{2}\s\d{7}$'
        return re.match(patron, ssn) is not None
    
    def extraer_campos_nomina(self, textos):
        """Extrae campos clave de la nómina"""
        campos = {
            'nombre': None,
            'nif': None,
            'ssn': None,
            'importe': None,
            'fecha': None
        }
        
        for i, texto in enumerate(textos):
            # NIF (8 números + letra)
            nif_match = re.search(r'\b(\d{8}[A-Z])\b', texto.upper())
            if nif_match:
                campos['nif'] = nif_match.group(1)
            
            # SSN (formato: XX XXXXXXX)
            ssn_match = re.search(r'\b(\d{2}\s\d{7})\b', texto)
            if ssn_match:
                campos['ssn'] = ssn_match.group(1)
            
            # Fecha
            fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
            if fecha_match:
                campos['fecha'] = fecha_match.group(1)
            
            # Nombre (después de "Nombre:")
            if 'Nombre:' in texto:
                partes = texto.split('Nombre:')
                if len(partes) > 1:
                    campos['nombre'] = partes[1].strip()
            
            # Importe TOTAL NETO
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
        """Extrae campos clave del DNI usando posiciones fijas"""
        campos = {
            'nombre': None,
            'nif': None,
            'fecha_nacimiento': None,
            'fecha_validez': None
        }
        
        for i, texto in enumerate(textos):
            # NIF (índice 4 en estructura típica)
            if i == 4:
                nif_match = re.search(r'\b(\d{8}[A-Z])\b', texto.upper())
                if nif_match:
                    campos['nif'] = nif_match.group(1)
            
            # Nombre (índice 8)
            if i == 8:
                campos['nombre'] = texto
            
            # Fecha validez (índice 9)
            if i == 9:
                fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
                if fecha_match:
                    campos['fecha_validez'] = fecha_match.group(1)
            
            # Fecha nacimiento (índice 12)
            if i == 12:
                fecha_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', texto)
                if fecha_match:
                    campos['fecha_nacimiento'] = fecha_match.group(1)
        
        return campos
    
    def validar_coherencia(self, campos_nomina, campos_dni):
        """
        Aplica las 7 reglas de detección de fraude N1
        Retorna: (veredicto, lista_anomalias)
        """
        anomalias = []
        
        # ============================================
        # REGLA 1: Nombre no coincide entre documentos
        # ============================================
        if campos_nomina['nombre'] and campos_dni['nombre']:
            nom_nom = campos_nomina['nombre'].lower().strip()
            nom_dni = campos_dni['nombre'].lower().strip()
            if nom_nom != nom_dni and nom_nom not in nom_dni and nom_dni not in nom_nom:
                anomalias.append(f"REGLA 1 - Nombre no coincide: nómina='{campos_nomina['nombre']}', DNI='{campos_dni['nombre']}'")
        
        # ============================================
        # REGLA 2: NIF no coincide entre documentos
        # ============================================
        if campos_nomina['nif'] and campos_dni['nif']:
            if campos_nomina['nif'] != campos_dni['nif']:
                anomalias.append(f"REGLA 2 - NIF no coincide: nómina='{campos_nomina['nif']}', DNI='{campos_dni['nif']}'")
        
        # ============================================
        # REGLA 3: Importe sospechoso (<300€ o >15000€)
        # ============================================
        if campos_nomina['importe']:
            importe = campos_nomina['importe']
            if importe < 300:
                anomalias.append(f"REGLA 3 - Importe sospechosamente bajo: {importe}€")
            elif importe > 15000:
                anomalias.append(f"REGLA 3 - Importe sospechosamente alto: {importe}€")
        
        # ============================================
        # REGLA 4: SSN inválido (formato incorrecto)
        # ============================================
        if campos_nomina['ssn']:
            if not self.validar_ssn(campos_nomina['ssn']):
                anomalias.append(f"REGLA 4 - SSN con formato inválido: '{campos_nomina['ssn']}'")
        
        # ============================================
        # REGLA 5: DNI caducado (fecha validez anterior a hoy)
        # ============================================
        if campos_dni['fecha_validez']:
            try:
                fecha_validez = datetime.strptime(campos_dni['fecha_validez'], '%d/%m/%Y')
                if fecha_validez < datetime.now():
                    anomalias.append(f"REGLA 5 - DNI caducado desde {campos_dni['fecha_validez']}")
            except:
                pass
        
        # ============================================
        # REGLA 6: Fecha nacimiento incoherente (<16 o >67 años)
        # ============================================
        if campos_dni['fecha_nacimiento']:
            try:
                fecha_nac = datetime.strptime(campos_dni['fecha_nacimiento'], '%d/%m/%Y')
                
                # Determinar fecha de referencia (nómina o actual)
                if campos_nomina['fecha']:
                    fecha_referencia = datetime.strptime(campos_nomina['fecha'], '%d/%m/%Y')
                else:
                    fecha_referencia = datetime.now()
                
                # Calcular edad
                edad = fecha_referencia.year - fecha_nac.year - ((fecha_referencia.month, fecha_referencia.day) < (fecha_nac.month, fecha_nac.day))
                
                if edad < 16:
                    anomalias.append(f"REGLA 6 - Edad menor de 16 años: {edad} años (fecha nacimiento: {campos_dni['fecha_nacimiento']})")
                elif edad > 67:
                    anomalias.append(f"REGLA 6 - Edad mayor de 67 años: {edad} años (fecha nacimiento: {campos_dni['fecha_nacimiento']})")
                
                # Si hay fecha de nómina, verificar que no sea anterior al nacimiento
                if campos_nomina['fecha']:
                    fecha_nomina = datetime.strptime(campos_nomina['fecha'], '%d/%m/%Y')
                    if fecha_nomina < fecha_nac:
                        anomalias.append(f"REGLA 6 - Nómina anterior a fecha de nacimiento")
            except Exception as e:
                # Si hay error, no hacer nada
                pass
                
        # ============================================
        # REGLA 7: NIF inválido (letra no corresponde)
        # ============================================
        if campos_nomina['nif']:
            if not self.validar_nif(campos_nomina['nif']):
                anomalias.append(f"REGLA 7 - NIF de nómina inválido: '{campos_nomina['nif']}'")
        
        if campos_dni['nif']:
            if not self.validar_nif(campos_dni['nif']):
                anomalias.append(f"REGLA 7 - NIF de DNI inválido: '{campos_dni['nif']}'")
        
        # Veredicto final
        if len(anomalias) > 0:
            veredicto = "FRAUDE_N1"
        else:
            veredicto = "VALIDO"
        
        return veredicto, anomalias
    
    def detectar(self, ruta_nomina, ruta_dni):
        """
        Proceso completo: OCR + reglas para un par de documentos
        Retorna: (veredicto, anomalias, campos_nomina, campos_dni)
        """
        # Extraer texto con OCR
        resultados_nomina = self.reader.readtext(ruta_nomina)
        textos_nomina = [texto for (_, texto, _) in resultados_nomina]
        
        resultados_dni = self.reader.readtext(ruta_dni)
        textos_dni = [texto for (_, texto, _) in resultados_dni]
        
        # Extraer campos
        campos_nomina = self.extraer_campos_nomina(textos_nomina)
        campos_dni = self.extraer_campos_dni(textos_dni)
        
        # Validar coherencia
        veredicto, anomalias = self.validar_coherencia(campos_nomina, campos_dni)
        
        return veredicto, anomalias, campos_nomina, campos_dni


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == '__main__':
    import os
    
    # Inicializar detector
    detector = FraudDetectorN1(gpu=False)
    
    # Probar con un par limpio
    print("=== PRUEBA CON PAR LIMPIO ===\n")
    ruta_nomina = r'C:\Users\Lenovo\Documents\TFM\dataset\processed\limpios\pair_0001\nomina.png'
    ruta_dni = r'C:\Users\Lenovo\Documents\TFM\dataset\processed\limpios\pair_0001\dni.png'
    
    if os.path.exists(ruta_nomina):
        veredicto, anomalias, campos_nomina, campos_dni = detector.detectar(ruta_nomina, ruta_dni)
        
        print("=== CAMPOS NÓMINA ===")
        for k, v in campos_nomina.items():
            print(f"  {k}: {v}")
        print("\n=== CAMPOS DNI ===")
        for k, v in campos_dni.items():
            print(f"  {k}: {v}")
        print(f"\n=== VEREDICTO: {veredicto} ===")
        if anomalias:
            print("Anomalías detectadas:")
            for a in anomalias:
                print(f"  - {a}")
    else:
        print(f"No se encontró: {ruta_nomina}")