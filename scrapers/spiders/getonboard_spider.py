# FILE: job-market-intelligence/scrapers/spiders/getonboard_spider.py
import scrapy
import datetime
import re
import logging
import urllib.parse
from scrapy.exceptions import CloseSpider # MODIFICACIÓN: Importar CloseSpider

from scrapers.items import JobItem
from config.geo import COMMON_GEO_DATA

class GetonBoardSpider(scrapy.Spider):
    name = 'getonboard'
    allowed_domains = ['getonbrd.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 3,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'DEBUG', # MODIFICACIÓN: Poner a DEBUG temporalmente
    }
    
    COUNTRY_CODES = {
        'Mexico': 'MX', 'Chile': 'CL', 'Colombia': 'CO', 'Argentina': 'AR',
        'Peru': 'PE', 'Brazil': 'BR', 'Uruguay': 'UY', 'Ecuador': 'EC'
    }

    def __init__(self, keywords=None, target_locations=None, start_date_filter=None, end_date_filter=None, max_jobs_to_scrape=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = keywords if keywords else []
        self.target_locations = target_locations if target_locations else ["Latam"]
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.max_jobs_to_scrape = max_jobs_to_scrape
        self.scraped_count = 0
        logging.info(f"GetonBoardSpider inicializado con keywords: {self.keywords}, ubicaciones: {self.target_locations}, Max Jobs: {self.max_jobs_to_scrape}")

    async def start(self):
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"GetonBoard: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Cerrando spider.")
            raise CloseSpider("Max jobs already scraped at spider start.")

        base_url = 'https://www.getonbrd.com/empleos'
        
        for keyword in self.keywords:
            for loc in self.target_locations:
                if self.scraped_count >= self.max_jobs_to_scrape: 
                    self.logger.info(f"GetonBoard: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{keyword}' en '{loc}'.")
                    raise CloseSpider("Max jobs scraped within keyword/location loop.")

                country_code = self.COUNTRY_CODES.get(loc, None)
                
                params = {'query': keyword}
                if country_code:
                    params['country'] = country_code

                query_string = urllib.parse.urlencode(params)
                search_url = f"{base_url}?{query_string}"
                
                self.logger.info(f"GetonBoard Request: KWORD='{keyword}', LOC='{loc}': {search_url}")
                
                yield scrapy.Request(
                    url=search_url,
                    callback=self.parse,
                    meta={
                        'keyword_search': keyword, 
                        'location_search': loc,
                        'start_date_filter': self.start_date_filter,
                        'end_date_filter': self.end_date_filter,
                        'target_locations': self.target_locations
                    },
                    errback=self.errback_httpbin
                )

    def parse(self, response):
        """Parse job listing page"""
        job_links = response.css('a[href*="/empleos/"]::attr(href)').getall()
        job_links = [l for l in job_links if l.count('/') >= 4 and l.startswith('/empleos/')]
        job_links = list(set(job_links))

        self.logger.info(f"GetonBoard Parse: Encontrados {len(job_links)} enlaces de trabajo (posibles) en {response.url}")

        for link in job_links:
            # MODIFICACIÓN: Detener el bucle de "job_links" si el límite ya se alcanzó, para no encolar más.
            if self.scraped_count >= self.max_jobs_to_scrape: 
                self.logger.info(f"GetonBoard: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. No se encolarán más detalles de ofertas de esta página.")
                break # Sale del bucle for link in job_links
            
            # self.logger.debug(f"GetonBoard: Enlace de trabajo potencial: {link}") # Descomentar para depurar enlaces
            yield response.follow(link, callback=self.parse_job, meta=response.meta)
    
        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            if self.scraped_count < self.max_jobs_to_scrape:
                self.logger.info(f"GetonBoard Paginación: Siguiendo a {next_page}")
                yield scrapy.Request(response.urljoin(next_page), callback=self.parse, meta=response.meta)
            else:
                self.logger.info(f"GetonBoard: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. No se seguirá paginando. Cerrando spider.")
                raise CloseSpider("Max jobs reached, stopping pagination.")

    def parse_job(self, response):
        """Parse individual job page"""
        item = JobItem()
    
        item['title'] = response.css('h1.gb-landing-cover__title::text').get(default='').strip()
        item['company_name'] = response.css('a.gb-landing-cover__company::text').get(default='').strip()
        
        location_elements = response.css('li.gb-landings-details__item:contains("Ubicación") span::text').getall()
        location_elements.extend(response.css('li:contains("Modalidad") span::text').getall())
        location_elements.extend(response.css('span[itemprop="address"]::text').getall())
        location = ', '.join([loc.strip() for loc in location_elements if loc.strip()])
        item['location'] = location or None

        item['description'] = response.css('div.gb-landing-section.description').get(default='')
        
        requirements_section = response.xpath('//h3[contains(text(), "Requisitos")]/following-sibling::div[1]').get()
        item['requirements'] = requirements_section or None

        item['source_url'] = response.url
        item['source_platform'] = 'GetonBoard'
        item['scraped_at'] = datetime.datetime.now().isoformat()
        
        job_id_match = re.search(r'/empleos/[^/]+/([a-zA-Z0-9-]+)', response.url)
        item['job_id'] = job_id_match.group(1) if job_id_match else None

        item['job_type'] = response.css('li:contains("Modalidad") span::text').get(default='').strip()
        item['seniority_level'] = response.css('li:contains("Seniority") span::text').get(default='').strip()
        item['salary_range'] = response.css('li:contains("Compensación") span::text').get(default='').strip()
        
        posted_date_str = response.css('time::attr(datetime)').get()
        if posted_date_str:
            item['posted_date'] = posted_date_str.split('T')[0]

        # MODIFICACIÓN: Logs detallados para ver qué se extrajo.
        self.logger.debug(f"GetonBoard: Extracción de campos para URL: {response.url}")
        self.logger.debug(f"  Title: '{item.get('title')}'")
        self.logger.debug(f"  Company: '{item.get('company_name')}'")
        self.logger.debug(f"  Job ID: '{item.get('job_id')}'")
        self.logger.debug(f"  Location: '{item.get('location')}'")
        self.logger.debug(f"  Country (parsed): '{item.get('country')}'")
        self.logger.debug(f"  Posted Date: '{item.get('posted_date')}'")
        self.logger.debug(f"  Salary: '{item.get('salary_range')}'")
        self.logger.debug(f"  Description length: {len(item.get('description') or '')}")


        location_matched = False
        extracted_loc_lower = (item['location'] or '').lower()
        
        for target_loc in response.meta['target_locations']:
            if target_loc.lower() in extracted_loc_lower or \
               (self.COUNTRY_CODES.get(target_loc) and self.COUNTRY_CODES[target_loc].lower() in extracted_loc_lower):
                location_matched = True
                item['country'] = target_loc
                break
        
        if not location_matched:
            self.logger.warning(f"❌ Vacante filtrada (GetonBoard): Ubicación extraída ('{item['location']}') no coincide con las ubicaciones de búsqueda ({', '.join(response.meta['target_locations'])}) para '{item['title']}'. Descartando.")
            return
        
        if response.meta['start_date_filter'] and item['posted_date']:
            posted_date_obj = datetime.datetime.strptime(item['posted_date'], '%Y-%m-%d').date()
            if posted_date_obj < response.meta['start_date_filter']:
                self.logger.info(f"Vacante '{item['title']}' descartada por fecha de publicación ({item['posted_date']}) anterior a {response.meta['start_date_filter']}.")
                return
        if response.meta['end_date_filter'] and item['posted_date']:
            posted_date_obj = datetime.datetime.strptime(item['posted_date'], '%Y-%m-%d').date()
            if posted_date_obj > response.meta['end_date_filter']:
                self.logger.info(f"Vacante '{item['title']}' descartada por fecha de publicación ({item['posted_date']}) posterior a {response.meta['end_date_filter']}.")
                return

        if item.get('title') and item.get('description') and item.get('job_id') and item.get('country'): # MODIFICACIÓN: También exigir país
            yield item
            self.scraped_count += 1
            if self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"GetonBoard: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Cerrando spider.")
                raise CloseSpider("Max jobs scraped in parse_job method.")
        else:
            missing_fields = []
            if not item.get('title'): missing_fields.append('title')
            if not item.get('description'): missing_fields.append('description')
            if not item.get('job_id'): missing_fields.append('job_id')
            if not item.get('country'): missing_fields.append('country')
            self.logger.warning(f"⚠️ Vacante GetonBoard incompleta (faltan: {', '.join(missing_fields)}): {response.url}. Título: '{item.get('title')}' Job ID: '{item.get('job_id')}' País: '{item.get('country')}'")


    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(scrapy.exceptions.HttpError):
            response = failure.value.response
            self.logger.error(f"❌ Request HTTPError (GetonBoard): {response.status} en {request.url}")
        elif failure.check(scrapy.exceptions.DNSLookupError):
            self.logger.error(f"❌ Request DNSLookupError (GetonBoard): {failure.value} en {request.url}")
        elif failure.check(scrapy.exceptions.TimeoutError):
            self.logger.error(f"❌ Request TimeoutError (GetonBoard): {failure.value} en {request.url}")
        else:
            self.logger.error(f"❌ Request fallido (GetonBoard): {failure.value} en {request.url}")
