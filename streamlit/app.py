# streamlit_dashboard/app.py (VERSIÓN FINAL Y COMPLETA con Corrección de Compatibilidad)

import streamlit as st
import pandas as pd
import altair as alt
import os
import re

# --- CONFIGURACIÓN Y CARGA DE DATOS ---

# Ruta al archivo consolidado final
DATA_PATH = "market_data_FINAL_CONSOLIDADO.csv" 

st.set_page_config(
    page_title="Job Market Intelligence Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data(path):
    """Carga, limpia y prepara los datos para el análisis."""
    if not os.path.exists(path):
        st.error(f"❌ ERROR: Archivo de datos no encontrado en la ruta: {path}. ¡Asegúrate de que el proceso de consolidación finalizó!")
        return pd.DataFrame()
        
    df = pd.read_csv(path)
    
    # --- CRITICAL FIXES FOR KEY ERROR ---
    
    # 1. Handle 'nivel_experiencia' (Seniority)
    # Si la columna no existe en el CSV (KeyError), la creamos y la llenamos con 'N/A'.
    if 'nivel_experiencia' in df.columns:
        df['nivel_experiencia'] = df['nivel_experiencia'].fillna('N/A')
    else:
        df['nivel_experiencia'] = 'N/A' 
    
    # 2. Handle 'skills'
    if 'skills' not in df.columns:
        # Si la columna falta, la creamos como lista vacía, necesaria para el explode.
        df['skills'] = [[] for _ in range(len(df))]
    
    # 3. Handle 'sector' (Keyword/Category)
    # Usamos la columna 'palabra_clave' como el sector base.
    if 'palabra_clave' in df.columns:
        df['sector'] = df['palabra_clave'].fillna('Indefinido') 
    else:
        df['sector'] = 'Indefinido'
    
    # --- END CRITICAL FIXES ---
    
    # Limpieza de habilidades (la versión final limpia los corchetes)
    def clean_skills(s):
        if pd.isna(s) or str(s) in ('[]', 'None', 'nan'):
            return []
        if isinstance(s, str):
            s = re.sub(r"[\[\]'\" ]", '', s) 
            return [skill.strip() for skill in s.split(',') if skill.strip()]
        return []

    df['skills'] = df['skills'].apply(clean_skills)
    
    return df

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
    options=sorted(df['pais'].dropna().unique().tolist()), 
    default=df['pais'].dropna().unique().tolist()
)

selected_sector = st.sidebar.multiselect(
    "Sector/Keyword", 
    options=sorted(df['sector'].dropna().unique().tolist()),
    default=df['sector'].dropna().unique().tolist()
)

# Aplicar filtros
df_filtered = df[df['pais'].isin(selected_country) & df['sector'].isin(selected_sector)]


# --- 2. KEY PERFORMANCE INDICATORS (KPIs) ---

st.header("1. Indicadores Clave de Demanda")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Vacantes Totales Únicas", f"{len(df_filtered):,}")
col2.metric("Fuentes Activas", df_filtered['plataforma'].nunique())
col3.metric("Países Analizados", df_filtered['pais'].nunique())
col4.metric("Promedio Salarial (Estimado)", "N/A (Requiere ETL/Moneda)")


# --- 3. GRÁFICOS ROBUSTOS Y ANÁLISIS ---

st.header("2. Distribución de Roles y Ubicación")

# GRÁFICO A: Distribución por País
st.subheader("Concentración de la Demanda por País")
country_counts = df_filtered.groupby('pais').size().reset_index(name='Conteo')

chart_country = alt.Chart(country_counts).mark_bar().encode(
    x=alt.X('Conteo', title='Nro. Vacantes'),
    y=alt.Y('pais', title='País', sort='-x'),
    tooltip=['pais', 'Conteo'],
    color=alt.Color('Conteo', scale=alt.Scale(range='heatmap', scheme='viridis'))
).properties(height=400)
# 🚨 CORRECCIÓN DE COMPATIBILIDAD APLICADA AQUÍ: width='stretch'
st.altair_chart(chart_country, width='stretch')


# GRÁFICO B: Distribución de Seniority
col_a, col_b = st.columns([3, 2])

with col_a:
    st.subheader("Demanda por Sector/Plataforma")
    platform_sector_df = df_filtered.groupby(['plataforma', 'sector']).size().reset_index(name='Conteo')
    
    chart_platform_sector = alt.Chart(platform_sector_df).mark_bar().encode(
        x=alt.X('Conteo', title='Nro. Vacantes'),
        y=alt.Y('sector', title='Sector', sort='-x'),
        color='plataforma',
        tooltip=['plataforma', 'sector', 'Conteo']
    ).properties(height=300)
    # 🚨 CORRECCIÓN DE COMPATIBILIDAD APLICADA AQUÍ
    st.altair_chart(chart_platform_sector, width='stretch')

with col_b:
    st.subheader("Distribución de Seniority")
    seniority_counts = df_filtered.groupby('nivel_experiencia').size().reset_index(name='Conteo')
    
    chart_seniority = alt.Chart(seniority_counts).mark_arc(outerRadius=120).encode(
        theta=alt.Theta(field="Conteo", type="quantitative"),
        color=alt.Color(field="nivel_experiencia", type="nominal", title="Nivel"),
        tooltip=["nivel_experiencia", "Conteo"]
    ).properties(title="Nivel de Experiencia", height=350)
    # 🚨 CORRECCIÓN DE COMPATIBILIDAD APLICADA AQUÍ
    st.altair_chart(chart_seniority, width='stretch')


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
    # 🚨 CORRECCIÓN DE COMPATIBILIDAD APLICADA AQUÍ
    st.altair_chart(chart_skills, width='stretch')
else:
    st.info("No hay datos de habilidades para mostrar.")


# --- 4. DATASET BRUTO ---
st.header("3. Dataset Consolidado (Muestra)")
st.dataframe(df_filtered[[
    'titulo', 'empresa', 'ubicacion', 'pais', 'plataforma', 'nivel_experiencia', 'sector'
]].head(100))