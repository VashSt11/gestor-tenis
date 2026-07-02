import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# Limpiamos la caché a la fuerza para borrar errores viejos
st.cache_resource.clear()

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # --- CÓDIGO DE AUTOSANACIÓN DE LA CLAVE ---
    raw_key = creds_dict["private_key"]
    
    # 1. Buscamos todo lo que está entre el BEGIN y el END
    match = re.search(r'-----BEGIN PRIVATE KEY-----(.*?)-----END PRIVATE KEY-----', raw_key, flags=re.DOTALL)
    
    if match:
        # 2. Extraemos la clave, y borramos saltos de línea falsos, espacios o comillas
        b64_string = match.group(1)
        b64_string = b64_string.replace('\\n', '').replace('\n', '').replace(' ', '').replace('"', '')
        
        # 3. Reconstruimos la clave con la estructura PERFECTA
        perfect_key = f"-----BEGIN PRIVATE KEY-----\n{b64_string}\n-----END PRIVATE KEY-----\n"
        creds_dict["private_key"] = perfect_key
    else:
        # Respaldo por si se borraron los encabezados en los Secrets
        clean_key = raw_key.replace('\\n', '').replace('\n', '').replace(' ', '')
        creds_dict["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----\n"
    # ------------------------------------------

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Intentar conectar
try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conexión restaurada con éxito!")
    
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")
