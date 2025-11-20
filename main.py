import logging
import sys
import os
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapers.spiders.linkedin_spider import LinkedInSpider
from scrapers.spiders.computrabajo_spider import ComputrabajoSpider
from scrapers.spiders.multitrabajo_spider import MultitrabajoSpider
from etl.enrichment import EnrichmentService

# Cargar variables de entorno explícitamente
load_dotenv()
logging.basicConfig(level=logging.INFO)

def run_scrapers():
    # Verificar credenciales antes de arrancar
    if "PON_TU_URL" in os.getenv("SUPABASE_URL", ""):
        logging.error("❌ DETENIENDO: Credenciales de Supabase no configuradas en .env")
        return

    logging.info("Starting Scrapers for LinkedIn, Computrabajo & Multitrabajo...")
    process = CrawlerProcess(get_project_settings())
    
    # Registrar los 3 spiders solicitados
    process.crawl(LinkedInSpider)
    process.crawl(ComputrabajoSpider)
    process.crawl(MultitrabajoSpider)
    
    process.start()

def run_enrichment():
    logging.info("Starting Enrichment Pipeline...")
    service = EnrichmentService()
    service.enrich_new_companies()

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "scrape"
    
    if command == "scrape":
        run_scrapers()
    elif command == "enrich":
        run_enrichment()
    else:
        print("Usage: python main.py [scrape|enrich]")