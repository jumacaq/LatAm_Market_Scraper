# Torre.co has a public API - much better than scraping!
# =============================================================================

import scrapy
import json
from jobscraper.items import JobItem
from datetime import datetime


class TorreSpider(scrapy.Spider):
    name = 'torre'
    allowed_domains = ['torre.ai']
    
    # Torre API endpoints
    api_base = 'https://search.torre.ai/opportunities/_search'
    
    def start_requests(self):
        """Start with API requests for different queries"""
        
        # Queries for EdTech, Fintech, Future of Work
        queries = [
            {
                'keywords': ['software', 'developer', 'engineer'],
                'countries': ['mexico', 'colombia', 'argentina', 'chile', 'peru']
            },
            {
                'keywords': ['data scientist', 'machine learning'],
                'countries': ['mexico', 'colombia', 'argentina', 'chile']
            },
            {
                'keywords': ['product manager', 'product owner'],
                'countries': ['mexico', 'colombia', 'argentina']
            }
        ]
        
        for query in queries:
            for keyword in query['keywords']:
                for country in query['countries']:
                    payload = self.build_search_payload(keyword, country)
                    
                    yield scrapy.Request(
                        url=self.api_base,
                        method='POST',
                        body=json.dumps(payload),
                        headers={'Content-Type': 'application/json'},
                        callback=self.parse_api_response,
                        meta={'keyword': keyword, 'country': country}
                    )
    
    @staticmethod
    def build_search_payload(keyword, country):
        """Build Torre API search payload"""
        return {
            "query": keyword,
            "offset": 0,
            "size": 20,  # Results per page
            "filters": {
                "locations": [
                    {
                        "country": country
                    }
                ],
                "type": ["job"]
            }
        }
    
    def parse_api_response(self, response):
        """Parse Torre API JSON response"""
        data = json.loads(response.text)
        
        for result in data.get('results', []):
            item = self.parse_job_from_api(result)
            if item:
                yield item
    
    def parse_job_from_api(self, job_data):
        """Convert Torre API job data to JobItem"""
        item = JobItem()
        
        # Basic info
        item['title'] = job_data.get('objective')
        
        # Company
        organization = job_data.get('organizations', [{}])[0]
        item['company_name'] = organization.get('name')
        
        # Location
        locations = job_data.get('locations', [])
        if locations:
            location = locations[0]
            item['country'] = location.get('country')
            item['location'] = f"{location.get('city', '')}, {location.get('country', '')}"
        
        # Job type
        remote = job_data.get('remote', False)
        item['job_type'] = 'Remote' if remote else 'Onsite'
        
        # Compensation (salary)
        compensation = job_data.get('compensation', {})
        if compensation:
            salary_data = compensation.get('data', {})
            currency = salary_data.get('currency', '')
            min_amount = salary_data.get('minAmount', '')
            max_amount = salary_data.get('maxAmount', '')
            
            if min_amount and max_amount:
                item['salary_range'] = f"{currency} {min_amount} - {max_amount}"
        
        # Description
        item['description'] = job_data.get('details', [{}])[0].get('text', '')
        
        # Posted date
        item['posted_date'] = job_data.get('deadline', '').split('T')[0] if job_data.get('deadline') else None
        
        # Metadata
        item['source_url'] = f"https://torre.ai/jobs/{job_data.get('id')}"
        item['source_platform'] = 'Torre'
        item['job_id'] = job_data.get('id')
        
        return item
