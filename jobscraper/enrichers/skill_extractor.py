# jobscraper/enrichers/skill_extractor.py

import re
import yaml
import os
from typing import Dict, List

class SkillExtractor:
    """
    Componente modular para extraer y categorizar habilidades técnicas a partir
    de la descripción de la vacante, utilizando config.yaml.
    """
    def __init__(self):
        self.tech_skills: List[str] = []
        self.skill_categories: Dict[str, List[str]] = {}
        self.load_skill_data()

    def load_skill_data(self):
        """Carga las habilidades técnicas y sus categorías desde el archivo de configuración."""
        
        # RUTA CORRECTA: Sube un nivel (de 'enrichers/' a 'jobscraper/') y accede a 'config/'
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
                self.tech_skills = config.get('tech_skills', [])
                
                # Definición de categorías estáticas para la clasificación de skills
                self.skill_categories = {
                    'Programming Language': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'TypeScript', 'R', 'Scala', 'Perl'],
                    'Framework/Library': ['React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Next.js', 'Flutter', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch'],
                    'Database': ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'Oracle', 'SQL Server'],
                    'Cloud/DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'CI/CD', 'Jenkins'],
                    'Methodology/Process': ['Scrum', 'Kanban', 'Agile'],
                    'Data Analysis/BI': ['Power BI', 'Tableau', 'ETL', 'Data Analysis'],
                    'Security/APIs': ['Cybersecurity Fundamentals', 'APIs & Microservices', 'Testing (Unit, Integration)'],
                    'Version Control': ['Git', 'GitHub', 'GitLab', 'Bitbucket'],
                    'Other': []
                }
                
                # Fallback: si tech_skills no estaba en YAML, se autocompleta
                if not self.tech_skills:
                     for skills_list in self.skill_categories.values():
                         self.tech_skills.extend(skills_list)
                     self.tech_skills = list(set(self.tech_skills))

        except FileNotFoundError:
            print(f"❌ Error CRÍTICO: Archivo de configuración YAML no encontrado en la ruta: {config_path}")
        except yaml.YAMLError as e:
            print(f"❌ Error CRÍTICO: Sintaxis incorrecta en config.yaml: {e}")

    def extract_skills(self, text: str) -> List[str]:
        """Extrae habilidades de un texto usando el diccionario cargado."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.tech_skills:
            skill_lower = skill.lower()
            
            # Patrones de búsqueda robustos
            patterns = [
                r'\b' + re.escape(skill_lower) + r'\b', 
                r'\b' + re.escape(skill_lower.replace('.', '')) + r'\b',
                r'\b' + re.escape(skill_lower.replace(' ', '')) + r'\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
                    break 
        
        return list(set(found_skills))

    def categorize_skill(self, skill_name: str) -> str:
        """Categoriza una habilidad según las categorías predefinidas."""
        for category, skills_list in self.skill_categories.items():
            if skill_name in skills_list:
                return category
        
        return 'Other'