import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import time
import logging
from dotenv import load_dotenv
from database.supabase_client import SupabaseClient
from analysis.report_generator import ReportGenerator
from analysis.trend_analyzer import TrendAnalyzer
import datetime
from config.geo import COMMON_GEO_DATA
from io import BytesIO
import json

# --- CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
st.set_page_config(
    page_title="Market Intelligence Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="📈"
)

# --- CACHE PARA REPORTES DE IA ---
if 'ai_report_cache' not in st.session_state:
    st.session_state.ai_report_cache = None
    st.session_state.ai_report_timestamp = None

# --- ESTILOS PERSONALIZADOS CON COLORES VIVOS ---
st.markdown("""
<style>
    /* Fondo general con gradiente sutil */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e7f1 100%);
    }
    
    /* Tarjetas de KPI con colores vibrantes y sombra */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-left: 6px solid;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-card:nth-child(1) { border-left-color: #FF6B6B; }
    .metric-card:nth-child(2) { border-left-color: #4ECDC4; }
    .metric-card:nth-child(3) { border-left-color: #45B7D1; }
    .metric-card:nth-child(4) { border-left-color: #FFA07A; }
    .metric-card:nth-child(5) { border-left-color: #98D8C8; }
    
    /* Botones más llamativos */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Headers con colores vibrantes */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 700 !important;
    }
    
    /* Expander con estilo */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #3498db, #2c3e50) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- TÍTULO PRINCIPAL CON ESTILO ---
st.title("📊 LatAm Job Market Intelligence")
st.markdown("""
Una visión en tiempo real del mercado laboral en **Latam** y más allá, 
con análisis de tendencias e insights generados por IA.
""")

# --- CARGAR CREDENCIALES (solo para uso interno, sin visualización) ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# --- SIDEBAR & CONTROLES ---
st.sidebar.header("⚙️ Panel de Control")

with st.sidebar:
    st.subheader("⚡ Acciones Rápidas")
    
    # Inputs para el scraper
    st.subheader("Configuración del Scraper")
    
    available_spider_names = ["linkedin", "computrabajo"] 
    selected_spiders_scrape = st.multiselect(
        "Scrapers a Ejecutar",
        options=available_spider_names,
        default=["linkedin"], 
        help="Selecciona uno o más scrapers para ejecutar."
    )

    continents = ["Selecciona un Continente"] + list(COMMON_GEO_DATA.keys())
    selected_continent_scrape = st.selectbox("Continente para Scrapear", continents, key="scrape_continent")
    
    countries_for_scrape = []
    if selected_continent_scrape != "Selecciona un Continente":
        countries_for_scrape = ["Todos los Países"] + COMMON_GEO_DATA[selected_continent_scrape]
    selected_country_scrape = st.selectbox("País para Scrapear", countries_for_scrape, key="scrape_country")
    
    today = datetime.date.today()
    default_start_date_scrape = today - datetime.timedelta(days=7)
    start_date_scrape = st.date_input("Fecha de Inicio de Vacantes", value=default_start_date_scrape, key="scrape_start_date")
    end_date_scrape = st.date_input("Fecha de Fin de Vacantes", value=today, key="scrape_end_date")

    max_jobs_scrape = st.number_input(
        "Número máximo de vacantes por scraper",
        min_value=1,
        value=100,
        step=10,
        help="El número máximo de vacantes que cada scraper intentará obtener."
    )

    def execute_scraper(selected_spiders, continent, country, start_date, end_date, max_jobs):
        env = os.environ.copy()
        
        cmd = ["python", "main.py"]
        
        if selected_spiders:
            cmd.extend(["--spiders", ",".join(selected_spiders)])
        else:
            st.error("Por favor, selecciona al menos un scraper para ejecutar.")
            return None
        
        continent_arg = str(continent).strip() if continent is not None else ""
        country_arg = str(country).strip() if country is not None else ""
        start_date_arg = start_date.strftime("%Y-%m-%d") if start_date is not None else ""
        end_date_arg = end_date.strftime("%Y-%m-%d") if end_date is not None else ""

        if continent_arg and continent_arg != "Selecciona un Continente":
            cmd.extend(["--continent", continent_arg])
        
        if country_arg and country_arg != "Todos los Países":
            cmd.extend(["--country", country_arg])
        elif country_arg == "Todos los Países" and continent_arg != "Selecciona un Continente":
            cmd.extend(["--country", "Todos los Países"])
        
        if start_date_arg:
            cmd.extend(["--start_date", start_date_arg])
        
        if end_date_arg:
            cmd.extend(["--end_date", end_date_arg])

        cmd.extend(["--max_jobs", str(max_jobs)])
        
        logging.info(f"Comando subprocess a ejecutar: {cmd}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False
        )
        return result

    if st.button("🔄 Ejecutar Scrapers", type="primary", use_container_width=True, key='run_scraper_btn'):
        if selected_continent_scrape == "Selecciona un Continente":
            st.error("Por favor, selecciona un continente para ejecutar el scraper.")
        elif not selected_spiders_scrape:
            st.error("Por favor, selecciona al menos un scraper para ejecutar.")
        else:
            with st.spinner(f"Extrayendo vacantes ({', '.join(selected_spiders_scrape)})... (Esto puede tardar varios minutos por scraper/seguridad)"):
                try:
                    result = execute_scraper(
                        selected_spiders_scrape,
                        selected_continent_scrape,
                        selected_country_scrape,
                        start_date_scrape,
                        end_date_scrape,
                        max_jobs_scrape
                    )
                    
                    if result and result.returncode == 0:
                        st.success("✅ Proceso de scraping finalizado")
                        logs = result.stderr + "\n" + result.stdout
                        if "Vacante" in logs and "guardada con éxito" in logs:
                            st.info("📊 Nuevos datos guardados en Supabase.")
                        else:
                            st.warning("⚠️ El scraper terminó, pero no se encontraron logs de datos guardados. Revisa los detalles.")
                        
                        with st.expander("Ver Detalles del Proceso"):
                            st.code(logs)
                        
                        time.sleep(1)
                        st.session_state.data_cache = None  # Limpiar cache manual
                        st.rerun()
                    else:
                        st.error("❌ Error en el proceso de scraping")
                        if result:
                            st.text_area("Log de Error", result.stderr + "\n" + result.stdout, height=200)
                        else:
                            st.warning("El proceso de scraping no devolvió un resultado válido.")
                except Exception as e:
                    st.error(f"Error ejecutando el scraper: {e}")

    st.markdown("---")
    st.subheader("📈 Generar Análisis de Tendencias")
    st.write("Calcula métricas de tendencias (habilidades, roles, etc.) y las almacena en la base de datos.")
    if st.button("✨ Ejecutar Análisis de Tendencias", type="secondary", use_container_width=True, key='run_trend_analysis_btn'):
        with st.spinner("Analizando tendencias y almacenando en Supabase..."):
            try:
                result = subprocess.run(
                    ["python", "main.py", "--analyze-trends"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    st.success("✅ Análisis de tendencias finalizado y almacenado.")
                    st.info("Refresca el dashboard para ver las nuevas visualizaciones de tendencias.")
                    with st.expander("Ver Logs del Análisis"):
                        st.code(result.stdout + result.stderr)
                    st.session_state.data_cache = None  # Limpiar cache manual
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al ejecutar el análisis de tendencias.")
                    st.text_area("Log de Error del Análisis", result.stderr, height=200)
            except Exception as e:
                st.error(f"Error ejecutando el análisis de tendencias: {e}")

    st.markdown("---")
    st.subheader("⚠️ Mantenimiento de Datos")

    if st.button("🗑️ Limpiar Base de Datos", type="secondary", use_container_width=True, key="clear_db_only_btn"):
        st.session_state['confirm_clear_only_db'] = True 

    if 'confirm_clear_only_db' in st.session_state and st.session_state['confirm_clear_only_db']:
        st.warning("¿Estás seguro de que quieres ELIMINAR TODOS los datos de las tablas 'jobs', 'skills', 'companies' y 'trends'? Esta acción es irreversible.")
        st.info("⚠️ Asegúrate de que tu clave de Supabase tenga **permisos de `delete`** y que no haya políticas de RLS que impidan la eliminación.")
        col_confirm_yes_clear, col_confirm_no_clear = st.columns(2)
        if col_confirm_yes_clear.button("Sí, Eliminar Datos", key="confirm_clear_yes_action"):
            db_client_for_clear = SupabaseClient()
            if db_client_for_clear.clear_jobs_table(): 
                st.success("✅ Base de datos (tablas 'jobs', 'skills', 'companies', 'trends') limpiada exitosamente.")
                st.session_state['confirm_clear_only_db'] = False
                st.session_state.data_cache = None  # Limpiar cache manual
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ No se pudo limpiar la base de datos. Por favor, revisa los logs y los permisos de Supabase.")
                st.session_state['confirm_clear_only_db'] = False
                time.sleep(1)
                st.rerun()
        if col_confirm_no_clear.button("No, Cancelar", key="confirm_clear_no_action"):
            st.info("Acción cancelada.")
            st.session_state['confirm_clear_only_db'] = False
            st.rerun()

# --- FILTROS DEL DASHBOARD --- 
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros de Visualización")

filter_continents = ["Todos"] + list(COMMON_GEO_DATA.keys())
selected_filter_continent = st.sidebar.selectbox("Filtrar por Continente", filter_continents, key="filter_continent_display")

filter_countries = ["Todos"]
if selected_filter_continent != "Todos":
    filter_countries.extend(COMMON_GEO_DATA.get(selected_filter_continent, []))
selected_filter_country = st.sidebar.selectbox("Filtrar por País", filter_countries, key="filter_country_display")

st.sidebar.markdown("---")
st.sidebar.subheader("Rango de Fechas")
min_date_available = datetime.date(2023, 1, 1)
max_date_available = datetime.date.today()

filter_start_date = st.sidebar.date_input("Desde:", value=min_date_available, min_value=min_date_available, max_value=max_date_available, key="filter_start_date_display")
filter_end_date = st.sidebar.date_input("Hasta:", value=max_date_available, min_value=min_date_available, max_value=max_date_available, key="filter_end_date_display")

if filter_start_date > filter_end_date:
    st.sidebar.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
    
# --- DATA LOADING (Sin hash de DataFrame, usando timestamp como key) ---
def load_and_process_data_from_supabase():
    try:
        db = SupabaseClient()
        response_jobs = db.get_jobs(limit=None)
        jobs = response_jobs.data if response_jobs and response_jobs.data else []
        
        response_trends = db.get_trends(limit=None)
        trends_data = response_trends.data if response_trends and response_trends.data else []

        df_loaded_jobs = pd.DataFrame()
        if jobs:
            # SOLUCIÓN DEFINITIVA: Convertir todos los valores ANTES de crear el DataFrame
            cleaned_jobs = []
            for job in jobs:
                cleaned_job = {}
                for key, value in job.items():
                    if isinstance(value, (list, dict)):
                        # Convertir listas/dicts a JSON string
                        cleaned_job[key] = json.dumps(value, ensure_ascii=False)
                    elif pd.isna(value) or value is None:
                        cleaned_job[key] = None
                    else:
                        cleaned_job[key] = value
                cleaned_jobs.append(cleaned_job)
            
            # Crear DataFrame con datos ya limpios
            df_loaded_jobs = pd.DataFrame(cleaned_jobs)
            
            # Procesar fechas
            date_cols = ['posted_date', 'scraped_at']
            for col in date_cols:
                if col in df_loaded_jobs.columns:
                    temp_series = pd.to_datetime(df_loaded_jobs[col], errors='coerce', utc=True)
                    if pd.api.types.is_datetime64_any_dtype(temp_series) and temp_series.dt.tz is not None:
                        df_loaded_jobs[col] = temp_series.dt.tz_localize(None)
                    else:
                        df_loaded_jobs[col] = temp_series
            
            # Columnas de texto: convertir a string
            text_cols = [
                'title', 'company_name', 'location', 'country', 'sector', 'job_type', 
                'seniority_level', 'source_platform', 'role_category', 'salary_range',
                'company_size', 'company_industry', 'company_hq_country', 'company_type', 'company_website',
                'id', 'job_id', 'source_url', 'company_id',
                'description', 'requirements', 'skills'
            ]
            for col in text_cols:
                if col in df_loaded_jobs.columns:
                    df_loaded_jobs[col] = df_loaded_jobs[col].astype(str).replace('nan', 'Desconocido').replace('None', 'Desconocido')
                else:
                    df_loaded_jobs[col] = 'Desconocido'
            
            # Columnas clave
            for col in ['seniority_level', 'role_category', 'sector']:
                if col not in df_loaded_jobs.columns:
                    df_loaded_jobs[col] = 'Desconocido'

            # Booleanos
            if 'is_active' in df_loaded_jobs.columns:
                df_loaded_jobs['is_active'] = df_loaded_jobs['is_active'].fillna(False).astype(bool)
            else:
                df_loaded_jobs['is_active'] = False

            df_loaded_jobs = df_loaded_jobs.sort_values('scraped_at', ascending=False)
        
        df_loaded_trends = pd.DataFrame()
        if trends_data:
            # Limpiar datos de trends ANTES de crear DataFrame
            cleaned_trends = []
            for trend in trends_data:
                cleaned_trend = {}
                for key, value in trend.items():
                    if isinstance(value, (list, dict)):
                        cleaned_trend[key] = json.dumps(value, ensure_ascii=False)
                    elif pd.isna(value) or value is None:
                        cleaned_trend[key] = None
                    else:
                        cleaned_trend[key] = value
                cleaned_trends.append(cleaned_trend)
            
            df_loaded_trends = pd.DataFrame(cleaned_trends)
            
            required_trend_cols = ['date', 'metric_name', 'metric_value', 'count', 'sector', 'country']
            for col in required_trend_cols:
                if col not in df_loaded_trends.columns:
                    df_loaded_trends[col] = None
            
            trend_text_cols = ['metric_name', 'metric_value', 'sector', 'country']
            for col in trend_text_cols:
                if col in df_loaded_trends.columns:
                    df_loaded_trends[col] = df_loaded_trends[col].astype(str).replace('nan', 'Desconocido').replace('None', 'Desconocido')

            if 'date' in df_loaded_trends.columns:
                df_loaded_trends['date'] = pd.to_datetime(df_loaded_trends['date'], errors='coerce')
            if 'count' in df_loaded_trends.columns:
                df_loaded_trends['count'] = pd.to_numeric(df_loaded_trends['count'], errors='coerce').fillna(0).astype(int)

            df_loaded_trends = df_loaded_trends.sort_values('date', ascending=False)

        return df_loaded_jobs, df_loaded_trends
    except Exception as e:
        st.error(f"❌ Error al conectar o cargar datos de Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- CACHE MANUAL CON SESSION_STATE ---
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = None
    st.session_state.cache_timestamp = None

# Verificar si necesitamos recargar (cache expirado o vacío)
cache_ttl = 3600  # 1 hora en segundos
current_time = time.time()
cache_expired = (
    st.session_state.cache_timestamp is None or 
    (current_time - st.session_state.cache_timestamp) > cache_ttl
)

if st.session_state.data_cache is None or cache_expired:
    df, df_trends = load_and_process_data_from_supabase()
    st.session_state.data_cache = (df, df_trends)
    st.session_state.cache_timestamp = current_time
else:
    df, df_trends = st.session_state.data_cache

# --- APLICAR FILTROS GLOBALES ---
filtered_df = df.copy()

if not filtered_df.empty:
    # Deserializar la columna 'skills' DESPUÉS de cargar desde cache
    if 'skills' in filtered_df.columns:
        def safe_json_loads(x):
            try:
                if isinstance(x, str) and x.strip() and x != 'Desconocido':
                    parsed = json.loads(x)
                    return parsed if isinstance(parsed, list) else []
                return []
            except (json.JSONDecodeError, ValueError):
                return []
        
        filtered_df['skills'] = filtered_df['skills'].apply(safe_json_loads)
        
    # Filtrar por continente
    if selected_filter_continent != "Todos":
        countries_in_continent = COMMON_GEO_DATA.get(selected_filter_continent, [])
        if 'country' in filtered_df.columns:
            continent_filter_mask = filtered_df['country'].str.lower().isin([c.lower() for c in countries_in_continent])
            filtered_df = filtered_df[continent_filter_mask]
        else:
            st.warning("La columna 'country' no está disponible en los datos para filtrar por continente.")
    
    # Filtrar por país
    if selected_filter_country != "Todos":
        if 'country' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['country'].str.contains(selected_filter_country, case=False, na=False)]
        else:
            st.warning("La columna 'country' no está disponible en los datos para filtrar por país.")

    # Filtrar por rango de fechas de publicación
    if 'posted_date' in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df['posted_date']):
        filtered_df = filtered_df[
            (filtered_df['posted_date'].dt.date >= filter_start_date) & 
            (filtered_df['posted_date'].dt.date <= filter_end_date)
        ]
    else:
        st.warning("La columna 'posted_date' no es de tipo fecha o no existe, el filtro de rango de fechas no se aplicará.")

# --- FILTRAR LAS TENDENCIAS POR LA FECHA MÁS RECIENTE ---
filtered_df_trends = df_trends.copy()
latest_analysis_date = None
if not filtered_df_trends.empty:
    if 'date' in filtered_df_trends.columns and not filtered_df_trends['date'].empty:
        latest_analysis_date = filtered_df_trends['date'].max()
        filtered_df_trends = filtered_df_trends[filtered_df_trends['date'] == latest_analysis_date]
    else:
        st.warning("La columna 'date' no está disponible en los datos de tendencias para filtrar por la fecha más reciente.")


# --- MAIN DASHBOARD CONTENT ---
if filtered_df.empty:
    st.info("La base de datos está vacía o no hay datos que coincidan con los filtros aplicados. Ejecuta los scrapers para obtener datos y refrescar el dashboard.")
else:
    # --- KPIs SECTION CON ESTILO VIBRANTE ---
    st.markdown("---")
    st.header("📈 Métricas Clave del Mercado Laboral")
    
    # Paleta de colores vibrantes para KPIs
    kpi_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_jobs_count = len(filtered_df)
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {kpi_colors[0]}">
                <h3 style="color: {kpi_colors[0]}; margin: 0;">{total_jobs_count}</h3>
                <p style="margin: 0; font-size: 14px; color: #666;">Vacantes Filtradas</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            unique_companies = filtered_df['company_name'].nunique() if 'company_name' in filtered_df.columns else 0
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {kpi_colors[1]}">
                <h3 style="color: {kpi_colors[1]}; margin: 0;">{unique_companies}</h3>
                <p style="margin: 0; font-size: 14px; color: #666;">Empresas Únicas</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            if 'scraped_at' in filtered_df.columns and filtered_df['scraped_at'].notna().any():
                last_update = filtered_df['scraped_at'].max().strftime("%Y-%m-%d %H:%M")
            else:
                last_update = "N/A"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {kpi_colors[2]}">
                <h3 style="color: {kpi_colors[2]}; margin: 0; font-size: 16px;">{last_update}</h3>
                <p style="margin: 0; font-size: 14px; color: #666;">Última Actualización</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            new_jobs_today = 0
            if 'posted_date' in filtered_df.columns and filtered_df['posted_date'].notna().any():
                today_date = datetime.date.today()
                new_jobs_today = filtered_df[filtered_df['posted_date'].dt.date == today_date].shape[0]
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {kpi_colors[3]}">
                <h3 style="color: {kpi_colors[3]}; margin: 0;">{new_jobs_today}</h3>
                <p style="margin: 0; font-size: 14px; color: #666;">Nuevas Vacantes (Hoy)</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col5:
            avg_job_age = "N/A"
            if 'posted_date' in filtered_df.columns and filtered_df['posted_date'].notna().any():
                now_naive = datetime.datetime.now().replace(tzinfo=None)
                days_since_post = (now_naive - filtered_df['posted_date']).dt.days
                avg_job_age = f"{days_since_post.mean():.1f} días"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {kpi_colors[4]}">
                <h3 style="color: {kpi_colors[4]}; margin: 0; font-size: 16px;">{avg_job_age}</h3>
                <p style="margin: 0; font-size: 14px; color: #666;">Edad Promedio Vacantes</p>
            </div>
            """, unsafe_allow_html=True)

    # --- GENERADOR DE REPORTES CON IA (CORREGIDO CON CACHE) ---
    st.markdown("---")
    st.header("🧠 Reporte de Inteligencia Artificial")
    with st.expander("Generar y ver Reporte Diario de IA"):
        st.write("Genera un resumen ejecutivo de las tendencias actuales basándose en los datos filtrados.")
        
        report_generator = None
        if gemini_api_key:
            report_generator = ReportGenerator()
        
        # Verificar cache del reporte
        cache_ttl_report = 3600  # 1 hora en segundos
        current_time = time.time()
        report_cache_expired = (
            st.session_state.ai_report_timestamp is None or 
            (current_time - st.session_state.ai_report_timestamp) > cache_ttl_report
        )
        
        if not gemini_api_key:
            st.warning("⚠️ La API de Gemini no está configurada. El reporte de IA no puede ser generado.")
        elif st.button("Generar Reporte de IA", type="primary", key="generate_ai_report_btn"):
            if report_generator and report_generator.model:
                # Usar cache si está disponible y vigente
                if st.session_state.ai_report_cache is not None and not report_cache_expired:
                    st.info("📦 Usando reporte de IA cacheado (generado hace menos de 1 hora)")
                    st.subheader("📄 Resumen Ejecutivo")
                    st.markdown(st.session_state.ai_report_cache)
                else:
                    # Generar nuevo reporte
                    with st.spinner("Generando reporte de IA..."):
                        try:
                            available_sources = filtered_df['source_platform'].unique() if 'source_platform' in filtered_df.columns else []
                            source_text = ""
                            if len(available_sources) > 0:
                                normalized_sources = []
                                for source in available_sources:
                                    if source and source != 'Desconocido':
                                        if 'linkedin' in source.lower():
                                            normalized_sources.append('LinkedIn')
                                        elif 'computrabajo' in source.lower():
                                            normalized_sources.append('CompuTrabajo')
                                        else:
                                            normalized_sources.append(source)
                                
                                if len(normalized_sources) == 1:
                                    source_text = f"Fuente: {normalized_sources[0]}"
                                elif len(normalized_sources) == 2:
                                    source_text = f"Fuentes: {normalized_sources[0]} y {normalized_sources[1]}"
                                else:
                                    source_text = f"Fuentes: {', '.join(normalized_sources[:-1])} y {normalized_sources[-1]}"
                            
                            if len(filtered_df) > 50:
                                sample_jobs_df = filtered_df[['title', 'company_name', 'sector', 'location', 'source_platform']].sample(50, random_state=42)
                            else:
                                sample_jobs_df = filtered_df[['title', 'company_name', 'sector', 'location', 'source_platform']]

                            sample_jobs_data = sample_jobs_df.to_dict('records')
                            
                            ai_report = report_generator.generate_daily_insight(sample_jobs_data)
                            
                            # Guardar en cache
                            st.session_state.ai_report_cache = ai_report
                            st.session_state.ai_report_timestamp = time.time()
                            
                            st.subheader("📄 Resumen Ejecutivo")
                            if source_text:
                                st.markdown(f"**{source_text}**")
                            
                            st.markdown(ai_report)
                            
                        except Exception as e:
                            error_msg = str(e)
                            if "429" in error_msg or "quota" in error_msg.lower():
                                st.error("⚠️ **Cuota de Gemini API agotada.** Has alcanzado el límite de 20 peticiones/día.")
                                st.info("💡 Soluciones: 1) Espera 24h para reinicio, 2) Actualiza a plan de pago, 3) Revisa el reporte cacheado manualmente en estado de sesión.")
                                
                                # Mostrar cache si existe (aunque esté expirado)
                                if st.session_state.ai_report_cache:
                                    st.success("📦 Mostrando último reporte cacheado:")
                                    st.markdown(st.session_state.ai_report_cache)
                            else:
                                st.error(f"❌ Error generando reporte: {error_msg}")
            else:
                st.error("Error al inicializar el generador de reportes de IA. Revisa tu clave API o la inicialización del modelo.")
        else:
            # Mostrar botón y cache si está disponible
            if st.session_state.ai_report_cache and not report_cache_expired:
                st.success("📦 Reporte de IA cacheado disponible (generado hace menos de 1 hora)")
            elif st.session_state.ai_report_cache:
                st.info("📦 Hay un reporte de IA cacheado disponible (expirado, pero usable)")
            
            st.info("Haz clic en el botón para generar un reporte con IA de los datos actuales.")
    
    # --- VISUALIZACIONES (GRÁFICOS) CON TABS ---
    st.markdown("---")
    st.header("📊 Análisis de Tendencias y Distribución")

    vibrant_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#FFA07A', '#DDA0DD', '#20B2AA', '#F0E68C', '#FFB6C1']
    
    tab_sector, tab_company, tab_country, tab_seniority, tab_roles, tab_skills_demand, tab_skills_growth, tab_platform_sector, tab_source_platform, tab_raw_data = st.tabs([
        "🏢 Por Sector", 
        "👥 Por Empresa", 
        "🌍 Por País", 
        "📶 Por Seniority",
        "👔 Top Roles",
        "💡 Skills Demandadas",
        "📈 Skills en Crecimiento",
        "🔌 Plataforma vs. Sector",
        "📱 Distribución por Plataforma",
        "📋 Datos Crudos"
    ])

    with tab_sector:
        st.subheader("📊 Distribución de Vacantes por Sector")
        if 'sector' in filtered_df.columns and not filtered_df['sector'].empty:
            sector_counts = filtered_df['sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Número de Vacantes']
            fig_sector = px.bar(
                sector_counts.head(15), 
                x='Número de Vacantes', 
                y='Sector', 
                orientation='h', 
                title='<b>Top Sectores con Vacantes</b>',
                color='Número de Vacantes',
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={'Número de Vacantes': 'Vacantes', 'Sector': 'Sector'},
                color_discrete_sequence=vibrant_colors
            )
            fig_sector.update_layout(
                yaxis={'categoryorder':'total ascending'},
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_sector, width='stretch')
        else:
            st.info("No hay datos de sector disponibles para mostrar.")

    with tab_company:
        st.subheader("🏆 Top Empresas con Vacantes")
        if 'company_name' in filtered_df.columns and not filtered_df['company_name'].empty: 
            top_n_companies = st.slider("Top N Compañías", 5, 30, 15, key="top_companies_slider_tab")
            company_counts = filtered_df['company_name'].value_counts().head(top_n_companies).reset_index()
            company_counts.columns = ['Empresa', 'Número de Vacantes']
            fig_company = px.bar(
                company_counts, 
                x='Número de Vacantes', 
                y='Empresa', 
                orientation='h', 
                title=f'<b>Top {top_n_companies} Compañías Contratando</b>',
                color='Número de Vacantes',
                color_continuous_scale=px.colors.sequential.Plasma,
                labels={'Número de Vacantes': 'Vacantes', 'Empresa': 'Empresa'}
            )
            fig_company.update_layout(
                yaxis={'categoryorder':'total ascending'},
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_company, width='stretch')
        else:
            st.info("No hay datos de empresa disponibles para mostrar.")

    with tab_country:
        st.subheader("🌍 Distribución de Vacantes por País")
        if 'country' in filtered_df.columns and not filtered_df['country'].empty:
            country_counts = filtered_df['country'].value_counts().reset_index()
            country_counts.columns = ['País', 'Número de Vacantes']
            
            col_pie, col_bar = st.columns(2)
            
            with col_pie:
                fig_country_pie = px.pie(
                    country_counts.head(10), 
                    values='Número de Vacantes', 
                    names='País', 
                    title='<b>Top 10 Países (Gráfico de Pie)</b>',
                    hole=0.4,
                    color_discrete_sequence=vibrant_colors
                )
                fig_country_pie.update_layout(
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_country_pie, width='stretch')
            
            with col_bar:
                fig_country_bar = px.bar(
                    country_counts.head(15), 
                    x='Número de Vacantes', 
                    y='País', 
                    orientation='h', 
                    title='<b>Top 15 Países (Gráfico de Barras)</b>',
                    color='Número de Vacantes',
                    color_continuous_scale=px.colors.sequential.Cividis,
                    labels={'Número de Vacantes': 'Vacantes', 'País': 'País'}
                )
                fig_country_bar.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_country_bar, width='stretch')
        else:
            st.info("No hay datos de país disponibles para mostrar.")

    with tab_seniority:
        st.subheader("📶 Distribución de Nivel de Experiencia")
        if 'seniority_level' in filtered_df.columns and not filtered_df['seniority_level'].empty:
            seniority_counts = filtered_df['seniority_level'].value_counts().reset_index()
            seniority_counts.columns = ['Nivel de Seniority', 'Conteo']
            
            col_pie_sen, col_bar_sen = st.columns(2)
            
            with col_pie_sen:
                fig_seniority_pie = px.pie(
                    seniority_counts, 
                    values='Conteo', 
                    names='Nivel de Seniority', 
                    title='<b>Distribución por Seniority (Pie)</b>',
                    hole=0.4,
                    color_discrete_sequence=vibrant_colors
                )
                fig_seniority_pie.update_layout(
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_seniority_pie, width='stretch')
            
            with col_bar_sen:
                fig_seniority_bar = px.bar(
                    seniority_counts, 
                    x='Conteo', 
                    y='Nivel de Seniority', 
                    orientation='h', 
                    title='<b>Distribución por Seniority (Barras)</b>',
                    color='Conteo',
                    color_continuous_scale=px.colors.sequential.Pinkyl,
                    labels={'Conteo': 'Vacantes', 'Nivel de Seniority': 'Seniority'}
                )
                fig_seniority_bar.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_seniority_bar, width='stretch')
        else:
            st.info("No hay datos de nivel de experiencia disponibles para mostrar.")

    with tab_roles:
        st.subheader("👔 Roles Más Demandados (Tendencias)")
        if not filtered_df_trends.empty and latest_analysis_date:
            demanded_roles_trends = filtered_df_trends[filtered_df_trends['metric_name'] == 'most_demanded_role']
            if not demanded_roles_trends.empty:
                top_roles_data = demanded_roles_trends.sort_values('count', ascending=False).head(15)
                fig_roles = px.bar(
                    top_roles_data, 
                    x='count', 
                    y='metric_value', 
                    orientation='h',
                    title=f'<b>Top Roles Más Demandados</b><br><sub>{latest_analysis_date.strftime("%Y-%m-%d")}</sub>',
                    color='count',
                    color_continuous_scale=px.colors.sequential.Sunset,
                    labels={'count': 'Vacantes', 'metric_value': 'Rol'}
                )
                fig_roles.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_roles, width='stretch')
            else:
                st.info("No hay datos de tendencias de roles demandados. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles o están incompletos. Ejecuta el análisis de tendencias.")

    with tab_skills_demand:
        st.subheader("💡 Habilidades Más Demandadas")
        if not filtered_df_trends.empty and latest_analysis_date:
            demanded_skills_trends = filtered_df_trends[filtered_df_trends['metric_name'] == 'most_demanded_skill']
            if not demanded_skills_trends.empty:
                top_skills_data = demanded_skills_trends.sort_values('count', ascending=False).head(15)
                fig_skills = px.bar(
                    top_skills_data, 
                    x='count', 
                    y='metric_value', 
                    orientation='h',
                    title=f'<b>Top Habilidades Más Demandadas</b><br><sub>{latest_analysis_date.strftime("%Y-%m-%d")}</sub>',
                    color='count',
                    color_continuous_scale=px.colors.sequential.Aggrnyl,
                    labels={'count': 'Vacantes', 'metric_value': 'Habilidad'}
                )
                fig_skills.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_skills, width='stretch')
            else:
                st.info("No hay datos de tendencias de habilidades demandadas. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles o están incompletos. Ejecuta el análisis de tendencias.")

    with tab_skills_growth:
        st.subheader("📈 Habilidades en Crecimiento")
        if not filtered_df_trends.empty and latest_analysis_date:
            growing_skills_trends = filtered_df_trends[filtered_df_trends['metric_name'] == 'growing_skill']
            if not growing_skills_trends.empty:
                top_growing_skills_data = growing_skills_trends.sort_values('count', ascending=False).head(15)
                fig_growing_skills = px.bar(
                    top_growing_skills_data, 
                    x='count', 
                    y='metric_value', 
                    orientation='h',
                    title=f'<b>Top Habilidades en Crecimiento</b><br><sub>{latest_analysis_date.strftime("%Y-%m-%d")}</sub>',
                    color='count',
                    color_continuous_scale=px.colors.sequential.Blugrn,
                    labels={'count': 'Vacantes Actuales', 'metric_value': 'Habilidad'}
                )
                fig_growing_skills.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_growing_skills, width='stretch')
            else:
                st.info("No hay datos de tendencias de habilidades en crecimiento. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles o están incompletos. Ejecuta el análisis de tendencias.")

    with tab_platform_sector:
        st.subheader("🔌 Distribución por Plataforma y Sector")
        if 'source_platform' in filtered_df.columns and 'sector' in filtered_df.columns and not filtered_df.empty:
            platform_sector_counts = filtered_df.groupby(['source_platform', 'sector']).size().reset_index(name='Conteo')
            fig_platform_sector = px.bar(
                platform_sector_counts, 
                x='Conteo', 
                y='sector', 
                color='source_platform',
                title='<b>Vacantes por Plataforma y Sector</b>',
                orientation='h',
                labels={'Conteo': 'Vacantes', 'sector': 'Sector', 'source_platform': 'Plataforma'},
                color_discrete_sequence=vibrant_colors
            )
            fig_platform_sector.update_layout(
                yaxis={'categoryorder':'total ascending'},
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_platform_sector, width='stretch')
        else:
            st.info("No hay datos de plataforma o sector disponibles para mostrar.")

    with tab_source_platform:
        st.subheader("📱 Distribución de Vacantes por Plataforma")
        if 'source_platform' in filtered_df.columns and not filtered_df['source_platform'].empty:
            platform_counts = filtered_df['source_platform'].value_counts().reset_index()
            platform_counts.columns = ['Plataforma', 'Número de Vacantes']
            
            col_pie_plat, col_bar_plat = st.columns(2)
            
            with col_pie_plat:
                fig_platform_pie = px.pie(
                    platform_counts, 
                    values='Número de Vacantes', 
                    names='Plataforma', 
                    title='<b>Distribución por Plataforma (Pie)</b>',
                    hole=0.4,
                    color_discrete_sequence=vibrant_colors
                )
                fig_platform_pie.update_layout(
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_platform_pie, width='stretch')
            
            with col_bar_plat:
                fig_platform_bar = px.bar(
                    platform_counts, 
                    x='Número de Vacantes', 
                    y='Plataforma', 
                    orientation='h', 
                    title='<b>Distribución por Plataforma (Barras)</b>',
                    color='Número de Vacantes',
                    color_continuous_scale=px.colors.sequential.Magenta,
                    labels={'Número de Vacantes': 'Vacantes', 'Plataforma': 'Plataforma'}
                )
                fig_platform_bar.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_platform_bar, width='stretch')
        else:
            st.info("No hay datos de plataforma disponibles para mostrar.")

    with tab_raw_data:
        st.subheader("📋 Datos Crudos de Vacantes")
        display_columns_for_dataframe = [
            'title', 'company_name', 'location', 'country', 'source_platform', 
            'seniority_level', 'role_category', 'sector','salary_range', 
            'posted_date', 'scraped_at', 'source_url', 'skills'
        ]
        
        df_display_raw = filtered_df.copy()
        
        if 'skills' in df_display_raw.columns:
            df_display_raw['skills'] = df_display_raw['skills'].apply(
                lambda x: ", ".join(
                    [s.get('skill_name', str(s)) if isinstance(s, dict) else str(s) 
                     for s in x] if isinstance(x, list) else []
                ) if isinstance(x, list) else ''
            )

        existing_display_columns = [col for col in display_columns_for_dataframe if col in df_display_raw.columns]
        
        st.dataframe(df_display_raw[existing_display_columns], width='stretch')

        st.markdown("---")
        st.subheader("📊 Datos Crudos de Tendencias")
        if not filtered_df_trends.empty:
            st.dataframe(filtered_df_trends, width='stretch')
        else:
            st.info("No hay datos de tendencias disponibles en la base de datos.")

        st.markdown("---")
        st.header("⬇️ Descargar Datos")
        if not filtered_df.empty:
            # ELIMINADO @st.cache_data - función sin decorador
            def convert_df_to_csv(df_to_convert):
                """
                Convierte un DataFrame a CSV sin usar @st.cache_data para evitar problemas
                con tipos de datos no hashable.
                """
                df_export = df_to_convert.copy()
                if 'skills' in df_export.columns:
                    # Convertir lista de skills a string para exportar
                    df_export['skills'] = df_export['skills'].apply(
                        lambda x: ", ".join(
                            [s.get('skill_name', str(s)) if isinstance(s, dict) else str(s) 
                             for s in x] if isinstance(x, list) else []
                        ) if isinstance(x, list) else str(x)
                    )
                return df_export.to_csv(index=False).encode('utf-8')

            csv_file = convert_df_to_csv(filtered_df[existing_display_columns])
            st.download_button(
                label="📥 Descargar datos de Vacantes como CSV",
                data=csv_file,
                file_name="job_market_data.csv",
                mime="text/csv",
                key="download_csv_tab"
            )

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_export_excel = filtered_df[existing_display_columns].copy()
                if 'skills' in df_export_excel.columns:
                    df_export_excel['skills'] = df_export_excel['skills'].apply(
                        lambda x: ", ".join(
                            [s.get('skill_name', str(s)) if isinstance(s, dict) else str(s) 
                             for s in x] if isinstance(x, list) else []
                        ) if isinstance(x, list) else ''
                    )
                df_export_excel.to_excel(writer, index=False, sheet_name='Job Data')
            excel_buffer.seek(0)
            st.download_button(
                label="📥 Descargar datos de Vacantes como Excel",
                data=excel_buffer,
                file_name="job_market_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_tab"
            )
        else:
            st.info("No hay datos de vacantes para descargar.")
        
        if not filtered_df_trends.empty:
            csv_file_trends = filtered_df_trends.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos de Tendencias como CSV",
                data=csv_file_trends,
                file_name="job_trends_data.csv",
                mime="text/csv",
                key="download_csv_trends_tab"
            )