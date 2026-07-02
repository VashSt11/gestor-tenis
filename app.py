import base64
# Reemplaza 'service_account.json' por la ruta de tu archivo original
with open("service_account.json", "r") as f:
    json_content = f.read()
    b64_encoded = base64.b64encode(json_content.encode()).decode()
    print(b64_encoded)
