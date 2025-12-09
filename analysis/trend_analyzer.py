# analysis/trend_analyzer.py

import pandas as pd
from typing import Dict, Any

class TrendAnalyzer:
    """Clase para calcular tendencias y KPIs clave."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def get_summary_kpis(self) -> Dict[str, Any]:
        """Calcula el resumen de vacantes y distribución."""
        
        total_jobs = len(self.df)
        top_country = self.df['pais'].mode()[0] if not self.df['pais'].empty else 'N/A'
        
        # Distribución de Seniority (ejemplo)
        seniority_counts = self.df['nivel_experiencia'].value_counts(normalize=True).to_dict()
        
        return {
            "Total Vacantes": total_jobs,
            "País Principal": top_country,
            "Distribución Seniority": {k: f"{v:.1%}" for k, v in seniority_counts.items()},
        }
        
    def get_top_skills(self, n=5) -> pd.DataFrame:
        """Calcula las top N habilidades."""
        skills_df = self.df.explode('skills')
        if skills_df.empty or 'skills' not in skills_df.columns:
            return pd.DataFrame({'Skill': ['N/A'], 'Frecuencia': [0]})
            
        return skills_df['skills'].value_counts().head(n).reset_index()

# La clase report_generator.py (omitida por brevedad) se encargaría de dar formato a esta salida.