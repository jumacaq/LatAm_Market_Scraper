# FILE: job-market-intelligence/scrapers/spiders/torre_spider.py
import scrapy
import json
import datetime
import logging
from scrapy.exceptions import CloseSpider # MODIFICACIÓN: Importar CloseSpider

from scrapers.items import JobItem

class TorreSpider(scrapy.Spider):
    name = 'torre'
    allowed_domains = ['torre.ai']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1,
        'ROBOTSTXT_OBEY': True,
        'LOG_LEVEL': 'DEBUG', # MODIFICACIÓN: Poner a DEBUG temporalmente
    }

    api_base = 'https://search.torre.ai/opportunities/_search'
    
    def __init__(self, keywords=None, target_locations=None, start_date_filter=None, end_date_filter=None, max_jobs_to_scrape=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = keywords if keywords else []
        self.target_locations = target_locations if target_locations else ["Latam"]
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.max_jobs_to_scrape = max_jobs_to_scrape
        self.scraped_count = 0
        logging.info(f"TorreSpider inicializado con keywords: {self.keywords}, ubicaciones: {self.target_locations}, Max Jobs: {self.max_jobs_to_scrape}")

    async def start(self):
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"Torre: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Cerrando spider.")
            raise CloseSpider("Max jobs already scraped at spider start.")

        for keyword in self.keywords:
            for loc in self.target_locations:
                if self.scraped_count >= self.max_jobs_to_scrape:
                    self.logger.info(f"Torre: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{keyword}' en '{loc}'.")
                    raise CloseSpider("Max jobs scraped within keyword/location loop.")
                
                payload = self.build_search_payload(keyword, loc, self.start_date_filter, self.end_date_filter, self.max_jobs_to_scrape - self.scraped_count)
                
                self.logger.info(f"Torre Request: KWORD='{keyword}', LOC='{loc}'")
                
                yield scrapy.Request(
                    url=self.api_base,
                    method='POST',
                    body=json.dumps(payload),
                    headers={'Content-Type': 'application/json'},
                    callback=self.parse_api_response,
                    meta={
                        'keyword_search': keyword, 
                        'location_search': loc,
                        'start_date_filter': self.start_date_filter,
                        'end_date_filter': self.end_date_filter
                    },
                    errback=self.errback_httpbin
                )
    
    @staticmethod
    def build_search_payload(keyword, country, start_date_filter, end_date_filter, size_limit):
        """Construye el payload de búsqueda para la API de Torre."""
        filters = {
            "locations": [
                {
                    "country": country
                }
            ],
            "type": ["job"]
        }
        
        return {
            "query": keyword,
            "offset": 0,
            "size": min(50, size_limit),
            "filters": filters
        }
    
    def parse_api_response(self, response):
        """Parse Torre API JSON response"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Torre: Error decodificando JSON: {response.text}")
            return
        
        for result in data.get('results', []):
            if self.scraped_count >= self.max_jobs_to_scrape: 
                self.logger.info(f"Torre: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Cerrando spider.")
                raise CloseSpider("Max jobs scraped in parse_api_response method.")

            item = self.parse_job_from_api(result, response.meta['keyword_search'])
            if item:
                if response.meta['start_date_filter'] and item['posted_date']:
                    try:
                        posted_date_obj = datetime.datetime.strptime(item['posted_date'], '%Y-%m-%d').date()
                        if posted_date_obj < response.meta['start_date_filter']:
                            self.logger.info(f"Vacante '{item['title']}' descartada por fecha de publicación ({item['posted_date']}) anterior a {response.meta['start_date_filter']}.")
                            continue
                    except ValueError:
                        self.logger.warning(f"No se pudo parsear posted_date en Torre para filtrar: {item['posted_date']}")
                
                if response.meta['end_date_filter'] and item['posted_date']:
                    try:
                        posted_date_obj = datetime.datetime.strptime(item['posted_date'], '%Y-%m-%d').date()
                        if posted_date_obj > response.meta['end_date_filter']:
                            self.logger.info(f"Vacante '{item['title']}' descartada por fecha de publicación ({item['posted_date']}) posterior a {response.meta['end_date_filter']}.")
                            continue
                    except ValueError:
                        pass

                yield item
                self.scraped_count += 1
            else:
                self.logger.warning(f"⚠️ Vacante Torre incompleta: {result.get('id', 'N/A')}. Descartando.")

    @staticmethod
    def parse_job_from_api(job_data, keyword_search):
        """Convierte Torre API job data a JobItem"""
        item = JobItem()
        
        item['job_id'] = job_data.get('id')
        item['title'] = job_data.get('objective')
        
        organization = job_data.get('organizations', [{}])[0]
        item['company_name'] = organization.get('name')
        
        locations = job_data.get('locations', [])
        if locations:
            location_info = locations[0]
            item['country'] = location_info.get('country')
            item['location'] = f"{location_info.get('city', '')}, {location_info.get('country', '')}".strip(', ')
        
        item['job_type'] = 'Remote' if job_data.get('remote', False) else 'Onsite'
        
        item['seniority_level'] = None

        compensation = job_data.get('compensation', {})
        if compensation:
            salary_data = compensation.get('data', {})
            currency = salary_data.get('currency', '')
            min_amount = salary_data.get('minAmount', '')
            max_amount = salary_data.get('maxAmount', '')
            
            if min_amount and max_amount:
                item['salary_range'] = f"{currency} {min_amount} - {max_amount}"
            elif min_amount:
                item['salary_range'] = f"{currency} {min_amount} +"

        description_parts = []
        for detail in job_data.get('details', []):
            if detail.get('text'):
                description_parts.append(detail['text'])
        item['description'] = '\n'.join(description_parts)
        item['requirements'] = item['description']

        posted_date_str = job_data.get('deadline')
        if posted_date_str:
            try:
                item['posted_date'] = posted_date_str.split('T')[0]
            except IndexError:
                 item['posted_date'] = posted_date_str
            except Exception as e:
                logging.warning(f"Torre: Error al parsear posted_date '{posted_date_str}': {e}")
                item['posted_date'] = None

        item['source_url'] = f"https://torre.ai/jobs/{job_data.get('id')}"
        item['source_platform'] = 'Torre'
        item['scraped_at'] = datetime.datetime.now().isoformat()
        item['is_active'] = True
        item['sector'] = keyword_search
        item['skills'] = [skill.get('name') for skill in job_data.get('skills', []) if skill.get('name')]

        # MODIFICACIÓN: Logs detallados para ver qué se extrajo.
        self.logger.debug(f"Torre: Extracción de campos para URL: {item.get('source_url')}")
        self.logger.debug(f"  Title: '{item.get('title')}'")
        self.logger.debug(f"  Company: '{item.get('company_name')}'")
        self.logger.debug(f"  Job ID: '{item.get('job_id')}'")
        self.logger.debug(f"  Location: '{item.get('location')}'")
        self.logger.debug(f"  Country (parsed): '{item.get('country')}'")
        self.logger.debug(f"  Posted Date: '{item.get('posted_date')}'")
        self.logger.debug(f"  Salary: '{item.get('salary_range')}'")
        self.logger.debug(f"  Description length: {len(item.get('description') or '')}")

        if item.get('title') and item.get('job_id') and item.get('country'): # MODIFICACIÓN: También exigir país
            return item
        return None

    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(scrapy.exceptions.HttpError):
            response = failure.value.response
            self.logger.error(f"❌ Request HTTPError (Torre): {response.status} en {request.url}")
        elif failure.check(scrapy.exceptions.DNSLookupError):
            self.logger.error(f"❌ Request DNSLookupError (Torre): {failure.value} en {request.url}")
        elif failure.check(scrapy.exceptions.TimeoutError):
            self.logger.error(f"❌ Request TimeoutError (Torre): {failure.value} en {request.url}")
        else:
            self.logger.error(f"❌ Request fallido (Torre): {failure.value} en {request.url}")
