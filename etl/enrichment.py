from scrapers.spiders.company_enrichment_spider import CompanyEnrichmentSpider
from scrapy.crawler import CrawlerProcess

class EnrichmentService:
    def enrich_new_companies(self):
        missing_companies = ['duolingo', 'coursera'] 
        process = CrawlerProcess()
        process.crawl(CompanyEnrichmentSpider, companies=missing_companies)
        process.start()