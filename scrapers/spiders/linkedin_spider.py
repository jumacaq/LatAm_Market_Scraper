# FILE: job-market-intelligence/scrapers/spiders/linkedin_spider.py
import scrapy
from scrapers.items import JobItem
import datetime
import re
import urllib.parse
import json
import os
import logging

class LinkedInSpider(scrapy.Spider):
    name = "linkedin_spider"
    allowed_domains = ["linkedin.com"]
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 15,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'ROBOTSTXT_OBEY': False,
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

    async def start(self):
        # MODIFICACIÓN: Comprobar el límite antes de generar CUALQUIER solicitud
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Cerrando spider.")
            raise scrapy.exceptions.CloseSpider("Max jobs already scraped at spider start.")

        for k in self.keywords:
            for loc in self.target_locations:
                # MODIFICACIÓN: Comprobar el límite antes de generar solicitudes para cada palabra clave/ubicación
                if self.scraped_count >= self.max_jobs_to_scrape:
                    self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{k}' en '{loc}'.")
                    raise scrapy.exceptions.CloseSpider("Max jobs scraped within keyword/location loop.") # Detener el spider si el límite se alcanzó aquí.

                search_location_param = loc 
                
                num_pages_to_fetch = (self.max_jobs_to_scrape // 25) + 1 
                max_start_index = min(100, num_pages_to_fetch * 25)

                for start_index in range(0, max_start_index, 25):
                    # MODIFICACIÓN: Comprobar de nuevo antes de enviar la solicitud específica
                    if self.scraped_count >= self.max_jobs_to_scrape:
                        self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{k}' en '{loc}'.")
                        raise scrapy.exceptions.CloseSpider("Max jobs scraped within pagination loop.")
                        
                    params = {
                        'keywords': k,
                        'location': search_location_param, 
                        'start': start_index
                    }
                    if self.f_tpr_value: 
                        params['f_TPR'] = self.f_tpr_value

                    query_string = urllib.parse.urlencode(params)
                    url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query_string}'
                    
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

    def parse(self, response):
        jobs = response.css('li')
        
        self.logger.info(f"LinkedIn Parse: Procesando URL: {response.url} (KWORD='{response.meta['keyword_search']}', LOC_BUSCADA='{response.meta['location_search']}')")

        if not jobs:
            self.logger.info(f"ℹ️ No se encontraron más vacantes en: {response.url}")
            return

        self.logger.info(f"🔎 Encontradas {len(jobs)} tarjetas de vacantes en {response.url}")

        for job in jobs:
            # MODIFICACIÓN: Si ya hemos raspado suficientes, detener el spider inmediatamente
            if self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"LinkedIn: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Cerrando spider.")
                raise scrapy.exceptions.CloseSpider("Max jobs scraped in parse method.") 

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
                
                source_url = job.css('a.base-card__full-link::attr(href)').get()
                location = job.css('span.job-search-card__location::text').get(default='').strip()
                
                posted_date_str = job.css('time::attr(datetime)').get()
                posted_date = None
                if posted_date_str:
                    try:
                        posted_date = datetime.datetime.strptime(posted_date_str, '%Y-%m-%d').date().isoformat()
                    except ValueError:
                        self.logger.warning(f"No se pudo parsear posted_date para LinkedIn: {posted_date_str}")
                        posted_date = datetime.datetime.now().date().isoformat()

                job_id = None
                if source_url:
                    job_id_match = re.search(r'(\d{10,})(?:\?|/|$)', source_url)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                    else:
                        job_id_match_simple = re.search(r'id=(\d+)', source_url)
                        if job_id_match_simple:
                            job_id = job_id_match_simple.group(1)
                
                item['job_id'] = job_id
                item['title'] = title
                item['company_name'] = company_name
                item['source_url'] = source_url
                item['location'] = location
                item['country'] = None
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


                if title and source_url and job_id:
                    if not company_name:
                        self.logger.warning(f"⚠️ Empresa no encontrada por selector para vacante: '{title}' en '{location}' (URL: {source_url})")
                    else:
                        self.logger.debug(f"✅ Empresa encontrada por selector: '{company_name}' para vacante: '{title}'")
                    
                    self.logger.debug(f"LinkedIn Extract: Ubicación extraída de la tarjeta: '{location}' (URL: {source_url})")

                    location_matched = False
                    extracted_loc_lower = (location or '').lower()
                    
                    for target_loc in self.target_locations:
                        if target_loc.lower() in extracted_loc_lower:
                            location_matched = True
                            item['country'] = target_loc
                            break
                    
                    if not location_matched:
                        self.logger.warning(f"❌ Vacante filtrada: Ubicación extraída ('{location}') no coincide con las ubicaciones de búsqueda deseada ({', '.join(self.target_locations)}) para '{title}'. Descartando.")
                        continue
                    
                    if self.start_date_filter and posted_date:
                        posted_date_obj = datetime.datetime.strptime(posted_date, '%Y-%m-%d').date()
                        if posted_date_obj < self.start_date_filter:
                            self.logger.info(f"Vacante '{title}' descartada por fecha de publicación ({posted_date}) anterior a {self.start_date_filter}.")
                            continue
                    if self.end_date_filter and posted_date:
                        posted_date_obj = datetime.datetime.strptime(posted_date, '%Y-%m-%d').date()
                        if posted_date_obj > self.end_date_filter:
                            self.logger.info(f"Vacante '{title}' descartada por fecha de publicación ({posted_date}) posterior a {self.end_date_filter}.")
                            continue

                    yield item
                    self.scraped_count += 1 
                else:
                    missing_fields = []
                    if not title: missing_fields.append('title')
                    if not source_url: missing_fields.append('URL')
                    if not job_id: missing_fields.append('job_id')
                    self.logger.warning(f"⚠️ Vacante incompleta (faltan: {', '.join(missing_fields)}): URL={source_url}, Title={title}. Descartando.")
            except Exception as e:
                self.logger.error(f"Error parseando item en LinkedInSpider: {e}")

    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(scrapy.exceptions.HttpError):
            response = failure.value.response
            self.logger.error(f"❌ Request HTTPError: {response.status} en {request.url}")
        elif failure.check(scrapy.exceptions.DNSLookupError):
            self.logger.error(f"❌ Request DNSLookupError: {failure.value} en {request.url}")
        elif failure.check(scrapy.exceptions.TimeoutError):
            self.logger.error(f"❌ Request TimeoutError: {failure.value} en {request.url}")
        else:
            self.logger.error(f"❌ Request fallido: {failure.value} en {request.url}")
