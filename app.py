import streamlit as st
import pandas as pd
import io
from datetime import date
import numpy as np

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

if "df" not in st.session_state:
    st.session_state.df = None

# ----------------------------------------
# 1. MOTOR DE IMPORTACIÓN (Volvimos al que funcionaba)
# ----------------------------------------
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subir matriz de alumnos (.xlsx)", type=["xlsx"])

# Botón para forzar el reseteo si querés subir un Excel nuevo
if st.sidebar.button("🔄 Cargar un archivo nuevo"):
    st.session_state.df = None
    st.rerun()

if uploaded_file is not None and st.session_state.df is None:
    df_temp = pd.read_excel(uploaded_file)
    
    # Limpieza inicial
    df_temp = df_temp.replace({np.nan: "", pd.NaT: ""})
    if "Clases a recuperar" not in df_temp.columns:
        df_temp["Clases a recuperar"] = 0
    df_temp["Clases a recuperar"] = pd.to_numeric(df_temp["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
    
    if "Ausencias Registradas" not in df_temp.columns:
        df_temp["Ausencias Registradas"] = ""
        
    st.session_state.df = df_temp.fillna("")
    st.sidebar.success("¡Base de datos cargada!")

if st.session_state.df is not None:
    df = st.session_state.df

    # --- PESTAÑAS DE LA APP ---
    tab_diario, tab_vacantes = st.tabs(["📅 Asistencias Diarias", "🔍 Buscar Suplente"])

    # ----------------------------------------
    # PESTAÑA 1: ASISTENCIAS DIARIAS
    # ----------------------------------------
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")
        
        # Buscador por nombre
        search_query = st.sidebar.text_input("🔎 Buscar por Nombre:", placeholder="Escribí un nombre...")
        
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        filtered_df = df.copy()
        
        if search_query.strip():
            filtered_df = filtered_df[filtered_df["Nombre del alumno"].astype(str).str.contains(search_query, case=False, na=False)]
            
        if sede_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
        
        if dia_filter != "Todos":
            filtered_df = filtered_df[
                filtered_df[dia_filter].notna() & 
                (filtered_df[dia_filter] != "") & 
                (filtered_df[dia_filter].astype(str).str.strip() != "")
            ]

        if search_query.strip():
            st.subheader(f"📍 Resultados para: '{search_query}'")
        else:
            st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")

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
                        
                    try:
                        recuperar = int(row['Clases a recuperar'])
                    except:
                        recuperar = 0
                        
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
                            try:
                                actual_val = int(st.session_state.df.at[index, "Clases a recuperar"])
                            except:
                                actual_val = 0
                                
                            st.session_state.df.at[index, "Clases a recuperar"] = actual_val + 1
                            fecha_str = fecha_falta.strftime("%d/%m/%Y")
                            
                            hist = str(st.session_state.df.at[index, "Ausencias Registradas"])
                            if hist == "nan" or hist.strip() == "":
                                st.session_state.df.at[index, "Ausencias Registradas"] = fecha_str
                            else:
                                st.session_state.df.at[index, "Ausencias Registradas"] = hist + ", " + fecha_str
                            
                            st.rerun()
                        
                        st.markdown("---")
                        
                        st.write("**Registrar Recuperación**")
                        if st.button("➖ Ya recuperó 1 clase", key=f"recup_{index}"):
                            if recuperar > 0:
                                grupo = str(row['Grupo']).lower()
                                if "privado" in grupo or "individual" in grupo:
                                    st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es {row['Grupo']}.")
                                
                                st.session_state.df.at[index, "Clases a recuperar"] = recuperar - 1
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
        
        ignorar_fecha = st.checkbox("Ignorar fecha (Ver lista completa de deudores)")
        
        if not ignorar_fecha:
            fecha_vacante = col_v3.date_input("¿Para qué fecha es la vacante?")
            fecha_vacante_str = fecha_vacante.strftime("%d/%m/%Y")
        
        st.write("---")
        
        df_deudores = df.copy()
        df_deudores["Clases a recuperar"] = pd.to_numeric(df_deudores["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
        df_deudores = df_deudores[df_deudores["Clases a recuperar"] > 0]
        
        if grupo_vacante != "Todos":
            df_deudores = df_deudores[df_deudores["Grupo"] == grupo_vacante]
        if sede_vacante != "Todas":
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vacante]
            
        def esta_ausente_ese_dia(historial, fecha_buscar):
            hist_str = str(historial)
            if hist_str == "nan" or hist_str.strip() == "": return False
            return fecha_buscar in hist_str

        if not ignorar_fecha:
            df_suplentes = df_deudores[~df_deudores["Ausencias Registradas"].apply(lambda x: esta_ausente_ese_dia(x, fecha_vacante_str))]
        else:
            df_suplentes = df_deudores
            
        if df_suplentes.empty:
            st.success("✅ No hay alumnos compatibles que deban clases con estos filtros.")
        else:
            st.warning(f"🎯 Encontramos **{len(df_suplentes)}** alumno/s disponibles:")
            for idx, suplente in df_suplentes.iterrows():
                with st.container():
                    st.markdown(f"🎾 **{suplente['Nombre del alumno']}** | Debe: **{int(suplente['Clases a recuperar'])} clase(s)** | Sede base: {suplente['Sede']}")

    # ----------------------------------------
    # DESCARGA DEL EXCEL ACTUALIZADO
    # ----------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("💾 Guardar Trabajo")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.df.to_excel(writer, index=False)
    
    st.sidebar.download_button(
        label="📥 Descargar Planilla Actualizada",
        data=buffer,
        file_name="Planilla_Alumnos_Actualizada.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.info("👋 ¡Hola! Subí la última versión de tu Excel para empezar.")
