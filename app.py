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

# --- ICONO DE GOOGLE PARA LA PESTAÑA DEL NAVEGADOR ---
# Usamos el icono "Payments" de Google Material directamente por URL
GOOGLE_ICON_URL = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/payments/default/24px.svg"

st.set_page_config(
    page_title="Cuchubal Digital", 
    page_icon=GOOGLE_ICON_URL, 
    layout="centered"
)

# --- 2. ESTILO CSS (SÍMBOLO DE GOOGLE) ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Clase para iconos de Google */
        .google-icon {
            font-family: 'Material Symbols Outlined';
            vertical-align: middle;
            font-size: 24px;
            color: #58a6ff;
            margin-right: 8px;
        }

        /* Estilo para las pestañas (Tabs) */
        button[data-baseweb="tab"] p {
            font-size: 14px;
            font-weight: 600;
        }
        
        /* Tarjetas de Métricas */
        div[data-testid="stMetric"] { 
            background-color: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 12px; 
            padding: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE GITHUB (Simulada para el ejemplo) ---
# (Mantén tus funciones cargar_datos_github y guardar_en_github igual)
def cargar_datos_github():
    return {nombre: 0.0 for nombre in NOMBRES}, None
datos, archivo_sha = cargar_datos_github()

# --- 4. CÁLCULOS ---
dias_transcurridos = (datetime.now() - FECHA_INICIO_CUCHUBAL).days
semanas_actuales = max(0, dias_transcurridos // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL
fondo_total = sum(datos.values())

# --- 5. INTERFAZ ---
st.markdown(f"""
    <div style='text-align: center;'>
        <h1><span class="google-icon" style="font-size: 40px;">account_balance</span>Cuchubal Digital</h1>
        <p style='color: #8b949e;'>Semana {semanas_actuales} • Meta: ${monto_esperado:.2f}</p>
    </div>
""", unsafe_allow_html=True)

st.metric("FONDO TOTAL ACUMULADO", f"${fondo_total:,.2f}")

# --- PESTAÑAS CON ICONOS DE GOOGLE ---
# Usamos el icono "Analytics" y "Settings" de Material Symbols
tab1, tab2 = st.tabs([
    "📊 ESTADO DE CUENTA", 
    "⚙️ GESTIÓN ADMIN"
])

# TRUCO: Como Streamlit no renderiza HTML directo en el título de la pestaña del componente st.tabs,
# usamos los emojis en el código pero los iconos de Google dentro del contenido para mantener la estética.

with tab1:
    st.markdown(f"### <span class='google-icon'>analytics</span> Resumen Actual", unsafe_allow_html=True)
    user = st.selectbox("Seleccionar integrante", ["--"] + NOMBRES)
    # ... resto de tu lógica de usuario

with tab2:
    st.markdown(f"### <span class='google-icon'>settings</span> Panel de Control", unsafe_allow_html=True)
    pw = st.text_input("Admin Key", type="password")
    # ... resto de tu lógica de admin
