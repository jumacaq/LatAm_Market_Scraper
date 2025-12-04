# FILE: job-market-intelligence/scrapers/settings.py
BOT_NAME = "market_scraper"
SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

# ADVERTENCIA: ROBOTSTXT_OBEY = False. Esto se hace por necesidad para acceder a sitios clave
# como LinkedIn y Computrabajo. Implica riesgos éticos y de bloqueo.
# Asegúrate de entender las implicaciones y de usar estrategias anti-bloqueo robustas.
ROBOTSTXT_OBEY = False

# --- CONFIGURACIONES ANTI-BLOQUEO (HUMANIZACIÓN) ---
# Reducir concurrencia y aumentar el retardo para no saturar al servidor (Evitar 429)
# Estas son configuraciones generales, pueden ser sobrescritas por custom_settings en cada spider
CONCURRENT_REQUESTS = 2 # Un poco más permisivo que 1, pero aún conservador
DOWNLOAD_DELAY = 5    # Retardo significativo entre peticiones
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle: Ajusta la velocidad según la latencia del servidor
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0 # Mantener una solicitud concurrente activa en promedio

COOKIES_ENABLED = True

# Headers predeterminados (pueden ser sobrescritos por middlewares o spiders)
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

DOWNLOADER_MIDDLEWARES = {
    'scrapers.middlewares.RotateUserAgentMiddleware': 400,
    # Puedes añadir otros middlewares aquí si son necesarios
}

ITEM_PIPELINES = {
   "scrapers.pipelines.CleaningPipeline": 100,
   "scrapers.pipelines.NormalizationPipeline": 200,
   "scrapers.pipelines.SkillExtractionPipeline": 300,
   "scrapers.pipelines.SectorClassificationPipeline": 400,
   "scrapers.pipelines.SupabasePipeline": 500,
}

# Configuración para el registro (logging)
LOG_LEVEL = 'INFO' # Puedes cambiar a 'DEBUG' para ver más detalles durante el desarrollo
# LOG_FILE = 'scrapy_log.log' # Descomenta para guardar los logs en un archivo

# Otros ajustes útiles:
# RETRY_ENABLED = True
# RETRY_TIMES = 3
