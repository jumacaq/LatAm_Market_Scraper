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

        # Supabase permite insertar múltiples registros en una sola llamada.
        # Esto es más eficiente que múltiples llamadas individuales.
        return self.supabase.table("skills").insert(valid_skill_records).execute()
    
    # NUEVO MÉTODO: Upsert para compañías
    def upsert_company(self, company_data):
        if 'name' not in company_data:
            raise ValueError("El nombre de la compañía es requerido para el upsert.")
        
        # Intentar actualizar o insertar la compañía
        return self.supabase.table("companies").upsert(
            company_data,
            on_conflict="name" # Conflictar por nombre para evitar duplicados
        ).execute()

    # NUEVO MÉTODO: Upsert para tendencias
    def upsert_trend(self, trend_data):
        if 'date' not in trend_data or 'metric_name' not in trend_data or 'metric_value' not in trend_data:
            raise ValueError("date, metric_name y metric_value son requeridos para el upsert de tendencias.")
        
        # Conflictar por una combinación de campos para asegurar unicidad de tendencias diarias
        return self.supabase.table("trends").upsert(
            trend_data,
            on_conflict="date,metric_name,metric_value,sector,country"
        ).execute()

    def get_jobs(self, limit=None, country=None, sector=None, start_date=None, end_date=None):
        query = self.supabase.table("jobs").select("*, skills(*)").order('scraped_at', desc=True) # Incluir skills

        if country:
            query = query.eq('country', country)
        if sector:
            query = query.eq('sector', sector)
        if start_date:
            query = query.gte('posted_date', start_date)
        if end_date:
            query = query.lte('posted_date', end_date)

        if limit is not None:
            query = query.limit(limit)
        return query.execute()

    def get_skills(self, limit=None, job_id=None):
        query = self.supabase.table("skills").select("*")
        if job_id:
            query = query.eq('job_id', job_id)
        if limit is not None:
            query = query.limit(limit)
        return query.execute()
    
    def get_trends(self, limit=None, date=None, metric_name=None, sector=None, country=None):
        query = self.supabase.table("trends").select("*").order('date', desc=True)
        if date:
            query = query.eq('date', date)
        if metric_name:
            query = query.eq('metric_name', metric_name)
        if sector:
            query = query.eq('sector', sector)
        if country:
            query = query.eq('country', country)
        if limit is not None:
            query = query.limit(limit)
        return query.execute()

    def clear_jobs_table(self):
        """Elimina todos los registros de las tablas 'skills', 'jobs' y 'trends'."""
        try:
            null_uuid_str = '00000000-0000-0000-0000-000000000000'
            
            # Limpiar tabla 'skills'
            skills_response = self.supabase.table("skills").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'skills' limpiada. {len(skills_response.data)} registros eliminados.")

            # Limpiar tabla 'trends' (NUEVO)
            trends_response = self.supabase.table("trends").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'trends' limpiada. {len(trends_response.data)} registros eliminados.")

            # Limpiar tabla 'jobs'
            jobs_response = self.supabase.table("jobs").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'jobs' limpiada. {len(jobs_response.data)} registros eliminados.")
            
            # También limpiar la tabla de 'companies' si queremos empezar de cero con las compañías
            companies_response = self.supabase.table("companies").delete().neq('id', null_uuid_str).execute()
            logging.info(f"✅ Tabla 'companies' limpiada. {len(companies_response.data)} registros eliminados.")

            return True
        except Exception as e:
            logging.error(f"❌ Error al limpiar las tablas de la base de datos: {e}")
            return False
