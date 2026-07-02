import streamlit as st
import pandas as pd
import io
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

if "df" not in st.session_state:
    st.session_state.df = None
# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

# ----------------------------------------
# 1. MOTOR DE IMPORTACIÓN (Volvimos al que funcionaba)
# ----------------------------------------
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subir matriz de alumnos (.xlsx)", type=["xlsx"])
try:
    client = init_connection()
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    
    # Extraer el ID de la planilla de forma segura
    sheet_id = SHEET_URL.split("/d/")[1].split("/")[0]
    sheet = client.open_by_key(sheet_id).sheet1

# Botón para forzar el reseteo si querés subir un Excel nuevo
if st.sidebar.button("🔄 Cargar un archivo nuevo"):
    st.session_state.df = None
    st.rerun()
    # Función para obtener datos frescos
    def get_data():
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if "Clases a recuperar" not in df.columns:
            df["Clases a recuperar"] = 0
        df["Clases a recuperar"] = pd.to_numeric(df["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
        
        if "Ausencias Registradas" not in df.columns:
            df["Ausencias Registradas"] = ""
            
        return df.fillna("")

if uploaded_file is not None and st.session_state.df is None:
    df_temp = pd.read_excel(uploaded_file)
    
    # Limpieza inicial
    df_temp = df_temp.replace({np.nan: "", pd.NaT: ""})
    if "Clases a recuperar" not in df_temp.columns:
        df_temp["Clases a recuperar"] = 0
    df_temp["Clases a recuperar"] = pd.to_numeric(df_temp["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
    
    if "Ausencias Registradas" not in df_temp.columns:
        df_temp["Ausencias Registradas"] = ""
    # Cargar datos al iniciar
    if "df" not in st.session_state:
        st.session_state.df = get_data()

    # Función para guardar datos en Google Sheets
    def update_sheet(df_actualizado):
        df_limpio = df_actualizado.copy()
        df_limpio = df_limpio.replace({np.nan: "", pd.NaT: "", None: ""}).fillna("")
        df_limpio["Clases a recuperar"] = df_limpio["Clases a recuperar"].astype(int)

    st.session_state.df = df_temp.fillna("")
    st.sidebar.success("¡Base de datos cargada!")
        sheet.clear()
        sheet.update(values=[df_limpio.columns.values.tolist()] + df_limpio.values.tolist())

if st.session_state.df is not None:
    df = st.session_state.df

    # --- PESTAÑAS DE LA APP ---
@@ -48,7 +66,7 @@
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")

        # Buscador por nombre
        # 1. Buscador por nombre integrado
        search_query = st.sidebar.text_input("🔎 Buscar por Nombre:", placeholder="Escribí un nombre...")

        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
@@ -73,6 +91,10 @@
            st.subheader(f"📍 Resultados para: '{search_query}'")
        else:
            st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")
            
        if st.button("🔄 Refrescar Datos desde Google Sheets"):
            st.session_state.df = get_data()
            st.rerun()

        if filtered_df.empty:
            st.info("No se encontraron alumnos con estos filtros.")
@@ -108,12 +130,7 @@
                        fecha_falta = st.date_input("Fecha de la ausencia:", key=f"fecha_{index}")

                        if st.button("➕ Confirmar Falta", key=f"falta_{index}"):
                            try:
                                actual_val = int(st.session_state.df.at[index, "Clases a recuperar"])
                            except:
                                actual_val = 0
                                
                            st.session_state.df.at[index, "Clases a recuperar"] = actual_val + 1
                            st.session_state.df.at[index, "Clases a recuperar"] = recuperar + 1
                            fecha_str = fecha_falta.strftime("%d/%m/%Y")

                            hist = str(st.session_state.df.at[index, "Ausencias Registradas"])
@@ -122,6 +139,7 @@
                            else:
                                st.session_state.df.at[index, "Ausencias Registradas"] = hist + ", " + fecha_str

                            update_sheet(st.session_state.df)
                            st.rerun()

                        st.markdown("---")
@@ -134,6 +152,7 @@
                                    st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es {row['Grupo']}.")

                                st.session_state.df.at[index, "Clases a recuperar"] = recuperar - 1
                                update_sheet(st.session_state.df)
                                st.rerun()
                    st.markdown("---")

@@ -149,6 +168,7 @@
        grupo_vacante = col_v1.selectbox("¿De qué Nivel/Grupo es el espacio libre?", grupos_disponibles)
        sede_vacante = col_v2.selectbox("¿En qué sede?", ["Todas", "Palermo", "Nuñez"])

        # 2. Casilla para ignorar la fecha
        ignorar_fecha = st.checkbox("Ignorar fecha (Ver lista completa de deudores)")

        if not ignorar_fecha:
@@ -184,20 +204,5 @@ def esta_ausente_ese_dia(historial, fecha_buscar):
                with st.container():
                    st.markdown(f"🎾 **{suplente['Nombre del alumno']}** | Debe: **{int(suplente['Clases a recuperar'])} clase(s)** | Sede base: {suplente['Sede']}")

    # ----------------------------------------
    # DESCARGA DEL EXCEL ACTUALIZADO
    # ----------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("💾 Guardar Trabajo")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.df.to_excel(writer, index=False)
    
    st.sidebar.download_button(
        label="📥 Descargar Planilla Actualizada",
        data=buffer,
        file_name="Planilla_Alumnos_Actualizada.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.info("👋 ¡Hola! Subí la última versión de tu Excel para empezar.")
except Exception as e:
    st.error(f"Error técnico con Google Sheets: {e}")
