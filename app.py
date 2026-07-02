import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CONEXIÓN A GOOGLE SHEETS MEJORADA ---
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    SHEET_URL = st.secrets["SPREADSHEET_URL"]
    
    # Extraer el ID de la planilla de forma segura
    sheet_id = SHEET_URL.split("/d/")[1].split("/")[0]
    sheet = client.open_by_key(sheet_id).sheet1

    # Función para obtener datos frescos
    def get_data():
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if "Clases a recuperar" not in df.columns:
            df["Clases a recuperar"] = 0
        df["Clases a recuperar"] = pd.to_numeric(df["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
        
        if "Ausencias Registradas" not in df.columns:
            df["Ausencias Registradas"] = ""
        return df

    # Cargar datos al iniciar
    if "df" not in st.session_state:
        st.session_state.df = get_data()

    # Función para guardar datos en Google Sheets
    def update_sheet(df_actualizado):
        df_limpio = df_actualizado.fillna("")
        sheet.clear()
        sheet.update(values=[df_limpio.columns.values.tolist()] + df_limpio.values.tolist())

    df = st.session_state.df

    # --- PESTAÑAS DE LA APP ---
    tab_diario, tab_vacantes = st.tabs(["📅 Asistencias Diarias", "🔍 Buscar Suplente"])

    # ----------------------------------------
    # PESTAÑA 1: ASISTENCIAS DIARIAS
    # ----------------------------------------
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")
        
        # NUEVO: Buscador por nombre
        search_query = st.sidebar.text_input("🔎 Buscar por Nombre:", placeholder="Escribí un nombre...")
        
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        filtered_df = df.copy()
        
        # Aplicar búsqueda por nombre primero (si hay texto)
        if search_query.strip():
            filtered_df = filtered_df[filtered_df["Nombre del alumno"].str.contains(search_query, case=False, na=False)]
            
        if sede_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
        
        if dia_filter != "Todos":
            filtered_df = filtered_df[filtered_df[dia_filter].notna() & (filtered_df[dia_filter] != "")]

        if search_query.strip():
            st.subheader(f"📍 Resultados para: '{search_query}'")
        else:
            st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")
            
        if st.button("🔄 Refrescar Datos desde Google Sheets"):
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
                        historial_actual = str(row.get("Ausencias Registradas", ""))
                        if historial_actual != "nan" and historial_actual.strip() != "":
                            st.markdown(f"**📅 Historial de Faltas:**\n\n`{historial_actual}`")
                        else:
                            st.markdown("*No tiene faltas registradas.*")
                        st.markdown("---")

                        st.write("**Registrar Ausencia**")
                        fecha_falta = st.date_input("Fecha de la ausencia:", key=f"fecha_{index}")
                        
                        if st.button("➕ Confirmar Falta", key=f"falta_{index}"):
                            st.session_state.df.at[index, "Clases a recuperar"] += 1
                            fecha_str = fecha_falta.strftime("%d/%m/%Y")
                            
                            if pd.isna(st.session_state.df.at[index, "Ausencias Registradas"]) or str(st.session_state.df.at[index, "Ausencias Registradas"]).strip() == "":
                                st.session_state.df.at[index, "Ausencias Registradas"] = fecha_str
                            else:
                                st.session_state.df.at[index, "Ausencias Registradas"] = str(st.session_state.df.at[index, "Ausencias Registradas"]) + ", " + fecha_str
                            
                            update_sheet(st.session_state.df)
                            st.rerun()
                        
                        st.markdown("---")
                        
                        st.write("**Registrar Recuperación**")
                        if st.button("➖ Ya recuperó 1 clase", key=f"recup_{index}"):
                            if recuperar > 0:
                                grupo = str(row['Grupo']).lower()
                                if "privado" in grupo or "individual" in grupo:
                                    st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es {row['Grupo']}.")
                                st.session_state.df.at[index, "Clases a recuperar"] -= 1
                                update_sheet(st.session_state.df)
                                st.rerun()
                    st.markdown("---")

    # ----------------------------------------
    # PESTAÑA 2: BUSCADOR DE SUPLENTES
    # ----------------------------------------
    with tab_vacantes:
        st.subheader("Buscador de Alumnos para Rellenar Vacantes")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        
        grupos_disponibles = ["Todos"] + sorted([g for g in df["Grupo"].dropna().unique() if str(g).strip() != ""])
        grupo_vacante = col_v1.selectbox("¿De qué Nivel/Grupo es el espacio libre?", grupos_disponibles)
        sede_vacante = col_v2.selectbox("¿En qué sede?", ["Todas", "Palermo", "Nuñez"])
        
        # NUEVO: Checkbox para ignorar la fecha y ver la lista completa
        ignorar_fecha = st.checkbox("Ignorar fecha (Ver lista completa de deudores)")
        
        if not ignorar_fecha:
            fecha_vacante = col_v3.date_input("¿Para qué fecha es la vacante?")
            fecha_vacante_str = fecha_vacante.strftime("%d/%m/%Y")
        
        st.write("---")
        
        # Filtramos solo los que deben clases
        df_deudores = df[df["Clases a recuperar"] > 0]
        
        # Aplicamos filtros de grupo y sede
        if grupo_vacante != "Todos":
            df_deudores = df_deudores[df_deudores["Grupo"] == grupo_vacante]
        if sede_vacante != "Todas":
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vacante]
            
        def esta_ausente_ese_dia(historial, fecha_buscar):
            if pd.isna(historial): return False
            return fecha_buscar in str(historial)

        # Si no se marca la casilla "ignorar_fecha", aplicamos la restricción de que no estén ausentes
        if not ignorar_fecha:
            df_suplentes = df_deudores[~df_deudores["Ausencias Registradas"].apply(lambda x: esta_ausente_ese_dia(x, fecha_vacante_str))]
        else:
            # Si marcamos la casilla, mostramos todos los deudores sin importar las fechas
            df_suplentes = df_deudores
            
        if df_suplentes.empty:
            st.success("✅ No hay alumnos compatibles que deban clases con estos filtros.")
        else:
            st.warning(f"🎯 Encontramos **{len(df_suplentes)}** alumno/s disponibles:")
            for idx, suplente in df_suplentes.iterrows():
                with st.container():
                    st.markdown(f"🎾 **{suplente['Nombre del alumno']}** | Debe: **{int(suplente['Clases a recuperar'])} clase(s)** | Sede base: {suplente['Sede']}")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets. Asegurate de haber configurado bien los Secrets. Detalle técnico: {e}")
