"""
Aplicación web para detección de fraude documental
Desarrollada con Streamlit
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import os
import sys

# Añadir directorio actual al path para importar pipeline
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar pipeline multimodal
from pipeline_multimodal import PipelineMultimodal

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================

st.set_page_config(
    page_title="Detector de Fraude Documental",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🔍 Detector de Fraude Documental")
st.markdown("---")

# ============================================
# BARRA LATERAL
# ============================================

with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Ruta del modelo
    modelo_path = st.text_input(
        "Ruta del modelo CNN",
        value=r"C:\Users\Lenovo\Documents\TFM\app\mejor_modelo_cnn.pth"
    )
    
    # Verificar si el modelo existe
    if os.path.exists(modelo_path):
        st.success("✅ Modelo encontrado")
    else:
        st.error("❌ Modelo no encontrado. Verifica la ruta.")
    
    st.markdown("---")
    st.header("📋 Instrucciones")
    st.markdown("""
    1. Sube la imagen de la **nómina** (PNG, JPG)
    2. Sube la imagen del **DNI** (PNG, JPG)
    3. Haz clic en **Analizar**
    4. Espera el resultado
    """)
    
    st.markdown("---")
    st.header("📊 Acerca de")
    st.markdown("""
    **Nivel 1**: OCR + 7 reglas de coherencia  
    **Nivel 2**: CNN (ResNet18) para detección de fuentes alteradas  
    **Exactitud global**: 87.5%
    """)

# ============================================
# ÁREA PRINCIPAL - SUBIDA DE IMÁGENES
# ============================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Nómina")
    nomina_file = st.file_uploader(
        "Sube la imagen de la nómina",
        type=['png', 'jpg', 'jpeg'],
        key="nomina"
    )
    
    if nomina_file is not None:
        st.image(nomina_file, caption="Nómina", use_column_width=True)

with col2:
    st.subheader("🆔 DNI")
    dni_file = st.file_uploader(
        "Sube la imagen del DNI",
        type=['png', 'jpg', 'jpeg'],
        key="dni"
    )
    
    if dni_file is not None:
        st.image(dni_file, caption="DNI", use_column_width=True)

# ============================================
# BOTÓN DE ANÁLISIS
# ============================================

st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    analizar = st.button("🔍 Analizar documentos", type="primary", use_container_width=True)

# ============================================
# PROCESAMIENTO Y RESULTADOS
# ============================================

if analizar:
    if nomina_file is None or dni_file is None:
        st.error("⚠️ Por favor, sube ambos documentos (nómina y DNI) antes de analizar.")
    elif not os.path.exists(modelo_path):
        st.error("⚠️ Modelo no encontrado. Verifica la ruta en la barra lateral.")
    else:
        # Guardar imágenes temporalmente
        with st.spinner("Procesando documentos..."):
            # Crear barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Guardar archivos temporales
            temp_nomina = f"temp_nomina_{int(time.time())}.png"
            temp_dni = f"temp_dni_{int(time.time())}.png"
            
            with open(temp_nomina, "wb") as f:
                f.write(nomina_file.getbuffer())
            progress_bar.progress(20)
            status_text.text("📄 Nómina guardada...")
            
            with open(temp_dni, "wb") as f:
                f.write(dni_file.getbuffer())
            progress_bar.progress(40)
            status_text.text("🆔 DNI guardado...")
            
            # Inicializar pipeline
            status_text.text("🚀 Inicializando módulos de detección...")
            progress_bar.progress(50)
            
            pipeline = PipelineMultimodal(modelo_path, gpu_ocr=False)
            
            # Ejecutar pipeline
            status_text.text("🔍 Analizando documentos...")
            progress_bar.progress(70)
            
            inicio = time.time()
            resultado = pipeline.procesar(temp_nomina, temp_dni)
            fin = time.time()
            tiempo_procesamiento = fin - inicio
            
            progress_bar.progress(100)
            status_text.text("✅ Análisis completado")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            # Limpiar archivos temporales
            os.remove(temp_nomina)
            os.remove(temp_dni)
        
        # ============================================
        # MOSTRAR RESULTADOS
        # ============================================
        
        st.markdown("---")
        st.header("📊 Resultados del análisis")
        
        # Métricas principales
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            veredicto = resultado['veredicto_final']
            if veredicto == "FRAUDE":
                st.metric("Veredicto final", veredicto, delta="⚠️ ALERTA", delta_color="inverse")
            else:
                st.metric("Veredicto final", veredicto, delta="✅ DOCUMENTO VÁLIDO")
        
        with col_r2:
            st.metric("Tiempo de procesamiento", f"{tiempo_procesamiento:.2f} segundos")
        
        with col_r3:
            confianza_n2 = resultado['nivel2']['confianza']
            st.metric("Confianza CNN (Nivel 2)", f"{confianza_n2:.1f}%")
        
        # Explicación
        st.markdown("---")
        st.subheader("📝 Explicación del veredicto")
        st.info(resultado['explicacion'])
        
        # ============================================
        # DETALLE NIVEL 1
        # ============================================
        
        with st.expander("🔍 Ver detalle del Nivel 1 (OCR + Reglas)"):
            col_n1_1, col_n1_2 = st.columns(2)
            
            with col_n1_1:
                st.markdown("**📄 Campos extraídos de la nómina**")
                campos_nomina = resultado['nivel1']['campos_nomina']
                st.json(campos_nomina)
            
            with col_n1_2:
                st.markdown("**🆔 Campos extraídos del DNI**")
                campos_dni = resultado['nivel1']['campos_dni']
                st.json(campos_dni)
            
            st.markdown("**⚠️ Anomalías detectadas por Nivel 1**")
            if resultado['nivel1']['anomalias']:
                for a in resultado['nivel1']['anomalias']:
                    st.warning(f"• {a}")
            else:
                st.success("No se detectaron anomalías en el Nivel 1")
        
        # ============================================
        # DETALLE NIVEL 2
        # ============================================
        
        with st.expander("🧠 Ver detalle del Nivel 2 (CNN)"):
            st.markdown(f"**Veredicto:** {resultado['nivel2']['veredicto']}")
            st.markdown(f"**Clase predicha:** {resultado['nivel2']['clase']}")
            st.markdown(f"**Confianza:** {resultado['nivel2']['confianza']:.2f}%")
            
            # Barra de confianza
            st.markdown("**Confianza de la predicción:**")
            conf = resultado['nivel2']['confianza'] / 100
            st.progress(conf)
            
            if resultado['nivel2']['clase'] == 'fraude':
                st.warning("⚠️ La CNN ha detectado una alteración en la fuente del importe neto.")
            else:
                st.success("✅ La CNN no ha detectado alteraciones visuales en la nómina.")
        
        # ============================================
        # EXPORTAR RESULTADOS
        # ============================================
        
        st.markdown("---")
        st.subheader("💾 Exportar resultados")
        
        # Preparar datos para exportar
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "veredicto_final": resultado['veredicto_final'],
            "explicacion": resultado['explicacion'],
            "tiempo_procesamiento_segundos": tiempo_procesamiento,
            "nivel1": {
                "veredicto": resultado['nivel1']['veredicto'],
                "anomalias": resultado['nivel1']['anomalias'],
                "campos_nomina": resultado['nivel1']['campos_nomina'],
                "campos_dni": resultado['nivel1']['campos_dni']
            },
            "nivel2": {
                "veredicto": resultado['nivel2']['veredicto'],
                "clase": resultado['nivel2']['clase'],
                "confianza": resultado['nivel2']['confianza']
            }
        }
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            # Exportar JSON
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Descargar informe (JSON)",
                data=json_str,
                file_name=f"informe_fraude_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col_e2:
            # Exportar CSV (versión simplificada)
            df_export = pd.DataFrame([{
                "timestamp": datetime.now().isoformat(),
                "veredicto": resultado['veredicto_final'],
                "tiempo_segundos": tiempo_procesamiento,
                "confianza_cnn": resultado['nivel2']['confianza'],
                "anomalias_n1": "; ".join(resultado['nivel1']['anomalias']) if resultado['nivel1']['anomalias'] else "Ninguna"
            }])
            
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resumen (CSV)",
                data=csv_data,
                file_name=f"resumen_fraude_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # ============================================
        # RECOMENDACIONES
        # ============================================
        
        if resultado['veredicto_final'] == "FRAUDE":
            st.markdown("---")
            st.error("""
            ### 🔴 RECOMENDACIONES
            - Se ha detectado fraude en la documentación.
            - Verificar manualmente los documentos originales.
            - Contactar al emisor para confirmar la autenticidad.
            - No aceptar la documentación sin verificación adicional.
            """)

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
st.markdown(
    "<center><small>Desarrollado para Trabajo Fin de Máster - UNIR</small></center>",
    unsafe_allow_html=True
)