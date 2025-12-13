# FILE: Proyecto/job-market-intelligence/database/supabase_client.py
import os
from supabase import create_client, Client
import logging
import datetime
import hashlib
from typing import List, Dict, Any, Optional

# Configuramos logging para esta clase
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SupabaseClient:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not service_key:
            logging.error("Faltan credenciales de Supabase (SUPABASE_URL o SUPABASE_SERVICE_KEY) en .env")
            raise Exception("Faltan credenciales de Supabase (SUPABASE_URL o SUPABASE_SERVICE_KEY) en .env")
            
        self.supabase: Client = create_client(url, service_key)
        logging.info("SupabaseClient inicializado.")

    def upsert_job(self, job_data: Dict[str, Any]):
        """
        Inserta o actualiza un registro de trabajo en la tabla 'jobs'.
        Utiliza 'job_id' y 'source_platform' para resolver conflictos (deduplicación por fuente).
        """
        required_fields = ['job_id', 'source_platform', 'title', 'company_name']
        if not all(field in job_data and job_data[field] for field in required_fields):
            logging.warning(f"Datos de vacante incompletos para upsert: {job_data.get('title')}. Faltan campos requeridos.")
            # Podemos generar un job_id aquí si no existe para al menos intentar guardar.
            if not job_data.get('job_id'):
                 unique_string = f"{job_data.get('title', '')}-{job_data.get('company_name', '')}-{job_data.get('location', '')}-{job_data.get('source_platform', '')}"
                 job_data['job_id'] = hashlib.md5(unique_string.encode()).hexdigest()
                 logging.info(f"Generated job_id for job: {job_data['job_id']}")
            
            # Si aún faltan campos críticos, lanzamos error o devolvemos None
            if not job_data.get('job_id') or not job_data.get('source_platform'):
                raise ValueError("job_id y source_platform son requeridos para el upsert.")

        return self.supabase.table("jobs").upsert(
            job_data,
            on_conflict="job_id,source_platform"
        ).execute()
        
    def insert_skills(self, skill_records: List[Dict[str, Any]]):
        """
        Inserta múltiples registros de habilidades. Espera una lista de diccionarios
        con 'job_id', 'skill_name', 'skill_category'.
        """
        if not skill_records:
            return None
        
        valid_skill_records = [
            record for record in skill_records if record.get('skill_name') and record.get('job_id')
        ]
        
        if not valid_skill_records:
            logging.warning("No se proporcionaron registros de habilidades válidos para insertar.")
            return None

        # Supabase permite insertar múltiples registros en una sola llamada.
        return self.supabase.table("skills").insert(valid_skill_records).execute()
    
    def upsert_company(self, company_data: Dict[str, Any]):
        """
        Inserta o actualiza un registro de compañía. Conflicta por el nombre.
        """
        if 'name' not in company_data or not company_data['name']:
            raise ValueError("El nombre de la compañía es requerido para el upsert.")
        
        return self.supabase.table("companies").upsert(
            company_data,
            on_conflict="name" # Conflictar por nombre para evitar duplicados
        ).execute()

    def upsert_trend(self, trend_data: Dict[str, Any]):
        """
        Inserta o actualiza un registro de tendencia.
        Conflicta por una combinación de campos para asegurar unicidad de tendencias diarias.
        """
        required_fields = ['date', 'metric_name', 'metric_value']
        if not all(field in trend_data and trend_data[field] for field in required_fields):
            raise ValueError(f"date, metric_name y metric_value son requeridos para el upsert de tendencias. Datos: {trend_data}")
        
        # Aseguramos que 'sector' y 'country' existan para el on_conflict, aunque sean None
        trend_data.setdefault('sector', None)
        trend_data.setdefault('country', None)

        return self.supabase.table("trends").upsert(
            trend_data,
            on_conflict="date,metric_name,metric_value,sector,country"
        ).execute()

    def get_jobs(self, limit: Optional[int] = None, country: Optional[str] = None, sector: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Obtiene trabajos de la base de datos, incluyendo sus habilidades asociadas.
        Los filtros de fecha esperan strings en formato 'YYYY-MM-DD'.
        """
        query = self.supabase.table("jobs").select("*, skills(*)").order('scraped_at', desc=True)

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

    def get_skills(self, limit: Optional[int] = None, job_id: Optional[str] = None):
        """Obtiene habilidades, opcionalmente filtradas por job_id."""
        query = self.supabase.table("skills").select("*")
        if job_id:
            query = query.eq('job_id', job_id)
        if limit is not None:
            query = query.limit(limit)
        return query.execute()
    
    def get_trends(self, limit: Optional[int] = None, date: Optional[str] = None, metric_name: Optional[str] = None, sector: Optional[str] = None, country: Optional[str] = None):
        """Obtiene tendencias, con varios filtros opcionales."""
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
        """
        Elimina todos los registros de las tablas 'skills', 'trends', 'jobs' y 'companies'.
        Requiere permisos de delete con la service_key.
        """
        try:
            # Para Supabase, delete().gt('id', 0) o delete().neq('id', 'algún_uuid_nulo_seguro')
            # suelen funcionar para eliminar todo en tablas con PKs numéricas o UUIDs.
            # Una forma más segura podría ser usar RLS que permita delete *si es la service_key*.

            # Eliminamos en cascada o en orden inverso a las dependencias.
            # skills -> jobs
            # trends (independiente)
            # jobs -> companies (si jobs tiene FK a companies)
            
            # Limpiar tabla 'skills'
            skills_response = self.supabase.table("skills").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logging.info(f"✅ Tabla 'skills' limpiada. {len(skills_response.data)} registros eliminados.")

            # Limpiar tabla 'trends'
            trends_response = self.supabase.table("trends").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logging.info(f"✅ Tabla 'trends' limpiada. {len(trends_response.data)} registros eliminados.")

            # Limpiar tabla 'jobs'
            jobs_response = self.supabase.table("jobs").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logging.info(f"✅ Tabla 'jobs' limpiada. {len(jobs_response.data)} registros eliminados.")
            
            # Limpiar la tabla de 'companies'
            companies_response = self.supabase.table("companies").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logging.info(f"✅ Tabla 'companies' limpiada. {len(companies_response.data)} registros eliminados.")

            return True
        except Exception as e:
            logging.error(f"❌ Error al limpiar las tablas de la base de datos: {e}")
            return False
