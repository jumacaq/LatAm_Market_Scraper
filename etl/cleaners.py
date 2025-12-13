# FILE: Proyecto/job-market-intelligence/etl/cleaners.py
import re
from bs4 import BeautifulSoup

class TextCleaner:
    def remove_html_tags(self, text):
        """Elimina etiquetas HTML de un texto."""
        if not text:
            return ""
        # Usar BeautifulSoup para una limpieza más robusta
        # Usamos 'html.parser' como fallback si 'lxml' no está disponible o da problemas,
        # aunque 'lxml' es más eficiente.
        try:
            soup = BeautifulSoup(text, "lxml") 
        except Exception:
            soup = BeautifulSoup(text, "html.parser")
        clean_text = soup.get_text(separator=' ', strip=True)
        return self.clean_whitespace(clean_text)

    def clean_whitespace(self, text):
        """Normaliza espacios en blanco, eliminando múltiples espacios y saltos de línea."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)  # Múltiples espacios a uno solo
        text = text.strip()
        return text

    def clean_title(self, title):
        """Limpia el título, eliminando información entre paréntesis y normalizando espacios."""
        if not title:
            return ""
        title = re.sub(r'\(.*?\)', '', title) # Elimina paréntesis y contenido
        return self.clean_whitespace(title)

    def process_text(self, text):
        """Procesa un texto aplicando limpieza de HTML y normalización de espacios."""
        return self.clean_whitespace(self.remove_html_tags(text))