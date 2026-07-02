import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import re

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
    
    # --- 3. PANEL LATERAL: CONTROL DE NOVEDADES Y AUTOMATIZACIÓN ---
    with st.sidebar:
        st.header("📝 Cargar Novedad")
        with st.form("registro_form", clear_on_submit=True):
            fecha_input = st.date_input("Fecha de la clase")
            alumno_input = st.selectbox("Seleccionar Alumno", nombres_alumnos)
            estado_input = st.radio("¿Qué pasó?", ["Se Ausentó (Debe recuperar)", "Vino a Recuperar"])
            obs_input = st.text_input("Nota breve (Opcional)")
            
            submit_btn = st.form_submit_button("💾 Guardar Novedad")
            
            if submit_btn:
                # 1. Conectamos con ambas pestañas
                client = init_connection()
                sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo")
                ws_asistencias = sheet.worksheet("Asistencias")
                ws_alumnos = sheet.worksheet("Alumnos")
                
                # 2. Guardamos el registro histórico en Asistencias
                nueva_fila = [
                    fecha_input.strftime("%d/%m/%Y"), 
                    alumno_input, 
                    estado_input, 
                    obs_input
                ]
                ws_asistencias.append_row(nueva_fila)
                
                # 3. LÓGICA MATEMÁTICA: Actualizamos el contador en Alumnos
                try:
                    # Buscamos en qué fila está el alumno y en qué columna está el contador
                    celda_alumno = ws_alumnos.find(alumno_input, in_column=1)
                    celda_columna = ws_alumnos.find("Clases a recuperar", in_row=1)
                    
                    if celda_alumno and celda_columna:
                        fila = celda_alumno.row
                        col = celda_columna.col
                        
                        # Leemos el valor actual
                        valor_actual_str = ws_alumnos.cell(fila, col).value
                        try:
                            valor_actual = int(valor_actual_str) if valor_actual_str else 0
                        except ValueError:
                            valor_actual = 0
                            
                        # Calculamos la suma o la resta
                        if estado_input == "Se Ausentó (Debe recuperar)":
                            nuevo_valor = valor_actual + 1
                        elif estado_input == "Vino a Recuperar":
                            nuevo_valor = max(0, valor_actual - 1) # max(0) evita que quede en números negativos
                            
                        # Actualizamos la celda en Google Sheets
                        ws_alumnos.update_cell(fila, col, nuevo_valor)
                        
                        st.cache_data.clear()
                        st.success(f"✅ ¡Novedad guardada! El saldo de {alumno_input} se actualizó a {nuevo_valor} clases.")
                        st.rerun()
                    else:
                        st.warning("Se guardó el registro, pero hubo un error buscando al alumno en el padrón para sumar la clase.")
                        
                except Exception as e:
                    st.error(f"Se guardó la novedad, pero falló la actualización del contador: {e}")

    # --- 4. VISTA CENTRAL ---
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
            
    with tab3:
        st.subheader("Buscador de Horarios para Recuperar")
        alumno_recupera = st.selectbox("Seleccioná un alumno para ver sus opciones:", [""] + nombres_alumnos)
        
        if alumno_recupera:
            datos_alumno = df_alumnos[df_alumnos["Nombre del alumno"] == alumno_recupera].iloc[0]
            sede_alumno = str(datos_alumno.get("Sede", "")).strip()
            grupo_alumno = str(datos_alumno.get("Grupo", "")).strip()
            
            st.markdown(f"**Nivel/Tipo actual:** Sede {sede_alumno} | {grupo_alumno}")
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
            
            def extraer_hora(texto):
                match = re.search(r'^(\d+)', str(texto).strip())
                return int(match.group(1)) if match else -1

            if "privado" in grupo_alumno.lower():
                st.info("ℹ️ Mostrando **horarios libres** en la sede (se omite la franja de 13 a 15 hs) y excepciones permitidas de 15 a 17 hs.")
                df_sede = df_alumnos[df_alumnos["Sede"] == sede_alumno]
                
                cols = st.columns(5)
                for idx, dia in enumerate(dias_semana):
                    with cols[idx]:
                        st.markdown(f"**{dia}**")
                        if dia in df_sede.columns:
                            horas_ocupadas = set()
                            for h in df_sede[dia].dropna():
                                num = extraer_hora(h)
                                if num != -1:
                                    horas_ocupadas.add(num)
                            
                            hay_opciones = False
                            for hora in range(8, 22):
                                if 13 <= hora < 15:
                                    continue
                                es_tarde = 15 <= hora < 17
                                if hora not in horas_ocupadas:
                                    st.write(f"✅ {hora} a {hora+1} hs")
                                    hay_opciones = True
                                elif es_tarde:
                                    st.write(f"⭐ {hora} a {hora+1} hs *(Excep.)*")
                                    hay_opciones = True
                            if not hay_opciones:
                                st.write("❌ Sin cupos")

            else:
                st.info("ℹ️ Mostrando opciones de tu mismo nivel en otros grupos.")
                df_otros = df_alumnos[
                    (df_alumnos["Sede"] == sede_alumno) & 
                    (df_alumnos["Grupo"] == grupo_alumno) & 
                    (df_alumnos["Nombre del alumno"] != alumno_recupera)
                ]
                
                cols = st.columns(5)
                for idx, dia in enumerate(dias_semana):
                    with cols[idx]:
                        st.markdown(f"**{dia}**")
                        if dia in df_otros.columns:
                            opciones_dia = []
                            for horario in df_otros[dia].dropna().unique():
                                val = str(horario).strip()
                                if val != "":
                                    opciones_dia.append(val)
                            
                            if opciones_dia:
                                opciones_dia.sort(key=extraer_hora)
                                for opc in opciones_dia:
                                    st.write(f"✅ {opc}")
                            else:
                                st.write("-")

except Exception as e:
    st.error(f"Error técnico: {e}")
