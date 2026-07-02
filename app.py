# --- CONEXIÓN DE PRUEBA ---
try:
    client = init_connection()
    # Usamos el ID directamente
    sheet_id = "1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo"
    
    # Intentamos abrir el archivo
    doc = client.open_by_key(sheet_id)
    
    # Intentamos abrir la primera hoja (si tu hoja tiene otro nombre, cambialo acá)
    sheet = doc.get_worksheet(0) 
    st.success("¡Conexión exitosa con Google Sheets!")
    
except Exception as e:
    st.error(f"Error específico de conexión: {e}")
