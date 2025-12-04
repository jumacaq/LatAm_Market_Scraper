# FILE: job-market-intelligence/etl/sector_classifier.py
import re
import yaml
import os

class SectorClassifier:
    def __init__(self):
        self.sector_keywords = {}
        self.load_sector_keywords()

    def load_sector_keywords(self):
        """Carga las palabras clave para la clasificación de sectores desde el archivo de configuración."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # Aseguramos que 'sectors' exista y tenga la estructura esperada
                self.sector_keywords = {
                    sector_name: details.get('keywords', [])
                    for sector_name, details in config.get('sectors', {}).items()
                }
        except FileNotFoundError:
            print(f"Error: Archivo de configuración no encontrado en {config_path}. La clasificación de sectores no funcionará.")
        except yaml.YAMLError as e:
            print(f"Error cargando config.yaml para sectores: {e}.")

    def classify_sector(self, item):
        """Clasifica una vacante en un sector basándose en el título, descripción y nombre de la empresa."""
        text = (
            str(item.get('title') or '') + ' ' + 
            str(item.get('description') or '') + ' ' + 
            str(item.get('company_name') or '')
        ).lower()
        
        for sector, keywords in self.sector_keywords.items():
            if any(keyword.lower() in text for keyword in keywords):
                return sector
        
        return 'Other' # Por defecto si no coincide con ningún sector conocido
