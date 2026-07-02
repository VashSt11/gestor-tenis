import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_connection():
    # Convertimos el dict de secretos en un dict normal de Python
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # FORZAMOS LA CORRECCIÓN DE LA CLAVE
    # Si hay caracteres escapados, los limpiamos y convertimos a saltos de línea reales
    key = creds_dict["private_key"]
    if isinstance(key, str):
        # Reemplazamos cualquier cosa que parezca un salto de línea falso por uno real
        key = key.replace("\\n", "\n")
        creds_dict["private_key"] = key
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conectado correctamente!")
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")
