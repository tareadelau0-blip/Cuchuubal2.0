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

GOOGLE_ICON_WHITE = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/payments/default/24px.svg?color=%23FFFFFF"

st.set_page_config(page_title="SISTEMA CUCHUBAL", page_icon=GOOGLE_ICON_WHITE, layout="centered")

# --- 2. CSS: ESTILO PROFESIONAL CUADRADO ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;600&family=Roboto:wght@400;700&display=swap" />
    <style>
        /* Fuente Profesional */
        html, body, [class*="css"] { 
            font-family: 'Roboto', sans-serif; 
        }
        
        /* Títulos en Mono para aspecto técnico */
        h1, h2, h3, .google-icon { 
            font-family: 'Roboto Mono', monospace; 
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .google-icon {
            vertical-align: middle;
            font-family: 'Material Symbols Outlined';
            color: var(--text-color);
        }

        /* TARJETAS CUADRADAS */
        div[data-testid="stMetric"] { 
            background-color: var(--secondary-background-color); 
            border: 2px solid var(--text-color); /* Borde fuerte y recto */
            border-radius: 0px !important; /* ELIMINAR REDONDEO */
            padding: 20px;
            box-shadow: 5px 5px 0px #58a6ff; /* Sombra sólida estilo industrial */
        }

        /* INPUTS Y BOTONES CUADRADOS */
        .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
            border-radius: 0px !important;
            border: 1px solid var(--text-color) !important;
        }

        .stButton>button { 
            background-color: transparent; 
            color: var(--text-color) !important;
            border: 2px solid var(--text-color) !important;
            border-radius: 0px !important; /* BOTÓN CUADRADO */
            height: 48px;
            font-weight: 700;
            text-transform: uppercase;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: var(--text-color) !important;
            color: var(--background-color) !important;
        }

        /* PESTAÑAS TIPO EXPEDIENTE */
        .stTabs [data-baseweb="tab"] {
            border-radius: 0px !important;
            border: 1px solid var(--border-color);
            margin-right: 4px;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] { 
            background-color: #58a6ff !important;
            color: white !important;
            border: 1px solid #58a6ff !important;
        }

        /* Iconos en Tabs */
        button[data-baseweb="tab"]:nth-child(1)::before {
            content: "table_chart"; font-family: 'Material Symbols Outlined';
            margin-right: 10px;
        }
        button[data-baseweb="tab"]:nth-child(2)::before {
            content: "admin_panel_settings"; font-family: 'Material Symbols Outlined';
            margin-right: 10px;
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
    <div style='border-bottom: 3px solid var(--text-color); margin-bottom: 30px; padding-bottom: 10px;'>
        <h2 style='margin: 0;'>
            <span class="google-icon" style="font-size: 35px;">account_balance_wallet</span>
            SISTEMA DE CONTROL DE CUCHUBAL
        </h2>
        <code style='font-size: 14px;'>ESTADO AL: {datetime.now().strftime('%Y-%m-%d %H:%M')} | SEMANA: {semanas_actuales}</code>
    </div>
""", unsafe_allow_html=True)

# Métrica Principal con diseño de bloque
st.metric("TOTAL EN FONDO (USD)", f"${fondo_total:,.2f}")

tab1, tab2 = st.tabs(["REPORTE GENERAL", "MODULO ADMINISTRATIVO"])

with tab1:
    st.write("")
    user = st.selectbox("IDENTIFICACIÓN DE USUARIO:", ["-- SELECCIONAR --"] + NOMBRES)
    if user != "-- SELECCIONAR --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        
        st.markdown(f"### <span class='google-icon'>label</span> EXPEDIENTE: {user.upper()}")
        
        c1, c2 = st.columns(2)
        c1.metric("APORTES TOTALES", f"${total_u:.2f}")
        
        if dif >= 0:
            c2.metric("ESTADO BALANCE", f"+${abs(dif):.2f}")
            st.info(f"SOLVENTE. Adelanto de {int(abs(dif)/CUOTA_SEMANAL)} períodos.")
        else:
            c2.metric("ESTADO BALANCE", f"-${abs(dif):.2f}", delta_color="inverse")
            st.error(f"DEUDA PENDIENTE: ${abs(dif):.2f}")

with tab2:
    st.write("")
    if st.text_input("ACCESO RESTRINGIDO (PIN):", type="password") == PASSWORD_ADMIN:
        st.markdown("#### REGISTRO DE TRANSACCIÓN")
        p_pago = st.selectbox("SELECCIONAR BENEFICIARIO:", NOMBRES)
        m_pago = st.number_input("MONTO DE CUOTA ($):", min_value=0.0, step=2.50, value=2.50)
        
        if st.button("PROCESAR Y SINCRONIZAR"):
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("TRANSACCIÓN COMPLETADA EXITOSAMENTE")
            st.rerun()
