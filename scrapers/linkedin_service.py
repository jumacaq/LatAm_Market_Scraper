# scrapers/linkedin_service.py

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from scrapers.spiders.linkedin_spider import LinkedInScrapySpider
from typing import List, Dict, Any
import logging

# ==========================================================
# 🚨 CORRECCIÓN: CLASE MOVIDA A NIVEL GLOBAL
# Esta clase actúa como un pipeline temporal para capturar los items.
# Debe estar fuera de cualquier función para que Scrapy la encuentre.
# ==========================================================
all_results_global: List[Dict[str, Any]] = []

class ItemCollectorPipeline:
    def process_item(self, item, spider):
        # Capturamos el resultado en la lista global
        all_results_global.append(dict(item))
        return item
# ==========================================================


def run_linkedin_spider(keywords: List[str], countries: List[str]) -> List[Dict[str, Any]]:
    """
    Ejecuta el Spider de Scrapy de LinkedIn y captura los resultados.
    """
    # Limpiamos la lista global antes de cada ejecución
    all_results_global.clear()

    # 1. Configurar el motor de Scrapy
    settings = get_project_settings()
    # Usamos __main__.ItemCollectorPipeline porque el script se ejecuta como main
    settings.set('ITEM_PIPELINES', {'__main__.ItemCollectorPipeline': 1}, priority='cmdline')
    settings.set('LOG_LEVEL', 'INFO', priority='cmdline')
    
    configure_logging({'LOG_LEVEL': 'INFO'})
    
    # 2. Inicializar y ejecutar el proceso
    try:
        process = CrawlerProcess(settings=settings)
        
        process.crawl(
            LinkedInScrapySpider, 
            keywords=keywords, 
            target_locations=countries,
            max_jobs_to_scrape=300
        )
        
        # Inicia el reactor de Scrapy (bloquea hasta que termina)
        # Esto iniciará y completará el scraping de LinkedIn
        process.start(stop_after_crawl=True) 

    except Exception as e:
        logging.error(f"❌ Error fatal al ejecutar el proceso Scrapy: {e}")

    # Retornamos la lista que fue llenada por el pipeline
    return all_results_global