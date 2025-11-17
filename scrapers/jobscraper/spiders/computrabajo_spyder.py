# Computrabajo is massive in LatAm (requires careful scraping)
# =============================================================================

import scrapy
from jobscraper.items import JobItem
import re


class ComputrabajoSpider(scrapy.Spider):
    name = 'computrabajo'
    allowed_domains = ['computrabajo.com', 'computrabajo.com.mx', 'computrabajo.com.co']
    
    # Start URLs for different countries
    start_urls = [
        # Mexico - Tech jobs
        'https://www.computrabajo.com.mx/ofertas-de-trabajo-de-programador',
        'https://www.computrabajo.com.mx/ofertas-de-trabajo-de-desarrollador',
        'https://www.computrabajo.com.mx/ofertas-de-trabajo-de-data-scientist',
        
        # Colombia
        'https://www.computrabajo.com.co/ofertas-de-trabajo-de-desarrollador-de-software',
        'https://www.computrabajo.com.co/ofertas-de-trabajo-de-ingeniero-de-sistemas',
        
        # Peru
        'https://www.computrabajo.com.pe/ofertas-de-trabajo-de-desarrollador',
        
        # Argentina
        'https://www.computrabajo.com.ar/ofertas-de-trabajo-de-desarrollador',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,  # Be extra respectful
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def parse(self, response):
        """Parse job listing page"""
        # Job links are in article elements
        job_links = response.css('article.box_offer a.fc_base::attr(href)').getall()
        
        for link in job_links:
            yield response.follow(link, callback=self.parse_job)
        
        # Pagination
        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_job(self, response):
        """Parse individual job page"""
        item = JobItem()
        
        # Title
        item['title'] = response.css('h1.title_offer::text').get()
        
        # Company
        item['company_name'] = response.css('p.title_offer a::text').get()
        
        # Location
        location = response.css('p.location::text').get()
        item['location'] = location.strip() if location else None
        
        # Extract country from URL or location
        item['country'] = self.extract_country_from_domain(response.url)
        
        # Description
        description = response.css('div.box_detail').get()
        item['description'] = description
        
        # Posted date (relative, like "Hace 3 días")
        posted = response.css('span.dO::text').get()
        item['posted_date'] = self.parse_relative_date(posted)
        
        # Salary (often not displayed)
        salary = response.css('p.salary::text').get()
        item['salary_range'] = salary.strip() if salary else None
        
        # Metadata
        item['source_url'] = response.url
        item['source_platform'] = 'Computrabajo'
        item['job_id'] = self.extract_job_id_from_url(response.url)
        
        yield item
    
    @staticmethod
    def extract_country_from_domain(url):
        """Extract country from domain"""
        domain_map = {
            'com.mx': 'Mexico',
            'com.co': 'Colombia',
            'com.ar': 'Argentina',
            'com.pe': 'Peru',
            'com.cl': 'Chile',
        }
        
        for domain, country in domain_map.items():
            if domain in url:
                return country
        return None
    
    @staticmethod
    def extract_job_id_from_url(url):
        """Extract job ID from URL"""
        match = re.search(r'/(\d+)/?$', url)
        return match.group(1) if match else None
    
    @staticmethod
    def parse_relative_date(date_str):
        """Convert relative dates like 'Hace 3 días' to date"""
        # For MVP, return None - can be enhanced later
        # Would need to calculate based on "Hace X días/horas"
        return None


print("✅ LatAm job spiders ready!")
print("\nAvailable spiders:")
print("1. getonboard: Scrapes GetonBrd.com (very reliable)")
print("2. torre: Uses Torre.ai API (fastest, most reliable)")
print("3. computrabajo: Scrapes Computrabajo (largest LatAm job site)")
print("\nRun with: scrapy crawl getonboard")