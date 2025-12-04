# FILE: job-market-intelligence/main.py
import logging
import sys
import os
import argparse
import yaml
import datetime
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Importamos los spiders
from scrapers.spiders.linkedin_spider import LinkedInSpider
from scrapers.spiders.getonboard_spider import GetonBoardSpider
from scrapers.spiders.computrabajo_spider import ComputrabajoSpider
from scrapers.spiders.torre_spider import TorreSpider

from config.geo import COMMON_GEO_DATA, LINKEDIN_TPR_MAP, COMPUTRABAJO_FTP_MAP

# Cargar variables de entorno explícitamente
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Carga la configuración desde config.yaml."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Error: Archivo de configuración no encontrado en {config_path}.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error cargando config.yaml: {e}.")
        sys.exit(1)

def get_search_keywords(config):
    """Obtiene las palabras clave de búsqueda (roles + keywords de sectores) de la configuración."""
    keywords = config.get('roles', [])
    for sector_info in config.get('sectors', {}).values():
        keywords.extend(sector_info.get('keywords', []))
    return list(set(keywords)) # Eliminar duplicados

def get_spider_selection():
    """Pregunta al usuario qué spiders desea ejecutar."""
    available_spider_names = ["linkedin", "getonboard", "computrabajo", "torre"]
    
    print("\n--- Selección de Scrapers ---")
    print("Selecciona los scrapers que deseas ejecutar (separados por comas):")
    for i, name in enumerate(available_spider_names):
        print(f"{i+1}. {name.capitalize()}")
    print("Ej. 1,3 para LinkedIn y Computrabajo")
    print("Ej. 1,2,3,4 para todos")

    while True:
        choice_input = input("Ingresa los números de los scrapers: ").strip()
        selected_indices = []
        try:
            selected_indices = [int(idx.strip()) for idx in choice_input.split(',')]
            
            selected_spider_names = []
            for idx in selected_indices:
                if 1 <= idx <= len(available_spider_names):
                    selected_spider_names.append(available_spider_names[idx - 1])
                else:
                    print(f"Número '{idx}' inválido. Por favor, selecciona números entre 1 y {len(available_spider_names)}.")
                    selected_spider_names = [] # Reset selection if any invalid
                    break
            
            if selected_spider_names:
                print(f"Scrapers seleccionados: {', '.join(selected_spider_names).capitalize()}")
                return selected_spider_names
        except ValueError:
            print("Entrada inválida. Por favor, ingresa números separados por comas.")

def get_interactive_input(config):
    """Obtiene el continente, país, rango de fechas y límite de vacantes del usuario de forma interactiva."""
    
    print("\n--- Configuración de Búsqueda de Ubicación y Fecha ---")
    
    # Continente
    continents = list(COMMON_GEO_DATA.keys())
    print("\nSelecciona un continente:")
    for i, cont in enumerate(continents):
        print(f"{i+1}. {cont}")
    
    continent_choice = None
    while continent_choice not in range(1, len(continents) + 1):
        try:
            choice = input(f"Ingresa el número del continente (1-{len(continents)}): ")
            continent_choice = int(choice)
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")
    
    selected_continent = continents[continent_choice - 1]
    
    # País
    countries = COMMON_GEO_DATA[selected_continent]
    print(f"\nSelecciona un país para {selected_continent}:")
    for i, country in enumerate(countries):
        print(f"{i+1}. {country}")
    print(f"{len(countries)+1}. Todos los países en {selected_continent}")
    
    country_choice = None
    while country_choice not in range(1, len(countries) + 2):
        try:
            choice = input(f"Ingresa el número del país (1-{len(countries)+1}): ")
            country_choice = int(choice)
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")
            
    if country_choice == len(countries) + 1:
        selected_countries_list = COMMON_GEO_DATA[selected_continent]
        logging.info(f"Buscando en todos los países de {selected_continent}: {', '.join(selected_countries_list)}.")
    else:
        selected_countries_list = [countries[country_choice - 1]]
        logging.info(f"Buscando en {selected_countries_list[0]}.")

    # Rango de fechas
    start_date_filter = None
    end_date_filter = None
    
    print("\nIntroduce el rango de fechas para las vacantes (formato YYYY-MM-DD).")
    print("Para no aplicar filtro de fecha, deja en blanco.")
    
    while True:
        start_date_str = input("Fecha de inicio (ej. 2023-01-01, o dejar en blanco): ").strip()
        if not start_date_str:
            break
        try:
            start_date_filter = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            break
        except ValueError:
            print("Formato de fecha inválido. Intenta YYYY-MM-DD.")

    while True:
        end_date_str = input("Fecha de fin (ej. 2023-12-31, o dejar en blanco): ").strip()
        if not end_date_str:
            if start_date_filter:
                end_date_filter = datetime.date.today()
            break
        try:
            end_date_filter = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date_filter and end_date_filter < start_date_filter:
                print("La fecha de fin no puede ser anterior a la fecha de inicio.")
                continue
            break
        except ValueError:
            print("Formato de fecha inválido. Intenta YYYY-MM-DD.")

    # Límite de vacantes
    max_jobs = 100 # Valor por defecto
    while True:
        max_jobs_str = input("Número máximo de vacantes a raspar por cada scraper (dejar en blanco para 100, o un número): ").strip()
        if not max_jobs_str:
            break
        try:
            max_jobs = int(max_jobs_str)
            if max_jobs <= 0:
                print("El número de vacantes debe ser positivo.")
                continue
            break
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número entero.")
            
    return selected_countries_list, start_date_filter, end_date_filter, max_jobs

def derive_linkedin_tpr(start_date_filter, end_date_filter):
    """Deriva el f_TPR de LinkedIn a partir de las fechas de inicio y fin."""
    if not start_date_filter or not end_date_filter:
        return LINKEDIN_TPR_MAP["any time"]
    
    delta = end_date_filter - start_date_filter
    if delta <= datetime.timedelta(days=1):
        return LINKEDIN_TPR_MAP["past 24 hours"]
    elif delta <= datetime.timedelta(days=7):
        return LINKEDIN_TPR_MAP["past week"]
    elif delta <= datetime.timedelta(days=30):
        return LINKEDIN_TPR_MAP["past month"]
    else:
        logging.warning("⚠️ Rango de fechas amplio para LinkedIn, utilizando filtro 'último mes' en la búsqueda inicial. El filtrado exacto se hará en el dashboard.")
        return LINKEDIN_TPR_MAP["past month"]

# MODIFICACIÓN: Lógica de f_tp de Computrabajo mejorada
def derive_computrabajo_ftp(start_date_filter, end_date_filter):
    """Deriva el f_tp de Computrabajo a partir de las fechas de inicio y fin, de forma más precisa."""
    if not start_date_filter or not end_date_filter:
        return COMPUTRABAJO_FTP_MAP["any time"]
    
    delta = end_date_filter - start_date_filter
    # Convertir a días para la comparación
    days_delta = delta.days

    if days_delta <= 1:
        return COMPUTRABAJO_FTP_MAP["past 24 hours"]
    elif days_delta <= 7:
        return COMPUTRABAJO_FTP_MAP["past week"]
    elif days_delta <= 30:
        return COMPUTRABAJO_FTP_MAP["past month"]
    else:
        # Si es más de un mes, Computrabajo no tiene un filtro directo para "más antiguo que 30 días" en su URL.
        # En este caso, lo mejor es no pasar un filtro f_tp y dejar que el filtrado se haga post-scrape.
        logging.warning("⚠️ Rango de fechas amplio para Computrabajo, se ignorará el filtro de fecha f_tp en la URL. El filtrado exacto se hará post-scrape.")
        return COMPUTRABAJO_FTP_MAP["any time"]


def run_scrapers(selected_spider_names, search_keywords, target_locations, start_date_filter, end_date_filter, max_jobs_to_scrape):
    # Verificar credenciales antes de arrancar
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or "TU_PROYECTO" in supabase_url or not supabase_service_key:
        logging.warning("⚠️ ADVERTENCIA: Credenciales de Supabase (URL o SERVICE_KEY) no configuradas en .env. Los datos NO se guardarán.")
    
    logging.info("🚀 Starting Job Market Intelligence Scrapers...")
    
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'scrapers.settings')
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    spider_kwargs = {
        'keywords': search_keywords,
        'target_locations': target_locations,
        'start_date_filter': start_date_filter,
        'end_date_filter': end_date_filter,
        'max_jobs_to_scrape': max_jobs_to_scrape
    }

    if "linkedin" in selected_spider_names:
        linkedin_tpr = derive_linkedin_tpr(start_date_filter, end_date_filter)
        process.crawl(LinkedInSpider, **spider_kwargs, f_tpr_value=linkedin_tpr)
    
    if "getonboard" in selected_spider_names:
        process.crawl(GetonBoardSpider, **spider_kwargs)
    
    if "computrabajo" in selected_spider_names:
        computrabajo_ftp = derive_computrabajo_ftp(start_date_filter, end_date_filter)
        process.crawl(ComputrabajoSpider, **spider_kwargs, f_tp_value=computrabajo_ftp)

    if "torre" in selected_spider_names:
        process.crawl(TorreSpider, **spider_kwargs)

    if not selected_spider_names:
        logging.warning("No se seleccionó ningún scraper para ejecutar.")
        return

    process.start()

if __name__ == "__main__":
    config = load_config()
    search_keywords = get_search_keywords(config)

    parser = argparse.ArgumentParser(description="Ejecuta el scraper de vacantes con parámetros opcionales.")
    parser.add_argument("--start_date", type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(), help="Fecha de inicio para filtrar vacantes (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(), help="Fecha de fin para filtrar vacantes (YYYY-MM-DD)")
    parser.add_argument("--continent", type=str, help="Continente a buscar (ej. Latam)")
    parser.add_argument("--country", type=str, help="País específico a buscar (ej. Mexico). Usa 'Todos los Países' para todos en el continente.")
    parser.add_argument("--spiders", type=str, help="Spiders a ejecutar, separados por comas (ej. linkedin,computrabajo)")
    parser.add_argument("--max_jobs", type=int, default=None, help="Número máximo de vacantes a raspar por cada scraper (por defecto: modo interactivo).")
    
    args = parser.parse_args()

    if len(sys.argv) > 1:
        # Modo CLI (se pasaron argumentos)
        target_locations_for_spider = []
        
        if args.country and args.country != "Todos los Países": 
            target_locations_for_spider = [args.country]
            logging.info(f"CLI: País único seleccionado para scraping: '{args.country}'.")
        elif args.continent and args.continent != "Selecciona un Continente" and args.continent in COMMON_GEO_DATA:
            if args.country == "Todos los Países":
                target_locations_for_spider = COMMON_GEO_DATA[args.continent]
                logging.info(f"CLI: Continente '{args.continent}' seleccionado para scrapear todos sus países: {', '.join(target_locations_for_spider)}")
            else: 
                target_locations_for_spider = COMMON_GEO_DATA[args.continent]
                logging.info(f"CLI: Continente '{args.continent}' seleccionado; asumiendo todos sus países: {', '.join(target_locations_for_spider)}")
        else:
            target_locations_for_spider = COMMON_GEO_DATA["Latam"]
            logging.info("CLI: No se especificó continente/país válido, o se especificó un continente inválido. Usando países predeterminados de Latam.")

        selected_spiders_cli = []
        if args.spiders:
            selected_spiders_cli = [s.strip().lower() for s in args.spiders.split(',')]
            valid_spider_names = ["linkedin", "getonboard", "computrabajo", "torre"]
            selected_spiders_cli = [s for s in selected_spiders_cli if s in valid_spider_names]
            if not selected_spiders_cli:
                logging.warning("No se encontraron spiders válidos en el argumento --spiders. No se ejecutará ningún scraper.")
        else:
            logging.info("No se especificaron spiders vía CLI. Ejecutando todos los spiders por defecto.")
            selected_spiders_cli = ["linkedin", "getonboard", "computrabajo", "torre"]

        max_jobs_cli = args.max_jobs if args.max_jobs is not None else 100 
        if max_jobs_cli <= 0:
            logging.warning(f"Límite de vacantes CLI ({max_jobs_cli}) inválido o 0. Usando 100 por defecto.")
            max_jobs_cli = 100

        run_scrapers(selected_spiders_cli, search_keywords, target_locations_for_spider, args.start_date, args.end_date, max_jobs_cli)
    else:
        selected_spider_names = get_spider_selection()
        selected_countries_list, start_date_filter, end_date_filter, max_jobs_to_scrape = get_interactive_input(config)
        run_scrapers(selected_spider_names, search_keywords, selected_countries_list, start_date_filter, end_date_filter, max_jobs_to_scrape)
