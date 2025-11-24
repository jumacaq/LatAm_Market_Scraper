import scrapy
from scrapers.items import JobItem
import datetime
# IGNORED TEMPORARILY AS REQUESTED
class ComputrabajoSpider(scrapy.Spider):
    name = "computrabajo_spider"
    allowed_domains = ["computrabajo.com"]
    def parse(self, response):
        pass