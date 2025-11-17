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
        # Mexico
        'https://www.getonbrd.com/jobs/programming/mexico',
        'https://www.getonbrd.com/jobs/data-science/mexico',
        # Chile
        'https://www.getonbrd.com/jobs/programming/chile',
        'https://www.getonbrd.com/jobs/data-science/chile',
        # Colombia
        'https://www.getonbrd.com/jobs/programming/colombia',
        # Argentina
        'https://www.getonbrd.com/jobs/programming/argentina',
        # Remote LatAm
        'https://www.getonbrd.com/jobs/programming/remote-latam',
    ]
    
    def parse(self, response):
        """Parse job listing page"""
        # Extract job cards
        job_cards = response.css('div.gb-results__item')
        
        for card in job_cards:
            job_url = card.css('a.gb-results__item-link::attr(href)').get()
            if job_url:
                yield response.follow(job_url, callback=self.parse_job)
        
        # Follow pagination
        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_job(self, response):
        """Parse individual job page"""
        item = JobItem()
        
        # Basic info
        item['title'] = response.css('h1.gb-landing-cover__title::text').get()
        item['company_name'] = response.css('a.gb-landing-cover__company::text').get()
        
        # Location
        location = response.css('span.gb-landing-cover__location::text').get()
        item['location'] = location.strip() if location else None
        
        # Job type (Remote, Onsite, Hybrid)
        modality = response.css('li:contains("Modalidad") span::text').get()
        if modality:
            item['job_type'] = 'Remote' if 'remoto' in modality.lower() else 'Onsite'
        
        # Seniority
        seniority = response.css('li:contains("Seniority") span::text').get()
        item['seniority_level'] = self.normalize_seniority(seniority)
        
        # Description
        description = response.css('div.gb-markdown-content').get()
        item['description'] = description
        
        # Requirements (usually in a separate section)
        requirements = response.css('div.gb-markdown-content ul').getall()
        item['requirements'] = ' '.join(requirements) if requirements else None
        
        # Salary (if available)
        salary = response.css('li:contains("Compensación") span::text').get()
        item['salary_range'] = salary.strip() if salary else None
        
        # Posted date
        posted = response.css('time::attr(datetime)').get()
        if posted:
            item['posted_date'] = posted.split('T')[0]  # Extract date only
        
        # Metadata
        item['source_url'] = response.url
        item['source_platform'] = 'GetonBoard'
        item['job_id'] = self.extract_job_id(response.url)
        
        yield item
    
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
