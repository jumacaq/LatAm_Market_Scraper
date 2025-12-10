# jobscraper/pipelines_collector/LinkedInItemCollectorPipeline.py

from typing import List, Dict, Any

class LinkedInItemCollectorPipeline:
    """
    Pipeline simple que recoge todos los items procesados (enriquecidos)
    y los almacena en una lista estática para ser usados por el script principal (main.py).
    """
    # 🚨 Esta lista estática guarda todos los registros de todos los spiders
    all_records: List[Dict[str, Any]] = []

    def process_item(self, item, spider):
        """Convierte el Item a un diccionario y lo añade a la lista estática."""
        if item:
            # Añadir una copia del item (como diccionario) a la lista estática
            LinkedInItemCollectorPipeline.all_records.append(dict(item))
        return item