import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_connection():
    # Cargamos el JSON string y lo convertimos a diccionario
    creds_dict = json.loads(st.secrets["GCP_CREDENTIALS"])
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    # Conectamos
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡CONEXIÓN EXITOSA!")
except Exception as e:
    st.error(f"Error: {e}")
