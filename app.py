import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Esta línea previene cualquier problema con los saltos de línea de Streamlit
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
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
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")
