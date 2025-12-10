# ETL Pipeline for cleaning, normalizing, and storing data - VERSIÓN FINAL y ESTABLE
# =============================================================================

import re
import hashlib
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv
from scrapy.exceptions import DropItem 
import yaml
from typing import List, Dict, Any

# 🚨 IMPORTACIONES MODULARES
from .enrichers.company_enricher import CompanyEnricher
from .enrichers.skill_extractor import SkillExtractor

# Cargar variables de entorno (necesario para Supabase)
load_dotenv()


# =============================================================================
# 1. CLEANING PIPELINE (PRIORIDAD 100) - DEDUPLICACIÓN MULTICANAL
# =============================================================================

class CleaningPipeline:
    """ Limpieza, normalización y deduplicación en batch. """
    def __init__(self):
        self.job_ids_seen = set()

    def process_item(self, item, spider):
        # 1. Limpieza básica
        if item.get('title'): item['title'] = self.clean_text(item['title'])
        if item.get('company_name'): item['company_name'] = self.clean_text(item['company_name'])
        if item.get('description'): item['description'] = self.clean_html(item['description'])
        
        # 2. Generar ID Único (Incluye Plataforma)
        if not item.get('job_id'): item['job_id'] = self.generate_job_id(item)
        
        # 3. Deduplicación
        job_id = item['job_id']
        if job_id in self.job_ids_seen:
            spider.logger.info(f"❌ Duplicado de batch descartado: {item['title']} - ID: {job_id}")
            raise DropItem(f"Duplicado: {job_id}")
        self.job_ids_seen.add(job_id)

        # 4. Normalización de ubicación y tiempo
        if item.get('location') and not item.get('country'):
            inferred_country = self.extract_country(item['location'])
            if inferred_country:
                item['country'] = inferred_country
        item['scraped_at'] = datetime.now().isoformat()
        
        return item
    
    # Métodos estáticos
    @staticmethod
    def clean_text(text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def clean_html(html_text):
        if not html_text: return ""
        clean = re.sub(r'<[^>]+>', '', html_text)
        return CleaningPipeline.clean_text(clean)
    
    @staticmethod
    def extract_country(location):
        countries = {
            'Mexico': ['mexico', 'cdmx', 'ciudad de mexico', 'guadalajara', 'monterrey'],
            'Colombia': ['colombia', 'bogota', 'medellin', 'cali'],
            'Argentina': ['argentina', 'buenos aires', 'cordoba', 'rosario'],
            'Chile': ['chile', 'santiago', 'valparaiso'],
            'Peru': ['peru', 'lima', 'arequipa'],
            'Brazil': ['brazil', 'brasil', 'sao paulo', 'rio de janeiro']
        }
        location_lower = location.lower()
        for country, keywords in countries.items():
            if any(keyword in location_lower for keyword in keywords):
                return country
        return None
    
    @staticmethod
    def generate_job_id(item):
        """Genera un job_id único incluyendo la plataforma para la deduplicación multicanal."""
        unique_string = (
            f"{item.get('title', '')}"
            f"{item.get('company_name', '')}"
            f"{item.get('location', '')}" 
            f"{item.get('source_platform', '')}" # INCLUYE PLATAFORMA
        )
        return hashlib.md5(unique_string.encode()).hexdigest()


# =============================================================================
# 2. SENIORITY PIPELINE (PRIORIDAD 150) - Inferencia de Nivel FINAL
# =============================================================================

class SeniorityPipeline:
    """ 
    Clasifica el nivel de senioridad, usando heurística agresiva para reducir 
    "Sin Nivel Específico" (Asigna 'Mid' a roles técnicos genéricos).
    """
    
    SENIORITY_MAP = {
        'Executive': ['vp', 'vice president', 'cxo', 'ceo', 'cmo', 'cto', 'co-founder', 'founder', 'director'],
        'Lead / Manager': ['lead', 'manager', 'head of', 'jefe', 'coordinador', 'principal', 'staff', 'team lead'],
        'Senior': ['senior', 'sr.', 'sr', 'advanced', 'expert'],
        'Mid': ['mid', 'semi-senior', 'semisenior', 'regular', 'intermedio'],
        'Junior': ['junior', 'jr.', 'jr', 'entry-level', 'trainee', 'practicante', 'pasante', 'asistente', 'early career'],
    }
    
    def process_item(self, item, spider):
        if not item.get('seniority_level') or item.get('seniority_level') == 'N/A' or item.get('seniority_level') == 'Sin Nivel Específico':
            item['seniority_level'] = self.classify_seniority(item)
        return item
    
    def classify_seniority(self, item):
        text = (
            str(item.get('title') or '') + ' ' + 
            str(item.get('description') or '')
        ).lower()
        
        # 1. Búsqueda explícita (De Executive a Junior)
        for level, keywords in self.SENIORITY_MAP.items():
            if any(re.search(r'\b' + re.escape(keyword) + r'\b', text) for keyword in keywords):
                return level
        
        # 2. Heurística forzada: Asignar 'Mid' a roles técnicos base sin prefijo
        implicit_mid_keywords = [
            'engineer', 'developer', 'analyst', 'specialist', 'architect', 
            'programador', 'consultor', 'diseñador', 'owner', 'scrum master' 
        ]
        
        if any(keyword in text for keyword in implicit_mid_keywords):
             return 'Mid' # Asignamos a MID por defecto si encontramos un rol técnico base
        
        return 'Sin Nivel Específico'


# =============================================================================
# 3. COMPANY ENRICHMENT PIPELINE (PRIORIDAD 250)
# =============================================================================

class CompanyEnrichmentPipeline:
    """ Enriquecimiento de Empresa usando lógica heurística modular. """
    
    def __init__(self):
        self.enricher = CompanyEnricher() 

    def process_item(self, item, spider):
        company_name = item.get('company_name')
        if not company_name: return item

        enrichment_data = self.enricher.enrich_company_info(company_name)
        
        # Mapeo a JobItem (usando nombres estandarizados)
        item['company_size'] = enrichment_data.get('tamaño', 'N/A')
        item['company_industry'] = enrichment_data.get('industria', 'N/A')
        item['company_contact'] = enrichment_data.get('contacto', 'N/A') 
        item['company_hq_country'] = enrichment_data.get('pais_sede', 'N/A')
        item['company_type'] = enrichment_data.get('tipo_empresa', 'N/A')
        
        return item


# =============================================================================
# 4. SKILL EXTRACTION PIPELINE (PRIORIDAD 300)
# =============================================================================

class SkillExtractionPipeline:
    """ Extracción de Habilidades usando el módulo SkillExtractor. """
    
    def __init__(self):
        self.extractor = SkillExtractor() 

    def process_item(self, item, spider):
        description = item.get('description', '') + ' ' + item.get('requirements', '')
        extracted_skills = self.extractor.extract_skills(description)
        item['skills'] = extracted_skills
        return item


# =============================================================================
# 5. SECTOR CLASSIFICATION PIPELINE (PRIORIDAD 350) - Clasificación FINAL
# =============================================================================

class SectorClassificationPipeline:
    """ 
    Clasificación de Sector, priorizando el nicho específico sobre el valor genérico 
    "Tecnología" de la empresa.
    """
    
    def __init__(self):
        self.SECTOR_KEYWORDS = self._load_sector_keywords()

    def _load_sector_keywords(self):
        """Carga la definición de sectores desde config.yaml."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                sector_data = {}
                for sector_name, details in config.get('sectors', {}).items():
                    sector_data[sector_name.replace('_', ' ').title()] = details.get('keywords', [])
                return sector_data
        except Exception:
            # Fallback simple si la carga falla
            return {
                'EdTech': ['education', 'learning', 'edtech'],
                'Fintech': ['fintech', 'financial', 'payment'],
                'Future of Work': ['remote work', 'collaboration']
            }
            
    def process_item(self, item, spider):
        company_industry = item.get('company_industry')
        specific_sector = self.classify_sector(item) # Usa keywords del YAML
        
        # 1. Caso de industria específica de la empresa (ej. "Retail", "Salud"). Se respeta.
        if company_industry and company_industry not in ['N/A', 'Other', 'Tecnología', 'Software']:
            item['sector'] = company_industry
            return item

        # 2. Si encontramos un nicho por palabra clave (Fintech, EdTech, etc.), lo usamos.
        if specific_sector != 'Other':
            item['sector'] = specific_sector
            return item
        
        # 3. No encontramos nicho, usamos la industria general de la empresa (Tecnología, si existe)
        if company_industry and company_industry not in ['N/A', 'Other']:
            item['sector'] = company_industry
        else:
            # Fallback final
            item['sector'] = 'Other'
            
        return item
    
    def classify_sector(self, item):
        text = (str(item.get('title') or '') + ' ' + str(item.get('description') or '')).lower()
        
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            # Buscar keywords con límites de palabra
            if any(re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text) for keyword in keywords):
                return sector
        return 'Other'


# =============================================================================
# 6. SUPABASE PIPELINE (PRIORIDAD 500)
# =============================================================================

class SupabasePipeline:
    """ Persistencia en DB, incluyendo prueba de conexión robusta y manejo de errores aislados. """
    
    def __init__(self):
        self.client = None
        self.table_name_jobs = 'jobs'
        self.table_name_skills = 'skills'
        self.skill_extractor = SkillExtractor() 
    
    def open_spider(self, spider):
        """Inicializa la conexión y prueba la autenticación."""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            spider.logger.error("❌ ERROR CRÍTICO: Credenciales de Supabase no encontradas en .env.")
            return
        
        try:
            self.client = create_client(supabase_url, supabase_service_key)
            self.client.table(self.table_name_jobs).select('job_id').limit(1).execute() 
            spider.logger.info("✅ CONEXIÓN EXITOSA A SUPABASE.")
        except Exception as e:
            spider.logger.error(f"❌ ERROR CRÍTICO AL CONECTAR/AUTENTICAR CON SUPABASE: {e}")
            self.client = None


    def process_item(self, item, spider):
        if not self.client: return item
             
        # 1. Preparación de job_data
        job_data = {
             'job_id': item.get('job_id'), 'title': item.get('title'),
             'company_name': item.get('company_name'), 'location': item.get('location'),
             'country': item.get('country'), 'job_type': item.get('job_type'), 
             'seniority_level': item.get('seniority_level'), 'sector': item.get('sector'),
             'description': item.get('description'), 'requirements': item.get('requirements'),
             'salary_range': item.get('salary_range'), 'posted_date': item.get('posted_date'),
             'source_url': item.get('source_url'), 'source_platform': item.get('source_platform'),
             'scraped_at': item.get('scraped_at'),
             # Campos de enriquecimiento
             'company_size': item.get('company_size'), 'company_industry': item.get('company_industry'),
             'company_contact': item.get('company_contact'), 'company_hq_country': item.get('company_hq_country'),
             'company_type': item.get('company_type'),
        }
        
        try:
            # 2. Upsert (Inserta o Actualiza en la tabla 'jobs')
            response = self.client.table(self.table_name_jobs).upsert(job_data).execute()
            
            # 3. Insertar Skills (BLOQUE AISLADO DE ERROR)
            if item.get('skills') and response.data:
                try:
                    job_internal_id = response.data[0]['id'] 
                    
                    self.client.table(self.table_name_skills).delete().eq('job_id', job_internal_id).execute()
                    
                    skill_records = []
                    for skill in item['skills']:
                        skill_records.append({
                            'job_id': job_internal_id, 
                            'skill_name': skill,
                            'skill_category': self.skill_extractor.categorize_skill(skill) 
                        })
                    
                    self.client.table(self.table_name_skills).insert(skill_records).execute()
                    
                except Exception as e:
                    # Si el error es solo en skills, logeamos y continuamos
                    spider.logger.error(f"❌ Error al insertar SKILLS para Job ID {item.get('job_id')}: {str(e)}")
            
            spider.logger.info(f"✅ Guardado/Actualizado: {item.get('title')} en {item.get('company_name')}")
            
        except Exception as e:
            # Si el error es en la tabla jobs, es un error crítico
            # 🚨 SINTAXIS CORREGIDA: La línea ahora termina correctamente
            spider.logger.error(f"❌ Error CRÍTICO al guardar en tabla JOBS (Job ID: {item.get('job_id')}): {str(e)}")
            
        return item
    
    def close_spider(self, spider):
        spider.logger.info("Cerrando el proceso de persistencia de Supabase.")