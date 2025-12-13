import pytest
from etl.cleaners import TextCleaner
from etl.normalizers import DataNormalizer
from etl.skill_extractor import SkillExtractor
from etl.sector_classifier import SectorClassifier
from etl.enrichment import CompanyEnricher
import os
import yaml

# Cargar la configuración de prueba para SectorClassifier y SkillExtractor
# Esto es importante porque los tests se ejecutarán en un entorno aislado.
@pytest.fixture(scope="session")
def config_data():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture
def text_cleaner():
    return TextCleaner()

@pytest.fixture
def data_normalizer():
    return DataNormalizer()

@pytest.fixture
def skill_extractor(config_data):
    # Asegurarse de que el extractor de habilidades carga las skills desde la config
    extractor = SkillExtractor()
    extractor.tech_skills = config_data.get('tech_skills', [])
    # También asegurar que skill_categories se construyan correctamente
    extractor.skill_categories = {
        'Programming Language': [s for s in config_data.get('tech_skills', []) if s in ['Python', 'Java']], # Ejemplo
        'Cloud/DevOps': [s for s in config_data.get('tech_skills', []) if s in ['AWS', 'Docker']] # Ejemplo
    }
    return extractor

@pytest.fixture
def sector_classifier(config_data):
    classifier = SectorClassifier()
    classifier.sector_keywords = {
        sector_name: details.get('keywords', [])
        for sector_name, details in config_data.get('sectors', {}).items()
    }
    return classifier

@pytest.fixture
def company_enricher():
    return CompanyEnricher()

# --- Tests para TextCleaner ---
def test_remove_html_tags(text_cleaner):
    html_text = "<h1>Title</h1><p>Description with <b>bold</b> text.</p>"
    cleaned_text = text_cleaner.remove_html_tags(html_text)
    assert cleaned_text == "Title Description with bold text."

def test_clean_whitespace(text_cleaner):
    dirty_text = "  Hello   World \n New Line "
    cleaned_text = text_cleaner.clean_whitespace(dirty_text)
    assert cleaned_text == "Hello World New Line"

# --- Tests para DataNormalizer ---
def test_extract_country_from_location(data_normalizer):
    assert data_normalizer.extract_country_from_location("Buenos Aires, Argentina") == "Argentina"
    assert data_normalizer.extract_country_from_location("Santiago de Chile") == "Chile"
    assert data_normalizer.extract_country_from_location("Somewhere in USA") == None # No está en tu COMMON_GEO_DATA Latam
    assert data_normalizer.extract_country_from_location("Guadalajara, Mexico") == "México" # Coincide con palabra clave
    assert data_normalizer.extract_country_from_location(None) == None

def test_normalize_seniority(data_normalizer):
    assert data_normalizer.normalize_seniority("Senior Developer", "Senior Python Developer") == "Senior"
    assert data_normalizer.normalize_seniority("Jr. Engineer", "Junior Software Engineer") == "Junior"
    assert data_normalizer.normalize_seniority(None, "Product Manager") == "Mid" # Inferencia
    assert data_normalizer.normalize_seniority(None, "CTO") == "Executive"
    assert data_normalizer.normalize_seniority("Entry-level", "Data Analyst") == "Junior"

# --- Tests para SkillExtractor ---
def test_extract_skills(skill_extractor):
    text = "Buscamos un desarrollador Python con experiencia en Django, AWS y un poco de Machine Learning."
    skills = skill_extractor.extract_skills(text)
    assert "Python" in skills
    assert "Django" in skills
    assert "AWS" in skills
    assert "Machine Learning" in skills
    assert "Ruby" not in skills

def test_categorize_skill(skill_extractor):
    assert skill_extractor.categorize_skill("Python") == "Programming Language"
    assert skill_extractor.categorize_skill("AWS") == "Cloud/DevOps"
    assert skill_extractor.categorize_skill("MongoDB") == "Database"
    assert skill_extractor.categorize_skill("UnknownSkill") == "Other"

# --- Tests para SectorClassifier ---
def test_classify_sector(sector_classifier):
    item_fintech = {'title': 'Ingeniero de Software Fintech', 'description': 'Trabajo en pagos digitales y blockchain.'}
    assert sector_classifier.classify_sector(item_fintech) == 'Fintech'

    item_edtech = {'title': 'Desarrollador de plataforma educativa', 'company_name': 'EdTech Solutions'}
    assert sector_classifier.classify_sector(item_edtech) == 'Edtech'

    item_other = {'title': 'Diseñador Gráfico', 'description': 'Necesario para agencia de publicidad.'}
    assert sector_classifier.classify_sector(item_other) == 'Other'

# --- Tests para CompanyEnricher ---
def test_enrich_company_info(company_enricher):
    info = company_enricher.enrich_company_info("Mercado Libre")
    assert info['size'] == 'Multinacional (1000+)'
    assert info['industry'] == 'E-commerce'
    assert info['hq_country'] == 'Argentina'

    info_startup = company_enricher.enrich_company_info("Innovate Labs")
    assert info_startup['size'] == 'Startup (1-50)'
    assert info_startup['industry'] == 'Tecnología/Software'

    info_unknown = company_enricher.enrich_company_info("")
    assert info_unknown['name'] == 'Empresa Desconocida'
