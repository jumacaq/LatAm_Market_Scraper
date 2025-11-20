import scrapy
from scrapers.items import JobItem
import datetime
import random

class LinkedInSpider(scrapy.Spider):
    name = "linkedin_spider"
    allowed_domains = ["linkedin.com"]
    
    def start_requests(self):
        keywords = ['EdTech', 'Fintech', 'Desarrollador']
        for k in keywords:
            url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={k}&location=Latam'
            yield scrapy.Request(url, callback=self.parse, meta={'keyword': k}, errback=self.errback_handler)

    def parse(self, response):
        jobs = response.css('li')
        
        if not jobs or len(jobs) == 0:
            self.logger.warning(f"⚠️ LinkedIn blocked or empty.")
            return

        for job in jobs:
            try:
                item = JobItem()
                item['title'] = job.css('h3.base-search-card__title::text').get(default='').strip()
                item['company'] = job.css('h4.base-search-card__subtitle::text').get(default='').strip()
                item['url'] = job.css('a.base-card__full-link::attr(href)').get()
                item['location'] = job.css('span.job-search-card__location::text').get(default='').strip()
                item['sector'] = response.meta['keyword']
                item['posted_date'] = datetime.date.today().isoformat()
                item['source'] = 'LinkedIn'
                item['seniority'] = 'Unknown'
                
                if item['title']:
                    yield item
            except Exception as e:
                self.logger.error(f"Error parsing job: {e}")

    def errback_handler(self, failure):
        self.logger.error(f"LinkedIn Request failed: {failure}")