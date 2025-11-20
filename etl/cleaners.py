import re
from bs4 import BeautifulSoup

class TextCleaner:
    def remove_html(self, text):
        if not text: return ""
        return BeautifulSoup(text, "html.parser").get_text()

    def clean_title(self, title):
        if not title: return ""
        return re.sub(r'\(.*?\)', '', title).strip()