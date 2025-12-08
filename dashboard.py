# FILE: job-market-intelligence/dashboard.py
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
from analysis.trend_analyzer import TrendAnalyzer # Importar TrendAnalyzer
import datetime
from config.geo import COMMON_GEO_DATA
from io import BytesIO

# --- CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📊 LatAm Job Market Intelligence")
st.markdown("Una visión en tiempo real del mercado laboral en Latam y más allá.")

# --- VERIFICACIÓN DE CREDENCIALES ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

with st.container(border=True):
    st.markdown("### 🔑 Estado de Credenciales")
    col_s_1, col_s_2, col_s_3 = st.columns(3)
    with col_s_1:
        if not supabase_url or "TU_PROYECTO" in supabase_url:
            st.error("❌ `SUPABASE_URL` no configurada en `.env` o aún con valor por defecto.")
            st.info("Por favor, edita el archivo `.env` y agrega tus credenciales de Supabase.")
        else:
            st.success("✅ Supabase URL configurada correctamente.")
    with col_s_2:
        if not supabase_key or "TU_PROYECTO" in supabase_key:
            st.error("❌ `SUPABASE_KEY` (Anon) no configurada en `.env` o aún con valor por defecto.")
            st.info("Necesaria para la lectura de datos del dashboard.")
        else:
            st.success("✅ Supabase Anon Key configurada.")
    with col_s_3:
        if not supabase_service_key or "TU_PROYECTO" in supabase_service_key:
            st.error("❌ `SUPABASE_SERVICE_KEY` no configurada en `.env` o aún con valor por defecto.")
            st.info("Necesaria para operaciones de escritura (scraper, limpieza DB).")
        else:
            st.success("✅ Supabase Service Key configurada.")
    
    if not gemini_api_key:
        st.warning("⚠️ `GEMINI_API_KEY` no configurada en `.env`.")
        st.info("Para generar reportes con IA, añade tu clave de Gemini.")
    else:
        st.success("✅ Gemini API configurada.")

# --- SIDEBAR & CONTROLS ---
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

    if st.button("🔄 Ejecutar Scrapers", type="primary", width='stretch', key='run_scraper_btn'):
        if selected_continent_scrape == "Selecciona un Continente":
            st.error("Por favor, selecciona un continente para ejecutar el scraper.")
        elif not selected_spiders_scrape:
            st.error("Por favor, selecciona al menos un scraper para ejecutar.")
        else:
            with st.spinner(f"Extrayendo vacantes ({', '.join(selected_spiders_scrape)})... (Esto puede tardar varios minutos por seguridad)"):
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
                        if "Vacante y habilidades guardadas" in logs:
                            st.info("📊 Nuevos datos guardados en Supabase.")
                        else:
                            st.warning("⚠️ El scraper terminó, pero no se encontraron logs de datos guardados. Revisa los detalles.")
                        
                        with st.expander("Ver Detalles del Proceso"):
                            st.code(logs)
                        
                        time.sleep(1)
                        st.cache_data.clear()
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
    if st.button("✨ Ejecutar Análisis de Tendencias", type="secondary", width='stretch', key='run_trend_analysis_btn'):
        with st.spinner("Analizando tendencias y almacenando en Supabase..."):
            try:
                # Llamar a main.py con el argumento --analyze-trends
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
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al ejecutar el análisis de tendencias.")
                    st.text_area("Log de Error del Análisis", result.stderr, height=200)
            except Exception as e:
                st.error(f"Error ejecutando el análisis de tendencias: {e}")


    st.markdown("---")
    st.subheader("⚠️ Mantenimiento de Datos")

    if st.button("🗑️ Limpiar Base de Datos", type="secondary", width='stretch', key="clear_db_only_btn"):
        st.session_state['confirm_clear_only_db'] = True 

    if 'confirm_clear_only_db' in st.session_state and st.session_state['confirm_clear_only_db']:
        st.warning("¿Estás seguro de que quieres ELIMINAR TODOS los datos de las tablas 'jobs', 'skills', 'companies' y 'trends'? Esta acción es irreversible.")
        st.info("⚠️ Asegúrate de que tu clave de Supabase tenga **permisos de `delete`** y que no haya políticas de RLS que impidan la eliminación.")
        col_confirm_yes_clear, col_confirm_no_clear = st.columns(2)
        if col_confirm_yes_clear.button("Sí, Eliminar Datos", key="confirm_clear_yes_action"):
            db_client_for_clear = SupabaseClient()
            if db_client_for_clear.clear_jobs_table(): # Este método ahora limpia más tablas
                st.success("✅ Base de datos (tablas 'jobs', 'skills', 'companies', 'trends') limpiada exitosamente.")
                st.session_state['confirm_clear_only_db'] = False
                st.cache_data.clear()
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
    
# --- DATA LOADING ---
df = pd.DataFrame()
df_trends = pd.DataFrame()

@st.cache_data(ttl=3600)
def load_data_from_supabase():
    try:
        db = SupabaseClient()
        response_jobs = db.get_jobs(limit=None)
        jobs = response_jobs.data if response_jobs and response_jobs.data else []
        
        response_trends = db.get_trends(limit=None)
        trends_data = response_trends.data if response_trends and response_trends.data else []

        df_loaded_jobs = pd.DataFrame()
        if jobs:
            df_loaded_jobs = pd.DataFrame(jobs)
            date_cols = ['posted_date', 'scraped_at']
            for col in date_cols:
                if col in df_loaded_jobs.columns:
                    temp_series = pd.to_datetime(df_loaded_jobs[col], errors='coerce')
                    if pd.api.types.is_datetime64_any_dtype(temp_series) and temp_series.dt.tz is not None:
                        df_loaded_jobs[col] = temp_series.dt.tz_localize(None)
                    else:
                        df_loaded_jobs[col] = temp_series
            
            if 'scraped_at' in df_loaded_jobs.columns:
                df_loaded_jobs = df_loaded_jobs.sort_values('scraped_at', ascending=False)
            elif 'posted_date' in df_loaded_jobs.columns:
                df_loaded_jobs = df_loaded_jobs.sort_values('posted_date', ascending=False)
            
            if 'sector' in df_loaded_jobs.columns:
                df_loaded_jobs['sector'] = df_loaded_jobs['sector'].apply(lambda x: x if isinstance(x, str) else str(x))
            
            if 'location' in df_loaded_jobs.columns:
                df_loaded_jobs['location'] = df_loaded_jobs['location'].astype(str)

            if 'company_name' in df_loaded_jobs.columns:
                df_loaded_jobs['company_name'] = df_loaded_jobs['company_name'].astype(str)
            else:
                 df_loaded_jobs['company_name'] = "Empresa Desconocida"
        
        df_loaded_trends = pd.DataFrame()
        if trends_data:
            df_loaded_trends = pd.DataFrame(trends_data)
            if 'date' in df_loaded_trends.columns:
                df_loaded_trends['date'] = pd.to_datetime(df_loaded_trends['date'], errors='coerce')
            df_loaded_trends = df_loaded_trends.sort_values('date', ascending=False)


        return df_loaded_jobs, df_loaded_trends
    except Exception as e:
        st.error(f"❌ Error al conectar o cargar datos de Supabase: {e}")
        st.info("Asegúrate de que tus credenciales de Supabase estén correctas y las tablas existan y tengan datos.")
        return pd.DataFrame(), pd.DataFrame()

df, df_trends = load_data_from_supabase()

# --- APLICAR FILTROS (ahora las variables ya están definidas) ---
filtered_df = df.copy()

if not filtered_df.empty:
    if selected_filter_continent != "Todos":
        countries_in_continent = COMMON_GEO_DATA.get(selected_filter_continent, [])
        if 'country' in filtered_df.columns and not filtered_df['country'].empty:
            continent_filter_mask = filtered_df['country'].str.lower().isin([c.lower() for c in countries_in_continent])
            filtered_df = filtered_df[continent_filter_mask]
        else:
            st.warning("La columna 'country' no está disponible en los datos para filtrar por continente.")
        
    if selected_filter_country != "Todos":
        if 'country' in filtered_df.columns and not filtered_df['country'].empty:
            filtered_df = filtered_df[
                filtered_df['country'].str.contains(selected_filter_country, case=False, na=False)
            ]
        else:
            st.warning("La columna 'country' no está disponible en los datos para filtrar por país.")

    if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
        filtered_df = filtered_df[
            (filtered_df['posted_date'].dt.date >= filter_start_date) & 
            (filtered_df['posted_date'].dt.date <= filter_end_date)
        ]

# También filtrar las tendencias si se aplica un filtro de país/continente
filtered_df_trends = df_trends.copy()
if not filtered_df_trends.empty:
    # Filtrar por fecha solo si la métrica de tendencia no es específica de fecha (e.g. "most_demanded_skill" siempre es para un día de análisis)
    # Por ahora, las tendencias están atadas a una `date` específica de análisis.
    # Podríamos filtrar para mostrar solo las tendencias del día más reciente.
    if 'date' in filtered_df_trends.columns and not filtered_df_trends['date'].empty:
        # Mostrar solo las tendencias del día de análisis más reciente para simplificar
        latest_analysis_date = filtered_df_trends['date'].max().date()
        filtered_df_trends = filtered_df_trends[filtered_df_trends['date'].dt.date == latest_analysis_date]


# --- MAIN DASHBOARD CONTENT ---
if filtered_df.empty:
    st.info("La base de datos está vacía o no hay datos que coincidan con los filtros aplicados. Ejecuta los scrapers para obtener datos y refrescar el dashboard.")
else:
    # --- KPIs SECTION ---
    st.markdown("---")
    st.header("📈 Métricas Clave del Mercado Laboral")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        
        total_jobs_count = len(filtered_df)
        col1.metric("Vacantes Filtradas", total_jobs_count)
        col2.metric("Empresas Únicas", filtered_df['company_name'].nunique() if 'company_name' in filtered_df.columns else 0)
        
        most_recent_date_col = None
        if 'scraped_at' in filtered_df.columns and filtered_df['scraped_at'].notna().any():
            col3.metric("Última Actualización de Scraper", filtered_df['scraped_at'].max().strftime("%Y-%m-%d %H:%M"))
        elif 'posted_date' in filtered_df.columns and filtered_df['posted_date'].notna().any():
            col3.metric("Última Publicación de Vacante", filtered_df['posted_date'].max().strftime("%Y-%m-%d"))
        else:
            col3.metric("Última Actualización", "N/A")

        new_jobs_today = 0
        if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
            today_date = datetime.date.today()
            new_jobs_today = filtered_df[filtered_df['posted_date'].dt.date == today_date].shape[0]
        col4.metric("Nuevas Vacantes (Hoy)", new_jobs_today)

    # --- GENERADOR DE REPORTES CON IA ---
    st.markdown("---")
    st.header("🧠 Reporte de Inteligencia Artificial")
    with st.expander("Generar y ver Reporte Diario de IA"):
        st.write("Genera un resumen ejecutivo de las tendencias actuales basándose en los datos filtrados.")
        
        report_generator = None
        if gemini_api_key:
            report_generator = ReportGenerator()
        
        if not gemini_api_key:
            st.warning("⚠️ La API de Gemini no está configurada. El reporte de IA no puede ser generado.")
        elif st.button("Generar Reporte de IA", key="generate_ai_report_btn"):
            if report_generator and report_generator.model:
                with st.spinner("Generando reporte de IA..."):
                    if len(filtered_df) > 50:
                        sample_jobs = filtered_df[['title', 'company_name', 'sector', 'location']].sample(50).to_dict('records')
                    else:
                        sample_jobs = filtered_df[['title', 'company_name', 'sector', 'location']].to_dict('records')

                    cleaned_sample_jobs = []
                    for job in sample_jobs:
                        cleaned_sample_jobs.append({
                            'title': job.get('title'),
                            'company': job.get('company_name'),
                            'sector': job.get('sector'),
                            'location': job.get('location')
                        })

                    ai_report = report_generator.generate_daily_insight(cleaned_sample_jobs)
                    st.markdown(ai_report)
            else:
                st.error("Error al inicializar el generador de reportes de IA. Revisa tu clave API o la inicialización del modelo.")
        else:
            st.info("Haz clic en el botón para generar un reporte con IA de los datos actuales.")
    
    # --- VISUALIZACIONES (GRÁFICOS) ---
    st.markdown("---")
    st.header("📊 Análisis de Tendencias y Distribución")

    tab_sector, tab_company, tab_location, tab_date, tab_skills, tab_roles, tab_growing_skills, tab_raw_data = st.tabs([
        "Vacantes por Sector", 
        "Vacantes por Empresa", 
        "Vacantes por Ubicación", 
        "Vacantes por Fecha",
        "Habilidades Demandadas", # Nueva pestaña
        "Roles Demandados",      # Nueva pestaña
        "Habilidades en Crecimiento", # Nueva pestaña
        "Datos Crudos"
    ])

    with tab_sector:
        st.subheader("Distribución de Vacantes por Sector")
        if 'sector' in filtered_df.columns and not filtered_df['sector'].empty:
            sector_counts = filtered_df['sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Número de Vacantes']
            fig_sector = px.bar(sector_counts, x='Número de Vacantes', y='Sector', orientation='h', 
                                title='Top Sectores con Vacantes', color='Número de Vacantes',
                                color_continuous_scale=px.colors.sequential.Plasma)
            fig_sector.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_sector, width='stretch')
        else:
            st.info("No hay datos de sector disponibles para mostrar.")

    with tab_company:
        st.subheader("Top Empresas con Vacantes")
        if 'company_name' in filtered_df.columns and not filtered_df['company_name'].empty: 
            top_n_companies = st.slider("Top N Compañías", 5, 20, 10, key="top_companies_slider_tab")
            company_counts = filtered_df['company_name'].value_counts().head(top_n_companies).reset_index()
            company_counts.columns = ['Empresa', 'Número de Vacantes']
            fig_company = px.bar(company_counts, x='Número de Vacantes', y='Empresa', orientation='h', 
                                 title=f'Top {top_n_companies} Compañías Contratando', color='Número de Vacantes',
                                 color_continuous_scale=px.colors.sequential.Viridis)
            fig_company.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_company, width='stretch')
        else:
            st.info("No hay datos de empresa disponibles para mostrar.")

    with tab_location:
        st.subheader("Distribución de Vacantes por Ubicación")
        if 'country' in filtered_df.columns and not filtered_df['country'].empty:
            location_counts = filtered_df['country'].value_counts().reset_index()
            location_counts.columns = ['Ubicación', 'Número de Vacantes']
            fig_location = px.pie(location_counts.head(10), values='Número de Vacantes', names='Ubicación', 
                                  title='Top 10 Países/Ubicaciones con más Vacantes',
                                  hole=0.3)
            st.plotly_chart(fig_location, width='stretch')
        elif 'location' in filtered_df.columns and not filtered_df['location'].empty:
            location_counts = filtered_df['location'].value_counts().reset_index()
            location_counts.columns = ['Ubicación', 'Número de Vacantes']
            fig_location = px.pie(location_counts.head(10), values='Número de Vacantes', names='Ubicación', 
                                  title='Top 10 Ubicaciones con más Vacantes',
                                  hole=0.3)
            st.plotly_chart(fig_location, width='stretch')
        else:
            st.info("No hay datos de ubicación disponibles para mostrar.")

    with tab_date:
        st.subheader("Tendencia de Vacantes por Fecha de Publicación")
        if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
            daily_posts = filtered_df.copy()
            daily_posts['posted_date'] = pd.to_datetime(daily_posts['posted_date']).dt.date
            daily_counts = daily_posts['posted_date'].value_counts().sort_index().reset_index(name='Número de Vacantes')
            daily_counts.columns = ['Fecha de Publicación', 'Número de Vacantes']
            
            fig_time = px.line(daily_counts, x='Fecha de Publicación', y='Número de Vacantes', 
                               title='Vacantes Publicadas a lo largo del Tiempo')
            st.plotly_chart(fig_time, width='stretch')
        else:
            st.info("No hay datos de fecha de publicación disponibles para mostrar tendencias.")

    with tab_skills: # Nueva pestaña para habilidades demandadas
        st.subheader("Habilidades Más Demandadas (Basado en el último análisis)")
        if not filtered_df_trends.empty:
            most_demanded_skills_df = filtered_df_trends[filtered_df_trends['metric_name'] == 'most_demanded_skill'].sort_values('count', ascending=False)
            if not most_demanded_skills_df.empty:
                fig_demanded_skills = px.bar(most_demanded_skills_df.head(15), x='count', y='metric_value', orientation='h',
                                            title='Top 15 Habilidades Más Demandadas', color='count',
                                            labels={'count': 'Número de Vacantes', 'metric_value': 'Habilidad'},
                                            color_continuous_scale=px.colors.sequential.Blues)
                fig_demanded_skills.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_demanded_skills, width='stretch')
            else:
                st.info("No hay datos de tendencias de habilidades demandadas. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles. Ejecuta el análisis de tendencias.")

    with tab_growing_skills: # Nueva pestaña para habilidades en crecimiento
        st.subheader("Habilidades en Crecimiento (Basado en el último análisis)")
        if not filtered_df_trends.empty:
            growing_skills_df = filtered_df_trends[filtered_df_trends['metric_name'] == 'growing_skill'].sort_values('count', ascending=False)
            if not growing_skills_df.empty:
                fig_growing_skills = px.bar(growing_skills_df.head(15), x='count', y='metric_value', orientation='h',
                                            title='Top 15 Habilidades en Crecimiento (Último Mes vs. Anterior)', color='count',
                                            labels={'count': 'Vacantes Actuales', 'metric_value': 'Habilidad (Tasa de Crecimiento)'},
                                            color_continuous_scale=px.colors.sequential.Greens)
                fig_growing_skills.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_growing_skills, width='stretch')
            else:
                st.info("No hay datos de tendencias de habilidades en crecimiento. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles. Ejecuta el análisis de tendencias.")

    with tab_roles: # Nueva pestaña para roles demandados
        st.subheader("Roles Más Demandados (Basado en el último análisis)")
        if not filtered_df_trends.empty:
            most_demanded_roles_df = filtered_df_trends[filtered_df_trends['metric_name'] == 'most_demanded_role'].sort_values('count', ascending=False)
            if not most_demanded_roles_df.empty:
                fig_demanded_roles = px.bar(most_demanded_roles_df.head(15), x='count', y='metric_value', orientation='h',
                                            title='Top 15 Roles Más Demandados', color='count',
                                            labels={'count': 'Número de Vacantes', 'metric_value': 'Rol'},
                                            color_continuous_scale=px.colors.sequential.Oranges)
                fig_demanded_roles.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_demanded_roles, width='stretch')
            else:
                st.info("No hay datos de tendencias de roles demandados. Ejecuta el análisis de tendencias.")
        else:
            st.info("No hay datos de tendencias disponibles. Ejecuta el análisis de tendencias.")

    with tab_raw_data:
        st.subheader("Datos Crudos de Vacantes")
        display_columns_for_dataframe = ['job_id', 'title', 'company_name', 'location', 'country', 'job_type', 
                                         'seniority_level', 'sector', 'posted_date', 'source_platform', 'source_url', 'scraped_at']
        
        existing_display_columns = [col for col in display_columns_for_dataframe if col in filtered_df.columns]
        
        st.dataframe(filtered_df[existing_display_columns], width='stretch')

        st.markdown("---")
        st.subheader("Datos Crudos de Tendencias")
        if not filtered_df_trends.empty:
            st.dataframe(filtered_df_trends, width='stretch')
        else:
            st.info("No hay datos de tendencias disponibles en la base de datos.")


        st.markdown("---")
        st.header("⬇️ Descargar Datos")
        if not filtered_df.empty:
            csv_file = filtered_df[existing_display_columns].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos de Vacantes como CSV",
                data=csv_file,
                file_name="job_market_data.csv",
                mime="text/csv",
                key="download_csv_tab"
            )

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                filtered_df[existing_display_columns].to_excel(writer, index=False, sheet_name='Job Data')
            excel_buffer.seek(0)
            st.download_button(
                label="Descargar datos de Vacantes como Excel",
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
                label="Descargar datos de Tendencias como CSV",
                data=csv_file_trends,
                file_name="job_trends_data.csv",
                mime="text/csv",
                key="download_csv_trends_tab"
            )