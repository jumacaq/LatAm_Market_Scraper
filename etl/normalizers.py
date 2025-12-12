# FILE: Proyecto/job-market-intelligence/etl/normalizers.py
import re
import yaml
import os
from typing import Dict, Any, Tuple, Optional # <--- ¡AÑADIR Optional AQUÍ!
from config.geo import COMMON_GEO_DATA # Importar datos geográficos

class DataNormalizer:
    def __init__(self):
        # El mapa de países se carga desde COMMON_GEO_DATA para consistencia
        self.countries_map = self._build_country_keywords_map()
        self.seniority_map = self._build_seniority_map()

    def _build_country_keywords_map(self):
        """Construye un mapa de palabras clave para la detección de países."""
        country_map = {}
        for continent, countries in COMMON_GEO_DATA.items():
            for country in countries:
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
                
                country_map[country] = list(set(keywords))
        return country_map

    def _build_seniority_map(self):
        """Define el mapa de palabras clave para la detección de seniority."""
        return {
            'Executive': ['vp', 'vice president', 'cxo', 'ceo', 'cmo', 'cto', 'co-founder', 'founder', 'director'],
            'Lead / Manager': ['lead', 'manager', 'head of', 'jefe', 'coordinador', 'principal', 'staff', 'team lead', 'líder'],
            'Senior': ['senior', 'sr.', 'sr', 'advanced', 'expert'],
            'Mid': ['mid', 'semi-senior', 'semisenior', 'regular', 'intermedio'],
            'Junior': ['junior', 'jr.', 'jr', 'entry-level', 'trainee', 'practicante', 'pasante', 'asistente', 'early career', 'nivel 1', 'level 1', 'becario', 'co-op'],
        }

    def extract_country_from_location(self, location):
        """Extrae el país de una cadena de ubicación usando palabras clave."""
        if not location:
            return None
        
        location_lower = location.lower()
        for country, keywords in self.countries_map.items():
            if any(keyword in location_lower for keyword in keywords):
                return country
        
        return None

    def normalize_seniority(self, seniority_text: Optional[str], title: str, description: str = "") -> str:
        """
        Normaliza el nivel de antigüedad basándose en texto, título o descripción.
        Prioriza la detección de seniority explícita, luego infiere.
        """
        text_to_analyze = (str(seniority_text or '') + ' ' + str(title or '') + ' ' + str(description or '')).lower()
        
        # 1. Búsqueda explícita (De Executive a Junior)
        for level, keywords in self.seniority_map.items():
            if any(re.search(r'\b' + re.escape(keyword) + r'\b', text_to_analyze) for keyword in keywords):
                return level
        
        # 2. Heurística forzada: Asignar 'Mid' a roles técnicos base sin prefijo explícito
        # Esto reduce el "Other" para roles comunes.
        implicit_mid_keywords = [
            'engineer', 'developer', 'analyst', 'specialist', 'architect', 
            'programador', 'consultor', 'diseñador', 'owner', 'scrum master',
            'desarrollador', 'ingeniero', 'analista', 'especialista'
        ]
        
        if any(keyword in text_to_analyze for keyword in implicit_mid_keywords):
             return 'Mid'
        
        return 'Other'

    def normalize_job_type(self, job_type_text, description=""):
        """Normaliza el tipo de trabajo (ej. Full-time, Remote, Hybrid)"""
        text_to_analyze = (job_type_text or "" + " " + description or "").lower()

        if 'full-time' in text_to_analyze or 'tiempo completo' in text_to_analyze:
            return 'Full-time'
        elif 'part-time' in text_to_analyze or 'medio tiempo' in text_to_analyze:
            return 'Part-time'
        elif 'contract' in text_to_analyze or 'contrato' in text_to_analyze or 'freelance' in text_to_analyze:
            return 'Contract'
        elif 'remote' in text_to_analyze or 'remoto' in text_to_analyze or 'work from home' in text_to_analyze:
            return 'Remote'
        elif 'hybrid' in text_to_analyze or 'híbrido' in text_to_analyze:
            return 'Hybrid'
        elif 'internship' in text_to_analyze or 'pasantía' in text_to_analyze:
            return 'Internship'

        return 'Other'
    
    def classify_role_category(self, title: str) -> str:
        """
        Clasifica una vacante en una categoría de rol de alto nivel.
        """
        title_lower = str(title).lower()
        
        if any(r in title_lower for r in ['data scientist', 'machine learning', 'ai', 'inteligencia artificial', 'ml engineer']):
            return "Data Science & ML"
        elif any(r in title_lower for r in ['data analyst', 'business intelligence', 'bi', 'analytics', 'analista de datos']):
            return "Data Analytics & BI"
        elif any(r in title_lower for r in ['full stack', 'backend', 'frontend', 'developer', 'engineer', 'dev', 'desarrollador', 'ingeniero de software']):
            return "Software Development"
        elif any(r in title_lower for r in ['product manager', 'product owner', 'po', 'gerente de producto']):
            return "Product Management"
        elif any(r in title_lower for r in ['devops', 'cloud', 'aws', 'azure', 'gcp', 'sre', 'ingeniero devops']):
            return "DevOps & Cloud"
        elif any(r in title_lower for r in ['scrum master', 'agile', 'project manager', 'jefe de proyecto']):
            return "Agile & Project Management"
        elif any(r in title_lower for r in ['qa engineer', 'quality assurance', 'tester']):
            return "QA & Testing"
        elif any(r in title_lower for r in ['ux/ui', 'diseñador ux', 'diseñador ui', 'product designer']):
            return "UX/UI Design"
        elif any(r in title_lower for r in ['cybersecurity', 'seguridad informática', 'security engineer']):
            return "Cybersecurity"
        
        return "General Tech" # Categoría por defecto