import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS (LA QUE YA TE FUNCIONABA) ---
# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    scopes = [
@@ -21,8 +21,8 @@

try:
    client = init_connection()
    # Usamos el ID fijo para que no falle
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    sheet = client.open_by_url(SHEET_URL).sheet1

    def get_data():
        data = sheet.get_all_records()
@@ -39,7 +39,7 @@
        st.session_state.df = get_data()

    def update_sheet(df_actualizado):
        df_limpio = df_actualizado.fillna("").copy()
        df_limpio = df_actualizado.copy().fillna("")
        df_limpio["Clases a recuperar"] = df_limpio["Clases a recuperar"].astype(int)
        sheet.clear()
        sheet.update([df_limpio.columns.values.tolist()] + df_limpio.values.tolist())
@@ -55,15 +55,12 @@
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")

        # 1. EL BUSCADOR POR NOMBRE
        search_query = st.sidebar.text_input("🔎 Buscar por Nombre:", "")
        
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        filtered_df = df.copy()

        # Aplicar el filtro de búsqueda de forma segura
        if search_query:
            filtered_df = filtered_df[filtered_df["Nombre del alumno"].astype(str).str.contains(search_query, case=False, na=False)]

@@ -79,6 +76,7 @@
            st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")

        if st.button("🔄 Refrescar Datos de la Nube"):
            st.cache_resource.clear() # Limpia el caché rebelde
            st.session_state.df = get_data()
            st.rerun()

@@ -88,7 +86,6 @@
            for index, row in filtered_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                    
                    col1.write(f"**{row['Nombre del alumno']}**")
                    col1.caption(f"Grupo: {row['Grupo']}")

@@ -122,7 +119,6 @@
                            st.rerun()

                        st.markdown("---")
                        
                        if st.button("➖ Ya recuperó 1 clase", key=f"btn_r_{index}"):
                            if recuperar > 0:
                                st.session_state.df.at[index, "Clases a recuperar"] = recuperar - 1
@@ -135,13 +131,11 @@
    # ----------------------------------------
    with tab_vacantes:
        st.subheader("Buscador de Alumnos para Rellenar Vacantes")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        grupos = ["Todos"] + sorted([g for g in df["Grupo"].dropna().unique() if str(g).strip() != ""])
        grupo_vac = col_v1.selectbox("¿Grupo libre?", grupos)
        sede_vac = col_v2.selectbox("¿En qué sede?", ["Todas", "Palermo", "Nuñez"])

        # 2. EL CHECKBOX PARA VER LA LISTA COMPLETA
        ignorar = st.checkbox("Ignorar fecha (Ver lista completa de deudores)")

        if not ignorar:
@@ -158,19 +152,17 @@
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vac]

        if not ignorar:
            # Filtra a los que avisaron que faltan ese día
            df_suplentes = df_deudores[~df_deudores["Ausencias Registradas"].astype(str).str.contains(fecha_vac_str, na=False)]
        else:
            # Trae a todos los deudores directo
            df_suplentes = df_deudores

        if df_suplentes.empty:
            st.success("✅ No hay alumnos compatibles que deban clases con estos filtros.")
        else:
            st.warning(f"🎯 Encontramos **{len(df_suplentes)}** alumno/s disponibles:")
            for idx, suplente in df_suplentes.iterrows():
                with st.container():
                    st.markdown(f"🎾 **{suplente['Nombre del alumno']}** | Debe: **{int(suplente['Clases a recuperar'])}** | Sede: {suplente['Sede']}")

except Exception as e:
    st.error(f"Error técnico: {e}")
