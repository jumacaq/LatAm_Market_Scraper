import logging
import time
import pandas as pd
import os
from typing import List, Dict, Any

# Scrapy setup
from scrapy.crawler import CrawlerProcess

# Importación de Spiders
from jobscraper.spiders.linkedin_spider import LinkedInSpider 
from jobscraper.spiders.computrabajo_spider import ComputrabajoSpider
from jobscraper.spiders.indeed_spider import IndeedSpider

# Importación de Item y Pipelines
from jobscraper.pipelines_full import (
    CleaningPipeline,
    SeniorityPipeline,
    CompanyEnrichmentPipeline,
    SkillExtractionPipeline,
    SectorClassificationPipeline,
    SupabasePipeline
)
# 🚨 CORRECCIÓN FINAL: Importación explícita del colector desde el archivo (módulo)
from jobscraper.pipelines_collector.LinkedInItemCollectorPipeline import LinkedInItemCollectorPipeline

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger('ScrapingManager')

# =================================================================
# 🎯 CONFIGURACIÓN GLOBAL DEL PROYECTO
# =================================================================

# 1. Países objetivo (usados por todos los spiders)
TARGET_COUNTRIES = ["Mexico", "Colombia", "Argentina", "Chile", "Peru"]

# 2. Configuración de Item Pipelines (prioridad: menor número, primero se ejecuta)
full_pipeline_settings = {
    'jobscraper.pipelines_full.CleaningPipeline': 100,
    'jobscraper.pipelines_full.SeniorityPipeline': 150,
    'jobscraper.pipelines_full.CompanyEnrichmentPipeline': 250,
    'jobscraper.pipelines_full.SkillExtractionPipeline': 300,
    'jobscraper.pipelines_full.SectorClassificationPipeline': 350,
    'jobscraper.pipelines_full.SupabasePipeline': 500,
    
    # 🚨 NOTA: La ruta final para el Collector debe ser la más específica para Scrapy
    'jobscraper.pipelines_collector.LinkedInItemCollectorPipeline.LinkedInItemCollectorPipeline': 900,
}

# Nombre del archivo de salida final
OUTPUT_CSV_FILE = 'market_data_final_linkedin.csv'


# =================================================================
# 🚀 FUNCIÓN PRINCIPAL DE EJECUCIÓN
# =================================================================

def run_full_cycle(countries: List[str], max_jobs=1000):
    """
    Ejecuta el proceso Scrapy completo, iniciando los tres spiders.
    """
    settings = {
        'FEEDS': {},
        'ITEM_PIPELINES': full_pipeline_settings,
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'scrapy_output.log', # Escribe en el directorio raíz
        'CLOSESPIDER_ITEMCOUNT': max_jobs * len(countries) * 3, # Límite para 3 spiders
    }

    try:
        process = CrawlerProcess(settings=settings)
        
        logger.info(f"Iniciando ciclo para {len(countries)} países con {len(full_pipeline_settings)} pipelines activos.")

        # 1. Ejecutar LinkedInSpider
        process.crawl(
            LinkedInSpider, 
            target_locations=countries,
            max_jobs_to_scrape=max_jobs
        )
        
        # 2. Ejecutar ComputrabajoSpider
        process.crawl(
            ComputrabajoSpider,
            target_locations=countries 
        )
        
        # 3. Ejecutar IndeedSpider
        process.crawl(
            IndeedSpider,
            target_locations=countries 
        )
        
        process.start(stop_after_crawl=True) 

    except Exception as e:
        logger.error(f"❌ Error fatal al ejecutar el proceso Scrapy: {e}")


def save_and_summarize(all_records: List[Dict[str, Any]]):
    """Guarda el resultado final en CSV y muestra un resumen."""
    
    if not all_records:
        logger.warning("No se recolectaron registros finales para guardar.")
        return

    # Convertir a DataFrame y manejar duplicados
    df = pd.DataFrame(all_records)
    df.drop_duplicates(subset=['job_id'], keep='first', inplace=True)

    # Guardar en CSV
    df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')
    logger.info(f"💾 ÉXITO: Datos enriquecidos guardados en {OUTPUT_CSV_FILE}.")

    # Resumen de resultados
    logger.info(f"✨ Total de registros procesados y únicos recolectados: {len(df)}")
    logger.info("✅ Ciclo de scraping finalizado. Datos disponibles en CSV y Supabase.")


# =================================================================
# 🏁 PUNTO DE ENTRADA
# =================================================================

if __name__ == '__main__':
    start_time = time.time()
    
    # Limpiar registros anteriores del colector
    LinkedInItemCollectorPipeline.all_records = []
    
    # 1. Ejecutar el ciclo de scraping y ETL
    run_full_cycle(countries=TARGET_COUNTRIES)
    
    # 2. Recolectar y guardar los registros finales
    final_records = LinkedInItemCollectorPipeline.all_records
    save_and_summarize(final_records)

    # 3. Mostrar resumen de tiempo
    elapsed_time = time.time() - start_time
    print("\n" + "="*50)
    print("🏁 RESUMEN DE EJECUCIÓN 🏁")
    print(f"Tiempo total transcurrido: {elapsed_time:.2f} segundos")
    print("="*50)