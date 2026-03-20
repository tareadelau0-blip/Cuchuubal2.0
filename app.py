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

st.set_page_config(page_title="COCHUBAL", page_icon="💳", layout="centered")

# --- 2. CSS: ESTILO INDUSTRIAL RECTO ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;600&display=swap" />
    <style>
        /* Tipografía técnica */
        html, body, [class*="css"] { font-family: 'Roboto Mono', monospace; }
        
        /* Contenedor de Título con borde inferior grueso */
        .header-box {
            border-bottom: 4px solid var(--text-color);
            margin-bottom: 25px;
            padding-bottom: 10px;
        }

        /* MÉTRICAS COMPLETAMENTE CUADRADAS */
        div[data-testid="stMetric"] { 
            background-color: var(--secondary-background-color); 
            border: 2px solid var(--text-color); 
            border-radius: 0px !important; 
            padding: 15px;
            box-shadow: 4px 4px 0px var(--text-color);
        }

        /* BOTONES Y SELECTORES CUADRADOS */
        .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div {
            border-radius: 0px !important;
            border: 2px solid var(--text-color) !important;
        }

        .stButton>button {
            background-color: var(--text-color);
            color: var(--background-color) !important;
            font-weight: bold;
            text-transform: uppercase;
        }

        /* Estilo para el Radio Horizontal como Menú */
        div[data-testid="stWidgetLabel"] p {
            font-weight: bold;
            text-transform: uppercase;
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
        repo.update_file(FILE_PATH, "REGISTRO_SISTEMA", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "INIT_SISTEMA", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
semanas_actuales = max(0, (datetime.now() - FECHA_INICIO_CUCHUBAL).days // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL
fondo_total = sum(datos.values())

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div class="header-box">
        <h2 style='margin: 0;'>[SISTEMA_CONTABLE_CUCHUBAL]</h2>
        <small>FECHA: {datetime.now().strftime('%d/%m/%Y')} | SEMANA: {semanas_actuales}</small>
    </div>
""", unsafe_allow_html=True)

st.metric("FONDO TOTAL ACUMULADO", f"${fondo_total:,.2f}")

# MENÚ DE NAVEGACIÓN ESTABLE (Sustituye a st.pills)
menu = st.radio(
    "SELECCIONE MÓDULO:",
    ["CONSULTA DE SALDOS", "REGISTRO ADMINISTRATIVO"],
    horizontal=True
)

st.write("---")

if menu == "CONSULTA DE SALDOS":
    user = st.selectbox("IDENTIFICACIÓN DE INTEGRANTE:", ["-- SELECCIONAR --"] + NOMBRES)
    if user != "-- SELECCIONAR --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        
        st.markdown(f"### REGISTRO: {user.upper()}")
        
        c1, c2 = st.columns(2)
        c1.metric("APORTES", f"${total_u:.2f}")
        
        if dif >= 0:
            c2.metric("BALANCE", f"+${abs(dif):.2f}")
            st.success(f"SOLVENTE: {int(abs(dif)/CUOTA_SEMANAL)} CUOTAS ADELANTADAS")
        else:
            c2.metric("BALANCE", f"-${abs(dif):.2f}", delta_color="inverse")
            st.error(f"PENDIENTE: DEBE ${abs(dif):.2f}")

elif menu == "REGISTRO ADMINISTRATIVO":
    if st.text_input("PASSWORD DE ACCESO:", type="password") == PASSWORD_ADMIN:
        st.markdown("#### ENTRADA DE DATOS")
        p_pago = st.selectbox("INTEGRANTE:", NOMBRES)
        m_pago = st.number_input("MONTO A REGISTRAR ($):", min_value=0.0, step=2.50, value=2.50)
        
        if st.button("EJECUTAR TRANSACCIÓN"):
            if p_pago not in datos: datos[p_pago] = 0.0
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("SISTEMA ACTUALIZADO CORRECTAMENTE")
            st.rerun()
