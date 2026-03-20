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
        html, body, [class*="css"] { font-family: 'Roboto Mono', monospace; }
        .header-box { border-bottom: 4px solid var(--text-color); margin-bottom: 25px; padding-bottom: 10px; }
        div[data-testid="stMetric"] { 
            background-color: var(--secondary-background-color); 
            border: 2px solid var(--text-color); 
            border-radius: 0px !important; padding: 15px;
            box-shadow: 4px 4px 0px var(--text-color);
        }
        .stButton>button, .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
            border-radius: 0px !important; border: 2px solid var(--text-color) !important;
        }
        .stButton>button {
            background-color: var(--text-color); color: var(--background-color) !important;
            font-weight: bold; text-transform: uppercase;
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
        # Asegurar que existan las claves de gastos
        if "gastos_total" not in db: db["gastos_total"] = 0.0
        if "historial_gastos" not in db: db["historial_gastos"] = []
        for n in NOMBRES:
            if n not in db: db[n] = 0.0
        return db, contents.sha
    except:
        # Si el archivo no existe, crear estructura base
        base = {n: 0.0 for n in NOMBRES}
        base.update({"gastos_total": 0.0, "historial_gastos": []})
        return base, None

def guardar_en_github(nuevos_datos, sha):
    contenido_json = json.dumps(nuevos_datos, indent=4)
    if sha:
        repo.update_file(FILE_PATH, "ACTUALIZACION_SISTEMA", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "INIT_SISTEMA", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
semanas_actuales = max(0, (datetime.now() - FECHA_INICIO_CUCHUBAL).days // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL

# El fondo total es la suma de aportes menos los retiros
ingresos_brutos = sum(datos[n] for n in NOMBRES)
fondo_neto = ingresos_brutos - datos["gastos_total"]

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div class="header-box">
        <h2 style='margin: 0;'>CONTROL DE CAJA CUCHUBAL</h2>
        <small>FECHA: {datetime.now().strftime('%d/%m/%Y')} | SEMANA: {semanas_actuales}</small>
    </div>
""", unsafe_allow_html=True)

# Métricas principales
col_f1, col_f2 = st.columns(2)
col_f1.metric("SALDO NETO EN CAJA", f"${fondo_neto:,.2f}")
col_f2.metric("TOTAL RETIRADO", f"${datos['gastos_total']:,.2f}", delta_color="inverse")

menu = st.radio(
    "SELECCIONE MÓDULO:",
    ["CONSULTA DE SALDOS", "REGISTRO DE INGRESOS", "RETIRO DE EFECTIVO"],
    horizontal=True
)

st.write("---")

# --- MÓDULO 1: SALDOS ---
if menu == "CONSULTA DE SALDOS":
    user = st.selectbox("IDENTIFICACIÓN DE INTEGRANTE:", ["-- SELECCIONAR --"] + NOMBRES)
    if user != "-- SELECCIONAR --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        st.markdown(f"### REGISTRO: {user.upper()}")
        c1, c2 = st.columns(2)
        c1.metric("APORTADO", f"${total_u:.2f}")
        c2.metric("BALANCE", f"{'+' if dif >= 0 else ''}${dif:.2f}", delta_color="normal" if dif >= 0 else "inverse")
        
        if dif >= 0: st.success("ESTADO: AL DÍA")
        else: st.error(f"ESTADO: PENDIENTE (${abs(dif):.2f})")

# --- MÓDULO 2: INGRESOS ---
elif menu == "REGISTRO DE INGRESOS":
    if st.text_input("PASSWORD ADMIN:", type="password") == PASSWORD_ADMIN:
        p_pago = st.selectbox("INTEGRANTE:", NOMBRES)
        m_pago = st.number_input("MONTO A INGRESAR ($):", min_value=0.0, step=2.50, value=2.50)
        if st.button("CONFIRMAR INGRESO"):
            datos[p_pago] += m_pago
