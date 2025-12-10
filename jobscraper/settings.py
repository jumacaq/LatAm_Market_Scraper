# jobscraper/settings.py (VERSION COMPLETA PARA ETL Y SUPABASE)

# Nombre del proyecto
BOT_NAME = "job_market_intelligence"

# Ubicación de los módulos
SPIDER_MODULES = ["jobscrapers.spiders"]
NEWSPIDER_MODULE = "jobscrapers.spiders"

# ====================================================================
# 1. CONFIGURACIÓN DE PIPELINES (ETL COMPLETO)
# * IMPORTANTE: Asegúrate de que 'scrapers.pipelines_full' sea la ruta correcta.
# * El orden (100, 200, 300, 500) es crucial para el flujo ETL/Supabase.
# ====================================================================

ITEM_PIPELINES = {
    'jobscrapers.pipelines_full.CleaningPipeline': 100,
    'jobscrapers.pipelines_full.SkillExtractionPipeline': 200,
    'jobscrapers.pipelines_full.SectorClassificationPipeline': 300,
    'jobscrapers.pipelines_full.SupabasePipeline': 500,
    
    # 🚨 NOTA: El LinkedInItemCollectorPipeline (para CSV) NO se incluye aquí,
    # se añade en main.py (Prioridad 400) para asegurar que el proceso de Supabase lo reciba primero,
    # y para que solo se ejecute cuando llamas a main.py.
}

# ====================================================================
# 2. CONFIGURACIÓN BÁSICA DE SCRAPY
# ====================================================================

# Deshabilita ROBOTSTXT por si la plataforma lo bloquea, aunque siempre es mejor obedecerlo.
ROBOTSTXT_OBEY = False 

# Nivel de logging (recomendado para desarrollo)
LOG_LEVEL = 'INFO'

# Descomentar para aplicar a TODOS los spiders (si no lo pones en el spider individual)
# DOWNLOAD_DELAY = 15
# CONCURRENT_REQUESTS = 1