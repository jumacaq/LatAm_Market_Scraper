# FILE: Proyecto/job-market-intelligence/scrapers/pipelines.py
import re
import hashlib
import datetime
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List

from database.supabase_client import SupabaseClient
from etl.cleaners import TextCleaner
from etl.normalizers import DataNormalizer
from etl.skill_extractor import SkillExtractor
from etl.sector_classifier import SectorClassifier
from etl.enrichment import CompanyEnricher # Importamos el CompanyEnricher

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CleaningPipeline:
    """Pipeline para limpiar y normalizar el texto de las vacantes y generar job_id si es necesario."""
    def __init__(self):
        self.cleaner = TextCleaner()
        logging.info("Pipeline de Limpieza inicializado.")

    def process_item(self, item, spider):
        item['title'] = self.cleaner.clean_title(item.get('title'))
        item['company_name'] = self.cleaner.clean_whitespace(item.get('company_name'))
        item['description'] = self.cleaner.process_text(item.get('description'))
        item['requirements'] = self.cleaner.process_text(item.get('requirements'))

        # Generar un job_id único si no existe, usando un hash de campos clave
        if not item.get('job_id'):
            unique_string = f"{item.get('title', '')}-{item.get('company_name', '')}-{item.get('location', '')}-{item.get('source_platform', '')}"
            item['job_id'] = hashlib.md5(unique_string.encode()).hexdigest()

        item['scraped_at'] = datetime.datetime.now().isoformat()
        
        if not item.get('company_name'):
            item['company_name'] = "Empresa Desconocida"

        return item

class NormalizationPipeline:
    """
    Pipeline para normalizar campos como país, tipo de trabajo, antigüedad y categoría de rol.
    Integra la lógica de DataNormalizer y clasifica el rol.
    """
    def __init__(self):
        self.normalizer = DataNormalizer()
        logging.info("Pipeline de Normalización inicializado.")

    def process_item(self, item, spider):
        # Normalización del País
        location_str = str(item.get('location')) if item.get('location') is not None else ''
        # Primero intenta usar el país de la meta del spider, luego lo infiere de la ubicación
        item['country'] = item.get('country') or self.normalizer.extract_country_from_location(location_str)
        if not item.get('country'): # Si aún no se detecta, intentamos inferir de la location de búsqueda
             item['country'] = item.get('location_search') # location_search es el país o continente de la búsqueda

        # Normalización del Nivel de Senioridad
        # Usa el seniority_level ya extraído por el spider o lo infiere del título/descripción
        item['seniority_level'] = item.get('seniority_level') or self.normalizer.normalize_seniority(
            item.get('seniority_level'), item.get('title'), item.get('description')
        )

        # Normalización del Tipo de Trabajo
        item['job_type'] = item.get('job_type') or self.normalizer.normalize_job_type(
            item.get('job_type'), item.get('description') # Pasa job_type si ya viene del spider
        )

        # Clasificación de la Categoría de Rol
        item['role_category'] = self.normalizer.classify_role_category(item.get('title'))

        # Asegurar formato de fecha ISO para 'posted_date'
        if item.get('posted_date') and isinstance(item['posted_date'], str):
            try:
                # Si viene con hora, se queda solo la fecha
                item['posted_date'] = datetime.datetime.strptime(item['posted_date'].split('T')[0], '%Y-%m-%d').date().isoformat()
            except ValueError:
                spider.logger.warning(f"No se pudo parsear posted_date en NormalizationPipeline para '{item.get('title')}': {item['posted_date']}. Usando None.")
                item['posted_date'] = None
        elif not item.get('posted_date'):
            item['posted_date'] = datetime.date.today().isoformat() # Por defecto, la fecha de hoy si no se encuentra

        return item

class CompanyEnrichmentPipeline:
    """
    Pipeline para enriquecer datos de compañía usando CompanyEnricher.
    Añade información como tamaño, industria, país de sede y tipo de compañía.
    """
    def __init__(self):
        self.enricher = CompanyEnricher()
        logging.info("Pipeline de Enriquecimiento de Compañía inicializado.")

    def process_item(self, item, spider):
        company_name = item.get('company_name')
        if not company_name:
            company_name = "Empresa Desconocida" # Asegura un nombre para el enriquecimiento
            item['company_name'] = company_name

        enrichment_data = self.enricher.enrich_company_info(company_name)
        
        # Mapeo a JobItem
        item['company_size'] = enrichment_data.get('size')
        item['company_industry'] = enrichment_data.get('industry')
        item['company_hq_country'] = enrichment_data.get('hq_country')
        item['company_type'] = enrichment_data.get('type')
        item['company_website'] = enrichment_data.get('website')
        
        return item

class SkillExtractionPipeline:
    """Pipeline para extraer habilidades de la descripción de la vacante."""
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        logging.info("Pipeline de Extracción de Habilidades inicializado.")

    def process_item(self, item, spider):
        # Combina título, descripción y requisitos para una extracción de habilidades más completa
        text_for_skills = (
            str(item.get('title', '') or '') + ' ' + 
            str(item.get('description', '') or '') + ' ' + 
            str(item.get('requirements', '') or '')
        )
        item['skills'] = self.skill_extractor.extract_skills(text_for_skills)
        return item

class SectorClassificationPipeline:
    """
    Pipeline para clasificar la vacante en un sector.
    Prioriza la clasificación por keywords y luego puede usar la industria de la compañía.
    """
    def __init__(self):
        self.sector_classifier = SectorClassifier()
        logging.info("Pipeline de Clasificación de Sector inicializado.")

    def process_item(self, item, spider):
        # 1. Intentar clasificar por keywords en el título/descripción
        classified_sector = self.sector_classifier.classify_sector(item)
        
        # 2. Si se clasifica, usar ese sector.
        if classified_sector != 'Other':
            item['sector'] = classified_sector
        else:
            # 3. Si no, usar la industria de la compañía (si ya está enriquecida)
            company_industry = item.get('company_industry')
            if company_industry and company_industry not in ['No especificado', 'Tecnología/Software']:
                item['sector'] = company_industry
            else:
                # 4. Fallback final, puede usar la categoría de rol o un genérico
                item['sector'] = item.get('role_category') or 'General Tech' # Puede ser "General Tech" o "Other"

        return item

class SupabasePipeline:
    """Pipeline final para almacenar los datos limpios y enriquecidos en Supabase."""
    def __init__(self):
        self.client = None
        self.skill_extractor = SkillExtractor() # Para categorizar las skills al guardar
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

        # Convertir Scrapy Item a diccionario, filtrando None y habilidades
        job_data = {k: v for k, v in dict(item).items() if v is not None}
        skills_to_insert = job_data.pop('skills', []) # Las habilidades se insertan por separado
        
        # Campos de compañía que se upsertarán en la tabla 'companies'
        company_name = job_data.get('company_name', 'Empresa Desconocida')
        company_data = {
            'name': company_name,
            'industry': job_data.pop('company_industry', None),
            'country': job_data.pop('company_hq_country', None),
            'website': job_data.pop('company_website', None),
            'size': job_data.pop('company_size', None),
            'type': job_data.pop('company_type', None),
        }
        
        # Aseguramos que 'role_category' no se guarde directamente en 'jobs' si no es una columna.
        # Si 'jobs' tiene 'role_category', entonces no lo hagamos pop.
        job_data.pop('role_category', None) # Asumimos que 'jobs' no tiene esta columna, o se mapea a 'sector'

        try:
            # 1. Upsertar/obtener la compañía y su ID
            company_response = self.client.upsert_company(company_data)
            db_company_id = None
            if company_response and company_response.data:
                db_company_id = company_response.data[0]['id']
                logging.debug(f"Compañía '{company_name}' upsertada o encontrada, ID: {db_company_id}")
            else:
                logging.warning(f"No se pudo upsertar la compañía '{company_name}' o no se recibió ID. Response: {company_response.data if company_response else 'N/A'}")
            
            # 2. Si el esquema de 'jobs' tiene 'company_id' (FK a companies.id), añadimos.
            # *CRÍTICO*: Si tu tabla `jobs` NO tiene una columna `company_id`, ¡esta línea debe ser eliminada!
            if db_company_id:
                job_data['company_id'] = db_company_id
            
            # 3. Upsertar la vacante
            response = self.client.upsert_job(job_data)
            
            if response and response.data:
                db_job_id = response.data[0]['id']
                logging.info(f"✅ Vacante '{item.get('title')}' ({item.get('company_name')}) guardada en 'jobs', ID en DB: {db_job_id}")
                
                # 4. Eliminar habilidades antiguas y luego insertar las nuevas para esa vacante
                if db_job_id:
                    self.client.supabase.table("skills").delete().eq('job_id', db_job_id).execute()
                    if skills_to_insert:
                        skill_records = []
                        for skill_name in skills_to_insert:
                            skill_records.append({
                                'job_id': db_job_id,
                                'skill_name': skill_name,
                                'skill_category': self.skill_extractor.categorize_skill(skill_name)
                            })
                        
                        skill_response = self.client.insert_skills(skill_records)
                        if skill_response and skill_response.data:
                            logging.info(f"✅ Habilidades ({len(skill_records)}) guardadas para la vacante '{item.get('title')}'.")
                        else:
                            logging.warning(f"⚠️ No se pudieron guardar habilidades para la vacante '{item.get('title')}' (ID: {db_job_id}). Respuesta: {skill_response.data if skill_response else 'N/A'}")
                    else:
                        logging.debug(f"DEBUG: No hay habilidades para insertar para la vacante '{item.get('title')}'.")
                else:
                    logging.warning(f"⚠️ No hay ID de vacante para enlazar habilidades para '{item.get('title')}'. Habilidades no guardadas.")

            else:
                logging.warning(f"⚠️ No se pudo guardar la vacante '{item.get('title')}' o no se recibió ID de respuesta. Respuesta de Supabase: {response.data if response else 'N/A'}")

        except Exception as e:
            logging.error(f"❌ Error crítico al guardar en Supabase: {e}. Vacante: {item.get('title')}. Datos enviados: {job_data}", exc_info=True)
        return item

    def close_spider(self, spider):
        logging.info("Cerrando conexión de Supabase desde el pipeline.")
