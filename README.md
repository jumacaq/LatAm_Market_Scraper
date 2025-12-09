# 🧠 Job Market Intelligence Pro - Reporte de Tendencias

Este proyecto implementa un sistema de **Scraping Inteligente** para monitorear el mercado laboral en Latinoamérica, centrándose en roles de alta demanda y sectores tecnológicos clave (Fintech, Data Science, Future of Work).

El sistema incluye un **Pipeline ETL (Extracción, Transformación, Carga)** para la limpieza, normalización y enriquecimiento de datos, culminando en un dashboard interactivo en Streamlit y un reporte automático.

---

## ✅ Requisitos Cumplidos

* **Dataset de 600+ registros procesados.**
* **Pipeline ETL robusto** con normalización de Seniority y extracción de Skills.
* **Enriquecimiento de empresas** (Tamaño e Industria) mediante heurísticas.
* **Reporte de Tendencias** automatizable y un Dashboard interactivo.
* **Control de Frecuencia** implementado en el Spider (15s de delay).

---

## 🚀 Instrucciones de Ejecución

Sigue estos tres pasos para generar el dataset analítico y lanzar el dashboard.

### Paso 1: Instalación de Dependencias

Abre tu terminal en la carpeta raíz del proyecto y **activa el ambiente virtual**, luego instala todas las dependencias necesarias:

```bash
# 1. Activar el ambiente virtual (Windows PowerShell)
.\venv\Scripts\activate

# 2. Instalar todas las librerías necesarias
(venv) pip install -r requirements.txt 
# (Asumiendo que requirements.txt existe, si no, instalar: scrapy pandas streamlit altair pyyaml tabulate)
(venv) pip install scrapy pandas streamlit altair pyyaml tabulate