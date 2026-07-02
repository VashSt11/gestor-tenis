import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Forzamos la limpieza de caché
st.cache_resource.clear()

st.set_page_config(page_title="Gestor de Alumnos", layout="wide")
st.title("🎾 Gestor de Asistencias y Recuperaciones")

# --- CREDENCIALES INTEGRADAS (Bypass de Streamlit Secrets) ---
# Al ponerlas acá, es imposible que haya errores de formato TOML
CREDS_DICT = {
    "type": "service_account",
    "project_id": "gestor-tenis",
    "private_key_id": "0ec8eea7f4ea5a21280c0224037eac8ca9c2db44",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC/OPghKtHobB7F\nPoIl1QT9WAKKX9RnvF90yW0SPjfBWFap+OMAmQwHUuojtgWIqPmD4Q4plTEeQObO\n9+ypc69xMp31cnhv+cpjxDMFBN0fj+MePbpUBMVz/LauHrPZW5px1uOranXEvRtQ\nlFxA1ca884G0mQ73sTht6AGO3QtcGfTZtVxuD4ebKLzKo/9RjrDFohP6mrXKS9bR\nGkRw0THGp49FTjaaLbTyGj4iGY0rvQ64jPsMsLgikYFlgLPzYLlwr8QBqvaSNoMN\nNcTNhYFzebWEtyI7SNr49lQ7yOc35xzkEKpsnN5vzL8SrlMDJCu4TTGtFmToPMBS\nG2HcHMUNAgMBAAECggEACP/CR1lPmuJ7JRcNoslwrpoaN1y8Kp54V9grvGNoer5i\n5AB1A4tnLbp8asmtFbVI6DsBh0MFOvSc0T6JP+mvwljxZocIghrUOpNMrV64A0+Y\nRZZr8ugkAUnf+ZMOv9rX+Df2ooF2c4VxWmxf1jWQKdj6/lEDHdACN3p5TpU6Wmqt\nJlmBUaQiqLGlu2bxN8GVXZ7E2PkpEmtz+BF8Zk4V9ZvL3YXtQz0ue/4HOHpBj6Tf\n0Kbphmph4mS5J5lMFiZbMBYyU8LcOL7HlPgsGAbV2iz66EjWEqudYiNo9OkF2a4R\nx3K3HVevc071958OQLZkwKfBZ2mEIlNT4XE3enqepwKBgQDrJO6+0do+86wdlikq\nSAQZyBeqHhuIvCv4z+JG8XUCWqXtdw8B70XX2mWdLkwV5bludO4iG1oLrAn1oeki\nx8hEnQAA+WTsX+IOxBpXEnx6zUdUbYHq7UPKKncm70vmp4yqlSGkLX/tFFE1SJcy\n/blaaHSOPK67hXQOq1mk6nRnqwKBgQDQLsWcj30cMMRCiJtjoFzvDUbDN85BsVAW\n6eL8Urqvr/iFikvaFFYe9YZj2wKgVroWp4IK3aCFkJ6BFU6P5+rBeSzUzfE5RkGr\nGDJ08Pm6U6Votf8oOi2jUOyLMMFJT7HIAHpt3xI0g3M6FOXrpcR7XSTWI+NwgZTU\nVI7BxADuJwKBgQDT/bvv9KlZz7z//3ylTb/ErowHJpWUNHFAI8rQQqdGtAqbh5bU\nG69P5ultR2v44d7HIkv+G8KWe0ePV6UjYhG/Kfvy5OSD5f2baliE33myDJeeGgvi\njH1tKdO6GkrHa455y3FE3nBSgNqluwf1RKFyTHGoOjUdgjcbcoejEmxXeQKBgQCT\nqNkZFt1SZXSPDH3KyC+ijvQl+yschTudRP9uoO8xNcs8TL9ISyxagSN1KB5Qw7Lx\n5pXiRxhYJB+IxygWAhUMbXpS5k+2pBJn3J3NPC6k7jdgcdYtHjbIo9ljUI2IBjK+\n/TfZPmOXQ7Uy+SerYMRgC8zY5lOntQFvKRqobPGL+QKBgQCoojv6Cnx77FhRNVe7\nVZR5olAUkzKHSMei8o6tr1rSs8bgtOcsb0HOVld8orEQBaB7rbJ9N9brcvP9Dp8a\n/zLbhm5zbNuPJsCPnRvwQiL6QOhRw9Y+EOzNpgyw11D6z/Islys7Y7qPsR5J+Xy\nXLlyHHbK4vmbnyy9sU8VkFwCvA==\n-----END PRIVATE KEY-----",
    "client_email": "asistencia-tenis@gestor-tenis.iam.gserviceaccount.com",
    "client_id": "102590138819807904903",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/asistencia-tenis%40gestor-tenis.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets", 
        "https://www.googleapis.com/auth/drive"
    ]
    # Usamos el diccionario integrado
    creds = Credentials.from_service_account_info(CREDS_DICT, scopes=scopes)
    return gspread.authorize(creds)

# Ejecutamos la conexión
try:
    client = init_connection()
    sheet = client.open_by_key("1MC0tdj5LJn8BtfEdTJjsYjSuk6PDirZejkKQEJlnoYo").sheet1
    st.success("✅ ¡Conexión restaurada con éxito! La base de datos está en línea.")
except Exception as e:
    st.error(f"Error técnico de conexión: {e}")
