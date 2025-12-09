import scrapy

class JobItem(scrapy.Item):
    job_id = scrapy.Field()
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    country = scrapy.Field()
    posted_date = scrapy.Field()
    description = scrapy.Field()
    salary = scrapy.Field()
    seniority = scrapy.Field()
    skills = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    sector = scrapy.Field()
