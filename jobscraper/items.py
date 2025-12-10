# C:\Users\Admin\job-market-intelligence\scrapers\items.py

import scrapy
from datetime import datetime
from scrapy.item import Field # Es buena práctica importarlo si se usa

class JobItem(scrapy.Item):
    """
    Estructura principal compatible con los Spiders (LinkedIn, Computrabajo) 
    y la cadena de Pipelines (Limpieza, Enriquecimiento, Supabase).
    """
    
    # 📌 CAMPOS BASE DEL SPIDER
    job_id = scrapy.Field()             # Identificador único de la fuente (usado para deduplicación)
    title = scrapy.Field()              # Título del trabajo
    
    # ¡IMPORTANTE! Cambiado de 'company' a 'company_name' para el Pipeline
    company_name = scrapy.Field()       # Nombre de la empresa
    
    location = scrapy.Field()           # Ubicación cruda de la fuente
    
    # ¡IMPORTANTE! Cambiado de 'url' a 'source_url' para el Pipeline
    source_url = scrapy.Field()         # URL de la oferta
    
    # ¡IMPORTANTE! Cambiado de 'source' a 'source_platform' para el Pipeline
    source_platform = scrapy.Field()    # Plataforma (LinkedIn, Computrabajo)
    
    posted_date = scrapy.Field()        # Fecha de publicación
    description = scrapy.Field()        # Descripción limpia
    
    # 📌 CAMPOS REQUERIDOS/REFINADOS POR EL PIPELINE DE ETL
    
    country = scrapy.Field()            # País normalizado (Inferido por CleaningPipeline de la ubicación)
    salary_range = scrapy.Field()       # Rango salarial (cambiado de 'salary')
    seniority_level = scrapy.Field()    # Nivel (cambiado de 'seniority')
    sector = scrapy.Field()             # Sector clasificado (Rellenado por SectorClassificationPipeline)
    
    requirements = scrapy.Field()       # Requisitos (puede ser parte de la descripción si no se extrae aparte)
    job_type = scrapy.Field()           # Tipo de empleo (Full-time, Part-time, Contract)
    
    # CAMPOS DE AUDITORÍA Y ENRIQUECIMIENTO
    scraped_at = scrapy.Field()         # Timestamp de scrapeo (Añadido por CleaningPipeline)
    skills = scrapy.Field()             # Lista de habilidades extraídas (Rellenado por SkillExtractionPipeline)

    # 📌 CAMPOS DE ENRIQUECIMIENTO DE EMPRESA
    company_industry = scrapy.Field()   # Industria (ej. Fintech, EdTech, Retail)
    company_size = scrapy.Field()       # Tamaño (ej. Startup (1-50), Grande (201-1000))
    company_contact = scrapy.Field()    # Contacto/URL principal
    company_hq_country = scrapy.Field() # País de sede (Detectado por heurística)
    company_type = scrapy.Field()       # Tipo (ej. Consultoría, Producto/Tecnología)
