import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds)

try:
    client = init_connection()
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    sheet = client.open_by_url(SHEET_URL).sheet1

    def get_data():
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if "Clases a recuperar" not in df.columns:
            df["Clases a recuperar"] = 0
        df["Clases a recuperar"] = pd.to_numeric(df["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
        
        if "Ausencias Registradas" not in df.columns:
            df["Ausencias Registradas"] = ""
        return df.fillna("")

    if "df" not in st.session_state:
        st.session_state.df = get_data()

    def update_sheet(df_actualizado):
        df_limpio = df_actualizado.copy().fillna("")
        df_limpio["Clases a recuperar"] = df_limpio["Clases a recuperar"].astype(int)
        sheet.clear()
        sheet.update([df_limpio.columns.values.tolist()] + df_limpio.values.tolist())

    df = st.session_state.df

    # --- PESTAÑAS DE LA APP ---
    tab_diario, tab_vacantes = st.tabs(["📅 Asistencias Diarias", "🔍 Buscar Suplente"])

    # ----------------------------------------
    # PESTAÑA 1: ASISTENCIAS DIARIAS
    # ----------------------------------------
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")
        
        search_query = st.sidebar.text_input("🔎 Buscar por Nombre:", "")
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        filtered_df = df.copy()
        
        if search_query:
            filtered_df = filtered_df[filtered_df["Nombre del alumno"].astype(str).str.contains(search_query, case=False, na=False)]
            
        if sede_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
        
        if dia_filter != "Todos":
            filtered_df = filtered_df[filtered_df[dia_filter].astype(str).str.strip() != ""]

        if search_query:
            st.subheader(f"📍 Resultados para: '{search_query}'")
        else:
            st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")
            
        if st.button("🔄 Refrescar Datos de la Nube"):
            st.cache_resource.clear() # Limpia el caché rebelde
            st.session_state.df = get_data()
            st.rerun()

        if filtered_df.empty:
            st.info("No se encontraron alumnos con estos filtros.")
        else:
            for index, row in filtered_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                    col1.write(f"**{row['Nombre del alumno']}**")
                    col1.caption(f"Grupo: {row['Grupo']}")
                    
                    if dia_filter != "Todos":
                        col2.write(f"🕒 {row[dia_filter]}")
                    else:
                        col2.write(f"📍 {row['Sede']}")
                        
                    recuperar = int(row['Clases a recuperar'])
                    col3.write(f"🔄 A recuperar: **{recuperar}**")
                    
                    with col4.expander("⚙️ Gestionar"):
                        historial = str(row.get("Ausencias Registradas", ""))
                        if historial.strip() != "":
                            st.markdown(f"**📅 Historial de Faltas:**\n`{historial}`")
                        else:
                            st.markdown("*No tiene faltas registradas.*")
                        
                        fecha_falta = st.date_input("Fecha de la ausencia:", key=f"f_{index}")
                        
                        if st.button("➕ Confirmar Falta", key=f"btn_f_{index}"):
                            st.session_state.df.at[index, "Clases a recuperar"] = recuperar + 1
                            f_str = fecha_falta.strftime("%d/%m/%Y")
                            
                            if historial.strip() == "":
                                st.session_state.df.at[index, "Ausencias Registradas"] = f_str
                            else:
                                st.session_state.df.at[index, "Ausencias Registradas"] = historial + ", " + f_str
                            
                            update_sheet(st.session_state.df)
                            st.rerun()
                        
                        st.markdown("---")
                        if st.button("➖ Ya recuperó 1 clase", key=f"btn_r_{index}"):
                            if recuperar > 0:
                                st.session_state.df.at[index, "Clases a recuperar"] = recuperar - 1
                                update_sheet(st.session_state.df)
                                st.rerun()
                    st.markdown("---")

    # ----------------------------------------
    # PESTAÑA 2: BUSCADOR DE SUPLENTES
    # ----------------------------------------
    with tab_vacantes:
        st.subheader("Buscador de Alumnos para Rellenar Vacantes")
        col_v1, col_v2, col_v3 = st.columns(3)
        grupos = ["Todos"] + sorted([g for g in df["Grupo"].dropna().unique() if str(g).strip() != ""])
        grupo_vac = col_v1.selectbox("¿Grupo libre?", grupos)
        sede_vac = col_v2.selectbox("¿En qué sede?", ["Todas", "Palermo", "Nuñez"])
        
        ignorar = st.checkbox("Ignorar fecha (Ver lista completa de deudores)")
        
        if not ignorar:
            fecha_vac = col_v3.date_input("¿Para qué fecha es la vacante?")
            fecha_vac_str = fecha_vac.strftime("%d/%m/%Y")
        
        st.write("---")
        
        df_deudores = df[df["Clases a recuperar"].astype(int) > 0]
        
        if grupo_vac != "Todos":
            df_deudores = df_deudores[df_deudores["Grupo"] == grupo_vac]
        if sede_vac != "Todas":
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vac]
            
        if not ignorar:
            df_suplentes = df_deudores[~df_deudores["Ausencias Registradas"].astype(str).str.contains(fecha_vac_str, na=False)]
        else:
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
