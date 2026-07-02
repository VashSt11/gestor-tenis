import streamlit as st
import gspread
import json
import os
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    # Leemos la variable de entorno que configuramos en Streamlit Cloud
    json_data = os.environ.get("GCP_CREDENTIALS_JSON")
    
    if not json_data:
        raise Exception("No se encontró la variable de entorno GCP_CREDENTIALS_JSON")
        
    creds_dict = json.loads(json_data)
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# Intentar conectar
try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conectado correctamente por Variable de Entorno!")
    
    # Aquí podés poner tu lógica de la app
    
except Exception as e:
    st.error(f"Error de conexión: {e}")
