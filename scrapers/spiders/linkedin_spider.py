# scrapers/spiders/linkedin_spider.py (VERSIÓN FINAL CON EARLY EXIT)

import scrapy
import datetime
import re
import urllib.parse
import logging
from typing import Dict, Any

class LinkedInScrapySpider(scrapy.Spider):
    name = "linkedin_api_scraper"
    allowed_domains = ["linkedin.com"]
    
    # Configuraciones Anti-Rate-Limit (CRÍTICAS)
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 15, # Delay alto es CLAVE
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'ROBOTSTXT_OBEY': False,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    def __init__(self, keywords=None, target_locations=None, max_jobs_to_scrape=600, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = keywords
        self.target_locations = target_locations
        self.max_jobs_to_scrape = max_jobs_to_scrape
        self.scraped_count = 0 
        logging.info(f"LinkedInSpider (Scrapy) inicializado. Target: {self.max_jobs_to_scrape}")

    def start_requests(self):
        
        for k in self.keywords:
            for loc in self.target_locations:
                
                # 🚨 CORRECCIÓN 1: Detener la generación de peticiones si la meta ya está cumplida
                if self.scraped_count >= self.max_jobs_to_scrape:
                    self.logger.info("Meta de scraping alcanzada en start_requests. Deteniendo generación de solicitudes.")
                    return # Detiene la función start_requests
                    
                num_pages = (self.max_jobs_to_scrape // 25) + 1 
                
                # Limitamos la paginación para no hacer peticiones innecesarias
                for start_index in range(0, min(100, num_pages * 25), 25):
                    
                    # 🚨 CORRECCIÓN 2: Romper el bucle de paginación
                    if self.scraped_count >= self.max_jobs_to_scrape:
                        break # Pasa a la siguiente keyword/location
                        
                    params = {'keywords': k, 'location': loc, 'start': start_index}
                    query_string = urllib.parse.urlencode(params)
                    url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query_string}'
                    
                    self.logger.info(f"Scrapy Request: KWORD='{k}', LOC='{loc}', START={start_index}") 
                    
                    yield scrapy.Request(
                        url, 
                        callback=self.parse, 
                        meta={'keyword_search': k, 'location_search': loc}
                    )

    def parse(self, response):
        jobs = response.css('li')
        if not jobs: return

        for job in jobs:
            
            # 🚨 CORRECCIÓN 3: Si se supera el límite durante el parseo, terminar inmediatamente
            if self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Cerrando spider.")
                # Cierra el motor de Scrapy, evitando más solicitudes y procesamiento
                raise scrapy.exceptions.CloseSpider("Max jobs reached in parse method.") 

            try:
                item: Dict[str, Any] = {}
                
                title = job.css('h3.base-search-card__title::text').get(default='').strip()
                company = job.css('h4.base-search-card__subtitle::text').get(default='').strip()
                url = job.css('a.base-card__full-link::attr(href)').get()
                location = job.css('span.job-search-card__location::text').get(default='').strip()
                posted_date_str = job.css('time::attr(datetime)').get()
                
                job_id_match = re.search(r'(\d{10,})(?:\?|/|$)', str(url))
                job_id = job_id_match.group(1) if job_id_match else None

                # Mapeo a tu formato estandarizado
                item['titulo'] = title
                item['empresa'] = company
                item['url'] = url
                item['ubicacion'] = location
                item['posted_date'] = posted_date_str
                item['plataforma'] = 'LinkedIn'
                item['pais'] = response.meta.get('location_search')
                item['palabra_clave'] = response.meta.get('keyword_search')
                item['source_job_id'] = job_id
                item['description'] = f"Vacante: {title} en {company}. Ubicación: {location}."
                item['seniority'] = 'N/A'
                item['skills'] = []
                item['salary'] = None
                
                if title and url:
                    self.scraped_count += 1
                    yield item
            except Exception as e:
                self.logger.error(f"Error parseando item: {e}")