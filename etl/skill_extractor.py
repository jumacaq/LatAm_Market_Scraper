# FILE: Proyecto/job-market-intelligence/etl/skill_extractor.py
import re
import yaml
import os
import logging
from typing import Dict, List

class SkillExtractor:
    def __init__(self):
        self.tech_skills = []
        self.skill_categories = {}
        self.load_skill_data()

    def load_skill_data(self):
        """Carga las habilidades técnicas y sus categorías desde el archivo de configuración."""
        # Ruta corregida para ser relativa al directorio raíz del proyecto
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.tech_skills = config.get('tech_skills', [])
                
                # Definición de categorías estáticas para la clasificación de skills
                # Esta es una versión más completa y ordenada.
                self.skill_categories = {
                    'Programming Language': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'TypeScript', 'R', 'Scala', 'Perl'],
                    'Framework/Library': ['React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Express.js', 'Next.js', 'React Native', 'Flutter', '.NET', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch'],
                    'Database': ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'Oracle', 'SQL Server'],
                    'Cloud/DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'Terraform', 'Ansible', 'CI/CD', 'SRE'],
                    'Data/AI': ['Machine Learning', 'Deep Learning', 'Data Analysis', 'Spark', 'Hadoop', 'Kafka', 'ETL', 'Big Data', 'Power BI', 'Tableau'],
                    'Version Control': ['Git', 'GitHub', 'GitLab', 'Bitbucket'],
                    'Methodology/Process': ['Agile', 'Scrum', 'Kanban', 'Jira', 'Confluence'],
                    'Software/Tools': ['Figma', 'UX/UI', 'Salesforce', 'SAP', 'ERP', 'Microservices', 'REST API', 'GraphQL'],
                    'Security/Testing': ['Testing (Unit, Integration)', 'Cybersecurity Fundamentals'],
                    'Soft Skill': ['Communication', 'Leadership', 'Problem Solving'], # Ejemplos adicionales
                    'Other': [] # Para habilidades que no encajan en una categoría clara
                }
                
                # Fallback: si tech_skills no estaba en YAML, se autocompleta con todas las de las categorías
                if not self.tech_skills:
                     for skills_list in self.skill_categories.values():
                         self.tech_skills.extend(skills_list)
                     self.tech_skills = list(set(self.tech_skills))

        except FileNotFoundError:
            logging.error(f"❌ Error CRÍTICO: Archivo de configuración YAML no encontrado en la ruta: {config_path}")
        except yaml.YAMLError as e:
            logging.error(f"❌ Error CRÍTICO: Sintaxis incorrecta en config.yaml: {e}")

    def extract_skills(self, text: str) -> List[str]:
        """Extrae habilidades de un texto usando el diccionario cargado."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.tech_skills:
            skill_lower = skill.lower()
            
            # Patrones de búsqueda robustos: límites de palabra, variantes sin '.' o ' '
            patterns = [
                r'\b' + re.escape(skill_lower) + r'\b',                                 # 'python'
                r'\b' + re.escape(skill_lower.replace('.', '')) + r'\b',               # 'node.js' -> 'nodejs'
                r'\b' + re.escape(skill_lower.replace(' ', '')) + r'\b',               # 'machine learning' -> 'machinelearning'
                r'\b' + re.escape(skill_lower.replace('-', '')) + r'\b',               # 'ci-cd' -> 'cicd'
                r'\b' + re.escape(skill_lower.replace(' ', '-')) + r'\b',              # 'power bi' -> 'power-bi'
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
                    break # Una vez encontrada, pasar a la siguiente habilidad
        
        return list(set(found_skills)) # Eliminar duplicados

    def categorize_skill(self, skill_name: str) -> str:
        """Categoriza una habilidad según las categorías predefinidas."""
        for category, skills_list in self.skill_categories.items():
            if skill_name in skills_list:
                return category
        
        return 'Other'
