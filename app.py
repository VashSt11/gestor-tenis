import streamlit as st
import gspread

# --- CONEXIÓN DIRECTA ---
@st.cache_resource
def init_connection():
    # Usamos el método nativo de gspread para conectar desde el dict de secretos
    creds_dict = st.secrets["gcp_service_account"]
    client = gspread.service_account_from_dict(creds_dict)
    return client

try:
    client = init_connection()
    # Usamos el ID de tu planilla directamente
    sheet_id = "1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo"
    sheet = client.open_by_key(sheet_id).sheet1
    st.write("✅ Conexión establecida")
except Exception as e:
    st.error(f"Error de conexión: {e}")
