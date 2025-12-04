# FILE: job-market-intelligence/etl/normalizers.py
import re
import yaml
import os

class DataNormalizer:
    def __init__(self):
        self.countries_map = {}
        self.load_country_keywords()

    def load_country_keywords(self):
        """Carga los keywords de países desde el archivo de configuración."""
        # Se asume que config.yaml se encuentra en el nivel superior de 'config'
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # La estructura 'countries' ya no está en config.yaml, la obtenemos de COMMON_GEO_DATA en geo.py
                # Para evitar circular imports, definimos una lista estática de LatAm aquí o la pasamos por init
                # Por ahora, usamos una lista interna para el normalizer.
                self.countries_map = {
                    'Mexico': ['mexico', 'cdmx', 'ciudad de mexico', 'guadalajara', 'monterrey'],
                    'Colombia': ['colombia', 'bogota', 'medellin', 'cali'],
                    'Argentina': ['argentina', 'buenos aires', 'cordoba', 'rosario'],
                    'Chile': ['chile', 'santiago', 'valparaiso'],
                    'Peru': ['peru', 'lima', 'arequipa'],
                    'Brazil': ['brazil', 'brasil', 'sao paulo', 'rio de janeiro']
                }
        except FileNotFoundError:
            print(f"Advertencia: No se encontró config.yaml en {config_path}. Se usarán keywords de país predeterminadas.")
        except yaml.YAMLError as e:
            print(f"Error cargando config.yaml: {e}. Se usarán keywords de país predeterminadas.")

    def extract_country_from_location(self, location):
        """Extrae el país de una cadena de ubicación usando palabras clave."""
        if not location:
            return None
        
        location_lower = location.lower()
        for country, keywords in self.countries_map.items():
            if any(keyword in location_lower for keyword in keywords):
                return country
        
        return None

    def normalize_seniority(self, seniority_text, title=""):
        """Normaliza el nivel de antigüedad basándose en texto o título."""
        if not seniority_text and not title:
            return 'Other' # O un valor por defecto más adecuado

        text_to_analyze = (seniority_text or "" + " " + title or "").lower()

        if 'junior' in text_to_analyze or 'jr' in text_to_analyze or 'practicante' in text_to_analyze or 'intern' in text_to_analyze:
            return 'Junior'
        elif 'mid' in text_to_analyze or 'semi senior' in text_to_analyze or 'ssr' in text_to_analyze:
            return 'Mid'
        elif 'senior' in text_to_analyze or 'sr' in text_to_analyze:
            return 'Senior'
        elif 'lead' in text_to_analyze or 'principal' in text_to_analyze or 'jefe' in text_to_analyze:
            return 'Lead'
        elif 'staff' in text_to_analyze: # LinkedIn a veces usa 'staff' para seniority
            return 'Senior' # O un nivel intermedio entre Senior y Lead
        
        return 'Other' # Si no se puede clasificar, se devuelve 'Other'


    def normalize_job_type(self, job_type_text, description=""):
        """Normaliza el tipo de trabajo (ej. Full-time, Remote, Hybrid)"""
        text_to_analyze = (job_type_text or "" + " " + description or "").lower()

        if 'full-time' in text_to_analyze or 'tiempo completo' in text_to_analyze:
            return 'Full-time'
        elif 'part-time' in text_to_analyze or 'medio tiempo' in text_to_analyze:
            return 'Part-time'
        elif 'contract' in text_to_analyze or 'contrato' in text_to_analyze:
            return 'Contract'
        elif 'remote' in text_to_analyze or 'remoto' in text_to_analyze:
            return 'Remote'
        elif 'hybrid' in text_to_analyze or 'híbrido' in text_to_analyze:
            return 'Hybrid'
        elif 'internship' in text_to_analyze or 'pasantía' in text_to_analyze:
            return 'Internship'

        return 'Other'
