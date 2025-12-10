import scrapy
import logging
import urllib.parse
import json
import os
import re
from typing import List, Dict, Any, Optional
import yaml
from jobscraper.items import JobItem 


class LinkedInSpider(scrapy.Spider):
    """
    Spider para scraping de ofertas de trabajo en LinkedIn.
    Carga keywords (roles) desde config.yaml.
    """
    name = "linkedin"
    allowed_domains = ["linkedin.com"]
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    # Mapeo de regiones metropolitanas a sus países para el filtrado.
    METRO_AREA_MAP = {
        'argentina': ['greater buenos aires', 'greater rosario', 'gran buenos aires', 'la plata'],
        'chile': ['santiago metropolitan area', 'región metropolitana de santiago', 'valparaíso'],
        'peru': ['lima metropolitan area', 'callao'],
        'colombia': ['bogotá d.c. metropolitan area', 'bogotá', 'medellín'],
        'mexico': ['mexico city metropolitan area', 'ciudad de méxico', 'cdmx', 'guadalajara', 'monterrey'],
        'ecuador': ['quito metropolitan area', 'guayaquil metropolitan area', 'quito', 'guayaquil'],
    }

    custom_settings = {
        'ROBOTSTXT_OBEY': False, 
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def __init__(self, target_locations=None, f_tpr_value="", start_date_filter=None, end_date_filter=None, continent_search=None, *args, **kwargs):
        super(LinkedInSpider, self).__init__(*args, **kwargs)

        self.target_locations = target_locations if target_locations else ["Latam"]  
        self.f_tpr_value = f_tpr_value
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.continent_search = continent_search 
        
        # Carga de palabras clave (roles) desde config.yaml
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.keywords = config.get('roles', []) 
                
            if not self.keywords:
                self.logger.warning(f"No se encontraron roles en '{config_path}', usando valores por defecto.")
                self.keywords = ['Data Analyst', 'Full Stack', 'Product Manager']
                
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error(f"Error cargando roles desde config.yaml ({e}), usando valores por defecto.")
            self.keywords = ['Data Analyst', 'Full Stack', 'Product Manager']

    def start_requests(self):
        for k in self.keywords:
            for loc in self.target_locations:
                search_location = loc if loc != "Todos los Países" else (self.continent_search if self.continent_search else 'Latam')  
                
                for start_index in range(0, 100, 25): 
                    
                    params = {
                        'keywords': k,
                        'location': search_location,
                        'start': start_index
                    }
                    if self.f_tpr_value: 
                        params['f_TPR'] = self.f_tpr_value

                    query_string = urllib.parse.urlencode(params)
                    url = f'{self.base_url}?{query_string}'
                    
                    self.logger.info(f"Spider Request: Solicitando URL para KWORD='{k}', LOC_BUSCADA='{loc}': {url}") 
                    
                    yield scrapy.Request(
                        url, 
                        callback=self.parse, 
                        meta={
                            'keyword': k, 
                            'location_search': loc, 
                            'continent_search': self.continent_search 
                        },
                        errback=self.errback_httpbin
                    )

    def parse(self, response):
        jobs = response.css('li')
        
        if not jobs:
            self.logger.info(f"ℹ️ No se encontraron vacantes en: {response.url}")
            return

        for job in jobs:
            try:
                item = JobItem()
                
                title = job.css('h3.base-search-card__title::text').get(default='').strip()
                url = job.css('a.base-card__full-link::attr(href)').get()
                location = job.css('span.job-search-card__location::text').get(default='').strip()
                posted_date = job.css('time::attr(datetime)').get()
                
                job_id_match = re.search(r'(\d{10,})(?:\?|/|$)', str(url))
                job_id = job_id_match.group(1) if job_id_match else None
                
                # Extracción robusta de compañía
                company = job.css('h4.base-search-card__subtitle::text').get(default='').strip()
                if not company: company = job.css('h4.base-search-card__subtitle a::text').get(default='').strip()  
                
                if not posted_date:
                    posted_date = datetime.date.today().isoformat()

                # 📝 Mapeo al JobItem
                item['job_id'] = job_id
                item['title'] = title
                item['company_name'] = company
                item['source_url'] = url
                item['location'] = location
                item['posted_date'] = posted_date
                item['source_platform'] = 'LinkedIn'
                item['country'] = response.meta['location_search']
                
                # Inicialización de campos para el Pipeline ETL
                item['sector'] = response.meta['keyword'] 
                item['description'] = f"Vacante: {title} en {company}. Ubicación: {location}. Enlace: {url}"
                item['seniority_level'] = 'N/A'
                item['skills'] = []
                item['salary_range'] = None
                
                if title and url and company:
                    if self.should_process_location(response.meta['location_search'], location, url, title):
                        yield item
                else:
                    self.logger.warning(f"❌ Saltando item sin título/url/empresa. URL: {url}")
                    
            except Exception as e:
                self.logger.error(f"Error parseando item: {e}")

    def should_process_location(self, target_loc_search: str, extracted_loc: str, url: str, title: str) -> bool:
        """
        Lógica robusta de filtrado de ubicación que acepta regiones metropolitanas y remotos.
        """
        if not extracted_loc or not target_loc_search: return False

        target_loc_lower = target_loc_search.lower()
        extracted_loc_lower = extracted_loc.lower()
        is_match = False

        # Caso 1: Coincidencia directa del país de búsqueda
        if target_loc_lower in extracted_loc_lower: is_match = True

        # Caso 2: Coincidencia por Región Metropolitana
        if not is_match and target_loc_lower in self.METRO_AREA_MAP:
            for area in self.METRO_AREA_MAP[target_loc_lower]:
                if area in extracted_loc_lower:
                    is_match = True
                    break
        
        # Caso 3: Palabras clave de ubicación remota
        if not is_match:
            remote_keywords = ["remote", "remoto", "work from home", "home office"]
            if any(kw in extracted_loc_lower for kw in remote_keywords): is_match = True
        
        # Caso 4: Lógica LATAM
        if target_loc_lower in ("latam", "latinoamérica", "latin america", "latin-america"):
            latam_countries = [
                "argentina", "chile", "mexico", "méxico", "peru", "perú", "colombia", "ecuador", 
                "uruguay", "paraguay", "bolivia", "costa rica", "panama", "panamá"
            ]
            if any(country in extracted_loc_lower for country in latam_countries): is_match = True

        if not is_match:
            self.logger.warning(f"❌ Vacante filtrada: Ubicación extraída ('{extracted_loc}') no coincide con la búsqueda ('{target_loc_search}') para '{title}'.")
            return False
        
        return True

    def errback_httpbin(self, failure):
        self.logger.error(f"❌ Request fallido: {failure.request.url} - Razón: {failure.value}")