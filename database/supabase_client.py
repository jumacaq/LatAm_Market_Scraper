import os
from supabase import create_client, Client

class SupabaseClient:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if url and key:
            self.supabase: Client = create_client(url, key)
        else:
            raise Exception("Supabase credentials missing in .env")

    def upsert_job(self, job_data):
        # Upsert data into 'jobs' table
        data = self.supabase.table("jobs").upsert(job_data).execute()
        return data
        
    def get_jobs(self, limit=100):
        return self.supabase.table("jobs").select("*").order('created_at', desc=True).limit(limit).execute()