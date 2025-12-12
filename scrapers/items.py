# FILE: Proyecto/job-market-intelligence/scrapers/items.py
import scrapy
from datetime import datetime

class JobItem(scrapy.Item):
    """Main job item structure for all scraped jobs."""
    job_id = scrapy.Field()             # Identificador único de la fuente (usado para upsert)
    title = scrapy.Field()
    company_name = scrapy.Field()       # Nombre de la empresa (consistente)
    location = scrapy.Field()
    country = scrapy.Field()            # País extraído/clasificado
    job_type = scrapy.Field()           # Tipo de contrato: Full-time, Part-time, Contract, Remote, Onsite, Hybrid
    seniority_level = scrapy.Field()    # Nivel: Junior, Mid, Senior, Lead (normalizado)
    sector = scrapy.Field()             # Sector clasificado: EdTech, Fintech, Future of Work, Other
    role_category = scrapy.Field()      # Categoría de rol más fina (ej. Data Science & ML, Software Development)
    description = scrapy.Field()
    requirements = scrapy.Field()       # Requisitos del puesto
    salary_range = scrapy.Field()       # Rango salarial
    posted_date = scrapy.Field()        # Fecha de publicación
    source_url = scrapy.Field()         # URL original de la vacante
    source_platform = scrapy.Field()    # Plataforma de origen: LinkedIn, Computrabajo, Indeed, etc.
    scraped_at = scrapy.Field()         # Timestamp de cuando fue scrapeada
    is_active = scrapy.Field()          # Si la vacante está activa (por defecto True)
    skills = scrapy.Field()             # Lista de habilidades técnicas extraídas

    # Campos de enriquecimiento de compañía (desde CompanyEnricher)
    company_size = scrapy.Field()       # Tamaño (ej. Startup (1-50), Grande (201-1000))
    company_industry = scrapy.Field()   # Industria (ej. Fintech, EdTech, Retail)
    company_hq_country = scrapy.Field() # País de sede (Detectado por heurística)
    company_type = scrapy.Field()       # Tipo (ej. Consultoría, Producto/Tecnología)
    company_website = scrapy.Field()    # Sitio web (si se pudiera obtener)