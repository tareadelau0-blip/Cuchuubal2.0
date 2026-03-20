import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
FECHA_INICIO_CUCHUBAL = datetime(2026, 2, 10) 
CUOTA_SEMANAL = 2.50
PASSWORD_ADMIN = "1234" 
NOMBRES = sorted(["Ociel", "Jonathan", "Gisselle", "Sofia", "Cristopher", "Leslie"])

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "datos_pagos.json"

GOOGLE_ICON_URL = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/payments/default/24px.svg?color=%23FFFFFF"

st.set_page_config(page_title="SISTEMA CUCHUBAL", page_icon=GOOGLE_ICON_URL, layout="centered")

# --- 2. CSS PROFESIONAL CUADRADO ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;600&family=Roboto:wght@400;700&display=swap" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <style>
        html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
        
        .title-container {
            border-bottom: 3px solid var(--text-color);
            margin-bottom: 30px;
            padding-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .google-icon-main {
            font-family: 'Material Symbols Outlined';
            font-size: 40px;
            color: var(--text-color);
        }

        /* METRICAS CUADRADAS */
        div[data-testid="stMetric"] { 
            background-color: var(--secondary-background-color); 
            border: 2px solid var(--text-color); 
            border-radius: 0px !important; 
            box-shadow: 5px 5px 0px #58a6ff;
        }

        /* BOTONES CUADRADOS */
        .stButton>button { 
            border-radius: 0px !important; 
            border: 2px solid var(--text-color) !important;
            text-transform: uppercase;
            font-weight: 700;
        }

        /* INPUTS CUADRADOS */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            border-radius: 0px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS ---
g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

def cargar_datos_github():
    try:
        contents = repo.get_contents(FILE_PATH)
        db = json.loads(contents.decoded_content.decode())
        for n in NOMBRES:
            if n not in db: db[n] = 0.0
        return db, contents.sha
    except:
        return {nombre: 0.0 for nombre in NOMBRES}, None

def guardar_en_github(nuevos_datos, sha):
    contenido_json = json.dumps(nuevos_datos, indent=4)
    if sha:
        repo.update_file(FILE_PATH, "REGISTRO_CONTABLE", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "INICIO_CONTABLE", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
semanas_actuales = max(0, (datetime.now() - FECHA_INICIO_CUCHUBAL).days // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL
fondo_total = sum(datos.values())

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div class="title-container">
        <span class="google-icon-main">payments</span>
        <div>
            <h2 style='margin: 0; line-height: 1;'>SISTEMA CUCHUBAL</h2>
            <code style='font-size: 12px;'>PERÍODO ACTIVO: {datetime.now().year} | SEMANA: {semanas_actuales}</code>
        </div>
    </div>
""", unsafe_allow_html=True)

st.metric("TOTAL EN FONDO (USD)", f"${fondo_total:,.2f}")

# SOLUCIÓN PARA LOS ICONOS: Usamos st.pills (disponible en versiones recientes) 
# o una botonera técnica si prefieres. Aquí usamos la navegación limpia:
menu = st.pills(
    "SELECCIONE MÓDULO:",
    ["REPORTE", "ADMINISTRACIÓN"],
    icons=["table_chart", "admin_panel_settings"], # Estos son iconos nativos que Streamlit sí reconoce
    selection_mode="single",
    default="REPORTE"
)

st.markdown("---")

if menu == "REPORTE":
    user = st.selectbox("IDENTIFICACIÓN DE USUARIO:", ["-- SELECCIONAR --"] + NOMBRES)
    if user != "-- SELECCIONAR --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        
        st.subheader(f"EXPEDIENTE: {user.upper()}")
        
        c1, c2 = st.columns(2)
        c1.metric("APORTES TOTALES", f"${total_u:.2f}")
        
        if dif >= 0:
            c2.metric("ESTADO BALANCE", f"+${abs(dif):.2f}")
            st.info(f"SOLVENTE. Adelanto de {int(abs(dif)/CUOTA_SEMANAL)} períodos.")
        else:
            c2.metric("ESTADO BALANCE", f"-${abs(dif):.2f}", delta_color="inverse")
            st.error(f"DEUDA PENDIENTE: ${abs(dif):.2f}")

elif menu == "ADMINISTRACIÓN":
    if st.text_input("ACCESO RESTRINGIDO (PIN):", type="password") == PASSWORD_ADMIN:
        st.markdown("#### REGISTRO DE TRANSACCIÓN")
        p_pago = st.selectbox("SELECCIONAR BENEFICIARIO:", NOMBRES)
        m_pago = st.number_input("MONTO DE CUOTA ($):", min_value=0.0, step=2.50, value=2.50)
        
        if st.button("PROCESAR Y SINCRONIZAR"):
            if p_pago not in datos: datos[p_pago] = 0.0
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("TRANSACCIÓN COMPLETADA")
            st.rerun()
