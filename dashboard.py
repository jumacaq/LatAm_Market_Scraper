import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import time
import logging
from dotenv import load_dotenv
from database.supabase_client import SupabaseClient
from analysis.trend_analyzer import TrendAnalyzer
from analysis.report_generator import ReportGenerator

# Configurar logs
logging.basicConfig(level=logging.INFO)

# Cargar variables de entorno
load_dotenv()

st.set_page_config(page_title="Market Intelligence", layout="wide")

st.title("🚀 Job Market Intelligence Dashboard")

# --- VERIFICACIÓN DE CREDENCIALES ---
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")

if "PON_TU_URL_AQUI" in supabase_url or not supabase_url or "PON_TU_ANON_KEY_AQUI" in supabase_key:
    st.error("🚨 CONFIGURACIÓN INCOMPLETA")
    st.markdown("""
    **No has configurado tus credenciales de Supabase en el archivo `.env`**.
    
    El dashboard no puede conectarse a la base de datos.
    
    1. Abre el archivo `.env` en la carpeta del proyecto.
    2. Reemplaza `PON_TU_URL_AQUI` con tu URL de Supabase.
    3. Reemplaza `PON_TU_KEY_AQUI` con tu Key Anon/Public.
    4. Reinicia este dashboard.
    """)
    st.stop()

# --- SIDEBAR & CONTROLS ---
st.sidebar.header("Control Panel")

# Botón para ejecutar Scraper desde la UI
st.sidebar.subheader("⚡ Acciones")
if st.sidebar.button("🔄 Ejecutar Scraper Ahora", type="primary"):
    with st.spinner("Scraping LinkedIn, Computrabajo & Multitrabajo..."):
        try:
            # Ejecuta el script principal como un subproceso
            # Pasamos el entorno actual para asegurar que .env se lea correctamente
            env = os.environ.copy()
            result = subprocess.run(["python", "main.py", "scrape"], capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                st.sidebar.success("✅ Scraping finalizado")
                # Análisis simple de logs para feedback inmediato
                if "Saved to DB" in result.stderr:
                    st.sidebar.info("📊 Se guardaron nuevos datos.")
                
                with st.expander("Ver Logs del Scraper"):
                    st.code(result.stderr)
                    
                time.sleep(1)
                st.rerun()
            else:
                st.sidebar.error("❌ Error en el scraping")
                st.sidebar.text_area("Error Log", result.stderr, height=200)
        except Exception as e:
            st.sidebar.error(f"Error ejecutando script: {e}")

# Botón de Diagnóstico
if st.sidebar.button("🛠️ Ejecutar Diagnóstico", help="Prueba la conexión y escritura a la BD"):
    st.sidebar.info("Iniciando prueba de conexión...")
    try:
        db_test = SupabaseClient()
        test_data = {
            "title": "TEST CONNECTION ROW",
            "company": "TEST",
            "url": f"https://test.com/{int(time.time())}",
            "sector": "TEST"
        }
        res = db_test.upsert_job(test_data)
        st.sidebar.success("✅ ¡Conexión Exitosa! La base de datos acepta escritura.")
        st.sidebar.json(res.data if res.data else "OK (Sin datos de retorno)")
    except Exception as e:
        st.sidebar.error("❌ PRUEBA FALLIDA")
        err_msg = str(e)
        st.sidebar.code(err_msg)
        if "401" in err_msg:
            st.sidebar.warning("Tu SUPABASE_KEY es incorrecta o ha expirado.")
        elif "policy" in err_msg or "permission" in err_msg:
            st.sidebar.warning("⚠️ PROBLEMA DE PERMISOS (RLS). Ejecuta el SQL para desactivar RLS.")
        elif "not found" in err_msg:
            st.sidebar.warning("La URL es incorrecta o la tabla 'jobs' no existe.")

sector = st.sidebar.multiselect("Filtrar por Sector", ["EdTech", "Fintech", "Future of Work"], default=["EdTech", "Fintech", "Future of Work"])

# --- DATA LOADING ---
try:
    db = SupabaseClient()
    
    # Consulta directa con manejo de errores explícito
    try:
        response = db.get_jobs(limit=200)
        jobs_data = response.data if response else []
    except Exception as e:
        st.error(f"❌ Error crítico al leer de Supabase: {e}")
        jobs_data = []

    if jobs_data:
        df = pd.DataFrame(jobs_data)
        
        st.success(f"🟢 Conectado a: {supabase_url}")

        # KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vacantes", len(df))
        col2.metric("Fuentes", f"{df['source'].nunique()} Sitios")
        date_col = 'created_at' if 'created_at' in df.columns else 'posted_date'
        col3.metric("Última Actualización", df[date_col].max()[:10] if date_col in df.columns else "N/A")

        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Distribución por Sector")
            if 'sector' in df.columns:
                sector_counts = df['sector'].value_counts().reset_index()
                sector_counts.columns = ['sector', 'count']
                fig = px.pie(sector_counts, names='sector', values='count', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            st.subheader("Distribución por Fuente")
            if 'source' in df.columns:
                source_counts = df['source'].value_counts().reset_index()
                source_counts.columns = ['source', 'count']
                fig2 = px.bar(source_counts, x='count', y='source', orientation='h')
                st.plotly_chart(fig2, use_container_width=True)

        # Data Table
        st.subheader("📋 Detalle de Vacantes Recientes")
        display_cols = [c for c in ['title', 'company', 'location', 'sector', 'source', 'posted_date'] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        
    else:
        st.warning("⚠️ Conexión establecida, pero la tabla 'jobs' está vacía.")
        st.info("Presiona '🔄 Ejecutar Scraper Ahora' en la barra lateral.")

except Exception as e:
    st.error(f"Error General: {e}")

# --- AI REPORT SECTION ---
st.divider()
st.subheader("🤖 AI Insights")

if st.button("Generar Reporte de Mercado"):
    if not jobs_data:
        st.error("Necesitamos datos para generar un reporte. Ejecuta el scraper primero.")
    else:
        with st.spinner("Analizando tendencias con Inteligencia Artificial..."):
            try:
                report_gen = ReportGenerator()
                insight = report_gen.generate_daily_insight(jobs_data[:15])
                st.markdown(insight)
            except Exception as e:
                st.error(f"Error generando reporte: {e}")
