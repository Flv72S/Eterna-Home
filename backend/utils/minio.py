from fastapi import UploadFile
import os
from datetime import datetime

UPLOAD_DIR = "uploads"

# Assicurati che la directory esista
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def upload_file(file: UploadFile) -> str:
    """
    Carica un file nella directory di upload e restituisce il percorso del file.
    """
    # Genera un nome file unico
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Salva il file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return file_path

def get_file_url(file_path: str) -> str:
    """
    Restituisce l'URL per accedere al file.
    """
    if not file_path:
        return None
    return f"/files/{os.path.basename(file_path)}" 