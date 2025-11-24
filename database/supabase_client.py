import os
from supabase import create_client, Client
import logging

class SupabaseClient:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise Exception("Faltan credenciales de Supabase en .env")
            
        self.supabase: Client = create_client(url, key)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Asegurar logging

    def upsert_job(self, job_data):
        # Upsert usando la URL como clave única para evitar duplicados
        # on_conflict='url' es clave aquí
        return self.supabase.table("jobs").upsert(job_data, on_conflict="url").execute()
        
    def get_jobs(self, limit=100):
        # Si limit es None, no se aplica límite (recupera todos los registros)
        query = self.supabase.table("jobs").select("*").order('created_at', desc=True)
        if limit is not None:
            query = query.limit(limit)
        return query.execute()

    def clear_jobs_table(self):
        """Elimina todos los registros de la tabla 'jobs'."""
        try:
            # Eliminar todos los registros
            response = self.supabase.table("jobs").delete().neq('id', 0).execute()
            # El filtro neq('id', 0) es un truco común para deletear todo, ya que Supabase
            # requiere un filtro para DELETE. Asume que el ID 0 no existe o es insignificante.
            # Alternativamente, si la tabla siempre tendrá IDs mayores que 0, puedes usar .gt('id', 0)
            logging.info(f"✅ Tabla 'jobs' limpiada. {response.count} registros eliminados.")
            return True
        except Exception as e:
            logging.error(f"❌ Error al limpiar la tabla 'jobs': {e}")
            return False