import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Configuración de página (siempre después de los imports)
st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    # Obtenemos los secretos
    creds_dict = dict(st.secrets["gcp_service_account"])
    # CORRECCIÓN CLAVE: Esto arregla el error "PEM file / InvalidKey"
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Intentar conectar
try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ Conectado a Google Sheets")
    
    # Aquí iría el resto de tu lógica...
    # (data = sheet.get_all_records(), etc.)
    
except Exception as e:
    st.error(f"Error de conexión: {e}")
