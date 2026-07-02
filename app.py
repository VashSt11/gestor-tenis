import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    # Leemos la variable directamente desde los secrets de Streamlit
    json_str = st.secrets["GCP_CREDENTIALS_JSON"]
    
    # Convertimos el string a diccionario real
    creds_dict = json.loads(json_str)
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    # Conectamos
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conexión exitosa!")
    
except Exception as e:
    st.error(f"Error de conexión: {e}")
