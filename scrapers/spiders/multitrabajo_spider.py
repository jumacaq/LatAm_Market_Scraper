import scrapy
from scrapers.items import JobItem
import datetime

class MultitrabajoSpider(scrapy.Spider):
    name = "multitrabajo_spider"
    allowed_domains = ["multitrabajos.com"]
    handle_httpstatus_list = [403, 429, 500]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,
        'DEFAULT_REQUEST_HEADERS': {
             'Authority': 'www.multitrabajos.com',
             'Referer': 'https://www.google.com/',
        }
    }

    def start_requests(self):
        # 1. Visit Homepage to establish session
        yield scrapy.Request(
            url='https://www.multitrabajos.com/',
            callback=self.start_search,
            dont_filter=True
        )

    def start_search(self, response):
        if response.status in [403, 429]:
             self.logger.error("⛔ Blocked at Multitrabajos Homepage.")
             return

        self.logger.info("✅ Multitrabajos Session established. Searching...")
        urls = [
            "https://www.multitrabajos.com/empleos-busqueda-tecnologia.html",
            "https://www.multitrabajos.com/empleos-busqueda-programador.html"
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if response.status in [403, 429]:
             self.logger.error(f"⛔ 403 Forbidden on {response.url}.")
             return

        self.logger.info(f"🔍 Parsing Real Data: {response.url}")
        
        # Navent / Multitrabajos structure (divs with ids like 'aviso-123')
        jobs = response.css('div[id^="aviso-"]')

        for job in jobs:
            try:
                item = JobItem()
                
                title = job.css('h2::text').get() or job.css('h3::text').get()
                company = job.css('label::text').get() or job.css('a[class*="Logo"]::attr(alt)').get() or "Confidencial"
                
                rel_url = job.css('a[id^="id-aviso"]::attr(href)').get()
                full_url = response.urljoin(rel_url) if rel_url else response.url
                
                loc = job.css('div[class*="Location"]::text').get() or "Ecuador"

                item['title'] = title.strip() if title else "Vacante"
                item['company'] = company.strip()
                item['url'] = full_url
                item['location'] = loc.strip()
                item['source'] = 'Multitrabajo'
                item['posted_date'] = datetime.date.today().isoformat()
                
                if 'tecnologia' in response.url:
                    item['sector'] = 'Future of Work'
                else:
                    item['sector'] = 'Other'
                
                item['seniority'] = 'Unknown'
                
                if item['title'] != "Vacante":
                    yield item
                    
            except Exception as e:
                self.logger.error(f"Error parsing Multitrabajo item: {e}")