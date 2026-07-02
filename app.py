import streamlit as st
import gspread
import json
import base64
import os
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")

@st.cache_resource
def init_connection():
    # Leemos la variable en Base64
    b64_data = os.environ.get("GCP_JSON_B64")
    if not b64_data:
        raise Exception("No se encontró la variable GCP_JSON_B64")
    
    # Decodificamos de vuelta a JSON
    json_data = base64.b64decode(b64_data).decode()
    creds_dict = json.loads(json_data)
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    # Usamos tu ID de planilla
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conectado correctamente via Base64!")
except Exception as e:
    st.error(f"Error técnico: {e}")
