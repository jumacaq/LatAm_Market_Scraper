import re

def normalize_country(location):
    if not location:
        return None
    txt = location.lower()

    if "méxico" in txt or "mexico" in txt: return "Mexico"
    if "colombia" in txt: return "Colombia"
    if "peru" in txt or "perú" in txt: return "Peru"
    if "argentina" in txt: return "Argentina"

    return None
