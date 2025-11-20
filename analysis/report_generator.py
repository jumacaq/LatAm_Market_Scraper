import google.generativeai as genai
import os

class ReportGenerator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_daily_insight(self, jobs_data):
        # Prepare text summary of data for the LLM
        data_summary = ""
        for job in jobs_data:
            data_summary += f"- {job.get('title')} at {job.get('company')} ({job.get('sector')})\n"
            
        prompt = f"""
        Act as a Senior Market Analyst.
        Here is a list of recent job postings scraped from the market (LinkedIn, Computrabajo, Multitrabajo):
        {data_summary}
        
        Please provide a short, bulleted executive summary of the trends you see in this data.
        Focus on:
        1. Dominant sectors
        2. Hiring patterns
        3. Advice for job seekers in these fields.
        
        Format as Markdown.
        """
        
        response = self.model.generate_content(prompt)
        return response.text