import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Diagnóstico de Conexión")

try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    
    # Intentar abrir por clave directa
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
    st.success("✅ ¡CONEXIÓN EXITOSA! El archivo fue encontrado.")
    
    # Intentar leer una celda
    val = sheet.sheet1.acell('A1').value
    st.write(f"Contenido de celda A1: {val}")

except Exception as e:
    st.error(f"FALLO DE CONEXIÓN: {e}")
    st.write("Si el error es 'PermissionError', el correo de servicio NO tiene permiso de Editor en la planilla.")
