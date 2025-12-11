# FILE: Proyecto/job-market-intelligence/scrapers/spiders/computrabajo_spider.py
import scrapy
import datetime
import re
import logging
import urllib.parse
from scrapy.exceptions import CloseSpider
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError 
from dateutil import parser as dateparser
import yaml
import os

from scrapers.items import JobItem

class ComputrabajoSpider(scrapy.Spider):
    name = 'computrabajo'
    allowed_domains = ["computrabajo.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        },
        'LOG_LEVEL': 'INFO',
    }

    COUNTRY_DOMAINS = {
        'argentina': 'ar', 'bolivia': 'bo', 'brasil': 'br', 'chile': 'cl',
        'colombia': 'co', 'costa rica': 'cr', 'ecuador': 'ec', 'el salvador': 'sv',
        'guatemala': 'gt', 'honduras': 'hn', 'méxico': 'mx', 'nicaragua': 'ni',
        'panamá': 'pa', 'paraguay': 'py', 'perú': 'pe', 'república dominicana': 'do',
        'uruguay': 'uy', 'venezuela': 've',
        'mexico': 'mx'
    }

    def __init__(self, keywords=None, target_locations=None, start_date_filter=None, end_date_filter=None, f_tp_value="", max_jobs_to_scrape=100, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.keywords = self._load_keywords_from_config()

        if not self.keywords:
            self.logger.warning("Las palabras clave de config.yaml están vacías o no pudieron cargarse. Recurriendo a una lista predeterminada para Computrabajo.")
            self.keywords = ["desarrollador", "software engineer", "data scientist", "ingeniero de software", "analista de datos", "gerente de producto", "devops", "frontend", "backend"]

        self.target_locations = target_locations if target_locations else ["Mexico", "Colombia", "Argentina", "Chile", "Peru"]

        self.start_date_filter = start_date_filter
        self.end_date_filter = end_date_filter
        self.f_tp_value = f_tp_value
        self.max_jobs_to_scrape = max_jobs_to_scrape
        self.scraped_count = 0
        logging.info(f"ComputrabajoSpider inicializado con keywords: {self.keywords}, ubicaciones: {self.target_locations}, f_tp: {self.f_tp_value}, Max Jobs: {self.max_jobs_to_scrape}")

    def _load_keywords_from_config(self):
        """
        Carga las palabras clave de búsqueda (roles + keywords de sectores + habilidades técnicas)
        directamente desde config.yaml.
        """
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'config.yaml'
        )
        all_keywords = []
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                roles = config.get('roles', [])
                all_keywords.extend(roles)

                sectors = config.get('sectors', {})
                for sector_details in sectors.values():
                    all_keywords.extend(sector_details.get('keywords', []))

                tech_skills = config.get('tech_skills', [])
                all_keywords.extend(tech_skills)

            return list(set(all_keywords))
        except FileNotFoundError:
            self.logger.error(f"Archivo de configuración no encontrado en {config_path}. No se pueden cargar las palabras clave para ComputrabajoSpider.")
            return []
        except yaml.YAMLError as e:
            self.logger.error(f"Error al analizar config.yaml para ComputrabajoSpider: {e}. No se pueden cargar las palabras clave.")
            return []

    # CAMBIO CRÍTICO: Renombrar start_requests a start y asegurar que sea async def
    async def start(self): # <--- CAMBIO AQUÍ
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"Computrabajo: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Cerrando spider.")
            raise CloseSpider("Max jobs already scraped at spider start.")

        keywords_to_process = self.keywords
        locations_to_process = self.target_locations

        for keyword in keywords_to_process:
            for loc in locations_to_process:
                if self.scraped_count >= self.max_jobs_to_scrape:
                    self.logger.info(f"Computrabajo: Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo nuevas solicitudes para '{keyword}' en '{loc}'.")
                    raise CloseSpider("Max jobs scraped within keyword/location loop.")

                domain_prefix = self.COUNTRY_DOMAINS.get(loc.lower())
                if not domain_prefix:
                    self.logger.warning(f"Computrabajo: País '{loc}' no tiene un dominio Computrabajo mapeado o es inválido. Saltando.")
                    continue

                search_term_slug = keyword.lower().replace(' ', '-')
                search_term_slug = re.sub(r'[^a-z0-9-]', '', search_term_slug)
                
                base_url = f"https://{domain_prefix}.computrabajo.com/trabajo-de-{search_term_slug}"

                params = {}
                if self.f_tp_value and self.f_tp_value != "":
                    params['f_tp'] = self.f_tp_value

                query_string = urllib.parse.urlencode(params)
                search_url = f"{base_url}?{query_string}" if query_string else base_url

                self.logger.info(f"Computrabajo Request: KWORD='{keyword}', LOC='{loc}': {search_url}")

                yield scrapy.Request(
                    url=search_url,
                    callback=self.parse,
                    meta={
                        'keyword_search': keyword,
                        'location_search': loc,
                        'start_date_filter': self.start_date_filter,
                        'end_date_filter': self.end_date_filter,
                        'country_domain_prefix': domain_prefix
                    },
                    errback=self.errback_httpbin
                )

    # ... (resto del código de parse y parse_job) ...
    # (Sin cambios en estos métodos, solo se renombra start_requests a start)

    def parse(self, response):
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"Computrabajo: Límite total de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo paginación y encolamiento en `parse`.")
            raise CloseSpider("Max jobs scraped at parse method start.")

        offers = response.css("article.box_offer")
        self.logger.info(f"🔍 Computrabajo: Encontradas {len(offers)} ofertas en {response.url}")

        remaining_jobs_capacity = self.max_jobs_to_scrape - self.scraped_count
        jobs_to_enqueue = min(len(offers), remaining_jobs_capacity)

        for i, offer in enumerate(offers):
            if i >= jobs_to_enqueue:
                self.logger.info(f"Computrabajo: Límite de encolamiento de {jobs_to_enqueue} alcanzado para esta página. Saltando el resto.")
                break

            relative_url = offer.css("h2 a.js-o-link::attr(href)").get()
            if relative_url:
                job_url = response.urljoin(relative_url)
                self.logger.debug(f"➡️ Computrabajo: Encolando detalle {i+1}/{jobs_to_enqueue} de la página: {job_url}")
                yield scrapy.Request(job_url, callback=self.parse_job, meta=response.meta)

        next_page = response.css("a[rel='next']::attr(href)").get() or \
                    response.css("a.pagination__next::attr(href)").get()

        if next_page and self.scraped_count < self.max_jobs_to_scrape:
            next_page_url = response.urljoin(next_page)
            self.logger.info(f"Computrabajo Paginación: Siguiendo a {next_page_url} (scrapeadas: {self.scraped_count}/{self.max_jobs_to_scrape})")
            yield scrapy.Request(next_page_url, callback=self.parse, meta=response.meta)
        else:
            if self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"Computrabajo: Límite total de {self.max_jobs_to_scrape} vacantes alcanzado. No se seguirá paginando.")
            else:
                self.logger.debug(f"Computrabajo: No hay más páginas en {response.url}. Finalizando para esta búsqueda.")


    def parse_job(self, response):
        self.logger.debug(f"Computrabajo: Parseando página de detalle: {response.url}")

        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"Límite de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo parseo de detalles.")
            raise CloseSpider("Max jobs reached in parse_job method.")

        item = JobItem()

        item["source_platform"] = "Computrabajo"
        item["source_url"] = response.url

        job_id_match = re.search(r'-([A-Fa-f0-9]{32})(?:#|$)', response.url)
        item["job_id"] = job_id_match.group(1) if job_id_match else None

        item["title"] = response.css("h1::text").get(default='').strip()

        company_name_selectors = [
            "p.title-company strong::text",             
            "a#verempresa strong::text",                
            "a#verempresa::text",                       
            "span.v_offer_em__name::text",              
            "p.title-company a::text",                  
            "div.box_border .mbB:first-child strong::text",
            "p.title-company > span:not([class])::text",
            "//p[@class='title-company']//text()[normalize-space()]",
            "//strong[contains(text(), 'Empresa:')]/following-sibling::span[1]/text()",
            "//h2[contains(., 'Empresa')]/following-sibling::p[1]//text()",
        ]

        raw_company_name = ''
        for idx, selector in enumerate(company_name_selectors):
            extracted_name = None
            if selector.startswith('//'):
                extracted_name = response.xpath(selector).get()
            else:
                extracted_name = response.css(selector).get()
            
            if extracted_name and extracted_name.strip():
                clean_extracted_name = re.sub(r'^(Empresa:|Compañía:|Company:)\s*', '', extracted_name, flags=re.IGNORECASE).strip()
                clean_extracted_name = re.sub(r'\s+', ' ', clean_extracted_name).strip()
                
                if not re.search(r'^(vacante|empleo|puesto)\s+(de|para)\s+', clean_extracted_name.lower()) and \
                   not re.search(r'(ver ofertas|más ofertas|ver más|ver empleo)', clean_extracted_name.lower()):
                    raw_company_name = clean_extracted_name
                    self.logger.debug(f"✅ Computrabajo: Empresa capturada con selector #{idx+1} ('{selector}'): '{raw_company_name}'")
                    break
                else:
                    self.logger.debug(f"❌ Computrabajo: Selector #{idx+1} capturó texto de vacante o CTA: '{clean_extracted_name}'. Descartando.")
            else:
                self.logger.debug(f"❌ Computrabajo: Selector #{idx+1} ('{selector}') no encontró empresa.")
        
        if raw_company_name:
            raw_company_name = re.sub(r'^(Empresa:|Compañía:|Company:)\s*', '', raw_company_name, flags=re.IGNORECASE).strip()
            raw_company_name = re.sub(r'\s+', ' ', raw_company_name).strip()

        generic_names = [
            "lo mejor", "empresa", "confidencial", "importante empresa",
            "salario", "empresa confidencial", "compañía", "company",
            "empresa líder", "reconocida empresa", "importante compañía",
            "ver ofertas", "más ofertas", "ver más", "ver empleo",
            "la empresa", "no especificado", "consultora", "agencia", "staffing",
            "búsqueda", "reclutamiento", "servicios", "solicita",
            "puesto", "vacante", "trabajo", "job",
            "a convenir", "a definir", "n/a", "no aplica", "n/e", "na",
            "huzzle.com", "nuval", "decodes",
            "empresa de reclutamiento", "empresa de selección", "empresa líder en el sector",
            "importante empresa del sector", "multinacional", "startup"
        ]
        
        is_generic_company = False
        if raw_company_name:
            normalized_company = raw_company_name.lower()
            if any(re.fullmatch(r'\b' + re.escape(gn) + r'\b', normalized_company) for gn in generic_names):
                is_generic_company = True
            elif re.fullmatch(r'\s*confidencial\s*', normalized_company):
                is_generic_company = True
            elif re.fullmatch(r'\s*empresa\s*', normalized_company):
                is_generic_company = True

        if is_generic_company:
            item["company_name"] = "Empresa Confidencial"
            self.logger.info(f"⚠️ Computrabajo: Nombre de empresa clasificado como 'Empresa Confidencial' para '{raw_company_name}'.")
        else:
            item["company_name"] = raw_company_name if raw_company_name else "Empresa Desconocida"

        item["location"] = response.css("span.location::text").get(default='').strip() or \
                           response.xpath("//div[@class='header_offer']//ul//li//span[contains(@class, 'icon_place')]//following-sibling::span//text()").get(default='').strip()
        item["country"] = response.meta['location_search']
        posted_date_str = response.css("p.create_time::text").get()
        item["posted_date"] = self._parse_computrabajo_date(posted_date_str)

        description_html = response.css("div#descripcion_oferta").get(default='').strip()
        item["description"] = description_html

        requirements_html = response.css("div#requisitos").get(default='').strip()
        item["requirements"] = requirements_html

        salary_range = response.css("p.precio_oferta::text").get(default='').strip()
        item["salary_range"] = salary_range if salary_range and "a convenir" not in salary_range.lower() else None

        item["job_type"] = None
        item["seniority_level"] = None
        item['sector'] = response.meta['keyword_search']
        item["scraped_at"] = datetime.datetime.now().isoformat()
        item["is_active"] = True
        item["skills"] = []
        item['role_category'] = None

        if item["title"] and item["source_url"] and item["job_id"]:
            self.scraped_count += 1
            yield item
        else:
            missing_fields = []
            if not item["title"]: missing_fields.append('title')
            if not item["source_url"]: missing_fields.append('URL')
            if not item["job_id"]: missing_fields.append('job_id')
            self.logger.warning(f"⚠️ Vacante incompleta (faltan: {', '.join(missing_fields)}): URL={item['source_url']}, Title={item['title']}. Descartando.")


    def _parse_computrabajo_date(self, date_string):
        """
        Parses Computrabajo date strings like "Publicado hace 3 días", "Publicado hoy".
        """
        if not date_string:
            return None
        
        date_string_lower = date_string.lower()
        today = datetime.date.today()

        if "hoy" in date_string_lower:
            return today.isoformat()
        elif "ayer" in date_string_lower:
            return (today - datetime.timedelta(days=1)).isoformat()
        elif "hace un día" in date_string_lower or "hace 1 día" in date_string_lower:
            return (today - datetime.timedelta(days=1)).isoformat()
        elif "hace" in date_string_lower:
            match = re.search(r'(\d+)\s+(día|días|semana|semanas|mes|meses|hora|horas)', date_string_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if "día" in unit:
                    return (today - datetime.timedelta(days=value)).isoformat()
                elif "semana" in unit:
                    return (today - datetime.timedelta(weeks=value)).isoformat()
                elif "mes" in unit:
                    return (today - datetime.timedelta(days=value * 30)).isoformat()
                elif "hora" in unit:
                    return today.isoformat()
        
        try:
            parsed_date = dateparser.parse(date_string).date()
            return parsed_date.isoformat()
        except Exception:
            self.logger.warning(f"Computrabajo: No se pudo parsear la fecha '{date_string}'. Usando fecha de scraping.")
            return today.isoformat()


    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"❌ Computrabajo Request HTTPError: {response.status} en {request.url}")
        elif failure.check(DNSLookupError):
            self.logger.error(f"❌ Computrabajo Request DNSLookupError: {failure.value} en {request.url}")
        elif failure.check(TimeoutError, TCPTimedOutError):
            self.logger.error(f"❌ Computrabajo Request TimeoutError: {failure.value} en {request.url}")
        else:
            self.logger.error(f"❌ Computrabajo Request fallido: {failure.value} en {request.url}")
