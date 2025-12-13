import google.generativeai as genai
import os

class ReportGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    def generate_daily_insight(self, jobs_data):
        if not self.model:
            return "⚠️ Configura GEMINI_API_KEY para generar reportes con IA."
            
        data_summary = ""
        for job in jobs_data:
            data_summary += f"- {job.get('title')} en {job.get('company')} ({job.get('sector')})\n"
            
        prompt = f"""
        Analiza estos datos recientes del mercado laboral:
        {data_summary}
        
        Genera un resumen ejecutivo breve en Markdown destacando:
        1. Roles más demandados.
        2. Empresas contratando activamente.
        3. Tendencias por sector.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generando reporte: {e}"