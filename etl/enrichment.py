import pandas as pd
import requests
import time
from typing import Dict, Optional

class CompanyEnricher:
    def __init__(self):
        self.cache = {}
        
    def enrich_company_info(self, company_name: str) -> Dict:
        """Obtener información pública de la empresa"""
        if company_name in self.cache:
            return self.cache[company_name]
        
        info = {
            'nombre': company_name,
            'tamaño': self._estimate_company_size(company_name),
            'industria': self._detect_industry(company_name),
            'pais_sede': self._detect_country(company_name),
            'tipo_empresa': self._classify_company_type(company_name),
            'contacto': None  # Podemos agregar búsqueda de emails después
        }
        
        self.cache[company_name] = info
        return info
    
    def _estimate_company_size(self, company_name: str) -> str:
        """Estimar tamaño de empresa basado en nombre y patrones"""
        name_lower = company_name.lower()
        
        # Patrones para startups
        startup_keywords = ['startup', 'labs', 'tech', 'innov', 'digital', 'smart']
        if any(keyword in name_lower for keyword in startup_keywords):
            return 'Startup (1-50)'
        
        # Patrones para empresas medianas
        medium_keywords = ['solutions', 'group', 'systems', 'consulting', 'services']
        if any(keyword in name_lower for keyword in medium_keywords):
            return 'Mediana (51-200)'
        
        # Patrones para grandes empresas
        large_keywords = ['corp', 'corporation', 'global', 'international', 'banco', 'financial']
        if any(keyword in name_lower for keyword in large_keywords):
            return 'Grande (201-1000)'
        
        # Patrones para multinacionales
        multinational_keywords = ['microsoft', 'google', 'amazon', 'ibm', 'oracle', 'accenture']
        if any(keyword in name_lower for keyword in multinational_keywords):
            return 'Multinacional (1000+)'
        
        return 'No especificado'
    
    def _detect_industry(self, company_name: str) -> str:
        """Detectar industria basada en nombre de empresa"""
        name_lower = company_name.lower()
        
        industries = {
            'Fintech': ['fintech', 'bank', 'banco', 'financial', 'finance', 'credit', 'lending'],
            'EdTech': ['edtech', 'education', 'educación', 'learning', 'academy', 'campus'],
            'Salud': ['health', 'medical', 'hospital', 'clinic', 'care', 'biotech'],
            'Retail': ['store', 'shop', 'market', 'retail', 'commerce', 'ecommerce'],
            'Tecnología': ['tech', 'software', 'it ', 'systems', 'data', 'cloud', 'digital']
        }
        
        for industry, keywords in industries.items():
            if any(keyword in name_lower for keyword in keywords):
                return industry
        
        return 'Tecnología'  # Default
    
    def _detect_country(self, company_name: str) -> str:
        """Detectar país de sede basado en nombre"""
        name_lower = company_name.lower()
        
        country_keywords = {
            'México': ['méxico', 'mexico', 'mx', 'cdmx', 'gdl', 'mtv'],
            'Colombia': ['colombia', 'co', 'bogota', 'medellin'],
            'Argentina': ['argentina', 'ar', 'buenos aires'],
            'España': ['españa', 'spain', 'es', 'madrid', 'barcelona'],
            'Estados Unidos': ['usa', 'us', 'united states', 'san francisco', 'ny', 'silicon valley']
        }
        
        for country, keywords in country_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return country
        
        return 'México'  # Default
    
    def _classify_company_type(self, company_name: str) -> str:
        """Clasificar tipo de empresa"""
        name_lower = company_name.lower()
        
        if any(word in name_lower for word in ['consultoría', 'consulting', 'services']):
            return 'Consultoría'
        elif any(word in name_lower for word in ['product', 'saas', 'software']):
            return 'Producto/Tecnología'
        elif any(word in name_lower for word in ['outsourcing', 'staffing', 'recruitment']):
            return 'Recursos Humanos'
        else:
            return 'Corporación'
        