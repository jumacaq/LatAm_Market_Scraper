
import scrapy
from jobscraper.items import JobItem
import datetime
import urllib.parse
import json 
import os   

class LinkedInSpider(scrapy.Spider):
    name = "linkedin"
    allowed_domains = ["linkedin.com"]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, target_locations=None, f_tpr_value="", start_date_filter=None, end_date_filter=None, continent_search=None, *args, **kwargs):
        super(LinkedInSpider, self).__init__(*args, **kwargs)
        # Remove the problematic line: self.logger = self.crawler.logger
        # self.logger is automatically available after super().__init__ is called.

        # Convertir target_locations a una lista de strings para búsquedas
        self.target_locations = target_locations if target_locations else ["Latam"] 
        self.f_tpr_value = f_tpr_value
        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.continent_search = continent_search # Store continent_search as an instance attribute
        
        # Guardar las ubicaciones objetivo en minúsculas para un filtrado robusto
        # Esto nos permite comparar "Estados Unidos" con "united states" o "US" de forma flexible
        self.parsed_target_locations = [loc.lower() for loc in self.target_locations if loc and loc != "Todos los Países"]


        keywords_path = os.path.join(os.path.dirname(__file__), '../../config/keywords.json')
        try:
            with open(keywords_path, 'r', encoding='utf-8') as f:
                self.keywords = json.load(f)
            if not self.keywords:
                self.logger.warning(f"No se encontraron palabras clave en {keywords_path}, usando valores por defecto.")
                self.keywords = ['EdTech', 'Fintech', 'Desarrollador', 'Full Stack', 'Frontend', 'Backend', 'Data Analyst', 'Product Manager']
        except FileNotFoundError:
            self.logger.error(f"Archivo de palabras clave no encontrado en {keywords_path}, usando valores por defecto.")
            self.keywords = ['EdTech', 'Fintech', 'Desarrollador', 'Full Stack', 'Frontend', 'Backend', 'Data Analyst', 'Product Manager']
        except json.JSONDecodeError:
            self.logger.error(f"Error decodificando JSON en {keywords_path}, usando valores por defecto.")
            self.keywords = ['EdTech', 'Fintech', 'Desarrollador', 'Full Stack', 'Frontend', 'Backend', 'Data Analyst', 'Product Manager']

    def start_requests(self):
        # The sanity check for errback_httpbin can remain, but it's redundant if the method is always defined.
        # It's generally better to let Python raise the AttributeError if the method is truly missing,
        # unless you have a specific fallback logic you want to implement here.
        
        for k in self.keywords:
            for loc in self.target_locations:
                # Si el loc es "Todos los Países", se itera sobre todos los países del continente.
                # Para simplificar la URL, solo pasamos el país individual o el nombre del continente si no se especificó un país
                # Use self.continent_search directly, with 'Latam' as a fallback if not set
                search_location = loc if loc != "Todos los Países" else (self.continent_search if self.continent_search else 'Latam') 
                
                for start_index in range(0, 100, 25): # Scrape first 4 pages for each search
                    params = {
                        'keywords': k,
                        'location': search_location, # Usamos la ubicación a buscar
                        'start': start_index
                    }
                    if self.f_tpr_value: 
                        params['f_TPR'] = self.f_tpr_value

                    query_string = urllib.parse.urlencode(params)
                    url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{query_string}'
                    
                    self.logger.info(f"Spider Request: Solicitando URL para KWORD='{k}', LOC_BUSCADA='{loc}': {url}") 
                    
                    yield scrapy.Request(
                        url, 
                        callback=self.parse, 
                        meta={
                            'keyword': k, 
                            'location_search': loc, # Esta es la ubicación que *queremos*
                            'continent_search': self.continent_search # Pass self.continent_search to request.meta
                        },
                        errback=self.errback_httpbin
                    )

    def parse(self, response):
        jobs = response.css('li')
        
        self.logger.info(f"Spider Parse: Procesando URL: {response.url} (originalmente para KWORD='{response.meta['keyword']}', LOC_BUSCADA='{response.meta['location_search']}')")

        if not jobs:
            self.logger.info(f"ℹ️ No se encontraron más vacantes en: {response.url}")
            return

        self.logger.info(f"🔎 Encontradas {len(jobs)} tarjetas de vacantes en {response.url}")

        for job in jobs:
            try:
                item = JobItem()
                
                title = job.css('h3.base-search-card__title::text').get(default='').strip()
                
                # --- MODIFICACIÓN CLAVE: Selector de compañía más robusto ---
                # Intentar primero el selector actual, si no funciona, probar con otros comunes
                company = job.css('h4.base-search-card__subtitle::text').get(default='').strip()
                if not company: # Si el primero falla, probar alternativas
                    company = job.css('h4.base-search-card__subtitle a::text').get(default='').strip() # A veces está en un <a>
                if not company:
                    company = job.css('span.job-result-card__subtitle a::text').get(default='').strip() # Otro patrón común
                if not company:
                    company = job.xpath('//h4[contains(@class, "base-search-card__subtitle")]/text()').get(default='').strip() # Usar XPath como fallback
                # --- FIN MODIFICACIÓN SELECTOR ---
                
                url = job.css('a.base-card__full-link::attr(href)').get()
                location = job.css('span.job-search-card__location::text').get(default='').strip()
                posted_date = job.css('time::attr(datetime)').get()
                
                if not posted_date:
                    posted_date = datetime.date.today().isoformat()

                item['title'] = title
                item['company_name'] = company
                item['source_url'] = url
                item['location'] = location
                item['sector'] = response.meta['keyword']
                item['posted_date'] = posted_date
                item['source_platform'] = 'LinkedIn'
                
                item['description'] = f"Vacante: {title} en {company}. Ubicación: {location}."
                
                item['seniority_level'] = 'N/A'
                item['skills'] = []

                if title and url:
                    if not company:
                        self.logger.warning(f"⚠️ Empresa no encontrada por selector para vacante: '{title}' en '{location}' (URL: {url})")
                    else:
                        self.logger.debug(f"✅ Empresa encontrada por selector: '{company}' para vacante: '{title}'")
                    
                    self.logger.debug(f"Spider Extract: Ubicación extraída de la tarjeta: '{location}' (URL: {url})")

                    # --- FILTRADO DE UBICACIÓN DESPUÉS DEL SCRAPE ---
                    # Si pedimos un país específico (no "Todos los Países"), filtramos
                    if response.meta['location_search'] != "Todos los Países":
                        # Convertir a minúsculas y verificar si la ubicación extraída contiene la ubicación deseada
                        # Esto es flexible por si LinkedIn devuelve "Estados Unidos" para "USA" o viceversa.
                        # Y también para ignorar "São Paulo, São Paulo, Brazil" si pedimos "Estados Unidos"
                        target_loc_lower = response.meta['location_search'].lower()
                        extracted_loc_lower = location.lower()
                        
                        # Comprobar si la ubicación extraída contiene el país objetivo o un sinónimo
                        # O si la URL de la vacante contiene el prefijo del país correcto (ej. /jobs/view/ para US, /br.linkedin.com/jobs/view/ para Brasil)
                        # Caso especial: búsqueda por LATAM
                        if target_loc_lower in ("latam", "latinoamérica", "latin america", "latin-america"):

                            latam_countries = [
                                "argentina", "chile", "mexico", "méxico", "peru", "perú",
                                "colombia", "ecuador", "uruguay", "paraguay", "bolivia",
                                "costa rica", "panama", "panamá", "honduras", "guatemala",
                                "nicaragua", "dominican republic", "republica dominicana",
                                "república dominicana", "el salvador", "latin america",
                                "latinoamérica", "latam"
                            ]

                            is_location_match = any(country in extracted_loc_lower for country in latam_countries)

                        else:
                            # Coincidencia normal por país
                            is_location_match = target_loc_lower in extracted_loc_lower

                        
                        # Añadir una verificación de dominio para mayor robustez
                        if target_loc_lower == "estados unidos" and not url.startswith("https://www.linkedin.com/jobs/view/"):
                             is_location_match = False # No es una URL de US si el dominio no es el base
                        elif target_loc_lower == "brasil" and not url.startswith("https://br.linkedin.com/jobs/view/"):
                             is_location_match = False # No es una URL de Brasil si el dominio no es br.linkedin.com
                        # Se podrían añadir más reglas para otros países si es necesario
                        
                        if not is_location_match:
                            self.logger.warning(f"❌ Vacante filtrada: Ubicación extraída ('{location}') no coincide con la ubicación de búsqueda deseada ('{response.meta['location_search']}') para '{title}'. Descartando.")
                            continue # Ignorar este item y pasar al siguiente
                        else:
                            self.logger.debug(f"✅ Vacante aprobada: Ubicación extraída ('{location}') coincide con la ubicación de búsqueda deseada ('{response.meta['location_search']}') para '{title}'.")
                    # --- FIN FILTRADO DE UBICACIÓN ---

                    yield item
            except Exception as e:
                self.logger.error(f"Error parseando item: {e}")

    def errback_httpbin(self, failure):
        self.logger.error(f"❌ Request fallido: {failure.request.url} - Razón: {failure.value}")