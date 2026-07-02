import streamlit as st
import gspread

# Usamos service_account_from_dict que es más amigable
@st.cache_resource
def get_connection():
    # Convertimos los Secrets en un diccionario simple
    creds_dict = dict(st.secrets["gcp_service_account"])
    # gspread se encarga de procesar la clave
    client = gspread.service_account_from_dict(creds_dict)
    return client

try:
    client = get_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("¡Conexión establecida con éxito!")
except Exception as e:
    st.error(f"Error: {e}")
