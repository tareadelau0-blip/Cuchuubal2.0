import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# --- CONFIGURACIÓN ---
FECHA_INICIO_CUCHUBAL = datetime(2026, 2, 10) 
CUOTA_SEMANAL = 2.50
PASSWORD_ADMIN = "1234" 
NOMBRES = ["Ociel", "Jonathan", "Gisselle", "Sofia", "Cristopher", "Leslie"]

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "datos_pagos.json"

# Configuración de página con tema oscuro/claro automático
st.set_page_config(page_title="Cuchubal 2.0", page_icon="🏦", layout="centered")

# --- ESTILO CSS PERSONALIZADO (Minimalismo) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 35px; font-weight: bold; color: #00d4ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px; color: white; border: none;
    }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00d4ff !important; }
    div.stButton > button {
        width: 100%; border-radius: 5px; height: 3em;
        background-color: #00d4ff; color: black; font-weight: bold; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- CÁLCULOS ---
dias_transcurridos = (datetime.now() - FECHA_INICIO_CUCHUBAL).days
semanas_actuales = max(0, dias_transcurridos // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL

# --- INTERFAZ ---
st.markdown("<h3 style='text-align: center; color: grey;'>SISTEMA DE GESTIÓN</h3>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>🏦 Cuchubal 2.0</h1>", unsafe_allow_html=True)

# 1. RESUMEN GLOBAL EN TARJETA
with st.container():
    fondo_total = sum(datos.values())
    st.metric(label="FONDO GLOBAL ACUMULADO", value=f"${fondo_total:,.2f}")
    
    c1, c2, c3 = st.columns(3)
    c1.caption(f"📅 Inicio: {FECHA_INICIO_CUCHUBAL.strftime('%d/%m/%Y')}")
    c2.caption(f"📆 Semanas: {semanas_actuales}")
    c3.caption(f"💵 Cuota: ${CUOTA_SEMANAL:.2f}")

st.write("")

# 2. SECCIONES
tab1, tab2 = st.tabs(["👤 CONSULTA INDIVIDUAL", "🔐 ADMINISTRACIÓN"])

with tab1:
    st.write("")
    user = st.selectbox("Selecciona un integrante:", ["--"] + NOMBRES)
    
    if user != "--":
        total_usuario = datos.get(user, 0.0)
        diferencia = total_usuario - monto_esperado
        
        with st.expander(f"Ver detalle de {user}", expanded=True):
            col_a, col_b = st.columns(2)
            col_a.metric("Total Aportado", f"${total_usuario:.2f}")
            
            if diferencia > 0:
                col_b.metric("Adelanto", f"${abs(diferencia):.2f}", delta_color="normal")
                st.success(f"Estás adelantado con {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas.")
            elif diferencia < 0:
                col_b.metric("Pendiente", f"-${abs(diferencia):.2f}", delta_color="inverse")
                st.error(f"Tienes {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas pendientes.")
            else:
                col_b.metric("Estatus", "Al día")
                st.info("Todo en orden, ¡gracias!")

with tab2:
    st.write("")
    pw = st.text_input("Acceso restringido", type="password", placeholder="Ingresa contraseña")
    
    if pw == PASSWORD_ADMIN:
        st.markdown("---")
        p_pago = st.selectbox("Registrar pago para:", NOMBRES)
        m_pago = st.number_input("Monto recibido ($)", min_value=0.0, step=2.50, value=2.50)
        
        if st.button("CONFIRMAR Y SINCRONIZAR"):
            with st.spinner("Subiendo a GitHub..."):
                datos[p_pago] += m_pago
                guardar_en_github(datos, archivo_sha)
                st.success(f"Pago de {p_pago} guardado con éxito.")
                st.rerun()
