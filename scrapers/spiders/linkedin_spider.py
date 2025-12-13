# FILE: Proyecto/job-market-intelligence/scrapers/spiders/linkedin_spider.py
import scrapy
from scrapers.items import JobItem
import datetime
import re
import urllib.parse
import json
import os
import logging
from scrapy.exceptions import CloseSpider

class LinkedInSpider(scrapy.Spider):
    name = "linkedin_spider"
    allowed_domains = ["linkedin.com"]
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 15,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, keywords=None, target_locations=None, f_tpr_value="", start_date_filter=None, end_date_filter=None, max_jobs_to_scrape=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.keywords = keywords if keywords else []
        self.target_locations = target_locations if target_locations else ["Latam"] 
        self.f_tpr_value = f_tpr_value
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.max_jobs_to_scrape = max_jobs_to_scrape
        self.scraped_count = 0 

        logging.info(f"LinkedInSpider inicializado con keywords: {self.keywords}, ubicaciones: {self.target_locations}, f_TPR: {self.f_tpr_value}, Max Jobs: {self.max_jobs_to_scrape}")

    # CAMBIO CRÍTICO: Renombrar start_requests a start y asegurar que sea async def
    async def start(self): # <--- CAMBIO AQUÍ
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Cerrando spider.")
            raise CloseSpider("Max jobs already scraped at spider start.")

        for k in self.keywords:
            for loc in self.target_locations:
                if self.scraped_count >= self.max_jobs_to_scrape:
                    self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{k}' en '{loc}'.")
                    raise CloseSpider("Max jobs scraped within keyword/location loop.")

                search_location_param = loc 
                
                max_start_index = min(975, (self.max_jobs_to_scrape // 25 + 1) * 25)

                for start_index in range(0, max_start_index, 25):
                    if self.scraped_count >= self.max_jobs_to_scrape:
                        self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{k}' en '{loc}'.")
                        raise CloseSpider("Max jobs scraped within pagination loop.")
                        
                    params = {
                        'keywords': k,
                        'location': search_location_param, 
                        'start': start_index
                    }
                    if self.f_tpr_value: 
                        params['f_TPR'] = self.f_tpr_value

                    query_string = urllib.parse.urlencode(params)
                    url = f'{self.base_url}?{query_string}'
                    
                    self.logger.info(f"LinkedIn Request: KWORD='{k}', LOC='{loc}', START={start_index}: {url}") 
                    
                    yield scrapy.Request(
                        url, 
                        callback=self.parse, 
                        meta={
                            'keyword_search': k, 
                            'location_search': loc,
                            'f_tpr_value': self.f_tpr_value
                        },
                        errback=self.errback_httpbin
                    )

    # El método parse puede seguir siendo síncrono o asíncrono según su implementación.
    # Como actualmente usa 'yield item' directamente, puede quedarse síncrono.
    def parse(self, response):
        jobs = response.css('li')
        # ... (resto del código de parse) ...
        # (Sin cambios en este método, solo se renombra start_requests a start)
        self.logger.info(f"LinkedIn Parse: Procesando URL: {response.url} (KWORD='{response.meta['keyword_search']}', LOC_BUSCADA='{response.meta['location_search']}')")

        if not jobs:
            self.logger.info(f"ℹ️ No se encontraron más vacantes en: {response.url}")
            return

        self.logger.info(f"🔎 Encontradas {len(jobs)} tarjetas de vacantes en {response.url}")

        for job in jobs:
            if self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Cerrando spider.")
                raise CloseSpider("Max jobs scraped in parse method.") 

            try:
                item = JobItem()
                
                title = job.css('h3.base-search-card__title::text').get(default='').strip()
                
                company_name = job.css('h4.base-search-card__subtitle::text').get(default='').strip()
                if not company_name: 
                    company_name = job.css('h4.base-search-card__subtitle a::text').get(default='').strip()
                if not company_name:
                    company_name = job.css('span.job-result-card__subtitle a::text').get(default='').strip()
                if not company_name:
                    company_name = job.xpath('.//h4[contains(@class, "base-search-card__subtitle")]/text()').get(default='').strip()
                if not company_name:
                    company_name = "Empresa Desconocida"

                source_url = job.css('a.base-card__full-link::attr(href)').get()
                
                location = job.css('span.job-search-card__location::text').get(default='').strip()
                if not location:
                    location = job.css('div.base-search-card__metadata span.base-search-card__label::text').get(default='').strip()


                posted_date_str = job.css('time::attr(datetime)').get()
                posted_date = None
                if posted_date_str:
                    try:
                        posted_date = datetime.datetime.strptime(posted_date_str, '%Y-%m-%d').date().isoformat()
                    except ValueError:
                        self.logger.warning(f"No se pudo parsear posted_date para LinkedIn: {posted_date_str}. Usando fecha de scraping.")
                        posted_date = datetime.datetime.now().date().isoformat()
                else:
                    posted_date = datetime.datetime.now().date().isoformat()

                job_id = None
                if source_url:
                    job_id_match = re.search(r'(\d{10,})(?:\?|/|$)', source_url)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                    else:
                        job_id_attr = job.css('div.base-card::attr(data-entity-urn)').get()
                        if job_id_attr and 'urn:li:jobPosting:' in job_id_attr:
                            job_id = job_id_attr.split(':')[-1]
                
                item['job_id'] = job_id
                item['title'] = title
                item['company_name'] = company_name
                item['source_url'] = source_url
                item['location'] = location
                item['country'] = response.meta['location_search']
                item['sector'] = response.meta['keyword_search']
                item['posted_date'] = posted_date
                item['source_platform'] = 'LinkedIn'
                item['scraped_at'] = datetime.datetime.now().isoformat()
                
                item['description'] = f"Vacante: {title} en {company_name}. Ubicación: {location}."
                item['requirements'] = None
                item['salary_range'] = None
                item['job_type'] = None
                item['seniority_level'] = None
                item['is_active'] = True
                item['skills'] = []
                item['role_category'] = None

                if not self.should_process_location(response.meta['location_search'], location, title):
                    continue
                    
                if title and source_url and job_id:
                    self.scraped_count += 1 
                    yield item
                else:
                    missing_fields = []
                    if not title: missing_fields.append('title')
                    if not source_url: missing_fields.append('URL')
                    if not job_id: missing_fields.append('job_id')
                    self.logger.warning(f"⚠️ Vacante incompleta (faltan: {', '.join(missing_fields)}): URL={source_url}, Title={title}. Descartando.")
            except Exception as e:
                self.logger.error(f"Error parseando item en LinkedInSpider: {e}", exc_info=True)


    def should_process_location(self, target_loc_search: str, extracted_loc: str, title: str) -> bool:
        """
        Lógica robusta de filtrado de ubicación que acepta regiones metropolitanas y remotos.
        Se usa el mapa de METRO_AREA_MAP para mejorar la coincidencia.
        """
        METRO_AREA_MAP = {
            'argentina': ['greater buenos aires', 'greater rosario', 'gran buenos aires', 'la plata'],
            'chile': ['santiago metropolitan area', 'región metropolitana de santiago', 'valparaíso'],
            'peru': ['lima metropolitan area', 'callao'],
            'colombia': ['bogotá d.c. metropolitan area', 'bogotá', 'medellín'],
            'mexico': ['mexico city metropolitan area', 'ciudad de méxico', 'cdmx', 'guadalajara', 'monterrey'],
            'ecuador': ['quito metropolitan area', 'guayaquil metropolitan area', 'quito', 'guayaquil'],
            'brasil': ['são paulo', 'rio de janeiro', 'distrito federal']
        }

        if not extracted_loc or not target_loc_search: return False

        target_loc_lower = target_loc_search.lower()
        extracted_loc_lower = extracted_loc.lower()
        is_match = False

        if target_loc_lower in extracted_loc_lower: 
            is_match = True

        if not is_match and target_loc_lower in METRO_AREA_MAP:
            for area in METRO_AREA_MAP[target_loc_lower]:
                if area in extracted_loc_lower:
                    is_match = True
                    break
        
        if not is_match:
            remote_keywords = ["remote", "remoto", "work from home", "home office", "a distancia", "anywhere"]
            if any(kw in extracted_loc_lower for kw in remote_keywords): 
                is_match = True
        
        if target_loc_lower in ("latam", "latinoamérica", "latin america", "latin-america"):
            from config.geo import COMMON_GEO_DATA
            latam_countries_lower = [c.lower() for c in COMMON_GEO_DATA.get("Latam", [])]
            if any(country_name in extracted_loc_lower for country_name in latam_countries_lower): 
                is_match = True

        if not is_match:
            self.logger.info(f"❌ Vacante filtrada: Ubicación extraída ('{extracted_loc}') no coincide con la búsqueda ('{target_loc_search}') para '{title}'.")
            return False
        
        return True

    def errback_httpbin(self, failure):
        request = failure.request
        self.logger.error(f"❌ Request fallido: {failure.request.url} - Razón: {failure.value}")