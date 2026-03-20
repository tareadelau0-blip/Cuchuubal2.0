import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- CONFIGURACIÓN INICIAL ---
archivo_datos = "datos_pagos.json"
PASSWORD_ADMIN = "1234"  # <--- Cambia esta contraseña
CUOTA_SEMANAL = 2.50
NOMBRES = ["Persona 1", "Persona 2", "Persona 3", "Persona 4", "Persona 5", "Persona 6"]

st.set_page_config(page_title="Control de Cuotas", page_icon="💰")

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    if os.path.exists(archivo_datos):
        with open(archivo_datos, "r") as f:
            return json.load(f)
    # Si no existe, inicializa a todos en 0
    return {nombre: 0.0 for nombre in NOMBRES}

def guardar_datos(datos):
    with open(archivo_datos, "w") as f:
        json.dump(datos, f)

datos = cargar_datos()

# --- INTERFAZ PÚBLICA (Para los 6 integrantes) ---
st.title("💰 Control de Aportaciones")
st.info("Cuota semanal: $2.50")

tab1, tab2 = st.tabs(["Consultar mi Estado", "Panel Administrador"])

with tab1:
    usuario = st.selectbox("Selecciona tu nombre:", ["-- Seleccionar --"] + NOMBRES)
    
    if usuario != "-- Seleccionar --":
        total_pagado = datos[usuario]
        # Cálculo de semanas (puedes ajustar la lógica de fecha si prefieres)
        semanas_pagadas = total_pagado / CUOTA_SEMANAL
        
        col1, col2 = st.columns(2)
        col1.metric("Total Aportado", f"${total_pagado:.2f}")
        col2.metric("Semanas Cubiertas", f"{semanas_pagadas:.2f}")
        
        st.divider()
        st.subheader(f"Fondo Global: ${sum(datos.values()):.2f}")

# --- PANEL DE ADMINISTRADOR (Para ti) ---
with tab2:
    pw = st.text_input("Contraseña de Admin", type="password")
    
    if pw == PASSWORD_ADMIN:
        st.success("Acceso concedido")
        st.subheader("Registrar Nuevo Pago")
        
        persona_pago = st.selectbox("¿Quién pagó?", NOMBRES, key="admin_sel")
        monto_nuevo = st.number_input("Monto a sumar ($)", min_value=0.0, step=2.50)
        
        if st.button("Registrar Pago"):
            datos[persona_pago] += monto_nuevo
            guardar_datos(datos)
            st.toast(f"¡Pago de {persona_pago} registrado!")
            st.rerun()
            
        st.divider()
        if st.button("Limpiar Base de Datos (Reset)", help="Pone todos los contadores a 0"):
            if st.checkbox("Confirmar reset total"):
                datos = {nombre: 0.0 for nombre in NOMBRES}
                guardar_datos(datos)
                st.rerun()
    elif pw != "":
        st.error("Contraseña incorrecta")
