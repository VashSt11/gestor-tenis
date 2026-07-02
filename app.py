import streamlit as st
import gspread

@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Convertimos manualmente los \n que Streamlit lee como texto
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)
