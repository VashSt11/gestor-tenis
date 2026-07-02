import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- DIAGNÓSTICO DE CONEXIÓN ---
st.set_page_config(page_title="Diagnóstico")
st.title("Diagnóstico de Conexión")

try:
    # Carga de credenciales desde Secrets
    info = st.secrets["gcp_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Intentar crear las credenciales
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    st.write("✅ Credenciales cargadas correctamente.")
    
    # Intentar autorizar
    client = gspread.authorize(creds)
    st.write("✅ Autorización de gspread exitosa.")
    
    # Intentar abrir la hoja
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
    st.success("🎉 ¡CONEXIÓN EXITOSA!")

except Exception as e:
    st.error(f"FALLO DE CONEXIÓN: {e}")
