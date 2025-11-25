# Computrabajo is massive in LatAm (requires careful scraping)
# =============================================================================

import scrapy
from jobscraper.items import JobItem
import re


class ComputrabajoSpider(scrapy.Spider):
    name = 'computrabajo'
    allowed_domains = ["computrabajo.com",
        "computrabajo.com.mx",
        "computrabajo.com.co",
        "computrabajo.com.pe",
        "computrabajo.com.ar",
    ]
    
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
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
        }
    }

    
    # Start URLs for different countries
    start_urls = [
        # Mexico - Tech jobs
        'https://mx.computrabajo.com/trabajo-de-programador',
        'https://mx.computrabajo.com/trabajo-de-desarrollador',
        'https://mx.computrabajo.com/trabajo-de-data-scientist',
        # Colombia
        'https://co.computrabajo.com/trabajo-de-programador',
        'https://co.computrabajo.com/trabajo-de-desarrollador',
        'https://co.computrabajo.com/trabajo-de-data-scientist',
    
        # Argentina
        'https://ar.computrabajo.com/trabajo-de-programador',
        'https://ar.computrabajo.com/trabajo-de-desarrollador',
        'https://ar.computrabajo.com/trabajo-de-data-scientist',
    
        # Perú
        'https://pe.computrabajo.com/trabajo-de-programador',
        'https://pe.computrabajo.com/trabajo-de-desarrollador',
        'https://pe.computrabajo.com/trabajo-de-data-scientist',
]
    
    
    
    def parse(self, response):
        """Parsea página de listados de ofertas"""
    
        offers = response.css("article.box_offer")
        self.logger.info(f"🔍 Encontradas {len(offers)} ofertas")
    
        for offer in offers:
            relative_url = offer.css("h2 a.js-o-link::attr(href)").get()
            if relative_url:
                self.logger.info(f"➡️ Siguiendo: {relative_url}") 
                yield response.follow(relative_url, callback=self.parse_job)
        # Paginación
        next_page = (
            response.css("a[rel='next']::attr(href)").get()
            or response.css("a.pagination__next::attr(href)").get()
        )
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_job(self, response):
        """Parsea una oferta individual"""
        item = JobItem()

        item["source_platform"] = "Computrabajo"
        item["source_url"] = response.url
        item["job_id"] = self.extract_job_id_from_url(response.url)

        # Título
        item["title"] = response.css("h1::text").get()

        # Empresa
        item["company_name"] = response.css("p.title-company a::text, a.company::text").get()
        # Solo yield si tiene company_name
        if item.get("company_name"):
            yield item
        else:
            self.logger.warning(f"Saltado (sin empresa): {response.url}")
        # Ubicación
        location = response.css("p.location span::text").get()
        item["location"] = location.strip() if location else None

        # País
        item["country"] = self.extract_country_from_domain(response.url)

        # Descripción
        desc = response.css("div#detail_box, div.box_detail").get()
        item["description"] = desc

        # Fecha de publicación
        raw_date = response.css("span.date, span.dO::text").get()
        item["posted_date"] = self.parse_relative_date(raw_date)

        # Salario
        salary = response.css("p.salary span::text, p.salary::text").get()
        item["salary_range"] = salary.strip() if salary else None

        yield item

    @staticmethod
    def extract_country_from_domain(url):
        domain_map = {
            "mx.com": "Mexico",
            "co.com": "Colombia",
            "pe.com": "Peru",
            "ar.com": "Argentina",
        }
        for d, country in domain_map.items():
            if d in url:
                return country
        return None

    @staticmethod
    def extract_job_id_from_url(url):
        match = re.search(r"/(\d+)$", url)
        return match.group(1) if match else None

    @staticmethod
    def parse_relative_date(text):
        """Convierte 'Hace 3 días' en fecha real"""
        if not text:
            return None

        text = text.lower()

        import datetime

        today = datetime.date.today()

        if "hace" in text:
            m = re.search(r"hace (\d+) día", text)
            if m:
                days = int(m.group(1))
                return str(today - datetime.timedelta(days=days))

            m = re.search(r"hace (\d+) hora", text)
            if m:
                hours = int(m.group(1))
                return str(today)

        # Si no matchea, devolverla cruda para cleaning pipeline
        return text