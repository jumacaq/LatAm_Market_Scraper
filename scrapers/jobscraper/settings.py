# Scrapy Settings
# =============================================================================

SCRAPY_SETTINGS = """
BOT_NAME = 'jobscraper'

SPIDER_MODULES = ['jobscraper.spiders']
NEWSPIDER_MODULE = 'jobscraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# Configure delay for requests (be respectful)
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable cookies (sometimes needed)
COOKIES_ENABLED = True

# Override user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Enable pipelines
ITEM_PIPELINES = {
    'jobscraper.pipelines.CleaningPipeline': 100,
    'jobscraper.pipelines.SkillExtractionPipeline': 200,
    'jobscraper.pipelines.SectorClassificationPipeline': 300,
    'jobscraper.pipelines.SupabasePipeline': 400,
}

# Enable AutoThrottle for adaptive delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Cache for development
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
"""

print("✅ Scrapy items and pipelines ready!")
print("\nPipeline flow:")
print("1. CleaningPipeline: Cleans and normalizes text")
print("2. SkillExtractionPipeline: Extracts tech skills")
print("3. SectorClassificationPipeline: Classifies into EdTech/Fintech/Future of Work")
print("4. SupabasePipeline: Stores in database with relationships")