import streamlit as st
import pandas as pd
import json
from github import Github
from datetime import datetime
import time
import uuid

# --- 1. CONFIGURACIÓN ---
FECHA_INICIO_CUCHUBAL = datetime(2026, 2, 10) 
CUOTA_SEMANAL = 2.50
PASSWORD_ADMIN = "1234gboc" 
NOMBRES = sorted(["Ociel", "Jonathan", "Gisselle", "Sofia", "Cristopher", "Leslie"])

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "datos_pagos.json"

st.set_page_config(page_title="CUCHUBAL", page_icon="💳", layout="centered")

# --- 2. INICIALIZAR SESSION STATE ---
if "procesando_ingreso" not in st.session_state:
    st.session_state.procesando_ingreso = False
if "procesando_retiro" not in st.session_state:
    st.session_state.procesando_retiro = False
if "procesando_correccion" not in st.session_state:
    st.session_state.procesando_correccion = False
if "confirmacion_ingreso" not in st.session_state:
    st.session_state.confirmacion_ingreso = None
if "confirmacion_retiro" not in st.session_state:
    st.session_state.confirmacion_retiro = None
if "confirmacion_correccion" not in st.session_state:
    st.session_state.confirmacion_correccion = None

# --- 3. CSS: ESTILO INDUSTRIAL RECTO ---
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
        .stButton>button:disabled {
            opacity: 0.5; cursor: not-allowed;
        }
        .confirmacion-box {
            border: 2px solid #00d084; background-color: #00d08420; padding: 15px;
            border-radius: 0px; margin: 15px 0; font-weight: bold;
        }
        .anulacion-box {
            border: 2px solid #ff6b6b; background-color: #ff6b6b20; padding: 15px;
            border-radius: 0px; margin: 15px 0; font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. LÓGICA DE DATOS ---
g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)

def cargar_datos_github():
    try:
        contents = repo.get_contents(FILE_PATH)
        db = json.loads(contents.decoded_content.decode())
        # Inicializar claves si no existen
        if "lista_retiros" not in db:
            db["lista_retiros"] = []
        if "historial_movimientos" not in db:
            db["historial_movimientos"] = []
        for n in NOMBRES:
            if n not in db:
                db[n] = 0.0
        return db, contents.sha
    except:
        base = {nombre: 0.0 for nombre in NOMBRES}
        base["lista_retiros"] = []
        base["historial_movimientos"] = []
        return base, None

def guardar_en_github(nuevos_datos, sha):
    contenido_json = json.dumps(nuevos_datos, indent=4, ensure_ascii=False)
    if sha:
        repo.update_file(FILE_PATH, "UPDATE_SISTEMA", contenido_json, sha)
    else:
        repo.create_file(FILE_PATH, "INIT_SISTEMA", contenido_json)

datos, archivo_sha = cargar_datos_github()

# --- 5. CÁLCULOS ---
semanas_actuales = max(0, (datetime.now() - FECHA_INICIO_CUCHUBAL).days // 7)
monto_esperado = semanas_actuales * CUOTA_SEMANAL

total_ingresos = sum(datos[n] for n in NOMBRES)
total_retiros = sum(r['monto'] for r in datos["lista_retiros"])
fondo_neto = total_ingresos - total_retiros

# --- 6. INTERFAZ ---
st.markdown(f"""
    <div class="header-box">
        <h2 style='margin: 0;'>CONTROL DE CAJA CUCHUBAL</h2>
        <small>FECHA: {datetime.now().strftime('%d/%m/%Y')} | SEMANA: {semanas_actuales}</small>
    </div>
""", unsafe_allow_html=True)

col_m1, col_m2 = st.columns(2)
col_m1.metric("FONDO NETO DISPONIBLE", f"${fondo_neto:,.2f}")
col_m2.metric("TOTAL RETIRADO", f"${total_retiros:,.2f}", delta_color="inverse")

menu = st.radio(
    "MÓDULO:",
    ["CONSULTA DE SALDOS", "REGISTRO DE INGRESOS", "CORRECCIÓN DE PAGOS", "RETIRO DE CAJA", "HISTORIAL DE MOVIMIENTOS"],
    horizontal=True
)

st.write("---")

# ---------- CONSULTA ----------
if menu == "CONSULTA DE SALDOS":
    user = st.selectbox("INTEGRANTE:", ["-- SELECCIONAR --"] + NOMBRES)
    if user != "-- SELECCIONAR --":
        total_u = datos.get(user, 0.0)
        dif = total_u - monto_esperado
        st.markdown(f"### ESTADO: {user.upper()}")
        c1, c2 = st.columns(2)
        c1.metric("APORTADO", f"${total_u:.2f}")
        c2.metric("BALANCE", f"{'+' if dif >= 0 else ''}${dif:.2f}", delta_color="normal" if dif >= 0 else "inverse")
        if dif >= 0:
            st.success("SOLVENTE")
        else:
            st.error("PENDIENTE DE PAGO")

# ---------- REGISTRO DE INGRESOS ----------
elif menu == "REGISTRO DE INGRESOS":
    if st.text_input("PASSWORD:", type="password") == PASSWORD_ADMIN:
        p_pago = st.selectbox("PAGADOR:", NOMBRES)
        m_pago = st.number_input("MONTO ($):", min_value=0.0, step=2.50, value=2.50)
        concepto = st.text_input("CONCEPTO (opcional):", placeholder="Ej. Pago semanal")
        
        if st.button("REGISTRAR INGRESO", disabled=st.session_state.procesando_ingreso, key="btn_ingreso"):
            st.session_state.procesando_ingreso = True
            st.rerun()
        
        if st.session_state.procesando_ingreso:
            try:
                id_mov = str(uuid.uuid4())
                datos[p_pago] += m_pago
                datos["historial_movimientos"].append({
                    "id": id_mov,
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tipo": "INGRESO",
                    "persona": p_pago,
                    "monto": m_pago,
                    "concepto": concepto.strip() if concepto else "Pago registrado"
                })
                guardar_en_github(datos, archivo_sha)
                
                st.markdown(f"""
                    <div class="confirmacion-box">
                        ✓ PAGO REGISTRADO EXITOSAMENTE<br>
                        <small>
                            PAGADOR: {p_pago.upper()}<br>
                            MONTO: ${m_pago:.2f}<br>
                            CONCEPTO: {concepto.strip() if concepto else 'Pago registrado'}<br>
                            HORA: {datetime.now().strftime('%H:%M:%S')}
                        </small>
                    </div>
                """, unsafe_allow_html=True)
                
                st.session_state.confirmacion_ingreso = {
                    "pagador": p_pago,
                    "monto": m_pago,
                    "concepto": concepto.strip() if concepto else "Pago registrado",
                    "hora": datetime.now().strftime('%H:%M:%S')
                }
                
                time.sleep(2)
                st.session_state.procesando_ingreso = False
                st.rerun()
                
            except Exception as e:
                st.error(f"ERROR AL GUARDAR: {str(e)}")
                st.session_state.procesando_ingreso = False
        
        if st.session_state.confirmacion_ingreso and not st.session_state.procesando_ingreso:
            conf = st.session_state.confirmacion_ingreso
            st.markdown(f"""
                <div class="confirmacion-box">
                    ✓ ÚLTIMO PAGO REGISTRADO<br>
                    <small>
                        PAGADOR: {conf['pagador'].upper()}<br>
                        MONTO: ${conf['monto']:.2f}<br>
                        CONCEPTO: {conf['concepto']}<br>
                        HORA: {conf['hora']}
                    </small>
                </div>
            """, unsafe_allow_html=True)

# ---------- CORRECCIÓN DE PAGOS ----------
elif menu == "CORRECCIÓN DE PAGOS":
    if st.text_input("PASSWORD ADMIN:", type="password") == PASSWORD_ADMIN:
        st.markdown("#### CORRECCIÓN DE PAGO ERRÓNEO")
        
        # Mostrar últimos ingresos
        ingresos = [m for m in datos["historial_movimientos"] if m["tipo"] == "INGRESO"]
        if ingresos:
            st.subheader("Últimos ingresos registrados:")
            ingresos_ordenados = sorted(ingresos, key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y %H:%M"), reverse=True)
            df_ing = pd.DataFrame(ingresos_ordenados[:20])
            st.table(df_ing)
        
        st.write("---")
        st.markdown("#### Seleccione el ingreso a anular:")
        
        # Crear opciones para desplegable
        if ingresos:
            opciones = []
            for mov in ingresos:
                opciones.append(f"{mov['fecha']} | {mov['persona']} | ${mov['monto']:.2f} | {mov['concepto']}")
            seleccion = st.selectbox("MOVIMIENTO A ANULAR:", opciones)
            idx_seleccionado = opciones.index(seleccion) if seleccion else 0
            mov_anular = ingresos[idx_seleccionado]
            
            st.markdown(f"""
                **DETALLES DEL MOVIMIENTO SELECCIONADO:**  
                - Fecha: {mov_anular['fecha']}  
                - Persona: {mov_anular['persona']}  
                - Monto: ${mov_anular['monto']:.2f}  
                - Concepto: {mov_anular['concepto']}
            """)
            
            st.write("---")
            st.markdown("#### Ingrese los datos correctos:")
            
            col1, col2 = st.columns(2)
            with col1:
                persona_correcta = st.selectbox("PERSONA CORRECTA:", NOMBRES)
            with col2:
                monto_correcto = st.number_input("MONTO CORRECTO ($):", min_value=0.0, step=0.10, value=mov_anular['monto'])
            
            motivo_correccion = st.text_input("MOTIVO DE LA CORRECCIÓN:")
            
            if st.button("CONFIRMAR CORRECCIÓN", disabled=st.session_state.procesando_correccion, key="btn_correccion"):
                # Validaciones
                if monto_correcto <= 0:
                    st.error("ERROR: INGRESE UN MONTO VÁLIDO.")
                elif persona_correcta == mov_anular['persona'] and monto_correcto == mov_anular['monto']:
                    st.error("ERROR: LOS DATOS CORRECTOS SON IGUALES AL ORIGINAL. NO HAY NADA QUE CORREGIR.")
                elif not motivo_correccion:
                    st.warning("DEBE ESPECIFICAR UN MOTIVO.")
                else:
                    st.session_state.procesando_correccion = True
                    st.rerun()
            
            if st.session_state.procesando_correccion:
                if monto_correcto <= 0:
                    st.error("ERROR: INGRESE UN MONTO VÁLIDO.")
                    st.session_state.procesando_correccion = False
                elif persona_correcta == mov_anular['persona'] and monto_correcto == mov_anular['monto']:
                    st.error("ERROR: LOS DATOS CORRECTOS SON IGUALES AL ORIGINAL.")
                    st.session_state.procesando_correccion = False
                elif not motivo_correccion:
                    st.warning("DEBE ESPECIFICAR UN MOTIVO.")
                    st.session_state.procesando_correccion = False
                else:
                    try:
                        # 1. Anular el movimiento original
                        id_anular = mov_anular['id']
                        persona_errada = mov_anular['persona']
                        monto_errado = mov_anular['monto']
                        
                        # Restar el monto de la persona errada
                        datos[persona_errada] -= monto_errado
                        
                        # Eliminar el movimiento original del historial
                        for i, m in enumerate(datos["historial_movimientos"]):
                            if m.get("id") == id_anular:
                                del datos["historial_movimientos"][i]
                                break
                        
                        # Registrar ANULACIÓN en el historial (trazabilidad)
                        datos["historial_movimientos"].append({
                            "id": str(uuid.uuid4()),
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tipo": "ANULACIÓN",
                            "persona": persona_errada,
                            "monto": -monto_errado,
                            "concepto": f"ANULADO - {motivo_correccion.upper()}"
                        })
                        
                        # 2. Registrar el nuevo ingreso correcto
                        datos[persona_correcta] += monto_correcto
                        datos["historial_movimientos"].append({
                            "id": str(uuid.uuid4()),
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "tipo": "INGRESO",
                            "persona": persona_correcta,
                            "monto": monto_correcto,
                            "concepto": f"CORRECCIÓN - {motivo_correccion.upper()}"
                        })
                        
                        guardar_en_github(datos, archivo_sha)
                        
                        st.markdown(f"""
                            <div class="confirmacion-box">
                                ✓ CORRECCIÓN REALIZADA EXITOSAMENTE<br>
                                <small>
                                    ANULACIÓN: -${monto_errado:.2f} a {persona_errada.upper()}<br>
                                    NUEVO INGRESO: +${monto_correcto:.2f} a {persona_correcta.upper()}<br>
                                    MOTIVO: {motivo_correccion.upper()}<br>
                                    HORA: {datetime.now().strftime('%H:%M:%S')}
                                </small>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.confirmacion_correccion = {
                            "persona_errada": persona_errada,
                            "monto_errado": monto_errado,
                            "persona_correcta": persona_correcta,
                            "monto_correcto": monto_correcto,
                            "motivo": motivo_correccion,
                            "hora": datetime.now().strftime('%H:%M:%S')
                        }
                        
                        time.sleep(2)
                        st.session_state.procesando_correccion = False
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"ERROR AL GUARDAR: {str(e)}")
                        st.session_state.procesando_correccion = False
            
            if st.session_state.confirmacion_correccion and not st.session_state.procesando_correccion:
                conf = st.session_state.confirmacion_correccion
                st.markdown(f"""
                    <div class="confirmacion-box">
                        ✓ ÚLTIMA CORRECCIÓN REALIZADA<br>
                        <small>
                            ANULACIÓN: -${conf['monto_errado']:.2f} de {conf['persona_errada'].upper()}<br>
                            INGRESO CORRECTO: +${conf['monto_correcto']:.2f} a {conf['persona_correcta'].upper()}<br>
                            MOTIVO: {conf['motivo'].upper()}<br>
                            HORA: {conf['hora']}
                        </small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay ingresos registrados para corregir.")

# ---------- RETIRO DE CAJA ----------
elif menu == "RETIRO DE CAJA":
    if st.text_input("PASSWORD ADMIN:", type="password") == PASSWORD_ADMIN:
        st.markdown("#### NUEVO RETIRO DE EFECTIVO")
        m_retiro = st.number_input("CANTIDAD A RETIRAR ($):", min_value=0.0, step=1.0)
        motivo = st.text_input("CONCEPTO / POR QUÉ:")
        
        if st.button("CONFIRMAR SALIDA DE DINERO", disabled=st.session_state.procesando_retiro, key="btn_retiro"):
            if m_retiro <= 0:
                st.error("ERROR: INGRESE UN MONTO VÁLIDO.")
            elif m_retiro > fondo_neto:
                st.error("ERROR: NO HAY SUFICIENTE DINERO EN CAJA.")
            elif not motivo:
                st.warning("DEBE ESPECIFICAR UN MOTIVO.")
            else:
                st.session_state.procesando_retiro = True
                st.rerun()
        
        if st.session_state.procesando_retiro:
            if m_retiro <= 0:
                st.error("ERROR: INGRESE UN MONTO VÁLIDO.")
                st.session_state.procesando_retiro = False
            elif m_retiro > fondo_neto:
                st.error("ERROR: NO HAY SUFICIENTE DINERO EN CAJA.")
                st.session_state.procesando_retiro = False
            elif not motivo:
                st.warning("DEBE ESPECIFICAR UN MOTIVO.")
                st.session_state.procesando_retiro = False
            else:
                try:
                    id_mov = str(uuid.uuid4())
                    nuevo_retiro = {
                        "id": id_mov,
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "monto": m_retiro,
                        "motivo": motivo.upper()
                    }
                    datos["lista_retiros"].append(nuevo_retiro)
                    datos["historial_movimientos"].append({
                        "id": id_mov,
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "tipo": "RETIRO",
                        "persona": None,
                        "monto": m_retiro,
                        "concepto": motivo.upper()
                    })
                    guardar_en_github(datos, archivo_sha)
                    
                    st.markdown(f"""
                        <div class="confirmacion-box">
                            ✓ RETIRO REGISTRADO EXITOSAMENTE<br>
                            <small>
                                MONTO: ${m_retiro:.2f}<br>
                                CONCEPTO: {motivo.upper()}<br>
                                FECHA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                            </small>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.confirmacion_retiro = {
                        "monto": m_retiro,
                        "motivo": motivo.upper(),
                        "fecha": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    }
                    
                    time.sleep(2)
                    st.session_state.procesando_retiro = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"ERROR AL GUARDAR: {str(e)}")
                    st.session_state.procesando_retiro = False
        
        if st.session_state.confirmacion_retiro and not st.session_state.procesando_retiro:
            conf = st.session_state.confirmacion_retiro
            st.markdown(f"""
                <div class="confirmacion-box">
                    ✓ ÚLTIMO RETIRO REGISTRADO<br>
                    <small>
                        MONTO: ${conf['monto']:.2f}<br>
                        CONCEPTO: {conf['motivo']}<br>
                        FECHA: {conf['fecha']}
                    </small>
                </div>
            """, unsafe_allow_html=True)
        
        if datos["lista_retiros"]:
            st.write("---")
            st.markdown("#### HISTORIAL DE RETIROS")
            df_retiros = pd.DataFrame(datos["lista_retiros"])
            st.table(df_retiros.iloc[::-1])

# ---------- HISTORIAL DE MOVIMIENTOS ----------
elif menu == "HISTORIAL DE MOVIMIENTOS":
    st.markdown("### REGISTRO COMPLETO DE MOVIMIENTOS")
    if not datos["historial_movimientos"]:
        st.info("No hay movimientos registrados aún.")
    else:
        historial = sorted(datos["historial_movimientos"], key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y %H:%M"), reverse=True)
        df_hist = pd.DataFrame(historial)
        df_hist.rename(columns={
            "fecha": "Fecha/Hora",
            "tipo": "Tipo",
            "persona": "Persona",
            "monto": "Monto ($)",
            "concepto": "Concepto"
        }, inplace=True)
        st.table(df_hist)
