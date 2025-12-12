import pandas as pd
import datetime
import logging
from database.supabase_client import SupabaseClient # Importar SupabaseClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TrendAnalyzer:
    def __init__(self):
        self.db = SupabaseClient()
        logging.info("TrendAnalyzer inicializado con SupabaseClient.")

    def _fetch_all_jobs_with_skills(self, start_date=None, end_date=None):
        """
        Obtiene todos los trabajos y sus habilidades asociadas dentro de un rango de fechas.
        Retorna un DataFrame de Pandas.
        """
        logging.info(f"Fetching jobs from Supabase for trend analysis (start_date={start_date}, end_date={end_date})...")
        # Asegurarse de que las fechas se pasen como string en formato 'YYYY-MM-DD' si SupabaseClient lo espera así
        start_date_str = start_date.isoformat() if start_date else None
        end_date_str = end_date.isoformat() if end_date else None

        response = self.db.get_jobs(limit=None, start_date=start_date_str, end_date=end_date_str)
        jobs_data = response.data if response and response.data else []

        if not jobs_data:
            logging.warning("No se encontraron datos de trabajos en Supabase para el análisis de tendencias en el período.")
            return pd.DataFrame()

        # Normalizar datos: convertir posted_date a datetime
        df = pd.DataFrame(jobs_data)
        if 'posted_date' in df.columns:
            df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce')
        if 'scraped_at' in df.columns:
            df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')

        # Procesar habilidades anidadas
        all_records = []
        for index, row in df.iterrows():
            # Obtener job_id de la tabla jobs (que es 'id')
            job_db_id = row['id'] 
            # Asegurarse de que 'skills' es una lista o iterable.
            # Supabase devuelve skills como una lista de diccionarios si se usa "*, skills(*)"
            skills_list = row.get('skills', []) 
            
            if skills_list:
                for skill_entry in skills_list:
                    # Crear un diccionario temporal para la fila
                    record_dict = row.to_dict() # Convertir la serie a diccionario
                    record_dict['job_id'] = job_db_id # Asegurar que job_id se mapea correctamente
                    record_dict['skill_id'] = skill_entry.get('id')
                    record_dict['skill_name'] = skill_entry.get('skill_name')
                    record_dict['skill_category'] = skill_entry.get('skill_category')
                    all_records.append(record_dict)
            
        # Crear un DataFrame con una fila por cada habilidad de cada trabajo
        df_flat = pd.DataFrame(all_records)
        logging.info(f"Loaded {len(df_flat)} flattened job/skill records.")
        # Filtrar solo si 'posted_date' existe y no es nulo, y 'skill_name' existe y no es nulo
        if 'posted_date' in df_flat.columns and 'skill_name' in df_flat.columns:
            return df_flat.dropna(subset=['posted_date', 'skill_name'])
        else:
            return pd.DataFrame(columns=['skill_name', 'posted_date']) # Devolver un DF vacío con columnas esperadas si no hay datos

    def get_most_demanded_skills(self, top_n=10, start_date=None, end_date=None):
        """Calcula las N habilidades más demandadas en el período."""
        df_jobs_skills = self._fetch_all_jobs_with_skills(start_date, end_date)
        if df_jobs_skills.empty:
            logging.info("No hay datos de habilidades para calcular las más demandadas.")
            return pd.DataFrame(columns=['skill_name', 'count']) # Devolver DF vacío con columnas esperadas

        demanded_skills = df_jobs_skills.groupby('skill_name').size().reset_index(name='count')
        demanded_skills = demanded_skills.sort_values('count', ascending=False).head(top_n)
        return demanded_skills

    def get_skills_growth_trend(self, period_days=30, top_n=10, end_date=None):
        """
        Identifica las habilidades con mayor crecimiento/decrecimiento en los últimos `period_days`.
        Compara el período actual con el período anterior de la misma duración.
        """
        if end_date is None:
            end_date = datetime.date.today()
        
        current_period_start = end_date - datetime.timedelta(days=period_days)
        previous_period_start = current_period_start - datetime.timedelta(days=period_days)
        
        df_current = self._fetch_all_jobs_with_skills(current_period_start, end_date)
        df_previous = self._fetch_all_jobs_with_skills(previous_period_start, current_period_start - datetime.timedelta(days=1)) # Excluir el día de inicio del periodo actual

        if df_current.empty and df_previous.empty:
            logging.info("No hay datos de habilidades en ninguno de los períodos para calcular tendencias de crecimiento.")
            return pd.DataFrame(columns=['skill_name', 'current_count', 'previous_count', 'change', 'growth_rate'])

        # Asegurarse de que los DataFrames tengan la columna 'skill_name' antes de value_counts
        current_skills_counts = pd.Series(dtype='int').rename('current_count')
        if not df_current.empty and 'skill_name' in df_current.columns:
            current_skills_counts = df_current['skill_name'].value_counts().rename('current_count')
        
        previous_skills_counts = pd.Series(dtype='int').rename('previous_count')
        if not df_previous.empty and 'skill_name' in df_previous.columns:
            previous_skills_counts = df_previous['skill_name'].value_counts().rename('previous_count')
        
        # Unir las series de conteo para formar un DataFrame, asegurando 'skill_name' como índice/columna
        merged_skills = pd.DataFrame({
            'current_count': current_skills_counts,
            'previous_count': previous_skills_counts
        }).reset_index()
        merged_skills = merged_skills.rename(columns={'index': 'skill_name'}).fillna(0) # Asegurar que skill_name existe

        merged_skills['change'] = merged_skills['current_count'] - merged_skills['previous_count']
        # Evitar división por cero si previous_count es 0
        merged_skills['growth_rate'] = (merged_skills['change'] / (merged_skills['previous_count'].replace(0, 1))) * 100 
        
        merged_skills = merged_skills[merged_skills['current_count'] > 0]
        
        growing_skills = merged_skills.sort_values('growth_rate', ascending=False).head(top_n)
        return growing_skills[['skill_name', 'current_count', 'previous_count', 'change', 'growth_rate']]


    def get_most_demanded_roles(self, top_n=10, start_date=None, end_date=None):
        """Calcula los N roles más demandados (basado en el título de la vacante, clasificado heurísticamente)."""
        df_jobs = self._fetch_all_jobs_with_skills(start_date, end_date) 
        if df_jobs.empty:
            logging.info("No hay datos de trabajos para calcular los roles más demandados.")
            return pd.DataFrame(columns=['simplified_role', 'count'])

        def simplify_role_title(title):
            title_lower = str(title).lower()
            if 'software engineer' in title_lower or 'ingeniero de software' in title_lower or 'desarrollador' in title_lower:
                return 'Software Engineer / Developer'
            elif 'data scientist' in title_lower or 'científico de datos' in title_lower:
                return 'Data Scientist'
            elif 'product manager' in title_lower or 'gerente de producto' in title_lower:
                return 'Product Manager'
            elif 'devops' in title_lower or 'ingeniero devops' in title_lower:
                return 'DevOps Engineer'
            elif 'frontend' in title_lower:
                return 'Frontend Developer'
            elif 'backend' in title_lower:
                return 'Backend Developer'
            elif 'full stack' in title_lower:
                return 'Full Stack Developer'
            elif 'qa' in title_lower or 'quality assurance' in title_lower:
                return 'QA Engineer'
            elif 'analista de datos' in title_lower or 'data analyst' in title_lower:
                return 'Data Analyst'
            return 'Other' # Simplificado a 'Other' en lugar del título original sin simplificar para roles menos comunes

        df_jobs['simplified_role'] = df_jobs['title'].apply(simplify_role_title)
        demanded_roles = df_jobs.groupby('simplified_role').size().reset_index(name='count')
        demanded_roles = demanded_roles.sort_values('count', ascending=False).head(top_n)
        return demanded_roles

    def get_sector_distribution(self, start_date=None, end_date=None):
        """Calcula la distribución de vacantes por sector."""
        df_jobs = self._fetch_all_jobs_with_skills(start_date, end_date)
        if df_jobs.empty:
            logging.info("No hay datos de trabajos para calcular la distribución por sector.")
            return pd.DataFrame(columns=['sector', 'count'])

        sector_distribution = df_jobs.groupby('sector').size().reset_index(name='count')
        sector_distribution = sector_distribution.sort_values('count', ascending=False)
        return sector_distribution

    def analyze_and_store_trends(self, analysis_date=None):
        """
        Ejecuta el análisis de tendencias para una fecha específica y las almacena en Supabase.
        Por defecto, analiza el día actual y compara con el mes anterior para algunas métricas.
        """
        if analysis_date is None:
            analysis_date = datetime.date.today()
        
        logging.info(f"Iniciando análisis y almacenamiento de tendencias para la fecha: {analysis_date}")

        # Rango de tiempo para análisis (últimos 30 días para muchas métricas)
        last_month_start = analysis_date - datetime.timedelta(days=30)

        # 1. Habilidades más demandadas (para el último mes)
        demanded_skills = self.get_most_demanded_skills(top_n=15, start_date=last_month_start, end_date=analysis_date)
        for _, row in demanded_skills.iterrows():
            trend_data = {
                'date': analysis_date.isoformat(),
                'metric_name': 'most_demanded_skill',
                'metric_value': row['skill_name'],
                'count': int(row['count']),
                'sector': None, 
                'country': None
            }
            self.db.upsert_trend(trend_data)
        logging.info(f"Tendencias de habilidades más demandadas almacenadas: {len(demanded_skills)} registros.")

        # 2. Habilidades en crecimiento (comparando el último mes con el anterior)
        growing_skills = self.get_skills_growth_trend(period_days=30, top_n=15, end_date=analysis_date)
        for _, row in growing_skills.iterrows():
            # Ajuste para el esquema existente: concatenar en metric_value
            skill_name = row['skill_name'] if pd.notna(row['skill_name']) else "Unknown Skill"
            growth_rate = row['growth_rate'] if pd.notna(row['growth_rate']) else 0.0
            current_count = row['current_count'] if pd.notna(row['current_count']) else 0

            trend_data_simplified = {
                'date': analysis_date.isoformat(),
                'metric_name': 'growing_skill',
                'metric_value': f"{skill_name} ({'+' if growth_rate >= 0 else ''}{growth_rate:.2f}%)", # Concatenar para mostrar tasa
                'count': int(current_count), 
                'sector': None,
                'country': None
            }
            self.db.upsert_trend(trend_data_simplified)
        logging.info(f"Tendencias de habilidades en crecimiento almacenadas: {len(growing_skills)} registros.")

        # 3. Roles más demandados (para el último mes)
        demanded_roles = self.get_most_demanded_roles(top_n=15, start_date=last_month_start, end_date=analysis_date)
        for _, row in demanded_roles.iterrows():
            trend_data = {
                'date': analysis_date.isoformat(),
                'metric_name': 'most_demanded_role',
                'metric_value': row['simplified_role'],
                'count': int(row['count']),
                'sector': None,
                'country': None
            }
            self.db.upsert_trend(trend_data)
        logging.info(f"Tendencias de roles más demandados almacenadas: {len(demanded_roles)} registros.")

        # 4. Distribución por sector (para el último mes)
        sector_distribution = self.get_sector_distribution(start_date=last_month_start, end_date=analysis_date)
        for _, row in sector_distribution.iterrows():
            trend_data = {
                'date': analysis_date.isoformat(),
                'metric_name': 'sector_distribution',
                'metric_value': row['sector'],
                'count': int(row['count']),
                'sector': row['sector'], 
                'country': None
            }
            self.db.upsert_trend(trend_data)
        logging.info(f"Tendencias de distribución por sector almacenadas: {len(sector_distribution)} registros.")

        logging.info("Análisis y almacenamiento de tendencias completado.")
        return True
