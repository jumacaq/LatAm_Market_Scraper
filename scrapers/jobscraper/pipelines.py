# ETL Pipeline for cleaning, normalizing, and storing data
# =============================================================================

import re
import hashlib
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()


class CleaningPipeline:
    """Clean and normalize raw scraped data"""
    
    def process_item(self, item, spider):
        # Clean title
        if item.get('title'):
            item['title'] = self.clean_text(item['title'])
        
        # Clean company name
        if item.get('company_name'):
            item['company_name'] = self.clean_text(item['company_name'])
        
        # Clean description
        if item.get('description'):
            item['description'] = self.clean_html(item['description'])
        
        # Normalize location
        if item.get('location'):
            item['country'] = self.extract_country(item['location'])
        
        # Add scraped timestamp
        item['scraped_at'] = datetime.now().isoformat()
        
        # Generate unique job_id if not provided
        if not item.get('job_id'):
            item['job_id'] = self.generate_job_id(item)
        
        return item
    
    @staticmethod
    def clean_text(text):
        """Remove extra whitespace and special characters"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = text.strip()
        return text
    
    @staticmethod
    def clean_html(html_text):
        """Remove HTML tags"""
        if not html_text:
            return ""
        clean = re.sub(r'<[^>]+>', '', html_text)
        return CleaningPipeline.clean_text(clean)
    
    @staticmethod
    def extract_country(location):
        """Extract country from location string"""
        countries = {
            'Mexico': ['mexico', 'cdmx', 'ciudad de mexico', 'guadalajara', 'monterrey'],
            'Colombia': ['colombia', 'bogota', 'medellin', 'cali'],
            'Argentina': ['argentina', 'buenos aires', 'cordoba', 'rosario'],
            'Chile': ['chile', 'santiago', 'valparaiso'],
            'Peru': ['peru', 'lima', 'arequipa'],
            'Brazil': ['brazil', 'brasil', 'sao paulo', 'rio de janeiro']
        }
        
        location_lower = location.lower()
        for country, keywords in countries.items():
            if any(keyword in location_lower for keyword in keywords):
                return country
        
        return None
    
    @staticmethod
    def generate_job_id(item):
        """Generate unique ID from job attributes"""
        unique_string = f"{item.get('title', '')}{item.get('company_name', '')}{item.get('source_url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()


class SkillExtractionPipeline:
    """Extract technical skills from job descriptions"""
    
    TECH_SKILLS = [
        # Programming Languages
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift',
        'Kotlin', 'TypeScript', 'R', 'Scala', 'Perl',
        
        # Frameworks & Libraries
        'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 
        'Spring Boot', 'Express.js', 'Next.js', 'React Native', 'Flutter',
        
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 
        'DynamoDB', 'Oracle', 'SQL Server',
        
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI',
        'Terraform', 'Ansible', 'CI/CD',
        
        # Data & AI
        'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas',
        'NumPy', 'Scikit-learn', 'Power BI', 'Tableau', 'Data Analysis',
        
        # Others
        'Git', 'Linux', 'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
    ]
    
    def process_item(self, item, spider):
        description = item.get('description', '') + ' ' + item.get('requirements', '')
        extracted_skills = self.extract_skills(description)
        item['skills'] = extracted_skills
        return item
    
    def extract_skills(self, text):
        """Extract skills from text using keyword matching"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.TECH_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates


class SectorClassificationPipeline:
    """Classify jobs into sectors based on keywords"""
    
    SECTOR_KEYWORDS = {
        'EdTech': ['education', 'learning', 'edtech', 'e-learning', 'training', 'course', 'student'],
        'Fintech': ['fintech', 'financial', 'payment', 'banking', 'crypto', 'blockchain', 'trading'],
        'Future of Work': ['remote', 'collaboration', 'productivity', 'automation', 'workspace']
    }
    
    def process_item(self, item, spider):
        if not item.get('sector'):
            item['sector'] = self.classify_sector(item)
        return item
    
    def classify_sector(self, item):
        """Classify job into a sector"""
        text = (
            str(item.get('title') or '') + ' ' + 
            str(item.get('description') or '') + ' ' + 
            str(item.get('company_name') or '')
        ).lower()
        
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return sector
        
        return 'Other'


class SupabasePipeline:
    """Store cleaned data in Supabase"""
    
    def __init__(self):
        self.client = None
    
    def open_spider(self, spider):
        """Initialize Supabase connection"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            spider.logger.error("Supabase credentials not found in environment variables")
            return
        
        self.client = create_client(supabase_url, supabase_service_key)
        spider.logger.info("Connected to Supabase")
    
    def process_item(self, item, spider):
        """Insert or update job in database"""
        if not self.client:
            spider.logger.error("Supabase client not initialized")
            return item
        
        try:
            # Prepare job data
            job_data = {
                'job_id': item.get('job_id'),
                'title': item.get('title'),
                'company_name': item.get('company_name'),
                'location': item.get('location'),
                'country': item.get('country'),
                'job_type': item.get('job_type'),
                'seniority_level': item.get('seniority_level'),
                'sector': item.get('sector'),
                'description': item.get('description'),
                'requirements': item.get('requirements'),
                'salary_range': item.get('salary_range'),
                'posted_date': item.get('posted_date'),
                'source_url': item.get('source_url'),
                'source_platform': item.get('source_platform'),
                'scraped_at': item.get('scraped_at')
            }
            
            # Upsert job (insert or update if exists)
            response = self.client.table('jobs').upsert(job_data).execute()
            
            # Insert skills
            if item.get('skills') and response.data:
                job_id = response.data[0]['id']
                for skill in item['skills']:
                    skill_data = {
                        'job_id': job_id,
                        'skill_name': skill,
                        'skill_category': self.categorize_skill(skill)
                    }
                    self.client.table('skills').insert(skill_data).execute()
            
            spider.logger.info(f"Saved job: {item.get('title')} at {item.get('company_name')}")
            
        except Exception as e:
            spider.logger.error(f"Error saving to Supabase: {str(e)}")
        
        return item
    
    @staticmethod
    def categorize_skill(skill):
        """Categorize skills"""
        programming = ['Python', 'JavaScript', 'Java', 'C++', 'Ruby', 'PHP', 'Go']
        frameworks = ['React', 'Angular', 'Django', 'Flask', 'Node.js', 'Spring Boot']
        databases = ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis']
        cloud = ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes']
        
        if skill in programming:
            return 'Programming Language'
        elif skill in frameworks:
            return 'Framework'
        elif skill in databases:
            return 'Database'
        elif skill in cloud:
            return 'Cloud/DevOps'
        else:
            return 'Other'
    
    def close_spider(self, spider):
        """Cleanup on spider close"""
        spider.logger.info("Closing Supabase connection")
