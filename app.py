import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Diagnóstico de Conexión")
st.title("Diagnóstico de Conexión")

try:
    # 1. Verificar qué email está leyendo la app
    info = st.secrets["gcp_service_account"]
    email_que_usa_la_app = info["client_email"]
    st.write(f"### 1. La app está intentando conectar con este email:")
    st.code(email_que_usa_la_app)
    
    # 2. Intentar conectar
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 3. Intentar acceder
    sheet_id = "1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo"
    st.write(f"### 2. Intentando abrir planilla con ID: {sheet_id}")
    
    doc = client.open_by_key(sheet_id)
    st.success("✅ ¡CONEXIÓN EXITOSA! La app tiene acceso.")
    st.write("Si ves este mensaje, la conexión ya está reparada.")
    
except Exception as e:
    st.error("❌ FALLÓ LA CONEXIÓN")
    st.write(f"Error detallado: {e}")
    st.write("---")
    st.write("### PASOS A SEGUIR:")
    st.write("1. Copiá el email de arriba (el de la app).")
    st.write("2. Abrí tu planilla de Sheets.")
    st.write("3. Compartir > Pegar ese email > **Rol: Editor** > Enviar.")
    st.write("4. Si ya lo hiciste, asegurate de que NO haya espacios vacíos al copiar el email.")
