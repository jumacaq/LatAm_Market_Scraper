# FILE: job-market-intelligence/database/supabase_client.py
import os
from supabase import create_client, Client
import logging
import datetime

class SupabaseClient:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not service_key:
            raise Exception("Faltan credenciales de Supabase (SUPABASE_URL o SUPABASE_SERVICE_KEY) en .env")
            
        self.supabase: Client = create_client(url, service_key)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def upsert_job(self, job_data):
        if 'job_id' not in job_data or 'source_platform' not in job_data:
            raise ValueError("job_id y source_platform son requeridos para el upsert.")

        return self.supabase.table("jobs").upsert(
            job_data,
            on_conflict="job_id,source_platform"
        ).execute()
        
    def insert_skills(self, skill_records):
        if not skill_records:
            return None
        
        valid_skill_records = [
            record for record in skill_records if record.get('skill_name')
        ]
        
        if not valid_skill_records:
            return None

        return self.supabase.table("skills").insert(valid_skill_records).execute()


    def get_jobs(self, limit=100):
        query = self.supabase.table("jobs").select("*").order('scraped_at', desc=True)
        if limit is not None:
            query = query.limit(limit)
        return query.execute()

    def clear_jobs_table(self):
        """Elimina todos los registros de la tabla 'jobs' y 'skills'."""
        try:
            null_uuid_str = '00000000-0000-0000-0000-000000000000'
            
            # CORRECCIÓN FINAL: Usar .neq() en lugar de .not_eq()
            skills_response = self.supabase.table("skills").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'skills' limpiada. {len(skills_response.data)} registros eliminados.")

            # CORRECCIÓN FINAL: Usar .neq() en lugar de .not_eq()
            jobs_response = self.supabase.table("jobs").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'jobs' limpiada. {len(jobs_response.data)} registros eliminados.")
            return True
        except Exception as e:
            logging.error(f"❌ Error al limpiar las tablas 'jobs' y 'skills': {e}")
            return False
