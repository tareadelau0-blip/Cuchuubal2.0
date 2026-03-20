import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
FECHA_INICIO_CUCHUBAL = datetime(2026, 2, 10) 
CUOTA_SEMANAL = 2.50
PASSWORD_ADMIN = "1234" 
NOMBRES = ["Ociel", "Jonathan", "Gisselle", "Sofia", "Cristopher", "Leslie"]

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "datos_pagos.json"

# Icono de la pestaña: Usamos una URL de un icono de Google para que sea consistente
ICON_URL = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/payments/default/24px.svg"
st.set_page_config(page_title="Cuchubal Digital", page_icon=ICON_URL, layout="centered")

# --- 2. INYECCIÓN DE ESTILOS Y GOOGLE ICONS ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Estilo para los iconos de Google */
        .google-icon {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            vertical-align: middle;
            color: #58a6ff;
            margin-right: 10px;
        }

        /* Tarjetas de Métricas */
        div[data-testid="stMetric"] { 
            background-color: #161b22; 
            border: 1px solid #30363d; 
            padding: 15px; 
            border-radius: 12px; 
        }

        /* Personalización de Tabs (Pestañas) */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #161b22;
            border-radius: 8px 8px 0 0;
            color: #8b949e;
            border: none;
        }
        .stTabs [aria-selected="true"] { 
            background-color: #30363d !important; 
            color: #58a6ff !important; 
            border-bottom: 2px solid #58a6ff !important;
        }

        /* Botón estilo Google/GitHub */
        .stButton>button { 
            background-color: #238636; 
            color: white; border: none; border-radius: 6px; 
            height: 45px; font-weight: 600; width: 100%;
        }
        .stButton>button:hover { background-color: #2ea043; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE GITHUB ---
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
        repo.update_file(FILE_PATH, "Update Cuchubal", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "Create DB", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
dias_transcurridos = (datetime.now() - FECHA_INICIO_CUCHUBAL).days
semanas_actuales = max(0, dias_transcurridos // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL
fondo_total = sum(datos.values())

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1><span class="google-icon" style="font-size: 40px;">account_balance</span>Cuchubal Digital</h1>
        <p style='color: #8b949e;'>Semana {semanas_actuales} • Meta: ${monto_esperado:.2f}</p>
    </div>
""", unsafe_allow_html=True)

st.metric("FONDO TOTAL ACUMULADO", f"${fondo_total:,.2f}")

# Aquí usamos HTML dentro de las pestañas para forzar los iconos de Google
t1_html = '<span class="google-icon">analytics</span> ESTADO'
t2_html = '<span class="google-icon">settings</span> GESTIÓN'

tab1, tab2 = st.tabs([t1_html, t2_html])

with tab1:
    st.write("")
    user = st.selectbox("Seleccionar integrante", ["-- Elegir --"] + NOMBRES)
    if user != "-- Elegir --":
        total_user = datos.get(user, 0.0)
        balance = total_user - monto_esperado
        st.markdown(f"### <span class='google-icon'>person</span> {user}", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Aportado", f"${total_user:.2f}")
        if balance >= 0:
            c2.metric("Balance", f"+${abs(balance):.2f}")
            st.success(f"Al día. Adelanto: {int(abs(balance)/CUOTA_SEMANAL)} semanas.")
        else:
            c2.metric("Balance", f"-${abs(balance):.2f}", delta_color="inverse")
            st.error(f"Pendiente. Debes {int(abs(balance)/CUOTA_SEMANAL)} semanas.")

with tab2:
    st.write("")
    key = st.text_input("Admin Key", type="password")
    if key == PASSWORD_ADMIN:
        st.markdown("---")
        c_a, c_b = st.columns([2, 1])
        p_pago = c_a.selectbox("Integrante:", NOMBRES)
        m_pago = c_b.number_input("Monto:", min_value=0.0, step=2.50, value=2.50)
        if st.button("REGISTRAR PAGO"):
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("Sincronizado")
            st.rerun()
