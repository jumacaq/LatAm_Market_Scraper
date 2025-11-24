import scrapy

class CompanyEnrichmentSpider(scrapy.Spider):
    name = "company_enrichment"
    
    def __init__(self, companies=None, *args, **kwargs):
        super(CompanyEnrichmentSpider, self).__init__(*args, **kwargs)
        self.companies = companies or []

    def start_requests(self):
        for company in self.companies:
            yield scrapy.Request(
                f"https://www.google.com/search?q={company}", 
                callback=self.parse
            )

    def parse(self, response):
        pass