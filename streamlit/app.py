# streamlit_dashboard/app.py

import streamlit as st
import pandas as pd
import altair as alt

import os
import re
from typing import List, Dict, Any, Optional
from pandas import DataFrame

# --- CONFIGURACIÓN Y CARGA DE DATOS ---

# Ruta al archivo consolidado final generado por main.py
DATA_PATH = "market_data_final_linkedin.csv" 

st.set_page_config(
    page_title="Job Market Intelligence Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data(path: str) -> DataFrame:
    """Carga, limpia y prepara los datos para el análisis, asegurando la compatibilidad con el ETL."""
    if not os.path.exists(path):
        st.error(f"❌ ERROR: Archivo de datos no encontrado en la ruta: {path}. ¡Asegúrate de que el proceso de scraping finalizó!")
        return pd.DataFrame()
        
    df = pd.read_csv(path)
    
    # --- CRITICAL FIXES FOR COMPATIBILITY (ESTANDARIZACIÓN) ---
    # Aseguramos que las columnas de salida del ETL existan y manejen NaNs.
    
    # Seniority Level
    if 'seniority_level' not in df.columns:
        df['seniority_level'] = 'Sin Nivel Específico' 
    else:
        df['seniority_level'] = df['seniority_level'].fillna('Sin Nivel Específico')
    
    # Sector
    if 'sector' not in df.columns:
        df['sector'] = 'Indefinido'
    else:
        df['sector'] = df['sector'].fillna('Indefinido')
    
    # Skills (Maneja el caso donde la columna es [[]] o falta)
    if 'skills' not in df.columns:
        df['skills'] = [[] for _ in range(len(df))]
    
    # Limpieza de habilidades (convertir string de lista a lista de Python)
    def clean_skills(s):
        if pd.isna(s) or str(s) in ('[]', 'None', 'nan', 'Sin Nivel Específico'):
            return []
        if isinstance(s, str):
            # Limpiamos corchetes, comillas y espacios para obtener una lista limpia
            s = re.sub(r"[\[\]'\" ]", '', s) 
            return [skill.strip() for skill in s.split(',') if skill.strip()]
        return []

    df['skills'] = df['skills'].apply(clean_skills)
    
    return df

def generate_executive_summary(df_filtered: DataFrame) -> str:
    """Genera un resumen ejecutivo de las principales tendencias del dataset."""
    
    total_jobs = len(df_filtered)
    if total_jobs == 0:
        return "⚠️ No hay datos filtrados para generar el resumen."

    # 1. Roles más demandados (Top 3 Títulos)
    top_roles = df_filtered['title'].value_counts().head(3).index.tolist()
    
    # 2. Empresas contratando activamente (Top 3 Compañías)
    top_companies = df_filtered['company_name'].value_counts().head(3).index.tolist()
    
    # 3. Tendencias por sector (Top 3 Sectores, excluyendo 'Tecnología', 'Other' y 'Indefinido')
    sector_counts = df_filtered[~df_filtered['sector'].isin(['Tecnología', 'Other', 'Indefinido'])]
    top_sectors = sector_counts['sector'].value_counts().head(3).index.tolist()
    
    # Construcción del Markdown
    summary_markdown = "## 📊 Resumen Ejecutivo del Mercado Laboral\n"
    summary_markdown += f"**Base de Análisis:** {total_jobs:,} vacantes únicas.\n\n"
    summary_markdown += "--- \n\n"
    
    summary_markdown += "### 🎯 Demanda de Roles\n"
    summary_markdown += f"Los **roles más solicitados** en la región son: **{', '.join(top_roles)}**.\n\n"
    
    summary_markdown += "### 🏢 Empleadores Activos\n"
    summary_markdown += f"Las **empresas contratando más activamente** incluyen: **{', '.join(top_companies)}**.\n\n"

    summary_markdown += "### 📈 Tendencias de Nicho\n"
    if top_sectors:
        summary_markdown += f"Los sectores de nicho con mayor crecimiento son: **{', '.join(top_sectors)}**.\n"
    else:
        summary_markdown += "El sector dominante es Tecnología/Software, sin nichos específicos detectados en el Top 3.\n"
        
    return summary_markdown


df = load_data(DATA_PATH)

# --- INICIO DEL DASHBOARD ---

st.title("🧠 Job Market Intelligence Pro")
st.markdown("Reporte robusto de tendencias de demanda en sectores clave (Fintech, EdTech, Future of Work).")

if df.empty:
    st.stop()
    
# --- 1. FILTROS EN BARRA LATERAL ---

st.sidebar.header("Filtros de Análisis")

selected_country = st.sidebar.multiselect(
    "País(es)", 
    options=sorted(df['country'].dropna().unique().tolist()), 
    default=df['country'].dropna().unique().tolist()
)

selected_sector = st.sidebar.multiselect(
    "Sector/Keyword", 
    options=sorted(df['sector'].dropna().unique().tolist()),
    default=df['sector'].dropna().unique().tolist()
)

# Aplicar filtros
df_filtered = df[df['country'].isin(selected_country) & df['sector'].isin(selected_sector)]

# --- 0. RESUMEN EJECUTIVO (Llamada) ---
st.header("0. Resumen Ejecutivo de Tendencias")
# 🚨 La función se llama AQUÍ, donde df_filtered ya existe.
st.markdown(generate_executive_summary(df_filtered)) 

# --- 2. KEY PERFORMANCE INDICATORS (KPIs) ---

st.header("1. Indicadores Clave de Demanda")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Vacantes Totales Únicas", f"{len(df_filtered):,}")
col2.metric("Fuentes Activas", df_filtered['source_platform'].nunique())
col3.metric("Países Analizados", df_filtered['country'].nunique())
col4.metric("Promedio Salarial (Estimado)", "N/A (Requiere ETL/Moneda)")


# --- 3. GRÁFICOS ROBUSTOS Y ANÁLISIS ---

st.header("2. Distribución de Roles y Ubicación")

# GRÁFICO A: Distribución por País
st.subheader("Concentración de la Demanda por País")
country_counts = df_filtered.groupby('country').size().reset_index(name='Conteo')

chart_country = alt.Chart(country_counts).mark_bar().encode(
    x=alt.X('Conteo', title='Nro. Vacantes'),
    y=alt.Y('country', title='País', sort='-x'),
    tooltip=['country', 'Conteo'],
    color=alt.Color('Conteo', scale=alt.Scale(range='heatmap', scheme='viridis'))
).properties(height=400)
st.altair_chart(chart_country, use_container_width=True)


# GRÁFICO B: Distribución de seniority_level
col_a, col_b = st.columns([3, 2])

with col_a:
    st.subheader("Demanda por Sector/Plataforma")
    platform_sector_df = df_filtered.groupby(['source_platform', 'sector']).size().reset_index(name='Conteo')
    
    chart_platform_sector = alt.Chart(platform_sector_df).mark_bar().encode(
        x=alt.X('Conteo', title='Nro. Vacantes'),
        y=alt.Y('sector', title='Sector', sort='-x'),
        color='source_platform',
        tooltip=['source_platform', 'sector', 'Conteo']
    ).properties(height=300)
    st.altair_chart(chart_platform_sector, use_container_width=True)

with col_b:
    st.subheader("Distribución de Nivel de Experiencia")
    seniority_level_counts = df_filtered.groupby('seniority_level').size().reset_index(name='Conteo')
    
    chart_seniority_level = alt.Chart(seniority_level_counts).mark_arc(outerRadius=120).encode(
        theta=alt.Theta(field="Conteo", type="quantitative"),
        color=alt.Color(field="seniority_level", type="nominal", title="Nivel"),
        tooltip=["seniority_level", "Conteo"]
    ).properties(title="Nivel de Experiencia", height=350)
    st.altair_chart(chart_seniority_level, use_container_width=True)


# GRÁFICO C: Top Skills

st.subheader("Top 15 Habilidades Técnicas más Solicitadas")

skills_df = df_filtered.explode('skills')

if not skills_df.empty and 'skills' in skills_df.columns:
    top_skills = skills_df['skills'].value_counts().head(15).reset_index()
    top_skills.columns = ['Skill', 'Frecuencia']
    
    chart_skills = alt.Chart(top_skills).mark_bar().encode(
        x=alt.X('Frecuencia', title='Frecuencia'),
        y=alt.Y('Skill', sort='-x', title='Habilidad'),
        tooltip=['Skill', 'Frecuencia'],
        color=alt.Color('Frecuencia', scale=alt.Scale(range='heatmap', scheme='magma'))
    ).properties(height=450)
    st.altair_chart(chart_skills, use_container_width=True)
else:
    st.info("No hay datos de habilidades para mostrar.")


# --- 4. DATASET BRUTO ---
st.header("3. Dataset Consolidado (Muestra)")
st.dataframe(df_filtered[[
    'title', 'company_name', 'location', 'country', 'source_platform', 'seniority_level', 'sector','salary_range', 
    'posted_date',
    'source_url'
]], 
    use_container_width=True
)