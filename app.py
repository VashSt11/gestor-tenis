import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

if "df" not in st.session_state:
    st.session_state.df = None

# 1. MOTOR DE IMPORTACIÓN
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subir matriz de alumnos (.xlsx)", type=["xlsx"])

if uploaded_file is not None and st.session_state.df is None:
    st.session_state.df = pd.read_excel(uploaded_file)
    
    # Preparar columnas si no existen
    if "Clases a recuperar" not in st.session_state.df.columns:
        st.session_state.df["Clases a recuperar"] = 0
    st.session_state.df["Clases a recuperar"] = pd.to_numeric(st.session_state.df["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
    
    # Nueva columna para guardar el historial de fechas de ausencias
    if "Ausencias Registradas" not in st.session_state.df.columns:
        st.session_state.df["Ausencias Registradas"] = ""
        
    st.sidebar.success("¡Base de datos cargada!")

if st.session_state.df is not None:
    df = st.session_state.df

    tab_diario, tab_vacantes = st.tabs(["📅 Asistencias Diarias", "🔍 Buscar Suplente"])

    # ----------------------------------------
    # PESTAÑA 1: ASISTENCIAS DIARIAS
    # ----------------------------------------
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        filtered_df = df.copy()
        if sede_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
        
        if dia_filter != "Todos":
            filtered_df = filtered_df[filtered_df[dia_filter].notna() & (filtered_df[dia_filter] != "")]

        st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")

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
                
                # Menú de gestión de faltas y recuperaciones
                with col4.expander("⚙️ Gestionar"):
                    # Registrar nueva falta con fecha
                    st.write("**Registrar Ausencia**")
                    fecha_falta = st.date_input("Fecha en la que falta/faltará:", key=f"fecha_{index}")
                    
                    if st.button("➕ Confirmar Falta", key=f"falta_{index}"):
                        st.session_state.df.at[index, "Clases a recuperar"] += 1
                        
                        # Guardar la fecha en el historial
                        fecha_str = fecha_falta.strftime("%Y-%m-%d")
                        actuales = str(st.session_state.df.at[index, "Ausencias Registradas"])
                        if pd.isna(st.session_state.df.at[index, "Ausencias Registradas"]) or actuales.strip() == "":
                            st.session_state.df.at[index, "Ausencias Registradas"] = fecha_str
                        else:
                            st.session_state.df.at[index, "Ausencias Registradas"] = actuales + ", " + fecha_str
                            
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # Registrar recuperación
                    st.write("**Registrar Recuperación**")
                    if st.button("➖ Ya recuperó 1 clase", key=f"recup_{index}"):
                        if recuperar > 0:
                            grupo = str(row['Grupo']).lower()
                            if "privado" in grupo or "individual" in grupo:
                                st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es {row['Grupo']}.")
                            st.session_state.df.at[index, "Clases a recuperar"] -= 1
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
        fecha_vacante = col_v3.date_input("¿Para qué fecha es la vacante?")
        fecha_vacante_str = fecha_vacante.strftime("%Y-%m-%d")
        
        st.write("---")
        
        df_deudores = df[df["Clases a recuperar"] > 0]
        
        if grupo_vacante != "Todos":
            df_deudores = df_deudores[df_deudores["Grupo"] == grupo_vacante]
        if sede_vacante != "Todas":
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vacante]
            
        # Filtrar a los que avisaron que ese día específico van a estar ausentes
        def esta_ausente_ese_dia(historial, fecha_buscar):
            if pd.isna(historial): return False
            return fecha_buscar in str(historial)

        df_suplentes = df_deudores[~df_deudores["Ausencias Registradas"].apply(lambda x: esta_ausente_ese_dia(x, fecha_vacante_str))]
            
        if df_suplentes.empty:
            st.success("✅ Genial, no hay alumnos compatibles que deban clases para esta fecha.")
        else:
            st.warning(f"🎯 Encontramos **{len(df_suplentes)}** alumno/s disponibles para recuperar en este espacio:")
            
            for idx, suplente in df_suplentes.iterrows():
                with st.container():
                    st.markdown(f"🎾 **{suplente['Nombre del alumno']}** | Debe: **{int(suplente['Clases a recuperar'])} clase(s)** | Sede base: {suplente['Sede']}")

    # ----------------------------------------
    # DESCARGA DEL EXCEL
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
    st.info("👋 ¡Hola! Para empezar, subí tu archivo de Excel en el menú de la izquierda.")
