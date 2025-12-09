import pandas as pd
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_jobs():
    data = supabase.table("jobs").select("*").execute().data
    return pd.DataFrame(data)

def jobs_by_country(df):
    return df["location"].value_counts()

def monthly_trends(df):
    df["month"] = pd.to_datetime(df["created_at"]).dt.to_period("M")
    return df.groupby("month").size()

def top_companies(df):
    return df["company_name"].value_counts().head(20)

if __name__ == "__main__":
    df = load_jobs()
    print(jobs_by_country(df))
    print(monthly_trends(df))
    print(top_companies(df))
