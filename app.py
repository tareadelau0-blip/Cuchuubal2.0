import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Estos datos los pondrás en "Settings > Secrets" de Streamlit Cloud
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"] # Ejemplo: "tu_usuario/tu_repositorio"
FILE_PATH = "datos_pagos.json"
PASSWORD_ADMIN = "1234" 
NOMBRES = ["Persona 1", "Persona 2", "Persona 3", "Persona 4", "Persona 5", "Persona 6"]

st.set_page_config(page_title="Control de Pagos Seguro", page_icon="💾")

# --- CONEXIÓN CON GITHUB ---
g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

def cargar_datos_github():
    try:
        contents = repo.get_contents(FILE_PATH)
        return json.loads(contents.decoded_content.decode()), contents.sha
    except:
        # Si el archivo no existe, crea uno inicial
        datos_iniciales = {nombre: 0.0 for nombre in NOMBRES}
        return datos_iniciales, None

def guardar_en_github(nuevos_datos, sha):
    contenido_json = json.dumps(nuevos_datos, indent=4)
    if sha:
        repo.update_file(FILE_PATH, "Actualización de pagos", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "Creación de archivo de pagos", contenido_json)

# Cargar datos al iniciar
datos, archivo_sha = cargar_datos_github()

# --- INTERFAZ ---
st.title("💰 Sistema de Pagos (Respaldo en GitHub)")

tab1, tab2 = st.tabs(["Consultar mi Estado", "Administración"])

with tab1:
    user = st.selectbox("Selecciona tu nombre:", ["--"] + NOMBRES)
    if user != "--":
        total = datos.get(user, 0.0)
        st.metric(label=f"Aportado por {user}", value=f"${total:.2f}")
        st.write(f"Semanas equivalentes: {total/2.5:.2f}")

with tab2:
    pw = st.text_input("Contraseña", type="password")
    if pw == PASSWORD_ADMIN:
        persona = st.selectbox("Registrar pago para:", NOMBRES)
        monto = st.number_input("Cantidad ($)", step=2.50)
        
        if st.button("Confirmar y Sincronizar con GitHub"):
            datos[persona] += monto
            guardar_en_github(datos, archivo_sha)
            st.success(f"¡Datos guardados en GitHub para {persona}!")
            st.rerun()
