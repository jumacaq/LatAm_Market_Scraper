# FILE: job-market-intelligence/scrapers/items.py
import scrapy
from datetime import datetime

class JobItem(scrapy.Item):
    """Main job item structure for all scraped jobs."""
    job_id = scrapy.Field()  # Identificador único de la fuente (usado para upsert)
    title = scrapy.Field()
    company_name = scrapy.Field() # Renombrado de 'company' a 'company_name' para consistencia
    location = scrapy.Field()
    country = scrapy.Field() # País extraído/clasificado
    job_type = scrapy.Field()  # Tipo de contrato: Full-time, Part-time, Contract, Remote, Onsite, Hybrid
    seniority_level = scrapy.Field()  # Nivel: Junior, Mid, Senior, Lead
    sector = scrapy.Field()  # Sector clasificado: EdTech, Fintech, Future of Work, Other
    description = scrapy.Field()
    requirements = scrapy.Field() # Requisitos del puesto
    salary_range = scrapy.Field() # Rango salarial
    posted_date = scrapy.Field()  # Fecha de publicación
    source_url = scrapy.Field()   # URL original de la vacante
    source_platform = scrapy.Field() # Plataforma de origen: LinkedIn, GetonBoard, Computrabajo, Torre
    scraped_at = scrapy.Field()   # Timestamp de cuando fue scrapeada
    is_active = scrapy.Field()    # Si la vacante está activa (por defecto True)
    skills = scrapy.Field()       # Lista de habilidades técnicas extraídas
    # Campos adicionales de 'Job_Market_Intelligence' que podrían ser útiles o se mapean:
    # 'raw_data': scrapy.Field() # Podría usarse si queremos guardar el JSON completo de una API como Torre