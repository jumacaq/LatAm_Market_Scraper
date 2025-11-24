import scrapy
from scrapers.items import JobItem
import datetime
# IGNORED TEMPORARILY AS REQUESTED
class MultitrabajoSpider(scrapy.Spider):
    name = "multitrabajo_spider"
    allowed_domains = ["multitrabajos.com"]
    def parse(self, response):
        pass