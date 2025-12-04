# FILE: job-market-intelligence/scrapers/pipelines.py
import re
import hashlib
# MODIFICACIÓN: Importar el módulo datetime completo
import datetime
import os
from dotenv import load_dotenv
import logging

from database.supabase_client import SupabaseClient
from etl.cleaners import TextCleaner
from etl.normalizers import DataNormalizer
from etl.skill_extractor import SkillExtractor
from etl.sector_classifier import SectorClassifier

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CleaningPipeline:
    """Pipeline para limpiar y normalizar el texto de las vacantes."""
    def __init__(self):
        self.cleaner = TextCleaner()
        logging.info("Pipeline de Limpieza inicializado.")

    def process_item(self, item, spider):
        item['title'] = self.cleaner.clean_title(item.get('title'))
        item['company_name'] = self.cleaner.clean_whitespace(item.get('company_name'))
        item['description'] = self.cleaner.process_text(item.get('description'))
        item['requirements'] = self.cleaner.process_text(item.get('requirements'))

        if not item.get('job_id'):
            unique_string = f"{item.get('title', '')}{item.get('company_name', '')}{item.get('source_url', '')}"
            item['job_id'] = hashlib.md5(unique_string.encode()).hexdigest()

        item['scraped_at'] = datetime.datetime.now().isoformat() # FIX
        
        if not item.get('company_name'):
            item['company_name'] = "Empresa Desconocida"

        return item

class NormalizationPipeline:
    """Pipeline para normalizar campos como ubicación, tipo de trabajo y antigüedad."""
    def __init__(self):
        self.normalizer = DataNormalizer()
        logging.info("Pipeline de Normalización inicializado.")

    def process_item(self, item, spider):
        location_str = str(item.get('location')) if item.get('location') is not None else ''
        item['country'] = item.get('country') or self.normalizer.extract_country_from_location(location_str)
        item['seniority_level'] = item.get('seniority_level') or self.normalizer.normalize_seniority(None, item.get('title'))
        item['job_type'] = item.get('job_type') or self.normalizer.normalize_job_type(None, item.get('description'))

        if item.get('posted_date') and isinstance(item['posted_date'], str):
            try:
                item['posted_date'] = datetime.datetime.strptime(item['posted_date'], '%Y-%m-%d').date().isoformat() # FIX
            except ValueError:
                item['posted_date'] = None
                spider.logger.warning(f"No se pudo parsear posted_date en NormalizationPipeline para '{item.get('title')}': {item['posted_date']}")

        return item

class SkillExtractionPipeline:
    """Pipeline para extraer habilidades de la descripción de la vacante."""
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        logging.info("Pipeline de Extracción de Habilidades inicializado.")

    def process_item(self, item, spider):
        description_and_requirements = (item.get('description', '') or '') + ' ' + (item.get('requirements', '') or '')
        item['skills'] = self.skill_extractor.extract_skills(description_and_requirements)
        return item

class SectorClassificationPipeline:
    """Pipeline para clasificar la vacante en un sector (EdTech, Fintech, etc.)."""
    def __init__(self):
        self.sector_classifier = SectorClassifier()
        logging.info("Pipeline de Clasificación de Sector inicializado.")

    def process_item(self, item, spider):
        item['sector'] = item.get('sector') or self.sector_classifier.classify_sector(item)
        return item

class SupabasePipeline:
    """Pipeline final para almacenar los datos limpios en Supabase."""
    def __init__(self):
        self.client = None
        self.skill_extractor = SkillExtractor()
        logging.info("Pipeline de Supabase inicializado.")

    def open_spider(self, spider):
        try:
            self.client = SupabaseClient()
            logging.info("Conectado a Supabase desde el pipeline.")
        except Exception as e:
            logging.error(f"Error al conectar a Supabase en open_spider: {e}")
            self.client = None

    def process_item(self, item, spider):
        if not self.client:
            logging.error(f"No se pudo guardar la vacante '{item.get('title')}' porque el cliente de Supabase no está inicializado.")
            return item

        try:
            job_data = {k: v for k, v in dict(item).items() if v is not None}
            
            skills_to_insert = job_data.pop('skills', [])

            response = self.client.upsert_job(job_data)
            
            if response and response.data:
                db_job_id = response.data[0]['id']
                
                if skills_to_insert:
                    skill_records = []
                    for skill_name in skills_to_insert:
                        skill_records.append({
                            'job_id': db_job_id,
                            'skill_name': skill_name,
                            'skill_category': self.skill_extractor.categorize_skill(skill_name)
                        })
                    
                    self.client.insert_skills(skill_records)
                
                logging.info(f"✅ Vacante y habilidades guardadas: {item.get('title')} ({item.get('company_name')}) de {item.get('source_platform')}")
            else:
                logging.warning(f"⚠️ No se pudo guardar la vacante '{item.get('title')}' o no se recibió ID de respuesta. Response: {response}")

        except Exception as e:
            logging.error(f"❌ Error al guardar en Supabase: {str(e)}. Vacante: {item.get('title')}")
        return item

    def close_spider(self, spider):
        logging.info("Cerrando conexión de Supabase desde el pipeline.")
