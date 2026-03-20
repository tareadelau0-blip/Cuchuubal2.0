import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# --- CONFIGURACIÓN ---
# IMPORTANTE: Pon aquí la fecha exacta en que inició el primer pago (Año, Mes, Día)
FECHA_INICIO_CUCHUBAL = datetime(2026, 2, 10) 
CUOTA_SEMANAL = 2.50
PASSWORD_ADMIN = "1234" 
NOMBRES = ["Ociel", "Jonathan", "Gisselle", "Sofia", "Cristopher", "Leslie"]

# Configuración de Secrets de Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "datos_pagos.json"

st.set_page_config(page_title="Cuchubal 2.0", page_icon="💰")

# --- LÓGICA DE GITHUB ---
g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

def cargar_datos_github():
    try:
        contents = repo.get_contents(FILE_PATH)
        return json.loads(contents.decoded_content.decode()), contents.sha
    except:
        return {nombre: 0.0 for nombre in NOMBRES}, None

def guardar_en_github(nuevos_datos, sha):
    contenido_json = json.dumps(nuevos_datos, indent=4)
    if sha:
        repo.update_file(FILE_PATH, "Update pagos", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "Create pagos", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- CÁLCULOS AUTOMÁTICOS ---
# Calculamos cuántas semanas han pasado desde el inicio hasta hoy
dias_transcurridos = (datetime.now() - FECHA_INICIO_CUCHUBAL).days
semanas_actuales = dias_transcurridos // 7
monto_esperado_por_persona = semanas_actuales * CUOTA_SEMANAL

# --- INTERFAZ DE USUARIO ---
st.title("🏦 Estado del Cuchubal")

# 1. VISUALIZACIÓN GLOBAL (Al entrar)
fondo_total = sum(datos.values())
st.metric(label="💰 FONDO GLOBAL ACUMULADO", value=f"${fondo_total:.2f}")

col_info1, col_info2 = st.columns(2)
col_info1.write(f"📅 **Inicio:** {FECHA_INICIO_CUCHUBAL.strftime('%d/%m/%Y')}")
col_info2.write(f"📆 **Semana actual:** {semanas_actuales}")

st.divider()

# 2. CONSULTA INDIVIDUAL
tab1, tab2 = st.tabs(["🔍 Mi Estado", "⚙️ Administrar"])

with tab1:
    user = st.selectbox("Selecciona tu nombre:", ["--"] + NOMBRES)
    if user != "--":
        total_usuario = datos.get(user, 0.0)
        diferencia = total_usuario - monto_esperado_por_persona
        
        c1, c2 = st.columns(2)
        c1.metric("Has aportado", f"${total_usuario:.2f}")
        
        # Lógica de colores para el estatus
        if diferencia > 0:
            c2.success(f"Adelantado: ${diferencia:.2f}")
            st.balloons()
        elif diferencia < 0:
            c2.error(f"Debes: ${abs(diferencia):.2f}")
        else:
            c2.info("Estás al día ✅")

with tab2:
    pw = st.text_input("Contraseña Admin", type="password")
    if pw == PASSWORD_ADMIN:
        st.subheader("Registrar Pago")
        p_pago = st.selectbox("Persona:", NOMBRES)
        m_pago = st.number_input("Monto ($)", step=2.50)
        
        if st.button("Guardar en GitHub"):
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("¡Sincronizado!")
            st.rerun()
