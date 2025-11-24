@echo off
title Market Scraper Dashboard
echo ===================================================
echo   JOB MARKET INTELLIGENCE - DASHBOARD
echo ===================================================
echo.
echo [PASO 1] Verificando e instalando dependencias...
python -m pip install -q -r requirements.txt

echo.
echo [PASO 2] Iniciando Dashboard...
echo Si el navegador no se abre, ve a: http://localhost:8501
echo.
python -m streamlit run dashboard.py
pause