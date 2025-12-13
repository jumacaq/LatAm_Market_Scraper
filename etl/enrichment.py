# FILE: Proyecto/job-market-intelligence/etl/enrichment.py
import logging
from typing import Dict, Optional
import os
import yaml
from config.geo import COMMON_GEO_DATA # Importar datos geográficos

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CompanyEnricher:
    """
    Componente modular para inferir el tamaño, industria y tipo de empresa
    usando heurística basada en el nombre.
    """
    def __init__(self):
        self.cache = {}
        # Cargamos explícitamente los países para la detección.
        # Podríamos cargar esto de config/geo.py
        self.country_keywords_map = self._build_country_keywords_map()
        
    def _build_country_keywords_map(self):
        """Construye un mapa de palabras clave para la detección de países."""
        country_map = {}
        for continent, countries in COMMON_GEO_DATA.items():
            for country in countries:
                # Normalizar el nombre del país para las keywords
                country_lower = country.lower()
                keywords = [country_lower]
                
                # Añadir palabras clave específicas por país si fuera necesario (ej. ciudades principales)
                if country == "México":
                    keywords.extend(['cdmx', 'ciudad de mexico', 'guadalajara', 'monterrey', 'mexico'])
                elif country == "Colombia":
                    keywords.extend(['bogota', 'medellin', 'cali'])
                elif country == "Argentina":
                    keywords.extend(['buenos aires', 'cordoba', 'rosario'])
                elif country == "Chile":
                    keywords.extend(['santiago', 'valparaiso'])
                elif country == "Perú":
                    keywords.extend(['lima', 'arequipa', 'peru'])
                elif country == "Brasil":
                    keywords.extend(['sao paulo', 'rio de janeiro', 'brasil'])
                
                # Evitar duplicados y añadir al mapa
                country_map[country] = list(set(keywords))
        return country_map

    def enrich_company_info(self, company_name: str) -> Dict:
        """Obtener información pública de la empresa (heurística)."""
        if not company_name:
            return self._default_company_info()

        if company_name in self.cache:
            return self.cache[company_name]
        
        info = {
            'name': company_name,
            'size': self._estimate_company_size(company_name),
            'industry': self._detect_industry(company_name),
            'hq_country': self._detect_country(company_name),
            'type': self._classify_company_type(company_name),
            'website': None # Placeholder para futuro enriquecimiento con APIs
        }
        
        self.cache[company_name] = info
        return info
    
    def _default_company_info(self):
        return {
            'name': 'Empresa Desconocida',
            'size': 'No especificado',
            'industry': 'No especificado',
            'hq_country': 'No especificado',
            'type': 'No especificado',
            'website': None
        }

    def _estimate_company_size(self, company_name: str) -> str:
        """Estimar tamaño de empresa basado en nombre y patrones."""
        name_lower = company_name.lower()
        
        multinational_keywords = ['google', 'amazon', 'microsoft', 'ibm', 'oracle', 'accenture', 'global', 'international', 'telefónica', 'santander', 'bbva', 'mercadolibre', 'uber', 'rappi', 'binance', 'spotify', 'netflix']
        if any(keyword in name_lower for keyword in multinational_keywords):
            return 'Multinacional (1000+)'
            
        large_keywords = ['corp', 'corporation', 'group', 'systems', 'financial group', 'holding', 'enterprise']
        if any(keyword in name_lower for keyword in large_keywords):
            return 'Grande (201-1000)'
            
        medium_keywords = ['solutions', 'services', 'agency', 'digital', 'agencia', 'consulting', 'consultoría']
        if any(keyword in name_lower for keyword in medium_keywords):
            return 'Mediana (51-200)'

        startup_keywords = ['startup', 'labs', 'tech', 'innov', 'digital', 'app', 'venture', 'platforma', 'software', 'cloud']
        if any(keyword in name_lower for keyword in startup_keywords):
            return 'Startup (1-50)'
        
        return 'No especificado'
    
    def _detect_industry(self, company_name: str) -> str:
        """Detectar industria basada en nombre de empresa."""
        name_lower = company_name.lower()
        
        industries = {
            'Fintech': ['fintech', 'bank', 'banco', 'financial', 'finance', 'credit', 'lending', 'payments', 'pagos', 'crypto', 'cripto'],
            'EdTech': ['edtech', 'education', 'educación', 'learning', 'academy', 'campus', 'universidad', 'escuela'],
            'HealthTech': ['health', 'medical', 'hospital', 'clinic', 'care', 'biotech', 'salud'],
            'E-commerce': ['store', 'shop', 'market', 'retail', 'commerce', 'ecommerce', 'marketplace'],
            'Consultoría': ['consulting', 'consultoría', 'services', 'solutions', 'strategy', 'asesoría'],
            'Manufactura': ['manufactura', 'manufacturing', 'industrial', 'fábrica'],
            'Logística': ['logistics', 'logística', 'delivery', 'envío'],
            'Telecomunicaciones': ['telecom', 'telefónica', 'movil'],
            'Automotriz': ['automotriz', 'automotive', 'carros', 'coches'],
            'Medios y Entretenimiento': ['media', 'entretenimiento', 'streaming', 'gaming', 'noticias'],
        }
        
        for industry, keywords in industries.items():
            if any(keyword in name_lower for keyword in keywords):
                return industry
        
        return 'Tecnología/Software' # Default más apropiado para el contexto del proyecto
    
    def _detect_country(self, company_name: str) -> str:
        """Detectar país de sede basado en nombre, usando el mapa de COMMON_GEO_DATA."""
        name_lower = company_name.lower()
        
        for country, keywords in self.country_keywords_map.items():
            if any(keyword in name_lower for keyword in keywords):
                return country
        
        return 'Latam' # Default a región si no se puede detectar un país específico
    
    def _classify_company_type(self, company_name: str) -> str:
        """Clasificar tipo de empresa."""
        name_lower = company_name.lower()
        
        if any(word in name_lower for word in ['consultoría', 'consulting', 'services']):
            return 'Consultoría'
        elif any(word in name_lower for word in ['product', 'saas', 'software', 'app', 'platform']):
            return 'Producto/Tecnología'
        elif any(word in name_lower for word in ['outsourcing', 'staffing', 'recruitment', 'rrhh', 'human resources']):
            return 'Recursos Humanos/Staffing'
        elif 'bank' in name_lower or 'banco' in name_lower or 'financial' in name_lower:
            return 'Financiera/Bancaria'
        else:
            return 'Corporación'
