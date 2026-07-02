import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def init_connection():
    # Streamlit ya convierte el bloque [gcp_service_account] en un dict automáticamente
    creds_dict = st.secrets["gcp_service_account"]
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conectado correctamente!")
except Exception as e:
    st.error(f"Error de conexión: {e}")
