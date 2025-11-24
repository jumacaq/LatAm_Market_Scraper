import scrapy

class JobItem(scrapy.Item):
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    posted_date = scrapy.Field()
    sector = scrapy.Field()
    seniority = scrapy.Field()
    skills = scrapy.Field()
    company_data = scrapy.Field()