from supabase import create_client
import os
from datetime import datetime
from collections import Counter

# --- Supabase config ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def run_trends():
    print("📈 Updating trends...")

    jobs = supabase.table("jobs").select("*").execute().data

    # --- Top skills ---
    all_skills = []
    for job in jobs:
        if job.get("skills"):
            all_skills.extend(job["skills"])

    skill_counts = Counter(all_skills).most_common(50)

    # delete old
    supabase.table("trends").delete().neq("id", -1).execute()

    # insert new
    for skill, count in skill_counts:
        supabase.table("trends").insert({
            "metric": "skills_top",
            "key": skill,
            "value": count,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

    print("✨ Trends updated.")

if __name__ == "__main__":
    run_trends()
