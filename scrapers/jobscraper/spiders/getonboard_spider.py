# GetonBoard is a popular LatAm tech job board (very scraper-friendly)

import scrapy
from datetime import datetime
import re
from jobscraper.items import JobItem


class GetonBoardSpider(scrapy.Spider):
    name = 'getonboard'
    allowed_domains = ['getonbrd.com']
    
    # Start URLs for different countries and sectors
    start_urls = [
    'https://www.getonbrd.com/empleos',
    'https://www.getonbrd.com/empleos?country=MX',  # Mexico
    'https://www.getonbrd.com/empleos?country=CL',  # Chile
    'https://www.getonbrd.com/empleos?country=CO',  # Colombia
    'https://www.getonbrd.com/empleos?country=AR',  # Argentina
    ]
    
    def parse(self, response):
        """Parse job listing page"""
        all_links = response.css('a::attr(href)').getall()
        #links = response.css('a[href*="/empleos/programacion/"]::attr(href)').getall()
        self.logger.info(f"🔍 Encontrados {len(all_links)} links")
    
        # Filtrar solo links de trabajos (no categorías)
        job_links = [l for l in all_links if '/empleos/' in l and l.count('/') >= 4]
        unique_links = list(set(job_links))
        
        self.logger.info(f"🔍 Encontrados {len(unique_links)} trabajos únicos")

        for link in unique_links:
            yield response.follow(link, callback=self.parse_job)
    
        
        # Follow pagination
        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_job(self, response):
        """Parse individual job page"""
        item = JobItem()
    
        item['title'] = response.css('h1.gb-landing-cover__title::text').get()
        item['company_name'] = response.css('span[itemprop="hiringOrganization"]::text').get()
        item['location'] = response.css('span[itemprop="address"]::text').get()
        item['description'] = response.css('div.gb-landing-section').get()
        item['source_url'] = response.url
        item['source_platform'] = 'GetonBoard'
        item['scraped_at'] = datetime.now().isoformat()
    
        # ✅ Solo yield si tiene título Y descripción
        if item.get('title') and item.get('description'):
            yield item
        else:
            self.logger.warning(f"⚠️ Saltado (datos incompletos): {response.url}")
    
    
    @staticmethod
    def extract_job_id(url):
        """Extract job ID from URL"""
        match = re.search(r'/jobs/([a-zA-Z0-9-]+)', url)
        return match.group(1) if match else None
    
    @staticmethod
    def normalize_seniority(seniority):
        """Normalize seniority levels"""
        if not seniority:
            return None
        
        seniority_lower = seniority.lower()
        if 'junior' in seniority_lower:
            return 'Junior'
        elif 'senior' in seniority_lower:
            return 'Senior'
        elif 'semi senior' in seniority_lower or 'ssr' in seniority_lower:
            return 'Mid'
        elif 'expert' in seniority_lower or 'lead' in seniority_lower:
            return 'Lead'
        else:
            return 'Mid'
        
    
    @staticmethod
    def extract_country_from_url(url):
        """Extract country from URL"""
        if '/mexico' in url:
            return 'Mexico'
        elif '/chile' in url:
            return 'Chile'
        elif '/colombia' in url:
            return 'Colombia'
        elif '/argentina' in url:
            return 'Argentina'
        elif '/remote-latam' in url:
            return 'Remote LatAm'
        return None
