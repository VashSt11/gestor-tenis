import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gestor de Tenis", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def init_connection():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

# --- 2. CARGA DE DATOS ---
@st.cache_data(ttl=600)
def load_worksheet(nombre_pestana):
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
    worksheet = sheet.worksheet(nombre_pestana)
    return pd.DataFrame(worksheet.get_all_records())

try:
    df_alumnos = load_worksheet("Alumnos")
    nombres_alumnos = df_alumnos["Nombre del alumno"].dropna().unique().tolist()
    
    # --- 3. PANEL LATERAL: CONTROL DE NOVEDADES ---
    with st.sidebar:
        st.header("📝 Cargar Novedad")
        with st.form("registro_form", clear_on_submit=True):
            fecha_input = st.date_input("Fecha de la clase")
            alumno_input = st.selectbox("Seleccionar Alumno", nombres_alumnos)
            estado_input = st.radio("¿Qué pasó?", ["Se Ausentó (Debe recuperar)", "Vino a Recuperar"])
            obs_input = st.text_input("Nota breve (Opcional)")
            
            submit_btn = st.form_submit_button("💾 Guardar Novedad")
            
            if submit_btn:
                client = init_connection()
                sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
                ws_asistencias = sheet.worksheet("Asistencias")
                
                nueva_fila = [
                    fecha_input.strftime("%d/%m/%Y"), 
                    alumno_input, 
                    estado_input, 
                    obs_input
                ]
                ws_asistencias.append_row(nueva_fila)
                
                st.cache_data.clear()
                st.success(f"¡Registro guardado para {alumno_input}!")
                st.rerun()

    # --- 4. VISTA CENTRAL (AHORA CON 3 PESTAÑAS) ---
    tab1, tab2, tab3 = st.tabs(["📋 Padrón General", "📅 Historial", "💡 Buscar Recuperación"])
    
    with tab1:
        st.subheader("Grilla General y Horarios")
        st.dataframe(df_alumnos, use_container_width=True, hide_index=True)
        
    with tab2:
        st.subheader("Auditoría de Ausencias y Recuperaciones")
        df_asistencias = load_worksheet("Asistencias")
        
        if not df_asistencias.empty:
            df_asistencias["Fecha"] = pd.to_datetime(df_asistencias["Fecha"], dayfirst=True, errors='coerce')
            rango_fechas = st.date_input("Filtrar (Inicio - Fin):", value=[], format="DD/MM/YYYY")
            
            if len(rango_fechas) == 2:
                inicio, fin = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
                mask = (df_asistencias["Fecha"] >= inicio) & (df_asistencias["Fecha"] <= fin)
                df_mostrar = df_asistencias.loc[mask].copy()
            else:
                df_mostrar = df_asistencias.copy()
                
            df_mostrar["Fecha"] = df_mostrar["Fecha"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        else:
            st.info("No hay ausencias ni recuperaciones registradas aún.")
            
    # --- PESTAÑA NUEVA: RECOMENDADOR ---
    with tab3:
        st.subheader("Buscador de Horarios para Recuperar")
        alumno_recupera = st.selectbox("Seleccioná un alumno para ver sus opciones:", [""] + nombres_alumnos)
        
        if alumno_recupera:
            # Identificamos los datos del alumno elegido
            datos_alumno = df_alumnos[df_alumnos["Nombre del alumno"] == alumno_recupera].iloc[0]
            sede_alumno = datos_alumno.get("Sede", "")
            grupo_alumno = datos_alumno.get("Grupo", "")
            
            st.markdown(f"**Nivel actual del alumno:** Sede {sede_alumno} | Grupo {grupo_alumno}")
            
            # Filtramos la grilla buscando otros alumnos del mismo grupo y sede
            # Descartamos al propio alumno para no sugerirle su horario original
            df_otros = df_alumnos[
                (df_alumnos["Sede"] == sede_alumno) & 
                (df_alumnos["Grupo"] == grupo_alumno) & 
                (df_alumnos["Nombre del alumno"] != alumno_recupera)
            ]
            
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
            horarios_disponibles = set()
            
            # Recorremos los días para extraer a qué hora hay clases de ese nivel
            for dia in dias_semana:
                if dia in df_otros.columns:
                    for horario in df_otros[dia].dropna().unique():
                        if str(horario).strip() != "":
                            horarios_disponibles.add(f"{dia}: {horario}")
            
            if horarios_disponibles:
                st.success("✅ Opciones encontradas para el mismo grupo y sede:")
                for h in sorted(horarios_disponibles):
                    st.write(f"- **{h}**")
            else:
                st.warning("No se encontraron horarios alternativos para este nivel en la grilla actual.")

except Exception as e:
    st.error(f"Error técnico: {e}")
