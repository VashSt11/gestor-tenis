import streamlit as st
import pandas as pd
import io

# Configuración de la página
st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# Inicializar variable de estado para guardar los datos en memoria mientras se usa la app
if "df" not in st.session_state:
    st.session_state.df = None

# 1. MOTOR DE IMPORTACIÓN
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subir matriz de alumnos (.xlsx)", type=["xlsx"])

if uploaded_file is not None and st.session_state.df is None:
    # Cargar el excel a la memoria
    st.session_state.df = pd.read_excel(uploaded_file)
    # Asegurar que las clases a recuperar sean números enteros
    if "Clases a recuperar" in st.session_state.df.columns:
        st.session_state.df["Clases a recuperar"] = pd.to_numeric(st.session_state.df["Clases a recuperar"], errors='coerce').fillna(0).astype(int)
    st.sidebar.success("¡Base de datos cargada!")

if st.session_state.df is not None:
    df = st.session_state.df

    # --- PESTAÑAS PARA ORGANIZAR LA APP ---
    tab_diario, tab_vacantes = st.tabs(["📅 Asistencias Diarias", "🔍 Buscar Suplente"])

    # ----------------------------------------
    # PESTAÑA 1: ASISTENCIAS DIARIAS
    # ----------------------------------------
    with tab_diario:
        st.sidebar.header("🔍 Filtros de Cancha")
        sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
        dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

        # Aplicar filtros
        filtered_df = df.copy()
        if sede_filter != "Todas":
            filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
        
        if dia_filter != "Todos":
            # Filtrar alumnos que tengan un horario asignado (no vacío) en el día seleccionado
            filtered_df = filtered_df[filtered_df[dia_filter].notna() & (filtered_df[dia_filter] != "")]

        st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")

        # Mostrar la lista en formato de tarjetas/filas
        for index, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                
                col1.write(f"**{row['Nombre del alumno']}**")
                col1.caption(f"Grupo: {row['Grupo']}")
                
                if dia_filter != "Todos":
                    col2.write(f"🕒 {row[dia_filter]}")
                else:
                    col2.write(f"📍 {row['Sede']}")
                    
                recuperar = int(row['Clases a recuperar'])
                col3.write(f"🔄 A recuperar: **{recuperar}**")
                
                # Botones de acción
                if col4.button("➕ Faltó", key=f"falta_{index}"):
                    st.session_state.df.at[index, "Clases a recuperar"] += 1
                    st.rerun()
                    
                if col5.button("➖ Recuperó", key=f"recup_{index}"):
                    if recuperar > 0:
                        grupo = str(row['Grupo']).lower()
                        if "privado" in grupo or "individual" in grupo:
                            st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es de grupo {row['Grupo']}. Recordá coordinar profesor/cancha.")
                        st.session_state.df.at[index, "Clases a recuperar"] -= 1
                        st.rerun()
                
                st.markdown("---")

    # ----------------------------------------
    # PESTAÑA 2: BUSCADOR DE SUPLENTES
    # ----------------------------------------
    with tab_vacantes:
        st.subheader("Buscador de Alumnos para Rellenar Vacantes")
        st.info("💡 Si te cancelan una clase, usá este filtro para ver rápidamente a quién podés llamar para que recupere en ese horario.")
        
        col_v1, col_v2 = st.columns(2)
        
        # Filtros de la vacante
        grupos_disponibles = ["Todos"] + sorted([g for g in df["Grupo"].dropna().unique() if str(g).strip() != ""])
        grupo_vacante = col_v1.selectbox("¿De qué Nivel/Grupo es el espacio que se liberó?", grupos_disponibles)
        sede_vacante = col_v2.selectbox("¿En qué sede?", ["Todas", "Palermo", "Nuñez"])
        
        st.write("---")
        
        # Filtrar solo a los que deben clases (mayor a 0)
        df_deudores = df[df["Clases a recuperar"] > 0]
        
        if grupo_vacante != "Todos":
            df_deudores = df_deudores[df_deudores["Grupo"] == grupo_vacante]
        if sede_vacante != "Todas":
            df_deudores = df_deudores[df_deudores["Sede"] == sede_vacante]
            
        if df_deudores.empty:
            st.success("✅ Genial, ningún alumno de estas características tiene clases pendientes para recuperar.")
        else:
            st.warning(f"🎯 Encontramos **{len(df_deudores)}** alumno/s que deben clases y pueden ocupar este espacio:")
            
            for idx, deudor in df_deudores.iterrows():
                with st.container():
                    st.markdown(f"🎾 **{deudor['Nombre del alumno']}** | Debe: **{int(deudor['Clases a recuperar'])} clase(s)** | Sede base: {deudor['Sede']}")
            

    # Botón de descarga en el sidebar
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
