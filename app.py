import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Forzamos la limpieza de caché para eliminar los errores viejos
st.cache_resource.clear()

@st.cache_resource
def init_connection():
    # Volvemos a la lectura estándar
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    # Esta línea asegura que la clave se lea bien, pase lo que pase
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Volvimos a conectar!")
except Exception as e:
    st.error(f"Error: {e}")
