# FILE: job-market-intelligence - copia - copia - copia/job-market-intelligence/scrapers/pipelines.py
from database.supabase_client import SupabaseClient
import logging
from etl.cleaners import TextCleaner # Importar TextCleaner

class SupabasePipeline:
    def __init__(self):
        try:
            self.client = SupabaseClient()
            self.cleaner = TextCleaner() # Instanciar TextCleaner
            logging.info("✅ Pipeline conectado a Supabase.")
        except Exception as e:
            logging.error(f"❌ Error de conexión a Supabase: {e}")
            self.client = None
            self.cleaner = None # Asegurarse de que cleaner también sea None si la conexión falla

    def process_item(self, item, spider):
        if self.client and self.cleaner: # Asegurarse de que tanto el cliente como el limpiador estén inicializados
            try:
                # Convert item to dict
                data = dict(item)
                
                # --- APLICAR LIMPIEZA ETL ---
                if 'title' in data and data['title']:
                    data['title'] = self.cleaner.clean_title(data['title'])
                
                # --- DEBUGGING DE EMPRESA DESCONOCIDA ---
                initial_company = data.get('company', '').strip()
                logging.debug(f"Pipeline: Empresa inicial (del spider): '{initial_company}' para vacante '{data.get('title')}'") 
                
                if 'company' in data and data['company']:
                    # Aplicar limpieza HTML y strip para la compañía
                    cleaned_company = self.cleaner.remove_html(data['company']).strip()
                    # Si después de limpiar sigue vacío, asigna un valor por defecto
                    if not cleaned_company:
                        cleaned_company = "Empresa Desconocida"
                    data['company'] = cleaned_company
                else:
                    # Si el campo 'company' no existe en el item o está vacío desde el spider, lo inicializa
                    data['company'] = "Empresa Desconocida"
                
                logging.debug(f"Pipeline: Empresa después de limpieza: '{data['company']}'") # DEBUG
                # --- FIN DEBUGGING ---

                if 'description' in data and data['description']:
                    data['description'] = self.cleaner.remove_html(data['description'])
                # --- FIN APLICACIÓN ETL ---

                # Remove fields with None values (esto debe hacerse DESPUÉS de la limpieza)
                data = {k: v for k, v in data.items() if v is not None}
                
                # Insert into DB
                self.client.upsert_job(data)
                logging.info(f"✅ Guardado en DB: {data.get('title')} ({data.get('company', 'N/A')})")
            except Exception as e:
                error_msg = str(e)
                logging.error(f"❌ Error guardando en DB: {error_msg}. Item: {item.get('title')}")
        else:
            logging.warning(f"⚠️ Item escrapeado pero NO guardado (Sin conexión a DB): {item.get('title')}")
            
        return item