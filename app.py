import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
FECHA_INICIO = datetime(2024, 3, 1) # Cambia a la fecha real de inicio
CUOTA_SEMANAL = 2.50
NOMBRES = ["Persona 1", "Persona 2", "Persona 3", "Persona 4", "Persona 5", "Persona 6"]

st.set_page_config(page_title="Control de Cuotas", layout="centered")

# Estilo para mantener profesionalismo
st.markdown("<h1 style='text-align: center;'>💰 Control de Aportaciones</h1>", unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
# En un entorno real, aquí leeríamos el CSV de GitHub o Google Sheets
# Por ahora simulamos los datos acumulados
datos_ejemplo = {
    "Nombre": NOMBRES,
    "Total_Pagado": [25.00, 30.00, 15.00, 25.00, 25.00, 27.50]
}
df = pd.DataFrame(datos_ejemplo)

# --- CÁLCULOS ---
semanas_transcurridas = (datetime.now() - FECHA_INICIO).days // 7
cuota_esperada = semanas_transcurridas * CUOTA_SEMANAL

# --- INTERFAZ DE USUARIO ---
user = st.selectbox("Selecciona tu nombre para consultar:", ["-- Seleccionar --"] + NOMBRES)

if user != "-- Seleccionar --":
    fila = df[df["Nombre"] == user].iloc[0]
    total_usuario = fila["Total_Pagado"]
    semanas_pagadas = total_usuario / CUOTA_SEMANAL
    diferencia = total_usuario - cuota_esperada

    st.divider()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Aportado", f"${total_usuario:.2f}")
    col2.metric("Semanas Pagadas", f"{semanas_pagadas:.1f}")
    
    # Lógica de Estatus
    if diferencia > 0:
        col3.success(f"Adelantado: ${diferencia:.2f}")
    elif diferencia < 0:
        col3.error(f"Debe: ${abs(diferencia):.2f}")
    else:
        col3.info("Al día")

st.divider()

# --- FONDO GLOBAL ---
fondo_total = df["Total_Pagado"].sum()
st.subheader(f"Fondo Global Acumulado: ${fondo_total:.2f}")

# Tabla general para transparencia (opcional)
if st.checkbox("Mostrar tabla de transparencia"):
    st.table(df)
