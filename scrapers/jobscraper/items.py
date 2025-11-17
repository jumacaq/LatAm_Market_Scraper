# Data models for scraped jobs

import scrapy
from datetime import datetime


class JobItem(scrapy.Item):
    """Main job item structure"""
    job_id = scrapy.Field()  # Unique identifier from source
    title = scrapy.Field()
    company_name = scrapy.Field()
    location = scrapy.Field()
    country = scrapy.Field()
    job_type = scrapy.Field()  # Full-time, Part-time, Contract
    seniority_level = scrapy.Field()  # Junior, Mid, Senior
    sector = scrapy.Field()  # EdTech, Fintech, Future of Work
    description = scrapy.Field()
    requirements = scrapy.Field()
    salary_range = scrapy.Field()
    posted_date = scrapy.Field()
    source_url = scrapy.Field()
    source_platform = scrapy.Field()
    scraped_at = scrapy.Field()
    skills = scrapy.Field()  # List of extracted skills
