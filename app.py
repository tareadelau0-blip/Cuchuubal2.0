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

# Icono de Google para la pestaña del navegador
GOOGLE_ICON_URL = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/payments/default/24px.svg"

st.set_page_config(page_title="Cuchubal Digital", page_icon=GOOGLE_ICON_URL, layout="centered")

# --- 2. CSS ADAPTATIVO (MODO CLARO Y OSCURO) ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        
        /* Forzamos la fuente Inter globalmente */
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Iconos de Google adaptativos */
        .google-icon {
            font-family: 'Material Symbols Outlined';
            vertical-align: middle;
            font-size: 28px;
            margin-right: 8px;
            color: #58a6ff; /* El azul resalta bien en ambos modos */
        }

        /* TARJETAS: Usamos variables nativas de Streamlit */
        div[data-testid="stMetric"] { 
            background-color: var(--secondary-background-color); 
            border: 1px solid var(--border-color); 
            padding: 15px; 
            border-radius: 12px; 
        }

        /* Texto de métricas adaptativo */
        div[data-testid="stMetricLabel"] { 
            color: var(--text-color) !important; 
            opacity: 0.8;
            font-weight: 600; 
        }
        div[data-testid="stMetricValue"] { 
            color: var(--text-color) !important; 
        }

        /* PESTAÑAS (TABS) ADAPTATIVAS */
        button[data-baseweb="tab"]:nth-child(1)::before {
            content: "analytics"; font-family: 'Material Symbols Outlined';
            margin-right: 8px; font-size: 20px;
        }
        button[data-baseweb="tab"]:nth-child(2)::before {
            content: "settings"; font-family: 'Material Symbols Outlined';
            margin-right: 8px; font-size: 20px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: var(--text-color);
            opacity: 0.7;
        }
        .stTabs [aria-selected="true"] { 
            opacity: 1 !important;
            color: #58a6ff !important; 
            border-bottom: 2px solid #58a6ff !important;
        }

        /* BOTÓN: Estilo estándar de éxito */
        .stButton>button { 
            background-color: #238636; 
            color: white !important; /* Siempre blanco porque el fondo es verde oscuro */
            border: none; border-radius: 6px; 
            height: 45px; font-weight: 600; width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE DATOS ---
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
        repo.update_file(FILE_PATH, "Sincronización", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "Creación DB", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
dias_transcurridos = (datetime.now() - FECHA_INICIO_CUCHUBAL).days
semanas_actuales = max(0, dias_transcurridos // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL
fondo_total = sum(datos.values())

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div style='text-align: center; padding-bottom: 20px;'>
        <h1 style='color: var(--text-color); margin-bottom: 5px;'>
            <span class="google-icon" style="font-size: 40px;">payments</span>
            Cuchubal Digital
        </h1>
        <p style='color: var(--text-color); opacity: 0.6;'>
            Semana {semanas_actuales} • Meta Individual: ${monto_esperado:.2f}
        </p>
    </div>
""", unsafe_allow_html=True)

st.metric("FONDO TOTAL ACUMULADO", f"${fondo_total:,.2f}")

tab1, tab2 = st.tabs(["ESTADO DE CUENTA", "GESTIÓN ADMIN"])

with tab1:
    st.write("")
    user = st.selectbox("Seleccionar integrante", ["-- Elegir --"] + NOMBRES)
    if user != "-- Elegir --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        st.markdown(f"### <span class='google-icon'>person</span> {user}", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Aportado", f"${total_u:.2f}")
        if dif >= 0:
            c2.metric("Balance", f"+${abs(dif):.2f}")
            st.success("Estás al día.")
        else:
            c2.metric("Balance", f"-${abs(dif):.2f}", delta_color="inverse")
            st.error(f"Pendiente. Debes ${abs(dif):.2f}")

with tab2:
    st.write("")
    if st.text_input("Llave de acceso", type="password") == PASSWORD_ADMIN:
        p_pago = st.selectbox("Integrante:", NOMBRES)
        m_pago = st.number_input("Monto:", min_value=0.0, step=2.50, value=2.50)
        if st.button("REGISTRAR PAGO"):
            datos[p_pago] += m_pago
            guardar_en_github(datos, archivo_sha)
            st.success("Sincronizado")
            st.rerun()
