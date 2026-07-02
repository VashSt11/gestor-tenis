import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Limpieza de saltos de línea para evitar el error de PEM
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 2. CARGA DE DATOS ---
# Usamos caché para que no cargue la planilla desde cero en cada clic (TTL de 10 min)
@st.cache_data(ttl=600)
def load_data():
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    # Traemos todo y lo convertimos a un DataFrame de Pandas
    datos = sheet.get_all_records()
    return pd.DataFrame(datos)

try:
    df = load_data()
    
    # --- 3. FILTRO DE FECHAS ---
    st.divider()
    st.subheader("🔍 Filtro de Registros")
    
    # IMPORTANTE: Cambiá "Fecha" por el nombre exacto de la columna en tu planilla
    columna_fecha = "Fecha" 
    
    if columna_fecha in df.columns:
        # Convertimos la columna a formato fecha (asumiendo formato Día/Mes/Año)
        df[columna_fecha] = pd.to_datetime(df[columna_fecha], dayfirst=True, errors='coerce')
        
        # Filtro en la pantalla
        rango_fechas = st.date_input(
            "Seleccioná un rango (Inicio - Fin):",
            value=[], # Empieza vacío
            format="DD/MM/YYYY"
        )
        
        # Aplicamos el filtro solo si el usuario seleccionó dos fechas
        if len(rango_fechas) == 2:
            inicio, fin = rango_fechas
            # Convertimos a datetime para poder comparar
            inicio = pd.to_datetime(inicio)
            fin = pd.to_datetime(fin)
            
            # Filtramos la tabla
            mask = (df[columna_fecha] >= inicio) & (df[columna_fecha] <= fin)
            df_mostrar = df.loc[mask].copy()
        else:
            # Si no hay filtro, mostramos todo
            df_mostrar = df.copy()
            
        # Volvemos a poner la fecha en un formato lindo para la tabla
        df_mostrar[columna_fecha] = df_mostrar[columna_fecha].dt.strftime('%d/%m/%Y')
        
    else:
        st.warning(f"No se encontró la columna '{columna_fecha}' en tu planilla. Mostrando tabla sin filtro.")
        df_mostrar = df.copy()

    # --- 4. MOSTRAR LA TABLA ---
    st.metric(label="Total de registros visibles", value=len(df_mostrar))
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    
except Exception as e:
    st.error(f"Error al cargar la aplicación: {e}")
