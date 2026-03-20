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

st.set_page_config(page_title="Cuchubal Digital", page_icon="💳", layout="centered")

# --- ESTILO CSS CON GOOGLE ICONS ---
st.markdown("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Iconos */
    .material-symbols-outlined {
        vertical-align: middle;
        font-size: 24px;
        margin-right: 8px;
        color: #58a6ff;
    }

    /* Tarjetas */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 12px;
    }
    
    /* Botón */
    .stButton>button {
        background-color: #238636;
        color: white; border: none; border-radius: 6px;
        height: 45px; font-weight: 600; width: 100%;
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
fondo_total = sum(datos.values())

# --- INTERFAZ ---
st.markdown(f"""
    <div style='text-align: center;'>
        <h1 style='margin-bottom: 0;'>
            <span class="material-symbols-outlined" style="font-size: 45px;">account_balance</span>
            Cuchubal Digital
        </h1>
        <p style='color: #8b949e;'>Semana {semanas_actuales} • Meta: ${monto_esperado:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

st.metric("FONDO GLOBAL", f"${fondo_total:,.2f}")

tab1, tab2 = st.tabs(["ESTADO", "ADMIN"])

with tab1:
    st.write("")
    user = st.selectbox("Seleccionar integrante", ["--"] + NOMBRES)
    
    if user != "--":
        total_usuario = datos.get(user, 0.0)
        diferencia = total_usuario - monto_esperado
        
        st.markdown(f"### <span class='material-symbols-outlined'>person</span> {user}", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.metric("Aportado", f"${total_usuario:.2f}")
        
        if diferencia >= 0:
            c2.metric("Balance", f"+${abs(diferencia):.2f}")
            st.success(f"Estás al día. Adelanto: {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas.")
        else:
            c2.metric("Balance", f"-${abs(diferencia):.2f}", delta_color="inverse")
            st.error(f"Pendiente. Debes {int(abs(diferencia)/CUOTA_SEMANAL)} cuotas.")

with tab2:
    st.write("")
    pw = st.text_input("Contraseña", type="password", placeholder="••••")
    
    if pw == PASSWORD_ADMIN:
        st.markdown("---")
        p_pago = st.selectbox("Integrante", NOMBRES)
        m_pago = st.number_input("Monto a registrar", min_value=0.0, step=2.50, value=2.50)
        
        if st.button("REGISTRAR PAGO"):
            with st.spinner("Sincronizando..."):
                datos[p_pago] += m_pago
                guardar_en_github(datos, archivo_sha)
                st.success("¡Sincronizado!")
                st.rerun()
