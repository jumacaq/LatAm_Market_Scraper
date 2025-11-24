# FILE: job-market-intelligence - copia - copia - copia/job-market-intelligence/main.py
import logging
import sys
import os
import argparse
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapers.spiders.linkedin_spider import LinkedInSpider
from config.geo import COMMON_GEO_DATA, LINKEDIN_TPR_MAP

# Cargar variables de entorno explícitamente
load_dotenv()
# Cambiar el nivel de logging a DEBUG para ver los logs detallados del spider y pipeline
logging.basicConfig(level=logging.DEBUG) 

def get_user_input():
    """Obtiene el continente, país y rango de fechas del usuario de forma interactiva."""
    
    print("\n--- Configuración de Búsqueda del Scraper ---")
    
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
        selected_countries = [selected_continent] # Pasar el continente si se seleccionan "Todos los países"
        logging.info(f"Buscando en todos los países de {selected_continent}.")
    else:
        selected_countries = [countries[country_choice - 1]]
        logging.info(f"Buscando en {selected_countries[0]}.")

    # Rango de fechas
    start_date = None
    end_date = None
    
    print("\nIntroduce el rango de fechas para las vacantes (formato YYYY-MM-DD).")
    print("Para no aplicar filtro de fecha, deja en blanco.")
    
    while True:
        start_date_str = input("Fecha de inicio (ej. 2023-01-01, o dejar en blanco): ").strip()
        if not start_date_str:
            break
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            break
        except ValueError:
            print("Formato de fecha inválido. Intenta YYYY-MM-DD.")

    while True:
        end_date_str = input("Fecha de fin (ej. 2023-12-31, o dejar en blanco): ").strip()
        if not end_date_str:
            if start_date:
                end_date = date.today()
            break
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date and end_date < start_date:
                print("La fecha de fin no puede ser anterior a la fecha de inicio.")
                continue
            break
        except ValueError:
            print("Formato de fecha inválido. Intenta YYYY-MM-DD.")
            
    return selected_countries, start_date, end_date, selected_continent # Retorna las fechas exactas y el continente seleccionado

def derive_f_tpr_value(start_date_cli, end_date_cli):
    """Deriva el f_TPR de LinkedIn a partir de las fechas de inicio y fin."""
    if start_date_cli and end_date_cli:
        delta = end_date_cli - start_date_cli
        if delta <= timedelta(days=1):
            return LINKEDIN_TPR_MAP["past 24 hours"]
        elif delta <= timedelta(days=7):
            return LINKEDIN_TPR_MAP["past week"]
        elif delta <= timedelta(days=30):
            return LINKEDIN_TPR_MAP["past month"]
        else: # For longer ranges, default to past month for guest API limitations
            logging.warning("⚠️ Rango de fechas amplio, utilizando filtro de LinkedIn 'último mes' para la búsqueda inicial. El filtrado exacto se hará en el dashboard.")
            return LINKEDIN_TPR_MAP["past month"]
    elif start_date_cli: # Only start date given, assume up to today
        delta = date.today() - start_date_cli
        if delta <= timedelta(days=1):
            return LINKEDIN_TPR_MAP["past 24 hours"]
        elif delta <= timedelta(days=7):
            return LINKEDIN_TPR_MAP["past week"]
        elif delta <= timedelta(days=30):
            return LINKEDIN_TPR_MAP["past month"]
        else:
            logging.warning("⚠️ Solo fecha de inicio dada, utilizando filtro de LinkedIn 'último mes' para la búsqueda inicial. El filtrado exacto se hará en el dashboard.")
            return LINKEDIN_TPR_MAP["past month"]
    else:
        logging.info("Sin filtro de fecha aplicado en el scraper.")
        return LINKEDIN_TPR_MAP["any time"]


def run_scrapers(target_locations_for_spider=None, start_date_filter=None, end_date_filter=None, continent_for_spider=None):
    # Verificar credenciales antes de arrancar
    supabase_url = os.getenv("SUPABASE_URL", "")
    if not supabase_url or "TU_PROYECTO" in supabase_url:
        logging.warning("⚠️  ADVERTENCIA: SUPABASE_URL no configurada en .env. Los datos NO se guardarán.")
    
    logging.info("🚀 Starting LinkedIn Scraper...")
    
    os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'scrapers.settings')
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    
    final_target_locations = []
    if target_locations_for_spider:
        final_target_locations = [loc for loc in target_locations_for_spider if loc is not None and loc.strip() != "" and loc != "Selecciona un Continente" and loc != "Todos los Países"]
    
    if not final_target_locations:
        final_target_locations = COMMON_GEO_DATA["Latam"] # Default a Latam si no hay ubicaciones válidas
        logging.info(f"No se especificaron ubicaciones válidas o eran inválidas, usando ubicaciones predeterminadas: {', '.join(final_target_locations)}")
    
    f_tpr_value = derive_f_tpr_value(start_date_filter, end_date_filter)

    logging.info(f"Scraping para ubicaciones: {', '.join(final_target_locations)}")
    logging.info(f"Filtro de fecha de LinkedIn (f_TPR): {f_tpr_value}")
    logging.info(f"Filtrando por fecha de publicación desde {start_date_filter} hasta {end_date_filter} (filtrado exacto en dashboard).")
    
    # Pasamos el continente seleccionado como parte del meta para que el spider pueda referenciarlo
    spider_kwargs = {
        'target_locations': final_target_locations, 
        'f_tpr_value': f_tpr_value,
        'start_date_filter': start_date_filter,
        'end_date_filter': end_date_filter
    }
    
    # Si se seleccionó un continente en el dashboard y luego "Todos los Países"
    if continent_for_spider and final_target_locations == [continent_for_spider]:
        spider_kwargs['continent_search'] = continent_for_spider
        # En este caso, target_locations_for_spider ya es el nombre del continente (ej. "Latam")
        # El spider usará esto para iterar sobre todos los países de ese continente en COMMON_GEO_DATA
        spider_kwargs['target_locations'] = COMMON_GEO_DATA.get(continent_for_spider, [])
        if not spider_kwargs['target_locations']:
            logging.error(f"Error: Continente '{continent_for_spider}' no encontrado en COMMON_GEO_DATA para expandir a países.")
            # Fallback a Latam si hay un problema
            spider_kwargs['target_locations'] = COMMON_GEO_DATA["Latam"]
            logging.info("Fallando a países predeterminados de Latam.")


    process.crawl(LinkedInSpider, **spider_kwargs)
    process.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecuta el scraper de LinkedIn con parámetros opcionales.")
    parser.add_argument("--continent", type=str, help="Continente a buscar (ej. Latam)")
    parser.add_argument("--country", type=str, help="País específico a buscar (ej. Mexico)")
    parser.add_argument("--start_date", type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(), help="Fecha de inicio para filtrar vacantes (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(), help="Fecha de fin para filtrar vacantes (YYYY-MM-DD)")
    
    args = parser.parse_args()

    if any(getattr(args, arg) for arg in ['continent', 'country', 'start_date', 'end_date']):
        # Modo no interactivo (ejecutado desde el dashboard o CLI con args)
        selected_locations_for_spider = []
        continent_passed = args.continent
        
        if args.country and args.country != "Todos los Países": 
            selected_locations_for_spider = [args.country]
            logging.info(f"CLI: País único seleccionado para scraping: '{args.country}'.")
        elif args.continent and args.continent != "Selecciona un Continente": 
            # Si se seleccionó un continente y luego "Todos los Países", pasamos el continente.
            # El spider será responsable de expandir este a países si es necesario.
            if args.country == "Todos los Países": # Este es el caso del dashboard cuando se selecciona "Todos los Países"
                selected_locations_for_spider = [args.continent]
                logging.info(f"CLI: Continente '{args.continent}' seleccionado para scrapear todos sus países.")
            else: # Se seleccionó un continente, pero no "Todos los Países" ni un país específico. Esto no debería pasar con el dashboard actual.
                selected_locations_for_spider = COMMON_GEO_DATA.get(args.continent, [])
                if not selected_locations_for_spider:
                    logging.error(f"CLI: Continente '{args.continent}' no encontrado en COMMON_GEO_DATA. Usando países predeterminados de Latam.")
                    selected_locations_for_spider = COMMON_GEO_DATA["Latam"]
                else:
                    logging.info(f"CLI: Continente seleccionado para scraping: '{args.continent}'. Países a scrapear: {', '.join(selected_locations_for_spider)}")
        else:
            selected_locations_for_spider = COMMON_GEO_DATA["Latam"]
            logging.info("CLI: No se especificó continente ni país válido, usando países predeterminados de Latam.")

        run_scrapers(selected_locations_for_spider, args.start_date, args.end_date, continent_passed)
    else:
        # Modo interactivo (ejecutado directamente sin argumentos)
        selected_countries, start_date, end_date, selected_continent = get_user_input()
        run_scrapers(selected_countries, start_date, end_date, selected_continent)