# FILE: Proyecto/job-market-intelligence/scrapers/settings.py
BOT_NAME = "market_scraper"
SPIDER_MODULES = ["scrapers.spiders"]
NEWSPIDER_MODULE = "scrapers.spiders"

# ADVERTENCIA: ROBOTSTXT_OBEY = False. Esto se hace por necesidad para acceder a sitios clave
# como LinkedIn y Computrabajo. Implica riesgos éticos y de bloqueo.
# Asegúrate de entender las implicaciones y de usar estrategias anti-bloqueo robustas.
ROBOTSTXT_OBEY = False

# --- CONFIGURACIONES ANTI-BLOQUEO (HUMANIZACIÓN) ---
CONCURRENT_REQUESTS = 2 # Considera 1 si hay muchos bloqueos
DOWNLOAD_DELAY = 5    # Retardo significativo entre peticiones (mínimo, puede ser mayor por AutoThrottle)
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle: Ajusta la velocidad según la latencia del servidor
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5 # Mantener una solicitud concurrente activa en promedio
AUTOTHROTTLE_DEBUG = False # Cambiar a True para ver logs de AutoThrottle

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
    # Añade más middlewares si son necesarios (ej. manejo de proxy)
}

# ORDEN CRÍTICO DE LOS PIPELINES
ITEM_PIPELINES = {
   "scrapers.pipelines.CleaningPipeline": 100,
   "scrapers.pipelines.NormalizationPipeline": 200,
   "scrapers.pipelines.CompanyEnrichmentPipeline": 300, # Nuevo pipeline de enriquecimiento
   "scrapers.pipelines.SkillExtractionPipeline": 400,
   "scrapers.pipelines.SectorClassificationPipeline": 500,
   "scrapers.pipelines.SupabasePipeline": 600, # Asegúrate de que este sea el último para la persistencia
}

# Configuración para el registro (logging)
LOG_LEVEL = 'INFO' # Mantener en INFO para producción, cambiar a DEBUG para depuración
# LOG_FILE = 'scrapy_log.log' # Descomenta para guardar los logs en un archivo

# Otros ajustes útiles:
# RETRY_ENABLED = True
# RETRY_TIMES = 3
# RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 400, 403, 404, 408] # Códigos para reintentar
