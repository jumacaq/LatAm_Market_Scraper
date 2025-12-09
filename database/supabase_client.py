# database/supabase_client.py

# ==========================================================
# 🚨 CARGA DE VARIABLES DE ENTORNO
# Se usa python-dotenv para cargar SUPABASE_URL y SUPABASE_KEY desde el archivo .env
# Esto es CRUCIAL para que el archivo funcione al ser importado.
import os
import dotenv
dotenv.load_dotenv()
# ==========================================================

import hashlib
from typing import List, Dict, Any
from supabase import create_client, Client 
from datetime import datetime

# --- CONFIGURACIÓN DE CONEXIÓN ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Esta verificación se ejecuta al importar
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("🚨 ERROR: Define SUPABASE_URL y SUPABASE_KEY en las variables de entorno.")

# Inicialización del cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_job_record(record: Dict[str, Any]) -> str:
    """Crea un hash único (SHA-256) basado en los campos clave de la vacante para deduplicación."""
    base = (
        str(record.get("titulo", "")).lower() +
        str(record.get("empresa", "")).lower() +
        str(record.get("ubicacion", "")).lower() +
        str(record.get("plataforma", "")).lower()
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def upsert_jobs(jobs: List[Dict[str, Any]]):
    """
    Intenta insertar o actualizar (upsert) registros en la tabla 'jobs' de Supabase.
    
    PRE-REQUISITO: La tabla 'jobs' debe tener un índice/constraint único en la columna 'hash'.
    """
    if not jobs:
        return {"inserted": 0, "status": "no_records"}
        
    payload = []
    for j in jobs:
        j_copy = dict(j)
        j_copy["hash"] = hash_job_record(j)
        j_copy["inserted_at"] = datetime.utcnow().isoformat()
        payload.append(j_copy)

    # Intentar UPSERT (Insertar si no existe, actualizar si existe)
    # Usamos 'hash' como clave de conflicto (gracias al índice único que creaste).
    try:
        response = supabase.table("jobs").upsert(payload, on_conflict="hash").execute()
        
        # Retornamos el estado de la operación (la deduplicación ocurre en la DB)
        return {"status": "success", "count_attempted": len(payload), "details": response.data}
    
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en upsert_jobs: {e}")
        return {"status": "failed", "error": str(e)}