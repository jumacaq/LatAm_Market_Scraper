# etl/normalizers.py (Versión FINAL - FIX de Empresa y Seniority)

import re
from typing import Dict, Any, Tuple 
from etl.enrichment import CompanyEnricher
from etl.skill_extractor import SkillExtractor 


def normalize_role_and_seniority(title: str, description: str = "") -> Tuple[str, str]:
    """
    Normaliza el título del trabajo y extrae el nivel de seniority.
    """
    title_lower = str(title).lower() 
    description_lower = str(description).lower()
    
    # --- LÓGICA DE DETECCIÓN DE SENIORITY MÁXIMA ---
    
    # 1. Chequeo Junior/Trainee
    junior_keywords = [
        'junior', 'jr.', 'trainee', 'entry level', 'practicante', 
        'intern', 'apprentice', 'asociado', 'associate', 'i', 'level 1', 'level 2', 
        'becario', 'co-op', 'entry-level', 'nivel 1'
    ]
    if any(s in title_lower for s in junior_keywords) or any(s in description_lower for s in ['0-2 años', '0-3 años', 'poca experiencia']):
        seniority = "Junior/Trainee"
    
    # 2. Chequeo Senior/Lead
    # Esta es la lista de keywords más amplia y la que rompe el default.
    senior_keywords = [
        'senior', 'sr.', 'lead', 'principal', 'manager', 'director', 'vp', 
        'expert', 'staff', 'architect', 'head of', 'level 3', 'level 4', 
        'level 5', 'iii', 'iv', 'v', 'especialista', 'sme', 'lider', 'nivel 4'
    ]
    desc_senior_keywords = ['experiencia 5+', 'liderazgo', 'mentor', '5+ years', '7+ years', '8+ years', '5 años de experiencia', '7 años de experiencia', 'senior level', 'nivel experto', '10+ years']
    
    is_senior_title = any(s in title_lower for s in senior_keywords)
    is_senior_desc = any(s in description_lower for s in desc_senior_keywords)
    
    if is_senior_title or is_senior_desc:
        seniority = "Senior/Lead"
    elif 'seniority' not in locals(): # Si no es Junior ni Senior, por defecto es Mid-level
        seniority = "Mid-level"


    # 3. Detección de Categoría de Rol (Se mantiene)
    role_category = "General Tech"
    if any(r in title_lower for r in ['data scientist', 'machine learning', 'ai', 'inteligencia artificial']):
        role_category = "Data Science & ML"
    elif any(r in title_lower for r in ['data analyst', 'business intelligence', 'bi', 'analytics']):
        role_category = "Data Analytics & BI"
    elif any(r in title_lower for r in ['full stack', 'backend', 'frontend', 'developer', 'engineer', 'dev']):
        role_category = "Software Development"
    elif any(r in title_lower for r in ['product manager', 'product owner', 'po']):
        role_category = "Product Management"
    elif any(r in title_lower for r in ['devops', 'cloud', 'aws', 'azure', 'gcp', 'sre']):
        role_category = "DevOps & Cloud"
    elif any(r in title_lower for r in ['scrum master', 'agile', 'project manager']):
        role_category = "Agile & PM"
    
    return role_category, seniority


def normalize_all(record: Dict[str, Any]) -> Dict[str, Any]:
    # Inicialización de las clases ETL
    enricher = CompanyEnricher()
    skill_extractor = SkillExtractor()
    
    # 🚨 FIX CRÍTICO FINAL: Asegurar que el nombre de la empresa se extraiga de cualquiera de las columnas posibles
    # Intentamos obtener de 'company', luego de 'empresa' y si ambos fallan, usamos 'Unknown Company'
    raw_company_name = record.get('company') or record.get('empresa')
    company_name = str(raw_company_name).strip()
    
    # FIX: Aseguramos que los valores sean strings para evitar TypeError
    title = str(record.get('title') or record.get('titulo', '')).strip()
    description = str(record.get('description') or record.get('descripcion', '')).strip()
    
    # 1. Normalización de Rol y Seniority
    role_category, seniority = normalize_role_and_seniority(title, description)
    record['role_category'] = role_category
    record['nivel_experiencia'] = seniority # Mapeo para el dashboard
    
    # 2. EXTRACCIÓN DE SKILLS
    all_text = title + " " + description 
    extracted_skills = skill_extractor.extract_skills(all_text)
    record['skills'] = extracted_skills 

    # 3. Enriquecimiento de Empresa
    if company_name and company_name.lower() not in ['nan', 'none', '']:
        company_info = enricher.enrich_company_info(company_name)
        
        # 🚨 FIX: Almacenamos el nombre original y los campos enriquecidos
        record['company'] = company_name 
        record['company_size'] = company_info.get('tamaño', 'No detectado')
        record['industry'] = company_info.get('industria', 'No detectado')
        record['company_type'] = company_info.get('tipo_empresa', 'No detectado')
    else:
        # Llenar con valores por defecto si no hay nombre válido
        record['company'] = 'Anónimo'
        record['company_size'] = 'No especificado'
        record['industry'] = 'No especificado'
        record['company_type'] = 'No especificado'
    
    # 4. Mapeo final para el dashboard
    if record.get('role_category'):
        record['sector'] = record['role_category']
    else:
        record['sector'] = record.get('keyword', 'General Tech')
         
    record.pop('role_category', None)
    
    return record