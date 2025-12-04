# FILE: job-market-intelligence/etl/skill_extractor.py
import re
import yaml
import os

class SkillExtractor:
    def __init__(self):
        self.tech_skills = []
        self.skill_categories = {}
        self.load_skill_data()

    def load_skill_data(self):
        """Carga las habilidades técnicas y sus categorías desde el archivo de configuración."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.tech_skills = config.get('tech_skills', [])
                # Agregamos categorías de habilidades para la columna skill_category
                # Esto es un ejemplo, se puede expandir mucho más.
                self.skill_categories = {
                    'Programming Language': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift', 'Kotlin', 'TypeScript', 'R', 'Scala', 'Perl'],
                    'Framework': ['React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring Boot', 'Express.js', 'Next.js', 'React Native', 'Flutter'],
                    'Database': ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'Oracle', 'SQL Server'],
                    'Cloud/DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'Terraform', 'Ansible', 'CI/CD'],
                    'Data/AI': ['Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Power BI', 'Tableau', 'Data Analysis', 'Spark', 'Hadoop', 'Kafka'],
                    'Version Control': ['Git', 'GitHub', 'GitLab', 'Bitbucket'],
                    'Soft Skill': ['Agile', 'Scrum', 'Communication', 'Leadership', 'Problem Solving'], # Ejemplo de soft skills
                    'Other': [] # Para habilidades que no encajan en una categoría clara
                }
        except FileNotFoundError:
            print(f"Error: Archivo de configuración no encontrado en {config_path}. Las habilidades no se cargarán.")
        except yaml.YAMLError as e:
            print(f"Error cargando config.yaml para habilidades: {e}.")

    def extract_skills(self, text):
        """Extrae habilidades de un texto usando el diccionario cargado."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.tech_skills:
            # Usar límites de palabra para evitar coincidencias parciales (ej. 'java' en 'javascript')
            # Y manejo de variantes (ej. 'nodejs' para 'Node.js')
            patterns = [
                r'\b' + re.escape(skill.lower()) + r'\b',
                r'\b' + re.escape(skill.lower().replace('.', '')) + r'\b' # Para Node.js -> nodejs
            ]
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found_skills.append(skill)
                    break # Una vez encontrada, pasar a la siguiente habilidad
        
        return list(set(found_skills)) # Eliminar duplicados

    def categorize_skill(self, skill_name):
        """Categoriza una habilidad según las categorías predefinidas."""
        for category, skills_list in self.skill_categories.items():
            if skill_name in skills_list:
                return category
        return 'Other'
