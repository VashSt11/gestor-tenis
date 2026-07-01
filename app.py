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
    # Llenar espacios vacíos en 'Clases a recuperar' con ceros
    if "Clases a recuperar" in st.session_state.df.columns:
        st.session_state.df["Clases a recuperar"] = st.session_state.df["Clases a recuperar"].fillna(0).astype(int)
    st.sidebar.success("¡Base de datos cargada!")

if st.session_state.df is not None:
    df = st.session_state.df

    # 2. TABLERO DE CONTROL (Filtros)
    st.sidebar.header("🔍 Filtros de Cancha")
    sede_filter = st.sidebar.selectbox("Seleccionar Sede", ["Todas", "Palermo", "Nuñez"])
    dia_filter = st.sidebar.selectbox("Seleccionar Día", ["Todos", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])

    # Aplicar filtros
    filtered_df = df.copy()
    if sede_filter != "Todas":
        filtered_df = filtered_df[filtered_df["Sede"] == sede_filter]
    
    if dia_filter != "Todos":
        # Filtrar alumnos que tengan un horario asignado (no vacío) en el día seleccionado
        filtered_df = filtered_df[filtered_df[dia_filter].notna()]

    st.subheader(f"📍 Mostrando alumnos de {sede_filter} - Día: {dia_filter}")

    # 3. GESTOR DE RECUPERACIONES
    # Mostrar la lista en formato de tarjetas/filas
    for index, row in filtered_df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            # Nombre y Grupo
            col1.write(f"**{row['Nombre del alumno']}**")
            col1.caption(f"Grupo: {row['Grupo']}")
            
            # Mostrar horario del día filtrado o Sede
            if dia_filter != "Todos":
                col2.write(f"🕒 {row[dia_filter]}")
            else:
                col2.write(f"📍 {row['Sede']}")
                
            # Contador actual
            recuperar = int(row['Clases a recuperar'])
            col3.write(f"🔄 A recuperar: **{recuperar}**")
            
            # Botones de acción
            if col4.button("➕ Faltó", key=f"falta_{index}"):
                st.session_state.df.at[index, "Clases a recuperar"] += 1
                st.rerun() # Recarga la pantalla
                
            if col5.button("➖ Recuperó", key=f"recup_{index}"):
                if recuperar > 0:
                    
                    # 4. ALERTA POR REGLAS DE GRUPO
                    grupo = str(row['Grupo']).lower()
                    if "privado" in grupo or "individual" in grupo:
                        st.toast(f"⚠️ Cuidado: {row['Nombre del alumno']} es de grupo {row['Grupo']}. Recordá coordinar el profesor/cancha.")
                        
                    st.session_state.df.at[index, "Clases a recuperar"] -= 1
                    st.rerun()
            
            st.markdown("---")

    # Botón para descargar el Excel actualizado al final del día
    st.sidebar.markdown("---")
    st.sidebar.header("💾 Guardar Trabajo")
    
    # Crear un buffer de memoria para descargar el archivo
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