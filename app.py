import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="Gestor de Tenis", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 2. CARGA DE DATOS POR PESTAÑA ---
@st.cache_data(ttl=600)
def load_worksheet(nombre_pestana):
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
    # Abrimos la pestaña específica por su nombre
    worksheet = sheet.worksheet(nombre_pestana)
    return pd.DataFrame(worksheet.get_all_records())

try:
    # --- 3. DISEÑO DE LA APP CON PESTAÑAS ---
    tab1, tab2 = st.tabs(["📋 Padrón de Alumnos", "📅 Registro de Asistencias"])
    
    # ----------------------------------------
    # PESTAÑA 1: PADRÓN (Tu grilla original)
    # ----------------------------------------
    with tab1:
        st.subheader("Grilla General y Horarios")
        df_alumnos = load_worksheet("Alumnos")
        st.dataframe(df_alumnos, use_container_width=True, hide_index=True)
        
    # ----------------------------------------
    # PESTAÑA 2: ASISTENCIAS (Con el filtro de fechas)
    # ----------------------------------------
    with tab2:
        st.subheader("Filtro Histórico de Clases")
        df_asistencias = load_worksheet("Asistencias")
        
        columna_fecha = "Fecha"
        
        if columna_fecha in df_asistencias.columns and not df_asistencias.empty:
            # Convertimos la columna a fecha matemática
            df_asistencias[columna_fecha] = pd.to_datetime(df_asistencias[columna_fecha], dayfirst=True, errors='coerce')
            
            # Selector de fechas
            rango_fechas = st.date_input(
                "Filtrar por rango de fechas (Inicio - Fin):",
                value=[], 
                format="DD/MM/YYYY"
            )
            
            # Lógica del filtro
            if len(rango_fechas) == 2:
                inicio, fin = rango_fechas
                inicio = pd.to_datetime(inicio)
                fin = pd.to_datetime(fin)
                
                mask = (df_asistencias[columna_fecha] >= inicio) & (df_asistencias[columna_fecha] <= fin)
                df_mostrar = df_asistencias.loc[mask].copy()
            else:
                df_mostrar = df_asistencias.copy()
                
            # Formateamos la fecha para que se vea linda en la tabla ("02/07/2026")
            df_mostrar[columna_fecha] = df_mostrar[columna_fecha].dt.strftime('%d/%m/%Y')
            
            # Mostramos resultados
            st.metric(label="Clases dictadas en este período", value=len(df_mostrar))
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
        else:
            st.info("Aún no hay registros de fechas cargados en la pestaña 'Asistencias' o falta la columna 'Fecha'.")
            st.dataframe(df_asistencias, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
