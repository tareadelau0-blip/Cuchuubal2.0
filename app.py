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

st.set_page_config(page_title="Cuchubal 2.0", page_icon="💳", layout="centered")

# --- ESTILO CSS AVANZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #0e1117; }
    
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; }
    div[data-testid="stMetricValue"] { color: #58a6ff !important; font-size: 32px !important; }

    /* Estilo de Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #21262d;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #c9d1d9;
    }
    .stTabs [aria-selected="true"] { background-color: #30363d !important; color: #58a6ff !important; }

    /* Botón de acción */
    .stButton>button {
        background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%);
        color: white; border: none; border-radius: 8px;
        height: 45px; font-weight: 600; transition: 0.3s;
    }
    .stButton>button:hover { opacity: 0.9; transform: translateY(-1px); }
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
fondo_total = sum(datos.values())

# --- HEADER ---
st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
st.markdown("<h2 style='margin-bottom: 0;'>🏦 Cuchubal Digital</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #8b949e;'>Semana {semanas_actuales} • Meta Individual: ${monto_esperado:.2f}</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- KPI PRINCIPAL ---
st.metric("FONDO GLOBAL", f"${fondo_total:,.2f}")

st.write("")

# --- SECCIONES ---
tab1, tab2 = st.tabs(["📊 ESTADO DE CUENTA", "🛠 GESTIÓN"])

with tab1:
    st.write("")
    user = st.selectbox("Seleccionar integrante", ["--"] + NOMBRES)
    
    if user != "--":
        total_usuario = datos.get(user, 0.0)
        diferencia = total_usuario - monto_esperado
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Aportado", f"${total_usuario:.2f}")
        with c2:
            if diferencia >= 0:
                st.metric("Balance", f"+${abs(diferencia):.2f}")
                st.success(f"**Al día.** Adelanto: {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas.")
            else:
                st.metric("Balance", f"-${abs(diferencia):.2f}", delta_color="inverse")
                st.error(f"**Pendiente.** Debe: {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas.")

with tab2:
    st.write("")
    with st.container():
        pw = st.text_input("Admin Key", type="password", placeholder="Contraseña de acceso")
        
        if pw == PASSWORD_ADMIN:
            st.markdown("---")
            col_a, col_b = st.columns([2, 1])
            p_pago = col_a.selectbox("Integrante:", NOMBRES)
            m_pago = col_b.number_input("Monto:", min_value=0.0, step=2.50, value=2.50)
            
            if st.button("REGISTRAR APORTACIÓN"):
                with st.spinner("Sincronizando..."):
                    datos[p_pago] += m_pago
                    guardar_en_github(datos, archivo_sha)
                    st.success("Registro exitoso")
                    st.rerun()
