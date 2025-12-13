# 🚀✨ Plataforma de Inteligencia de Mercado Laboral: LatAm Insights

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Built with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Powered by Supabase](https://img.shields.io/badge/Supabase-Powered-green?logo=supabase&logoColor=white)](https://supabase.com/)
[![Google Gemini API](https://img.shields.io/badge/Google_Gemini-API-purple?logo=google-gemini&logoColor=white)](https://ai.google.dev/)

---

## 🌟 Descripción General del Proyecto

Sumérgete en el corazón del mercado laboral de Latinoamérica con la **Plataforma de Inteligencia de Mercado Laboral**. Esta solución integral y automatizada está diseñada para **rastrear, procesar, analizar y visualizar** las tendencias de empleo digital más relevantes, con un enfoque principal en **Latinoamérica** y la capacidad de expansión global.

Construida en **Python**, nuestra plataforma de vanguardia integra:
*   **Scrapy** para un web scraping potente y eficiente.
*   Un sofisticado **Pipeline de ETL** (Extracción, Transformación, Carga) para asegurar la máxima calidad y coherencia de los datos.
*   **Supabase** como una base de datos robusta y escalable en la nube.
*   Capacidades de **Análisis de Tendencias** para descifrar patrones ocultos.
*   Un **Generador de Reportes inteligente** potenciado por la **IA de Google Gemini** para insights accionables.
*   Todo presentado en un **Dashboard interactivo y dinámico** creado con **Streamlit**.

Nuestro objetivo es simple: **democratizar el acceso a la inteligencia del mercado laboral.** Proporcionamos una visión cristalina y casi en tiempo real sobre:
*   📈 Las **habilidades técnicas más codiciadas**.
*   🚀 Los **roles con mayor demanda y crecimiento**.
*   🏢 Las **empresas líderes en contratación**.
*   🌍 Las **tendencias emergentes por sector** (FinTech, EdTech, HealthTech, ¡y más!).

Esta valiosa información empodera a profesionales, reclutadores, instituciones educativas y empresas para tomar decisiones estratégicas basadas en datos sólidos.

---

## ✨ Características Estelares

Explora la potencia de nuestra plataforma a través de sus componentes clave:

### 🕸️ Web Scraping Multi-Plataforma (`scrapers/`)
*   **Adaptabilidad:** Spiders especializados para extraer vacantes de **LinkedIn** y **Computrabajo**, con expansión flexible a otras plataformas.
*   **Búsqueda Inteligente:** Configura tus búsquedas por palabras clave (roles, habilidades, sectores) y ubicaciones geográficas precisas (continentes, países).
*   **Anti-Bloqueo Avanzado:** Implementa rotación de User-Agents, retrasos aleatorios y AutoThrottle para una recolección de datos sigilosa y efectiva.
*   **Exploración Profunda:** Navegación automática por múltiples páginas de resultados para una cobertura exhaustiva.

### 🧹 Pipeline ETL de Vanguardia (`etl/` & `scrapers/pipelines.py`)
Un sistema cuidadosamente diseñado para transformar datos crudos en información valiosa:
*   **Limpieza de Datos (`etl/cleaners.py`):** Elimina etiquetas HTML, espacios redundantes y caracteres especiales. Los datos se pulen para ser legibles y coherentes. Generación de IDs únicos (`job_id`) robustos.
*   **Normalización Estándar (`etl/normalizers.py`):** Estandariza la jerarquía profesional (Junior, Mid, Senior, Lead, Executive), el tipo de contrato (Full-time, Remote, Hybrid) y la clasificación de roles (Data Science & ML, Software Development).
*   **Enriquecimiento Corporativo (`etl/enrichment.py`):** Utiliza heurísticas para inferir información clave de empresas: tamaño, industria, país de sede y tipo de organización, aportando contexto invaluable.
*   **Extracción de Habilidades (`etl/skill_extractor.py`):** Identifica y clasifica automáticamente habilidades técnicas cruciales (ej. `Python`, `AWS`, `Machine Learning`) de las descripciones de empleo.
*   **Clasificación Sectorial (`etl/sector_classifier.py`):** Asigna cada vacante a un sector industrial específico (Fintech, Edtech, etc.) basándose en un análisis inteligente de palabras clave.

### 💾 Persistencia en Supabase (`database/supabase_client.py`)
*   **Almacenamiento Confiable:** Tu centro de datos en la nube, impulsado por PostgreSQL a través de Supabase, garantizando escalabilidad y seguridad.
*   **Deduplicación Inteligente:** Mecanismos `upsert` que evitan registros duplicados y mantienen la información fresca y actualizada.
*   **Modelo Relacional:** Organiza eficientemente vacantes, habilidades, compañías y tendencias en un esquema de base de datos interconectado.

### 📊 Análisis de Tendencias Detallado (`analysis/trend_analyzer.py`)
*   **Métricas Esenciales:** Calcula y almacena las **habilidades más demandadas**, las **habilidades con mayor crecimiento**, los **roles más buscados** y la **distribución de vacantes por sector**.
*   **Visión Temporal:** Realiza análisis comparativos entre diferentes periodos de tiempo, revelando la evolución del mercado.
*   **Historial de Tendencias:** Los resultados se persisten en Supabase, construyendo un valioso archivo histórico de la evolución del mercado laboral.

### 🧠 Generación de Insights con IA (`analysis/report_generator.py`)
*   **Inteligencia Artificial con Google Gemini:** Aprovecha el poder de los modelos generativos de Google para transformar datos en narrativas coherentes.
*   **Reportes Ejecutivos:** Genera resúmenes diarios concisos que resaltan las tendencias clave, como los roles emergentes o las empresas más activas en contratación.

### 🌐 Dashboard Interactivo (`dashboard.py`)
*   **Interfaz Amigable:** Un panel de control intuitivo y visualmente atractivo construido con Streamlit, accesible desde tu navegador.
*   **Control Total:** Ejecuta procesos de scraping y análisis de tendencias directamente desde la interfaz, sin necesidad de comandos complejos.
*   **Filtros Dinámicos:** Explora los datos con filtros por continente, país y rango de fechas para una personalización total.

### ⚙️ Gestión Centralizada de Configuración (`config/`)
*   **`config.yaml`:** Un archivo YAML fácil de editar que centraliza todos los parámetros clave: roles de búsqueda, palabras clave para sectores y una biblioteca exhaustiva de habilidades técnicas.
*   **`geo.py`:** Define la geografía del proyecto, con mapeos de continentes, países y configuraciones específicas para los filtros de fecha de cada plataforma.

### ⏰ Programación de Tareas (`scheduler.py`)
*   **Automatización Sencilla:** Un script ligero que utiliza la librería `schedule` para automatizar la ejecución periódica de tareas esenciales como el scraping y el análisis, manteniendo tus datos siempre al día.

---

## 📂 Estructura del Proyecto

Una visión rápida de cómo está organizado este ingenioso sistema:

```
Proyecto Automatizado/
├── analysis/                     # Módulos para análisis y generación de reportes IA.
│   ├── report_generator.py       # Crea resúmenes inteligentes con Google Gemini.
│   └── trend_analyzer.py         # Descubre tendencias de habilidades, roles y sectores.
├── config/                       # Archivos esenciales de configuración.
│   ├── config.yaml               # Define tu universo de búsqueda: roles, sectores y habilidades clave.
│   └── geo.py                    # Datos geográficos y mapeos para una búsqueda precisa.
├── database/                     # La capa de interacción con tu base de datos Supabase.
│   └── supabase_client.py        # Gestiona todas las operaciones CRUD y `upsert` con Supabase.
├── dashboard.py                  # Tu centro de mando visual: el Dashboard interactivo de Streamlit.
├── etl/                          # El corazón de la transformación de datos.
│   ├── cleaners.py               # Limpia y estandariza el texto de las vacantes.
│   ├── enrichment.py             # Enriquecimiento heurístico para datos de compañías.
│   ├── normalizers.py            # Normaliza campos clave como antigüedad y tipo de trabajo.
│   ├── sector_classifier.py      # Clasifica vacantes por sector industrial.
│   └── skill_extractor.py        # Extrae y categoriza habilidades técnicas automáticamente.
├── scrapers/                     # Donde nacen los datos: tus herramientas de scraping.
│   ├── __init__.py               # Paquete Python para los scrapers.
│   ├── items.py                  # Define la estructura de datos para cada vacante.
│   ├── middlewares.py            # Estrategias anti-bloqueo como rotación de User-Agents.
│   ├── pipelines.py              # La secuencia de procesamiento de datos antes de Supabase.
│   └── spiders/                  # Los "bots" que rastrean las plataformas de empleo.
│       ├── computrabajo_spider.py# Spider dedicado a Computrabajo.
│       ├── linkedin_spider.py    # Spider dedicado a LinkedIn.
│       └── company_enrichment_spider.py # Un concepto para futuras expansiones de enriquecimiento.
├── tests/                        # Garantizando la calidad: pruebas unitarias del proyecto.
│   ├── __init__.py
│   └── test_etl_components.py    # Pruebas para tus módulos ETL críticos.
├── main.py                       # El director de orquesta: punto de entrada para todas las operaciones.
├── README.md                     # ¡Este mismo archivo! Tu guía principal.
├── requirements.txt              # La lista de ingredientes: todas las dependencias de Python.
├── scheduler.py                  # El automatizador: para ejecutar tareas programadas.
└── ver_dashboard.bat             # El atajo: script de Windows para lanzar el dashboard al instante.
```

---

## 🛠️ Configuración y Requisitos Previos: Guía Completa de Instalación

¡Prepara tu entorno de desarrollo para esta emocionante aventura!

### 1. Requisitos del Sistema 💻

Asegúrate de que tu sistema operativo tenga instalados los siguientes elementos:

*   **Python 3.9 o superior:**
    *   ⬇️ Descarga desde: [python.org](https://www.python.org/downloads/)
    *   ✨ **Verificación:** Abre tu terminal (o Símbolo del Sistema/PowerShell en Windows) y escribe `python --version` (o `python3 --version`). Deberías ver una versión como `Python 3.9.x` o superior.
*   **Git:**
    *   ⬇️ Descarga desde: [git-scm.com](https://git-scm.com/downloads)
    *   ✨ **Verificación:** En tu terminal, escribe `git --version`.

### 2. Clonar el Repositorio del Proyecto 📥

1.  Abre tu terminal (o Git Bash en Windows).
2.  Navega al directorio donde deseas guardar el proyecto.
3.  Ejecuta el siguiente comando para descargar una copia local del código:

    ```bash
    git clone https://github.com/tu-usuario/Proyecto-Automatizado.git # ⚠️ ¡IMPORTANTE! Reemplaza "tu-usuario/Proyecto-Automatizado.git" con la URL REAL de tu repositorio de GitHub.
    cd Proyecto-Automatizado
    ```
    Este comando creará una nueva carpeta `Proyecto-Automatizado` y te posicionará dentro de ella.

### 3. Configurar Supabase como tu Base de Datos 🔗

Supabase actúa como el back-end de nuestra plataforma, almacenando todos los datos recopilados y analizados.

#### A. Crear un Nuevo Proyecto en Supabase 🚀
1.  **Visita Supabase:** Dirígete a [supabase.com](https://supabase.com/).
2.  **Regístrate/Inicia Sesión:** Crea una cuenta o inicia sesión en tu panel de control.
3.  **Nuevo Proyecto:** Haz clic en el botón "New project" para comenzar la creación.
4.  **Detalles del Proyecto:**
    *   **Name:** Elige un nombre descriptivo (ej. "JobMarketIntelligence").
    *   **Database Password:** **Crea y anota una contraseña segura.** ¡Es crucial para tu base de datos!
    *   **Region:** Selecciona la región geográfica más cercana a tu ubicación (o donde planeas desplegar el proyecto) para optimizar el rendimiento.
5.  **Obtén tus Credenciales API:** Una vez que Supabase haya terminado de provisionar tu proyecto (puede tardar unos minutos), navega a "Project Settings" ➡️ "API" en el panel lateral izquierdo.
    *   **Project URL:** Copia la URL de tu proyecto. Tendrá un formato similar a `https://[TU_PROYECTO_ID].supabase.co`.
    *   **Anon Key (`anon public`):** Copia esta clave. Se utiliza principalmente para operaciones de **lectura** desde el dashboard de Streamlit.
    *   **Service Role Key (`service_role secret`):** Copia esta clave. Posee permisos de **administrador completo** y se utilizará para las operaciones de **escritura (upsert)** y **borrado** desde el backend del scraper y el análisis. **¡MANTÉN ESTA CLAVE BAJO EXTREMA SEGURIDAD Y NUNCA LA EXPONGAS EN EL CÓDIGO DEL LADO DEL CLIENTE!**

#### B. Aplicar el Esquema SQL para Crear las Tablas 🧱
Necesitas definir la estructura de las tablas en tu base de datos Supabase para que el proyecto pueda almacenar los datos correctamente.

1.  **Localiza el Archivo SQL:** El script SQL necesario para crear las tablas (`companies`, `jobs`, `skills`, `trends`) se encuentra en el archivo **`SQL_PARA_SUPABASE.sql`** en la raíz del directorio de tu proyecto local (`Proyecto Automatizado/`).
    *   **Descripción del Esquema:** Este archivo está meticulosamente diseñado. Define las relaciones entre tablas (con claves foráneas como `company_id` y `job_id`), establece restricciones de unicidad para evitar duplicados y crea índices para acelerar las consultas, garantizando la integridad y eficiencia de tus datos.
2.  **Accede al SQL Editor de Supabase:** En el panel de control de tu proyecto Supabase, haz clic en "SQL Editor" en la barra lateral izquierda.
3.  **Crea un Nuevo Query:** Haz clic en el botón "New query".
4.  **Copia y Pega el Contenido:** Abre el archivo `SQL_PARA_SUPABASE.sql` desde tu proyecto local con cualquier editor de texto, copia **todo su contenido** y pégalo en el área de texto del editor de queries de Supabase.
5.  **Ejecuta el Query:** Haz clic en el botón "Run" (generalmente un triángulo ▶️) para ejecutar el script SQL. En pocos segundos, todas las tablas necesarias se crearán en tu base de datos.

### 4. Configurar Variables de Entorno (`.env`) 🔑

Para que tu proyecto Python pueda acceder a Supabase y a la API de Google Gemini, debes configurar tus credenciales como variables de entorno.

1.  **Crear el Archivo `.env`:** En el directorio raíz de tu proyecto (`Proyecto Automatizado/`), crea un nuevo archivo y nómbralo exactamente `.env` (sin ninguna extensión visible).
2.  **Añadir Credenciales:** Copia y pega el siguiente contenido en el archivo `.env`. **¡REEMPLAZA los valores `[TU_...]` con tus credenciales reales** obtenidas de Supabase y Google!

    ```dotenv
    # .env
    # --------------------------------------------------------------------------------------
    # Configuraciones de Supabase
    # SUPABASE_URL: La URL de tu proyecto Supabase (ej. https://abcdefghijk.supabase.co)
    SUPABASE_URL="https://[TU_PROYECTO_ID].supabase.co"

    # SUPABASE_KEY: Tu "anon public" key. Se usa principalmente para operaciones de LECTURA
    #               desde el dashboard de Streamlit, o para escritura si RLS está configurado.
    SUPABASE_KEY="[TU_SUPABASE_ANON_KEY]" 

    # SUPABASE_SERVICE_KEY: Tu "service_role secret" key. Tiene permisos de ADMINISTRADOR.
    #                       Se usa para operaciones de ESCRITURA (upsert) y BORRADO de datos
    #                       desde los pipelines de Scrapy y el script de limpieza.
    #                       ¡MANTÉN ESTA CLAVE EXTREMADAMENTE SEGURA Y NO LA EXPONGAS EN EL CLIENTE!
    SUPABASE_SERVICE_KEY="[TU_SUPABASE_SERVICE_ROLE_KEY]"

    # --------------------------------------------------------------------------------------
    # Configuraciones de Google Gemini
    # GEMINI_API_KEY: Tu clave de API para Google Gemini. Necesaria para el generador de reportes de IA.
    #                 Obtén una clave en https://ai.google.dev/
    GEMINI_API_KEY="[TU_GOOGLE_GEMINI_API_KEY]"
    ```
    **⚠️ ADVERTENCIA DE SEGURIDAD:** El archivo `.env` **NUNCA** debe ser compartido públicamente (ej. subido a GitHub). Asegúrate de que tu archivo `.gitignore` incluya `.env` para evitar esto.

### 5. Instalar las Dependencias de Python 📦

Con tu terminal aún en el directorio `Proyecto Automatizado/`, instala todas las bibliotecas de Python que el proyecto requiere.

1.  Ejecuta el siguiente comando:
    ```bash
    pip install -r requirements.txt
    ```
    Este comando leerá la lista de paquetes en `requirements.txt` y los instalará automáticamente. Este proceso puede tardar unos minutos en completarse.

---

## 🚀 Uso de la Plataforma: Guía Detallada de Operación

¡Estás listo para darle vida a tu Plataforma de Inteligencia de Mercado Laboral! Sigue estos pasos para comenzar a recopilar datos, analizarlos y visualizarlos.

### 1. Ejecutar los Scrapers para Recopilar Vacantes 🕷️

Puedes iniciar el proceso de extracción de datos de dos maneras: interactivamente a través de la terminal o mediante argumentos de línea de comandos para una automatización precisa.

#### A. Modo Interactivo (¡Recomendado para las primeras exploraciones!)
Este modo te guiará con preguntas sencillas para configurar tu sesión de scraping.
1.  Abre tu terminal en el directorio `Proyecto Automatizado/`.
2.  Ejecuta el script principal sin ningún argumento:
    ```bash
    python main.py
    ```
3.  **Sigue las Instrucciones:** El script te solicitará la siguiente información:
    *   **Selección de Scrapers:** Te mostrará una lista de spiders disponibles (ej. `linkedin`, `computrabajo`). Ingresa los números correspondientes separados por comas (ej. `1,2` para ambos, o `1` para solo LinkedIn).
    *   **Selección de Continente:** Escoge el continente de tu interés de la lista presentada.
    *   **Selección de País:** Dentro del continente elegido, podrás optar por un país específico o seleccionar "Todos los países" para abarcar todas las ubicaciones en ese continente.
    *   **Rango de Fechas (Opcional):** Se te pedirá ingresar una "Fecha de inicio" y una "Fecha de fin" (formato `YYYY-MM-DD`). Si dejas estos campos en blanco, el scraper intentará obtener todas las vacantes disponibles sin un filtro de fecha estricto desde la plataforma de origen (el filtrado por fecha preciso se realizará en el pipeline de ETL si los spiders no lo soportan nativamente en la URL).
    *   **Número Máximo de Vacantes:** Define el número límite de vacantes que **cada scraper** intentará obtener en esta ejecución.

#### B. Modo Línea de Comandos (¡Ideal para automatización y scripts!)
Si ya conoces tus parámetros de búsqueda, puedes pasarlos directamente al script, perfecto para integraciones o ejecuciones repetitivas.
1.  Abre tu terminal en el directorio `Proyecto Automatizado/`.
2.  Ejecuta el script `main.py` con los argumentos apropiados. Aquí tienes un ejemplo exhaustivo:
    ```bash
    python main.py \
      --spiders linkedin,computrabajo \
      --continent Latam \
      --country "Todos los Países" \
      --start_date 2024-03-01 \
      --end_date 2024-03-31 \
      --max_jobs 200
    ```
    *   **`--spiders [spider1,spider2,...]`**: Especifica qué spiders ejecutar, separados por comas (ej. `linkedin,computrabajo`).
    *   **`--continent [NombreContinente]`**: El continente objetivo (ej. `Latam`, `Europa`, `Norte America`).
    *   **`--country [NombrePais | "Todos los Países"]`**: Un país específico (ej. `Mexico`, `Argentina`). Si eliges `"Todos los Países"`, rastreará todas las ubicaciones dentro del `--continent` especificado.
    *   **`--start_date [YYYY-MM-DD]`**: La fecha de inicio mínima para las vacantes publicadas.
    *   **`--end_date [YYYY-MM-DD]`**: La fecha de fin máxima para las vacantes publicadas.
    *   **`--max_jobs [Numero]`**: El número máximo de vacantes que **cada spider** intentará raspar en esta ejecución.

### 2. Ejecutar el Análisis de Tendencias 📈

Después de haber recopilado una cantidad significativa de vacantes, el siguiente paso es ejecutar el módulo de análisis de tendencias. Este proceso calculará métricas clave y almacenará los insights resultantes en tu base de datos Supabase.

1.  Abre tu terminal en el directorio `Proyecto Automatizado/`.
2.  Ejecuta el script principal con el argumento `--analyze-trends`:
    ```bash
    python main.py --analyze-trends
    ```
    Este comando calculará las tendencias más demandadas (habilidades, roles, sectores) utilizando los datos disponibles y las almacenará en la tabla `trends` de tu base de datos Supabase, asociándolas a la fecha actual.

3.  **Análisis para una Fecha Específica (Opcional):**
    Si necesitas realizar un análisis retrospectivo para una fecha en particular, puedes especificarla:
    ```bash
    python main.py --analyze-trends --analysis-date 2024-03-15
    ```

### 3. Iniciar el Dashboard de Streamlit 📊

El Dashboard de Streamlit es tu centro de comando visual, donde podrás explorar los datos recopilados, visualizar gráficos, métricas y los insights generados por la IA.

1.  Abre tu terminal en el directorio `Proyecto Automatizado/`.
2.  Ejecuta el siguiente comando para lanzar la aplicación de Streamlit:
    ```bash
    streamlit run dashboard.py
    ```
3.  **Accede al Dashboard:** Streamlit iniciará un servidor web local y, en la mayoría de los casos, abrirá automáticamente el dashboard en tu navegador web predeterminado (generalmente en `http://localhost:8501`).
    *   **Para Usuarios de Windows:** Para mayor comodidad, puedes simplemente hacer doble clic en el archivo `ver_dashboard.bat` (si existe en la raíz de tu proyecto) o ejecutarlo desde el Símbolo del Sistema. Este script está diseñado para lanzar el dashboard rápidamente.
4.  **Explora e Interactúa:** Una vez en el dashboard, te encontrarás con:
    *   **Panel de Control (Barra Lateral):** Aquí tienes acceso directo para ejecutar nuevos procesos de scraping, iniciar el análisis de tendencias, y, si es necesario, limpiar la base de datos.
    *   **Filtros Dinámicos:** Utiliza los filtros en la barra lateral (por continente, país, rango de fechas) para afinar los datos que se muestran en los gráficos y tablas.
    *   **Visualizaciones Impactantes:** Observa gráficos interactivos que ilustran las habilidades más demandadas, los roles predominantes, la distribución por sector y los valiosos reportes de IA generados por Google Gemini.

### 4. Programar Tareas Periódicas (Opcional - Uso Avanzado) ⏰

El script `scheduler.py` te permite automatizar la ejecución de las tareas de scraping y análisis a intervalos regulares, manteniendo tu plataforma actualizada sin intervención manual.

1.  **Localiza y Adapta `scheduler.py`:** El archivo `scheduler.py` se encuentra en la raíz de tu proyecto. Ábrelo con tu editor de texto preferido.
    *   **Entiende la Estructura:** Este archivo contiene funciones Python (ej. `job_scrape_latam_linkedin()`, `job_analyze_trends()`) que envuelven las llamadas a `main.py` mediante `subprocess.run()`.
    *   **Modifica la Lógica:** Ajusta estas funciones para que reflejen tus necesidades específicas de automatización (ej. qué spiders ejecutar, qué países, qué rangos de fechas). Asegúrate de que los argumentos pasados a `subprocess.run` concuerden con los que `main.py` espera en modo CLI.
    *   **Define la Frecuencia:** Modifica las líneas `schedule.every().day.at("02:00").do(...)` para establecer la periodicidad y la hora de ejecución de cada tarea. Puedes usar `every().hour`, `every().monday`, `every(5).minutes`, etc.
2.  **Ejecutar el Scheduler:**
    Para que las tareas programadas se ejecuten, el script `scheduler.py` debe permanecer activo en segundo plano.
    *   **En Desarrollo/Pruebas:** Puedes ejecutarlo directamente desde tu terminal:
        ```bash
        python scheduler.py
        ```
        Mantén esta terminal abierta. Puedes detener el scheduler en cualquier momento presionando `Ctrl+C`.
    *   **En Producción (Recomendado):** Para un despliegue robusto y fiable, se aconseja ejecutar el scheduler como un proceso en segundo plano que sea gestionado por un sistema. Herramientas comunes para esto incluyen `nohup` (en Linux/macOS), `systemd` (Linux), `supervisor` o `pm2`.
        *   **Ejemplo con `nohup` (Linux/macOS):**
            ```bash
            nohup python scheduler.py > scheduler_output.log 2>&1 &
            ```
            Este comando ejecutará el scheduler de forma persistente en segundo plano. Su salida (logs) se redirigirá a `scheduler_output.log`, y tu terminal quedará libre para otros usos.

### 5. Limpiar la Base de Datos (¡🚨 ADVERTENCIA: ACCIÓN IRREVERSIBLE! 🚨) 🗑️

Existe una funcionalidad en el dashboard de Streamlit para eliminar **todos los datos** de las tablas `jobs`, `skills`, `companies` y `trends`. Utiliza esta opción con extrema precaución.

1.  **Inicia el Dashboard:** Asegúrate de que tu dashboard de Streamlit esté activo y funcionando (`streamlit run dashboard.py`).
2.  **Navega al Panel de Control:** En la barra lateral izquierda del dashboard, busca la sección "⚠️ Mantenimiento de Datos".
3.  **Haz Clic en "Limpiar Base de Datos":** Al activar este botón, aparecerá una ventana de confirmación con una advertencia clara.
4.  **Confirma la Acción:** **LEE CUIDADOSAMENTE LA ADVERTENCIA.** Si estás absolutamente seguro de proceder, haz clic en "Sí, Eliminar Datos".
    *   **¡Importante!** Esta operación requiere que la `SUPABASE_SERVICE_KEY` configurada en tu archivo `.env` tenga los **permisos explícitos de `delete`** en Supabase. Si la limpieza falla, revisa los logs en la terminal de Streamlit para identificar posibles errores de permisos o problemas de conexión a la base de datos.

---

## 🌐 Tecnologías y Librerías Utilizadas 🚀

Este proyecto es una muestra del poder del ecosistema Python, utilizando una selección de herramientas y bibliotecas de vanguardia:

*   **Lenguaje de Programación:** `Python` (3.9+) 🐍
*   **Web Scraping y Automatización:**
    *   `Scrapy`: El framework fundamental para el rastreo web de alto rendimiento.
    *   `beautifulsoup4`: Una librería versátil para parsear HTML de manera eficiente (utilizada en `TextCleaner`).
    *   `selenium` & `webdriver-manager`: Para interactuar con navegadores web reales (útil para contenido dinámico de JS, aunque no siempre activo en todos los spiders).
    *   `requests`: Para realizar solicitudes HTTP sencillas y directas.
    *   `lxml`: Un potente parser de XML/HTML optimizado para velocidad.
    *   `fake-useragent`: Para generar encabezados `User-Agent` realistas y aleatorios, mejorando la resistencia a bloqueos.
*   **Base de Datos y Persistencia:**
    *   `supabase-py`: El cliente oficial de Python para interactuar sin problemas con tu base de datos Supabase.
    *   `python-dotenv`: Gestiona y carga tus variables de entorno desde el archivo `.env` de forma segura.
*   **Procesamiento y Análisis de Datos:**
    *   `pandas`: La piedra angular para la manipulación, limpieza y análisis de datos tabulares.
    *   `numpy`: Proporciona soporte para operaciones numéricas y arrays de alto rendimiento.
    *   `pyyaml`: Para la fácil lectura y escritura de tus archivos de configuración YAML.
    *   `python-dateutil`: Un módulo poderoso para el parsing y manipulación inteligente de fechas y horas.
    *   `scikit-learn`: (Potencialmente para futuras extensiones de ML, no explícitamente usado para modelos en el MVP de ETL).
*   **Visualización y Dashboards Interactivas:**
    *   `streamlit`: El innovador framework que transforma scripts de Python en elegantes aplicaciones web interactivas y dashboards.
    *   `plotly`: Librería de gráficos interactivos de última generación para visualizaciones ricas y dinámicas.
    *   `altair`: (Posiblemente utilizado para algunas visualizaciones declarativas, aunque Plotly es el principal motor gráfico).
*   **Inteligencia Artificial y Modelos Generativos:**
    *   `google-generativeai`: El SDK de Python para integrar las capacidades de los modelos de IA de Google Gemini.
*   **Automatización y Scheduling:**
    *   `schedule`: Una librería simple y eficaz para programar la ejecución de tareas recurrentes directamente en Python.
*   **Herramientas de Desarrollo y Testing:**
    *   `flake8`: Para asegurar la conformidad con el estilo de código PEP8 y mantener un código limpio.
    *   `pytest`: Un framework de pruebas robusto para escribir tests unitarios eficientes y escalables.
    *   `openpyxl` & `xlsxwriter`: (Si se implementan funcionalidades avanzadas de exportación de reportes a Excel).

---

## 🤝 Contribuciones 💡

¡Valoramos inmensamente cada contribución a este proyecto! Tu apoyo es fundamental para hacerlo crecer y mejorarlo. Si tienes ideas, detectas un error o deseas añadir una nueva funcionalidad, te animamos a participar.

Para contribuir, sigue los pasos de un flujo de trabajo estándar de GitHub:

1.  **Haz un Fork:** Dirígete al repositorio original en GitHub y haz clic en el botón "Fork" para crear una copia personal en tu cuenta.
2.  **Clona tu Fork:** Descarga la copia de tu repositorio a tu máquina local.
3.  **Crea una Rama Nueva:** Antes de realizar cualquier cambio, crea una rama específica para tu contribución. Esto mantiene el historial de cambios organizado.
    ```bash
    git checkout -b feature/tu-nueva-funcionalidad # Para añadir características
    git checkout -b fix/solucion-del-problema       # Para corregir errores
    ```
4.  **Realiza tus Cambios:** Implementa tus mejoras o correcciones. Esfuérzate por seguir las buenas prácticas de codificación y mantener la consistencia del estilo del proyecto.
5.  **Añade Pruebas (¡Si Aplica!):** Si estás introduciendo nuevas funcionalidades o corrigiendo un bug, por favor, incluye pruebas unitarias relevantes en el directorio `tests/`. Esto garantiza que tus cambios no introduzcan nuevos problemas y que la funcionalidad sea robusta.
6.  **Commitea tus Cambios:** Escribe mensajes de commit claros, concisos y descriptivos que expliquen qué cambios has realizado y por qué.
    ```bash
    git commit -am 'feat: Integrar un nuevo scraper para la plataforma X'
    git commit -am 'fix: Mejorar el parsing de salarios en el Computrabajo spider'
    ```
7.  **Sincroniza y Haz Push:** Antes de enviar tu Pull Request, asegúrate de que tu rama esté actualizada con la versión más reciente del repositorio principal para evitar conflictos. Luego, sube tus cambios a tu fork:
    ```bash
    git pull origin main # Sincroniza con la rama principal (main)
    git push origin feature/tu-nueva-funcionalidad
    ```
8.  **Abre un Pull Request (PR):** Finalmente, ve a la página de tu fork en GitHub. Verás una opción para "Open a Pull Request". Proporciona una descripción detallada de tus cambios, el problema que resuelven o la funcionalidad que añaden. ¡Estaremos encantados de revisarlo!

---

## 📄 Licencia ⚖️

Este proyecto está distribuido bajo la **Licencia MIT**. Esto te otorga una gran libertad para usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del software.

La única condición es que se incluya el aviso de derechos de autor original y este aviso de licencia en todas las copias o partes sustanciales del Software.

Para leer el texto completo de la licencia, por favor, consulta el archivo `LICENSE` ubicado en la raíz del repositorio.

---
**Desarrollado con ❤️ para empoderar el mercado laboral.**