import scrapy
import datetime
import re
import logging
import urllib.parse
from scrapy.exceptions import CloseSpider
# Importar errores de Twisted y HttpError de Scrapy middleware para manejo de errback
# Estas son las importaciones correctas para Scrapy 2.13.4
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
        'LOG_LEVEL': 'INFO', # Mantener en INFO para producción, pero recomendar DEBUG para pruebas
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

                # Esto es clave para buscar en más sectores/habilidades:
                tech_skills = config.get('tech_skills', [])
                all_keywords.extend(tech_skills)

            return list(set(all_keywords))
        except FileNotFoundError:
            self.logger.error(f"Archivo de configuración no encontrado en {config_path}. No se pueden cargar las palabras clave para ComputrabajoSpider.")
            return []
        except yaml.YAMLError as e:
            self.logger.error(f"Error al analizar config.yaml para ComputrabajoSpider: {e}. No se pueden cargar las palabras clave.")
            return []

    async def start(self):
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

    def parse(self, response):
        if self.scraped_count >= self.max_jobs_to_scrape:
            self.logger.info(f"Computrabajo: Límite total de {self.max_jobs_to_scrape} vacantes alcanzado. Deteniendo paginación y encolamiento en `parse`.")
            raise CloseSpider("Max jobs scraped at parse method start.")

        offers = response.css("article.box_offer")
        self.logger.info(f"🔍 Computrabajo: Encontradas {len(offers)} ofertas en {response.url}")

        jobs_to_enqueue = min(len(offers), self.max_jobs_to_scrape - self.scraped_count)

        for i, offer in enumerate(offers):
            if i >= jobs_to_enqueue or self.scraped_count >= self.max_jobs_to_scrape:
                self.logger.info(f"Computrabajo: Límite de encolamiento o límite global alcanzado. Solo se encolarán {jobs_to_enqueue} ofertas de esta página.")
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

        if self.logger.isEnabledFor(logging.DEBUG):
            # Log HTML section for company if in debug mode, as it helps identify new patterns
            company_section_debug = response.css("p.title-company").get()
            if company_section_debug:
                self.logger.debug(f"🔍 HTML de sección empresa (para depuración): {company_section_debug[:500]}") # Limitado a 500 chars
            else:
                self.logger.debug("🔍 Sección de empresa 'p.title-company' no encontrada para depuración.")

        item = JobItem()

        item["source_platform"] = "Computrabajo"
        item["source_url"] = response.url

        job_id_match = re.search(r'-([A-Fa-f0-9]{32})(?:#|$)', response.url)
        item["job_id"] = job_id_match.group(1) if job_id_match else None

        item["title"] = response.css("h1::text").get(default='').strip()

        # START: Extracción de nombre de empresa (basado en tu versión "original")
        # Se ha reincorporado la lista exacta de selectores de tu archivo original.
        # La depuración (DEBUG log) ayudará a entender qué selector está funcionando.
        company_name_selectors = [
            "p.title-company strong::text",
            "a#verempresa strong::text",
            "a#verempresa::text",
            "span.v_offer_em__name::text",
            "p.title-company a::text",
            "p.title-company a strong::text",
            "div.box_border .mbB:first-child strong::text",
            "div.v_offer h2 + p.title-company::text",
            "div.v_offer h2 + p strong::text",
            "p.title-company > span:not([class])::text",
            "//strong[contains(text(), 'Empresa:')]/following-sibling::span[1]/text()",
            "//p[@class='title-company']//text()[normalize-space()]", # General dentro de p.title-company
            "//div[@class='info_items']//p[1]//strong/text()",
            "//h2[contains(., 'Empresa')]/following-sibling::p[1]//text()",
            "//h3[contains(., 'Empresa')]/following-sibling::p[1]//text()",
            "//div[contains(@class, 'company')]//text()[normalize-space()]", # General en divs con 'company'
            "//div[@class='v_offer']//p[not(contains(@class, 'title'))]/strong/text()", # En la sección v_offer
        ]

        raw_company_name = ''
        for idx, selector in enumerate(company_name_selectors):
            extracted_name = None
            if selector.startswith('//'): # Es un XPath
                extracted_name = response.xpath(selector).get()
            else: # Es un selector CSS
                extracted_name = response.css(selector).get()
            
            if extracted_name and extracted_name.strip():
                raw_company_name = extracted_name.strip()
                self.logger.debug(f"✅ Computrabajo: Empresa capturada con selector #{idx+1} ('{selector}'): '{raw_company_name}'")
                break # Salir del bucle una vez que se encuentra un nombre válido
            else:
                self.logger.debug(f"❌ Computrabajo: Selector #{idx+1} ('{selector}') no encontró empresa.")
        
        # Lógica de limpieza y clasificación como "Empresa Confidencial"
        if raw_company_name:
            raw_company_name = re.sub(r'^(Empresa:|Compañía:|Company:)\s*', '', raw_company_name, flags=re.IGNORECASE).strip()
            raw_company_name = re.sub(r'\s+', ' ', raw_company_name).strip()

        generic_names = [
            "lo mejor", "empresa", "confidencial", "importante empresa",
            "salario", "empresa confidencial", "compañía", "company",
            "empresa líder", "reconocida empresa", "importante compañía",
            "", "n/a", "no especificado"
        ]

        # Si después de la limpieza y la búsqueda el nombre sigue siendo genérico o vacío
        if not raw_company_name or raw_company_name.lower() in generic_names or len(raw_company_name) < 2:
            item["company_name"] = "Empresa Confidencial"
            self.logger.info(f"⚠️ Computrabajo: Compañía genérica o vacía ('{raw_company_name}') para: '{item.get('title')}' (URL: {response.url}). Asignado 'Empresa Confidencial'.")
        else:
            item["company_name"] = raw_company_name
            self.logger.info(f"✓ Computrabajo: Empresa encontrada y validada para '{item.get('title')}': '{raw_company_name}'")
        # END: Extracción de nombre de empresa
        
        # El resto del código de parse_job (título, job_id, etc.) se mantiene como estaba
        item["source_platform"] = "Computrabajo"
        item["source_url"] = response.url

        job_id_match = re.search(r'-([A-Fa-f0-9]{32})(?:#|$)', response.url)
        item["job_id"] = job_id_match.group(1) if job_id_match else None

        item["title"] = response.css("h1::text").get(default='').strip()
        
        location_candidates = [
            response.css("p.location strong::text").get(),
            response.css("p.location span::text").get(),
            response.css("div.box_detail_inner_info li:has(i.fa-map-marker-alt) strong::text").get(),
            response.css("div.box_border .mbB span.tag::text").get(),
            response.xpath("//div[contains(@class, 'box_detail_inner_info')]//li[contains(., 'Ubicación')]//span[last()]/text()").get(),
            response.xpath("//div[contains(@class, 'box_detail_inner_info')]//li[contains(., 'Modalidad')]//span[last()]/text()").get(),
            response.xpath("//*[@class='v_offer_info']//p[contains(@class, 'fs16')]/text()").get(),
            response.xpath("//div[@class='info_items']//p[contains(.,'Ubicación')]/text()").get(),
        ]
        raw_location = next((l.strip() for l in location_candidates if l), '')

        raw_location = re.sub(r'publicado.*', '', raw_location, flags=re.IGNORECASE).strip()
        is_salary_in_location = bool(re.search(r'\d[\.,]\d{3}|mensual|anual|bruto|neto|usd|ars', raw_location, re.IGNORECASE))

        if raw_location and not is_salary_in_location:
            item["location"] = re.sub(r',?\s*(Contrato por|Jornada|Presencial|Remoto|A convenir|Salario|Tipo de Contrato|experiencia).*', '', raw_location, flags=re.IGNORECASE).strip()
            if not item["location"]:
                item["location"] = None
        else:
            if is_salary_in_location:
                self.logger.warning(f"⚠️ Posible captura de salario como ubicación para '{item.get('title')}'. Valor: '{raw_location}'. Descartando esta ubicación.")
            item["location"] = None

        item["country"] = self.reverse_country_domain_lookup(response.meta['country_domain_prefix'])

        description_selector = response.css("div#detail_box, div.box_detail")
        item["description"] = description_selector.get(default='')

        requirements_selector = response.xpath("//h2[contains(., 'Requisitos')]/following-sibling::ul[1]").get()
        if not requirements_selector:
             requirements_selector = response.xpath("//h3[contains(., 'Requisitos')]/following-sibling::div[1]").get()
        item["requirements"] = requirements_selector or None
        if not item["requirements"] and "requisitos" in item["description"].lower():
            req_match = re.search(r'(requisitos|requirements)[:.]?[\s\S]+?(?:funciones|responsabilidades|ofrecemos|we offer)', item["description"].lower())
            if req_match:
                item["requirements"] = item["description"][req_match.start():req_match.end()]

        raw_date = self._extract_posted_date(response)
        item["posted_date"] = self.parse_relative_date_computrabajo(raw_date)

        if not item["posted_date"]:
            self.logger.debug(f"⚠️ No se pudo extraer fecha de detalle, usando fecha actual como fallback para {response.url}")
            item["posted_date"] = str(datetime.date.today())

        salary = response.css("p.salary span::text, p.salary::text").get(default='').strip()
        item["salary_range"] = salary or None

        item['job_type'] = self._extract_job_type(response)
        item['seniority_level'] = self._extract_seniority_level(response, item['title'])
        item['is_active'] = True
        item['skills'] = []
        item['sector'] = response.meta['keyword_search']

        # --- FILTRO: Verificar que la vacante contenga palabras clave tecnológicas ---
        combined_text = (item.get('title', '') + ' ' +
                         item.get('description', '') + ' ' +
                         (item.get('requirements', '') or '')).lower()

        found_tech_keyword = False
        lowercased_tech_keywords = {kw.lower() for kw in self.keywords}

        for keyword in lowercased_tech_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                found_tech_keyword = True
                break
            if ' ' in keyword and keyword in combined_text:
                found_tech_keyword = True
                break

        if not found_tech_keyword:
            self.logger.info(f"❌ Vacante Computrabajo descartada: No se encontraron palabras clave tecnológicas en el título/descripción/requisitos para: '{item.get('title')}' (URL: {response.url}). Posiblemente una vacante no tecnológica (ej. 'limpieza', 'operario').")
            return

        self.logger.debug(f"Computrabajo: Extracción de campos para URL: {response.url}")
        self.logger.debug(f"  Title: '{item.get('title')}'")
        self.logger.debug(f"  Company: '{item.get('company_name')}'")
        self.logger.debug(f"  Job ID: '{item.get('job_id')}'")
        self.logger.debug(f"  Location: '{item.get('location')}'")
        self.logger.debug(f"  Country (parsed): '{item.get('country')}'")
        self.logger.debug(f"  Posted Date: '{item.get('posted_date')}'")
        self.logger.debug(f"  Salary: '{item.get('salary_range')}'")
        self.logger.debug(f"  Job Type: '{item.get('job_type')}'")
        self.logger.debug(f"  Seniority Level: '{item.get('seniority_level')}'")
        self.logger.debug(f"  Sector (initial): '{item.get('sector')}'")
        self.logger.debug(f"  Description length: {len(item.get('description') or '')}")
        self.logger.debug(f"  Requirements length: {len(item.get('requirements') or '')}")

        if item.get('title') and item.get('job_id') and item.get('country') and item.get('posted_date'):
            if self.scraped_count < self.max_jobs_to_scrape:
                self.scraped_count += 1
                self.logger.info(f"✅ Computrabajo: Ítem válido #{self.scraped_count}/{self.max_jobs_to_scrape}: '{item['title']}' ({item['company_name']}, {item['country']})")
                yield item

                if self.scraped_count == self.max_jobs_to_scrape:
                    self.logger.info(f"Computrabajo: ✅ Límite exacto de {self.max_jobs_to_scrape} vacante(s) alcanzado. Cerrando spider.")
                    raise CloseSpider(f"Exactamente {self.max_jobs_to_scrape} vacante(s) scrapeada(s) exitosamente.")
            else:
                self.logger.info(f"Computrabajo: Límite de {self.max_jobs_to_scrape} vacantes ya alcanzado. Descartando este ítem: '{item['title']}'.")
                return
        else:
            missing_fields = []
            if not item.get('title'): missing_fields.append('title')
            if not item.get('job_id'): missing_fields.append('job_id')
            if not item.get('country'): missing_fields.append('country')
            if not item.get('posted_date'): missing_fields.append('posted_date')
            self.logger.warning(f"⚠️ Vacante Computrabajo incompleta (faltan: {', '.join(missing_fields)}). URL: {response.url}. Título: '{item.get('title')}' Compañía: '{item.get('company_name')}' Job ID: '{item.get('job_id')}' País: '{item.get('country')}' Posted Date: '{item.get('posted_date')}'")
            return

    def _extract_posted_date(self, response):
        """
        Extrae la fecha de publicación con múltiples estrategias de selección.
        Retorna el texto crudo de la fecha encontrada.
        """
        date_candidates = [
            response.css("span.dO::text").get(),
            response.css("span.tag::text").re_first(r'(hace\s+\d+.*?|hoy|ayer|\d{1,2}\s+de\s+\w+)'),
            response.css("p.mtB::text").re_first(r'(hace\s+\d+.*?|hoy|ayer|\d{1,2}\s+de\s+\w+)'),
            response.css("time::attr(datetime)").get(),
            response.xpath("//time/@datetime").get(),
            response.xpath("//li[contains(., 'Publicación')]//span[last()]/text()").get(),
            response.xpath("//li[contains(., 'Actualización')]//span[last()]/text()").get(),
            response.xpath("//p[contains(@class, 'fs16')]//text()[contains(., 'hace') or contains(., 'Hace')]").get(),
            response.xpath("//span[contains(@class, 'tag')]//text()[contains(., 'hace') or contains(., 'Hace')]").get(),
            response.css("div.box_detail_inner_info p.mtB::text").get(),
            response.xpath("//div[@class='info_items']//p[contains(., 'Publicado')]/text()").get(),
            response.xpath("//text()[contains(., 'publicado') or contains(., 'Publicado')]").re_first(r'(publicado(?:\s+el)?[:.]?\s+(?:hace\s+\d+.*?|hoy|ayer|\d{1,2}\s+de\s+\w+|\d{1,2}[\/-]\d{1,2}[\/-]\d{4}))', default='')
        ]

        raw_date = None
        irrelevant_texts = ['requerimientos', 'educación', 'experiencia', 'palabras clave', 'aptitudes', 'conocimientos', 'modalidad', 'jornada', 'tipo de contrato', 'salario']

        for candidate in date_candidates:
            if candidate and candidate.strip():
                candidate_lower = candidate.strip().lower()
                if not any(irrelevant in candidate_lower for irrelevant in irrelevant_texts) or \
                   ('hace' in candidate_lower or 'hoy' in candidate_lower or 'ayer' in candidate_lower or re.search(r'\d{1,2}\s+de\s+\w+', candidate_lower) or re.search(r'\d{1,2}[\/-]\d{1,2}[\/-]\d{4}', candidate_lower)):
                    raw_date = candidate.strip()
                    break

        if raw_date:
            self.logger.debug(f"📅 Fecha encontrada (cruda): '{raw_date}'")
        else:
            self.logger.debug(f"❌ No se encontró fecha en la página")

        return raw_date

    def _extract_job_type(self, response):
        job_type_text_candidates = [
            response.xpath("//p[contains(@class, 'js-item') and contains(., 'Jornada')]/span/text()").get(),
            response.xpath("//li[contains(., 'Jornada')]/span/text()").get(),
            response.xpath("//p[contains(@class, 'js-item') and contains(., 'Tipo de Contrato')]/span/text()").get(),
            response.xpath("//li[contains(., 'Tipo de Contrato')]/span/text()").get(),
            response.css('h1::text').get(),
            response.css('div#detail_box, div.box_detail').get()
        ]

        text_to_analyze = " ".join([t for t in job_type_text_candidates if t is not None]).lower()

        if 'completa' in text_to_analyze or 'full-time' in text_to_analyze:
            return 'Full-time'
        elif 'parcial' in text_to_analyze or 'part-time' in text_to_analyze:
            return 'Part-time'
        elif 'remoto' in text_to_analyze or 'remote' in text_to_analyze:
            return 'Remote'
        elif 'híbrido' in text_to_analyze or 'hybrid' in text_to_analyze:
            return 'Hybrid'
        elif 'contrato' in text_to_analyze or 'indefinido' in text_to_analyze:
            return 'Contract'
        elif 'eventual' in text_to_analyze:
            return 'Contract'
        elif 'pasantía' in text_to_analyze or 'internship' in text_to_analyze:
            return 'Internship'
        return 'Full-time'

    def _extract_seniority_level(self, response, title):
        seniority_text_candidates = [
            response.xpath("//p[contains(@class, 'js-item') and contains(., 'Nivel')]/span/text()").get(),
            response.xpath("//li[contains(., 'Nivel')]/span/text()").get(),
            response.xpath("//strong[contains(text(), 'Nivel de Experiencia:')]/following-sibling::span[1]/text()").get(),
            title
        ]

        text_to_analyze = " ".join([t for t in seniority_text_candidates if t is not None]).lower()

        if 'junior' in text_to_analyze or 'jr' in text_to_analyze or 'practicante' in text_to_analyze or 'intern' in text_to_analyze:
            return 'Junior'
        elif 'senior' in text_to_analyze or 'sr' in text_to_analyze or 'sénior' in text_to_analyze:
            return 'Senior'
        elif 'semi senior' in text_to_analyze or 'ssr' in text_to_analyze or 'mid' in text_to_analyze:
            return 'Mid'
        elif 'lead' in text_to_analyze or 'principal' in text_to_analyze or 'jefe' in text_to_analyze or 'gerente' in text_to_analyze:
            return 'Lead'
        elif 'staff' in text_to_analyze:
            return 'Senior'
        return None

    @staticmethod
    def extract_job_id_from_url(url):
        match = re.search(r'-([A-Fa-f0-9]{32})(?:#|$)', url)
        return match.group(1) if match else None

    def reverse_country_domain_lookup(self, domain_prefix):
        for country, prefix in self.COUNTRY_DOMAINS.items():
            if prefix == domain_prefix:
                return country.capitalize()
        return None

    @staticmethod
    def parse_relative_date_computrabajo(text):
        if not text:
            return None

        text = text.lower().strip()
        today = datetime.date.today()

        meses_es_to_en = {
            'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr',
            'may': 'may', 'jun': 'jun', 'jul': 'jul', 'ago': 'aug',
            'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec',
            'enero': 'january', 'febrero': 'february', 'marzo': 'march', 'abril': 'april',
            'mayo': 'may', 'junio': 'june', 'julio': 'july', 'agosto': 'august',
            'septiembre': 'september', 'octubre': 'october', 'noviembre': 'november', 'diciembre': 'december'
        }

        if "hoy" in text:
            return str(today)
        elif "ayer" in text:
            return str(today - datetime.timedelta(days=1))

        m_day = re.search(r"hace\s+(\d+)\s+día(?:s)?", text)
        if m_day:
            days = int(m_day.group(1))
            return str(today - datetime.timedelta(days=days))

        m_hour = re.search(r"hace\s+(\d+)\s+hora(?:s)?", text)
        if m_hour:
            return str(today)

        m_full_date_spanish = re.search(r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})', text)
        if m_full_date_spanish:
            day, month_name_es, year = m_full_date_spanish.groups()
            month_name_en = meses_es_to_en.get(month_name_es, month_name_es)
            try:
                parsed_date = dateparser.parse(f"{day} {month_name_en} {year}", fuzzy=True).date()
                return str(parsed_date)
            except (ValueError, AttributeError):
                logging.debug(f"Computrabajo: No se pudo parsear fecha 'DD de Month de YYYY' '{text}'")

        m_slash_dash_date = re.search(r'(\d{1,2}[\/-]\d{1,2}[\/-]\d{4})', text)
        if m_slash_dash_date:
            try:
                parsed_date = datetime.datetime.strptime(m_slash_dash_date.group(1), '%d/%m/%Y').date()
                return str(parsed_date)
            except ValueError:
                try:
                    parsed_date = datetime.datetime.strptime(m_slash_dash_date.group(1), '%d-%m-%Y').date()
                    return str(parsed_date)
                except ValueError:
                    logging.debug(f"Computrabajo: No se pudo parsear fecha DD/MM/YYYY o DD-MM-YYYY '{text}'")

        try:
            clean_text = re.sub(r'publicado(?:\s+el)?:?', '', text).strip()
            parsed_date = dateparser.parse(clean_text, fuzzy=True, languages=['es', 'en'], dayfirst=True)

            if parsed_date:
                parsed_date = parsed_date.date()
                if parsed_date > today + datetime.timedelta(days=30):
                    if parsed_date.month < today.month or (parsed_date.month == today.month and parsed_date.day < today.day):
                        parsed_date = parsed_date.replace(year=today.year - 1)
                return str(parsed_date)
        except Exception as e:
            logging.debug(f"Computrabajo: No se pudo parsear la fecha '{text}' con dateutil.parser: {e}")

        return None

    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"❌ Request HTTPError (Computrabajo): {response.status} en {request.url}")
        elif failure.check(DNSLookupError):
            self.logger.error(f"❌ Request DNSLookupError (Computrabajo): {failure.value} en {request.url}")
        elif failure.check(TimeoutError, TCPTimedOutError):
            self.logger.error(f"❌ Request TimeoutError (Computrabajo): {failure.value} en {request.url}")
        else:
            self.logger.error(f"❌ Request fallido (Computrabajo): {failure.value} en {request.url}")
