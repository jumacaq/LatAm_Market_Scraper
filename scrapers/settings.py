BOT_NAME = "market_scraper"
SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

ROBOTSTXT_OBEY = False 

# --- ANTI-BLOCKING SETTINGS (HUMANIZACIÓN) ---
# Reducir concurrencia para no saturar al servidor (Evitar 429)
CONCURRENT_REQUESTS = 1

# Retardo MUY significativo entre peticiones para evitar bloqueo de LinkedIn
# 10 segundos es lento, pero seguro.
DOWNLOAD_DELAY = 10
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle: Ajusta velocidad según latencia del servidor
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

COOKIES_ENABLED = True

DOWNLOADER_MIDDLEWARES = {
    'scrapers.middlewares.RotateUserAgentMiddleware': 400,
}

ITEM_PIPELINES = {
   "scrapers.pipelines.SupabasePipeline": 300,
}