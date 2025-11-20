BOT_NAME = "market_scraper"
SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

# IMPORTANT for scraping job sites:
ROBOTSTXT_OBEY = False 
CONCURRENT_REQUESTS = 1 # Very low concurrency to avoid bans
DOWNLOAD_DELAY = 5 # Increased delay to 5s to be very polite
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = True # Essential for session persistence

# Headers default (will be overwritten by middleware)
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'es',
}

DOWNLOADER_MIDDLEWARES = {
    'scrapers.middlewares.RotateUserAgentMiddleware': 543,
}

ITEM_PIPELINES = {
   "scrapers.pipelines.SupabasePipeline": 300,
}