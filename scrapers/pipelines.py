# scrapers/pipelines.py (VERSIÓN FINAL ETL)

from typing import List, Dict, Any
from database.supabase_client import upsert_jobs, hash_job_record
import re
import datetime
# 🚨 NUEVA IMPORTACIÓN: Importamos la función de normalización del módulo ETL
from etl.normalizers import normalize_all 


class Pipeline:
    # Ahora __init__ acepta 3 argumentos (url, key) para ser llamado desde main.py
    def __init__(self, supabase_url: str, supabase_key: str):
        # Almacenamos las credenciales (aunque supabase_client.py ya las lee del .env)
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

    def _normalize_fieldnames(self, r: Dict) -> Dict:
        """
        Normalización de campos: español -> inglés, formato estándar.
        (Esta función se mantiene para mapeo básico, la normalización avanzada está en etl/normalizers.py)
        """
        out = dict(r)
        
        # Mapeo de campos (tus nombres de scraper -> nombres finales de la DB)
        mapping = {
            "titulo": "title",
            "empresa": "company",
            "ubicacion": "location",
            "pais": "country",
            "salario": "salary",
            "descripcion": "description",
            "plataforma": "source",
            "url": "url",
            "nivel_experiencia": "seniority",
            "palabra_clave": "keyword", # Mantenemos keyword y el normalizer.py creará 'sector'
            "posted_date": "posted_date"
        }
        for k, v in mapping.items():
            if k in out and v not in out:
                out[v] = out.pop(k)

        # Limpieza básica
        for k in ["title", "company", "location", "salary", "source"]:
            if k in out and isinstance(out[k], str):
                out[k] = re.sub(r"\s+", " ", out[k]).strip()
        
        # Manejo de Skills
        skills = out.get("skills") or []
        if isinstance(skills, str):
            out["skills"] = [s.strip() for s in re.split(r",|;", skills) if s.strip()]
        
        # Campos por defecto si faltan
        out.setdefault("seniority", "N/A")
        out.setdefault("skills", [])
        
        # Remover campos temporales no necesarios
        for k in ["plataforma_pais", "fecha_scraping", "keyword", "tipo_empleo"]:
            out.pop(k, None)
            
        return out

    def clean_record(self, rec: Dict) -> Dict:
        """
        Aplica el mapeo inicial y luego llama al proceso de Normalización/Enriquecimiento ETL.
        """
        # 1. Mapeo Básico de Nombres
        r_mapped = self._normalize_fieldnames(rec)
        
        # 2. 🚨 PASO CRÍTICO: Normalización y Enriquecimiento
        # Aquí se llenan los campos 'role_category', 'seniority', 'industry', etc.
        r_final = normalize_all(r_mapped) 
        
        # Aseguramos que el campo 'sector' use la categoría limpia si existe
        if r_final.get('role_category'):
            r_final['sector'] = r_final['role_category']
        elif r_final.get('keyword'):
             r_final['sector'] = r_final['keyword']
        else:
             r_final['sector'] = 'General Tech'
             
        # Limpieza final de campos intermedios
        r_final.pop('role_category', None)
        r_final.pop('keyword', None)

        return r_final


    def process(self, records: List[Dict]):
        """Normaliza, deduplica en memoria y envía a Supabase."""
        clean_records = [self.clean_record(r) for r in records if r]
        
        # 🚨 DEDUPLICACIÓN EN MEMORIA: Soluciona el error 'cannot affect row a second time'
        deduped_records = {}
        for record in clean_records:
            # Calculamos el hash (necesario para la deduplicación en memoria)
            record_hash = hash_job_record(record)
            deduped_records[record_hash] = record
            
        final_records = list(deduped_records.values())

        print(f"Total registros únicos a Supabase: {len(final_records)}")
        
        # Enviamos el lote limpio a la función de upsert en Supabase
        resp = upsert_jobs(final_records)
        return resp