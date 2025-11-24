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
import datetime
from config.geo import COMMON_GEO_DATA
from io import BytesIO # Importar BytesIO para manejar archivos en memoria

# --- CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📊 LinkedIn Market Intelligence")
st.markdown("Una visión en tiempo real del mercado laboral en Latam y más allá.")

# --- VERIFICACIÓN DE CREDENCIALES ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

with st.container(border=True):
    st.markdown("### 🔑 Estado de Credenciales")
    col_s_1, col_s_2 = st.columns(2)
    with col_s_1:
        if not supabase_url or "TU_PROYECTO" in supabase_url:
            st.error("❌ `SUPABASE_URL` no configurada en `.env` o aún con valor por defecto.")
            st.info("Por favor, edita el archivo `.env` y agrega tus credenciales de Supabase.")
        else:
            st.success("✅ Supabase configurado correctamente.")
    with col_s_2:
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
    
    # Continente
    continents = ["Selecciona un Continente"] + list(COMMON_GEO_DATA.keys())
    selected_continent_scrape = st.selectbox("Continente para Scrapear", continents, key="scrape_continent")
    
    # País
    countries_for_scrape = []
    if selected_continent_scrape != "Selecciona un Continente":
        countries_for_scrape = ["Todos los Países"] + COMMON_GEO_DATA[selected_continent_scrape]
    selected_country_scrape = st.selectbox("País para Scrapear", countries_for_scrape, key="scrape_country")
    
    # Fechas
    today = datetime.date.today()
    default_start_date_scrape = today - datetime.timedelta(days=7) # Last 7 days
    start_date_scrape = st.date_input("Fecha de Inicio de Vacantes", value=default_start_date_scrape, key="scrape_start_date")
    end_date_scrape = st.date_input("Fecha de Fin de Vacantes", value=today, key="scrape_end_date")

    # --- Función para ejecutar el scraper con argumentos ---
    def execute_scraper(continent, country, start_date, end_date):
        env = os.environ.copy()
        
        cmd = ["python", "main.py"]
        
        continent_arg = str(continent).strip() if continent is not None else ""
        country_arg = str(country).strip() if country is not None else ""
        start_date_arg = start_date.strftime("%Y-%m-%d") if start_date is not None else ""
        end_date_arg = end_date.strftime("%Y-%m-%d") if end_date is not None else ""

        # Pasar siempre el continente si ha sido seleccionado, 
        # incluso si el país es "Todos los Países"
        if continent_arg and continent_arg != "Selecciona un Continente":
            cmd.extend(["--continent", continent_arg])
        
        # Pasar el país si ha sido seleccionado (puede ser "Todos los Países")
        if country_arg: # No verificamos si es "Todos los Países" aquí, lo maneja main.py
            cmd.extend(["--country", country_arg])
        
        if start_date_arg:
            cmd.extend(["--start_date", start_date_arg])
        
        if end_date_arg:
            cmd.extend(["--end_date", end_date_arg])
        
        logging.info(f"Comando subprocess a ejecutar: {cmd}") # Imprimir el comando para depuración

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False
        )
        return result

    # Botón de ejecutar scraper (separado del borrado)
    if st.button("🔄 Ejecutar LinkedIn Scraper", type="primary", width='stretch', key='run_scraper_btn'):
        if selected_continent_scrape == "Selecciona un Continente":
            st.error("Por favor, selecciona un continente para ejecutar el scraper.")
        else:
            with st.spinner("Extrayendo vacantes de LinkedIn... (Esto puede tardar varios minutos por seguridad)"):
                try:
                    result = execute_scraper(selected_continent_scrape, selected_country_scrape, start_date_scrape, end_date_scrape)
                    
                    if result.returncode == 0:
                        st.success("✅ Proceso de scraping finalizado")
                        logs = result.stderr + "\n" + result.stdout
                        if "Saved to DB" in logs:
                            st.info("📊 Nuevos datos guardados en Supabase.")
                        
                        with st.expander("Ver Detalles del Proceso"):
                            st.code(logs)
                        
                        time.sleep(1)
                        st.cache_data.clear() # Limpiar cache para forzar la recarga de datos
                        st.rerun()
                    else:
                        st.error("❌ Error en el proceso de scraping")
                        st.text_area("Log de Error", result.stderr + "\n" + result.stdout, height=200)
                except Exception as e:
                    st.error(f"Error ejecutando el scraper: {e}")

    st.markdown("---")
    st.subheader("⚠️ Mantenimiento de Datos")

    # NUEVO: Botón para limpiar solo la DB
    if st.button("🗑️ Limpiar Base de Datos", type="secondary", width='stretch', key="clear_db_only_btn"):
        # Usar session_state para mantener el estado de confirmación
        st.session_state['confirm_clear_only_db'] = True 

    # Lógica de confirmación para limpiar la DB
    if 'confirm_clear_only_db' in st.session_state and st.session_state['confirm_clear_only_db']:
        st.warning("¿Estás seguro de que quieres ELIMINAR TODOS los datos de la base de datos? Esta acción es irreversible.")
        st.info("⚠️ Asegúrate de que tu clave de Supabase tenga **permisos de `delete`** y que no haya políticas de RLS que impidan la eliminación.")
        col_confirm_yes_clear, col_confirm_no_clear = st.columns(2)
        if col_confirm_yes_clear.button("Sí, Eliminar Datos", key="confirm_clear_yes_action"):
            db_client_for_clear = SupabaseClient() # Instanciar cliente DB para limpiar
            if db_client_for_clear.clear_jobs_table():
                st.success("✅ Base de datos limpiada exitosamente.")
                st.session_state['confirm_clear_only_db'] = False # Reset confirmation
                st.cache_data.clear() # Limpiar cache para reflejar DB vacía
                time.sleep(1) # Pequeño delay para que el mensaje sea visible
                st.rerun()
            else:
                st.error("❌ No se pudo limpiar la base de datos. Por favor, revisa los logs y los permisos de Supabase.")
                st.session_state['confirm_clear_only_db'] = False # Reset confirmation
                time.sleep(1) # Pequeño delay para que el mensaje sea visible
                st.rerun()
        if col_confirm_no_clear.button("No, Cancelar", key="confirm_clear_no_action"):
            st.info("Acción cancelada.")
            st.session_state['confirm_clear_only_db'] = False # Reset confirmation
            st.rerun() # Refresh to remove confirmation message

# --- FILTROS DEL DASHBOARD ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros de Visualización")

# Filtro por Continente
filter_continents = ["Todos"] + list(COMMON_GEO_DATA.keys())
selected_filter_continent = st.sidebar.selectbox("Filtrar por Continente", filter_continents, key="filter_continent")

# Filtro por País (dependiente del continente seleccionado)
filter_countries = ["Todos"]
if selected_filter_continent != "Todos":
    filter_countries.extend(COMMON_GEO_DATA[selected_filter_continent])
selected_filter_country = st.sidebar.selectbox("Filtrar por País", filter_countries, key="filter_country")

# Filtro por Rango de Fechas
st.sidebar.markdown("---")
st.sidebar.subheader("Rango de Fechas")
min_date_available = datetime.date(2023, 1, 1) # Arbitrary minimum date for the picker
max_date_available = datetime.date.today()

filter_start_date = st.sidebar.date_input("Desde:", value=min_date_available, min_value=min_date_available, max_value=max_date_available, key="filter_start_date")
filter_end_date = st.sidebar.date_input("Hasta:", value=max_date_available, min_value=min_date_available, max_value=max_date_available, key="filter_end_date")

# Asegurarse de que la fecha de inicio no sea posterior a la fecha de fin
if filter_start_date > filter_end_date:
    st.sidebar.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
    # No se detiene la ejecución, pero el filtro no funcionará correctamente hasta que se corrija.


# --- DATA LOADING ---
jobs_data = []
df = pd.DataFrame() # Initialize empty DataFrame

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data_from_supabase():
    try:
        db = SupabaseClient()
        response = db.get_jobs(limit=100000) # Increased limit to 100,000 for "more than 10000"
        jobs = response.data if response and response.data else []
        if jobs:
            df_loaded = pd.DataFrame(jobs)
            
            # --- MANEJO ROBUSTO DE FECHAS: Convertir a datetime y luego asegurar timezone-naive ---
            date_cols = ['posted_date', 'created_at']
            for col in date_cols:
                if col in df_loaded.columns:
                    temp_series = pd.to_datetime(df_loaded[col], errors='coerce')
                    
                    # Si la serie es de tipo datetime y tiene una zona horaria, la quitamos
                    if pd.api.types.is_datetime64_any_dtype(temp_series) and temp_series.dt.tz is not None:
                        df_loaded[col] = temp_series.dt.tz_localize(None)
                    else:
                        df_loaded[col] = temp_series
            # ------------------------------------------------------------------------------------
            
            # Sort by the most recent date available
            if 'created_at' in df_loaded.columns:
                df_loaded = df_loaded.sort_values('created_at', ascending=False)
            elif 'posted_date' in df_loaded.columns:
                df_loaded = df_loaded.sort_values('posted_date', ascending=False)
            
            # Clean 'sector' for consistency (assuming it's a string, if it comes as list etc.)
            if 'sector' in df_loaded.columns:
                df_loaded['sector'] = df_loaded['sector'].apply(lambda x: x if isinstance(x, str) else str(x))
            
            # Ensure 'location' is a string for filtering
            if 'location' in df_loaded.columns:
                df_loaded['location'] = df_loaded['location'].astype(str)

            # Ensure 'company' is a string for filtering and nunique()
            if 'company' in df_loaded.columns:
                df_loaded['company'] = df_loaded['company'].astype(str)

            return df_loaded
        return pd.DataFrame() # Return empty DataFrame if no data
    except Exception as e:
        st.error(f"❌ Error al conectar o cargar datos de Supabase: {e}")
        st.info("Asegúrate de que tus credenciales de Supabase estén correctas y la tabla `jobs` exista y tenga datos.")
        return pd.DataFrame()

df = load_data_from_supabase()

# --- APLICAR FILTROS ---
filtered_df = df.copy()

if not filtered_df.empty:
    # Filter by Continent
    if selected_filter_continent != "Todos":
        countries_in_continent = COMMON_GEO_DATA[selected_filter_continent]
        continent_filter_mask = filtered_df['location'].apply(
            lambda x: any(country.lower() in x.lower() for country in countries_in_continent)
        )
        filtered_df = filtered_df[continent_filter_mask]
        
    # Filter by Country
    if selected_filter_country != "Todos":
        filtered_df = filtered_df[
            filtered_df['location'].str.contains(selected_filter_country, case=False, na=False)
        ]

    # Filter by Date Range
    if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
        # La columna 'posted_date' ya debe ser timezone-naive debido al procesamiento en `load_data_from_supabase`
        # Solo necesitamos comparar las partes de la fecha.
        filtered_df = filtered_df[
            (filtered_df['posted_date'].dt.date >= filter_start_date) & 
            (filtered_df['posted_date'].dt.date <= filter_end_date)
        ]


# --- MAIN DASHBOARD CONTENT ---
if filtered_df.empty:
    st.info("La base de datos está vacía o no hay datos que coincidan con los filtros aplicados. Ejecuta el scraper para obtener datos de LinkedIn y refrescar el dashboard.")
else:
    # --- KPIs SECTION ---
    st.markdown("---")
    st.header("📈 Métricas Clave del Mercado Laboral")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        
        total_jobs_count = len(filtered_df)
        col1.metric("Vacantes Filtradas", total_jobs_count)
        col2.metric("Empresas Únicas", filtered_df['company'].nunique() if 'company' in filtered_df.columns else 0)
        
        most_recent_date_col = None
        if 'posted_date' in filtered_df.columns and filtered_df['posted_date'].notna().any():
            most_recent_date_col = 'posted_date'
        elif 'created_at' in filtered_df.columns and filtered_df['created_at'].notna().any():
            most_recent_date_col = 'created_at'
        
        if most_recent_date_col:
            col3.metric("Última Actualización de Vacante", filtered_df[most_recent_date_col].max().strftime("%Y-%m-%d"))
        else:
            col3.metric("Última Actualización de Vacante", "N/A")

        # MODIFICACIÓN: Cálculo de "Nuevas Vacantes (Hoy)" usando 'posted_date'
        new_jobs_today = 0
        if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
            today_date = datetime.date.today()
            # Aseguramos que 'posted_date' es timezone-naive y comparamos solo la fecha
            new_jobs_today = filtered_df[filtered_df['posted_date'].dt.date == today_date].shape[0]
        col4.metric("Nuevas Vacantes (Hoy)", new_jobs_today) # Muestra la métrica corregida

    # --- GENERADOR DE REPORTES CON IA ---
    st.markdown("---")
    st.header("🧠 Reporte de Inteligencia Artificial")
    with st.expander("Generar y ver Reporte Diario de IA"):
        report_generator = ReportGenerator()
        if st.button("Generar Reporte con IA"):
            if report_generator.model: # Verifica si el modelo de Gemini está configurado
                with st.spinner("Generando reporte con Gemini..."):
                    # Para evitar exceder los límites de tokens, se pasa una muestra de los datos
                    sample_jobs = filtered_df.head(50).to_dict(orient='records') # Limitar a 50 registros para el prompt
                    ai_report = report_generator.generate_daily_insight(sample_jobs)
                    st.markdown(ai_report)
            else:
                st.warning("⚠️ `GEMINI_API_KEY` no configurada. No se puede generar el reporte con IA.")
    
    # --- VISUALIZACIONES (GRÁFICOS) ---
    st.markdown("---")
    st.header("📊 Análisis de Tendencias y Distribución")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Vacantes por Sector", "Vacantes por Empresa", "Vacantes por Ubicación", "Vacantes por Fecha", "Datos Crudos"])

    with tab1:
        st.subheader("Distribución de Vacantes por Sector")
        if 'sector' in filtered_df.columns and not filtered_df['sector'].empty:
            sector_counts = filtered_df['sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Número de Vacantes']
            fig_sector = px.bar(sector_counts, x='Número de Vacantes', y='Sector', orientation='h', 
                                title='Top Sectores con Vacantes', color='Número de Vacantes',
                                color_continuous_scale=px.colors.sequential.Plasma)
            fig_sector.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_sector, use_container_width=True)
        else:
            st.info("No hay datos de sector disponibles para mostrar.")

    with tab2:
        st.subheader("Top Empresas con Vacantes")
        if 'company' in filtered_df.columns and not filtered_df['company'].empty:
            company_counts = filtered_df['company'].value_counts().reset_index()
            company_counts.columns = ['Empresa', 'Número de Vacantes']
            fig_company = px.bar(company_counts.head(15), x='Número de Vacantes', y='Empresa', orientation='h', 
                                 title='Top 15 Empresas Contratando', color='Número de Vacantes',
                                 color_continuous_scale=px.colors.sequential.Viridis)
            fig_company.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_company, use_container_width=True)
        else:
            st.info("No hay datos de empresa disponibles para mostrar.")

    with tab3:
        st.subheader("Distribución de Vacantes por Ubicación")
        if 'location' in filtered_df.columns and not filtered_df['location'].empty:
            location_counts = filtered_df['location'].value_counts().reset_index()
            location_counts.columns = ['Ubicación', 'Número de Vacantes']
            fig_location = px.pie(location_counts.head(10), values='Número de Vacantes', names='Ubicación', 
                                  title='Top 10 Ubicaciones con más Vacantes',
                                  hole=0.3)
            st.plotly_chart(fig_location, use_container_width=True)
        else:
            st.info("No hay datos de ubicación disponibles para mostrar.")

    with tab4:
        st.subheader("Tendencia de Vacantes por Fecha de Publicación")
        if 'posted_date' in filtered_df.columns and not filtered_df['posted_date'].empty:
            # Agrupar por fecha de publicación y contar
            daily_counts = filtered_df.groupby(filtered_df['posted_date'].dt.date).size().reset_index(name='Número de Vacantes')
            daily_counts.columns = ['Fecha de Publicación', 'Número de Vacantes']
            
            fig_time = px.line(daily_counts, x='Fecha de Publicación', y='Número de Vacantes', 
                               title='Vacantes Publicadas a lo largo del Tiempo')
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No hay datos de fecha de publicación disponibles para mostrar tendencias.")

    with tab5:
        st.subheader("Datos Crudos de Vacantes")
        st.dataframe(filtered_df[['title', 'company', 'location', 'sector', 'posted_date', 'url']], use_container_width=True)

        # --- Descarga de Datos (Ahora dentro de la pestaña de Datos Crudos, para mayor coherencia) ---
        st.markdown("---")
        st.header("⬇️ Descargar Datos")
        if not filtered_df.empty:
            # Para CSV
            csv_file = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos como CSV",
                data=csv_file,
                file_name="job_market_data.csv",
                mime="text/csv",
                key="download_csv"
            )

            # Para Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Incluye solo las columnas deseadas para la descarga, si prefieres no todas
                filtered_df[['title', 'company', 'location', 'sector', 'posted_date', 'url']].to_excel(writer, index=False, sheet_name='Job Data')
            excel_buffer.seek(0) # Rebobinar el buffer al inicio
            st.download_button(
                label="Descargar datos como Excel",
                data=excel_buffer,
                file_name="job_market_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
        else:
            st.info("No hay datos para descargar.")