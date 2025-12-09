# scrapers/settings.py

BOT_NAME = "job_market_intelligence"
SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

# Settings para el Spider de LinkedIn (Scrapy Puro)
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 15 # Delay crucial
CONCURRENT_REQUESTS = 1 
LOG_LEVEL = 'INFO'