import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import textwrap

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")

# Limpiamos caché forzadamente
st.cache_resource.clear()

@st.cache_resource
def init_connection():
    # Tomamos los secretos tal cual están en tu panel
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # --- RECONSTRUCCIÓN MATEMÁTICA DE LA CLAVE PEM ---
    raw_key = creds_dict["private_key"]
    
    # 1. Quitamos los encabezados viejos para dejar solo la ensalada de letras (base64)
    clean_b64 = re.sub(r'-----[A-Z ]+-----', '', raw_key)
    
    # 2. Borramos TODO espacio, salto de línea o carácter invisible
    clean_b64 = re.sub(r'\s+', '', clean_b64)
    
    # 3. La librería exige renglones de exactamente 64 caracteres. Esto lo hace automático.
    wrapped_b64 = textwrap.fill(clean_b64, width=64)
    
    # 4. Volvemos a empaquetar la clave con los saltos de línea perfectos
    final_key = f"-----BEGIN PRIVATE KEY-----\n{wrapped_b64}\n-----END PRIVATE KEY-----\n"
    
    # Reemplazamos la clave rota por la perfecta
    creds_dict["private_key"] = final_key
    # ------------------------------------------------

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Ejecutamos la conexión
try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conexión restaurada con éxito! La base de datos está en línea.")
    
    # A partir de acá abajo volveremos a armar tu aplicación y el filtro de fechas
    # cuando estemos 100% seguros de que ves el cartel verde.
    
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")
