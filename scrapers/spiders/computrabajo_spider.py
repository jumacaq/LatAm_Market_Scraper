import scrapy
from scrapers.items import JobItem
import datetime
import random

class ComputrabajoSpider(scrapy.Spider):
    name = "computrabajo_spider"
    allowed_domains = ["computrabajo.com"]
    # Capture 403s to handle them gracefully
    handle_httpstatus_list = [403, 429, 500, 503]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 4,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,
        'DEFAULT_REQUEST_HEADERS': {
            'Authority': 'ec.computrabajo.com',
            'Referer': 'https://www.google.com/',
        }
    }

    def start_requests(self):
        # STRATEGY: Visit Homepage first to establish cookies/session
        yield scrapy.Request(
            url='https://ec.computrabajo.com/',
            callback=self.start_search,
            dont_filter=True
        )

    def start_search(self, response):
        if response.status in [403, 429]:
             self.logger.error("⛔ Blocked at Homepage (403). Try changing IP or waiting.")
             return

        self.logger.info("✅ Computrabajo Session established. Starting Search...")
        urls = [
            "https://ec.computrabajo.com/trabajo-de-programador",
            "https://ec.computrabajo.com/trabajo-de-analista",
            "https://ec.computrabajo.com/trabajo-de-tecnologia"
        ]
        for url in urls:
            # Add timestamp to avoid cache
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if response.status in [403, 429]:
             self.logger.error(f"⛔ 403 Forbidden on {response.url}.")
             return

        self.logger.info(f"🔍 Scanning Real Data: {response.url}")
        
        # Updated Selectors for Computrabajo structure
        jobs = response.css('article.box_offer')
        if not jobs:
            jobs = response.css('div.offer')

        for job in jobs:
            try:
                item = JobItem()
                
                # Robust selector logic
                title = job.css('h2.fs18 a::text').get() or job.css('a.js-o-link::text').get()
                company = job.css('p.fs16 span::text').get() or job.css('a.empr::text').get()
                
                rel_url = job.css('a.js-o-link::attr(href)').get()
                full_url = response.urljoin(rel_url) if rel_url else response.url
                
                location = job.css('p.fs16 span.fc_base::text').get()
                desc = job.css('p.body-word-break::text').get() or ""

                item['title'] = title.strip() if title else "Sin Título"
                item['company'] = company.strip() if company else "Confidencial"
                item['url'] = full_url
                item['location'] = location.strip() if location else "Ecuador"
                item['description'] = desc.strip()
                item['source'] = 'Computrabajo'
                item['posted_date'] = datetime.date.today().isoformat()
                
                # Sector categorization
                t_lower = item['title'].lower()
                if 'banc' in t_lower or 'finan' in t_lower:
                    item['sector'] = 'Fintech'
                elif 'profesor' in t_lower or 'docente' in t_lower:
                    item['sector'] = 'EdTech'
                else:
                    item['sector'] = 'Future of Work'
                
                item['seniority'] = 'Mid-Level'
                
                if item['title'] != "Sin Título":
                    yield item
            except Exception as e:
                self.logger.error(f"Error parsing job: {e}")