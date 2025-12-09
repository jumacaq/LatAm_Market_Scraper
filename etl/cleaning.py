import re
import pandas as pd

# ----------------------------------------------
# TEXT CLEANING
# ----------------------------------------------
def clean_text(t):
    if not t:
        return None
    t = re.sub(r"\s+", " ", t)
    t = t.replace("\u200b", "")
    return t.strip()


# ----------------------------------------------
# LOCATION & COUNTRY NORMALIZATION
# ----------------------------------------------
COUNTRY_MAP = {
    "méxico": "Mexico",
    "mexico": "Mexico",
    "cdmx": "Mexico",
    "perú": "Peru",
    "peru": "Peru",
    "chile": "Chile",
    "argentina": "Argentina",
    "colombia": "Colombia",
    "ecuador": "Ecuador",
    "brasil": "Brazil",
    "brazil": "Brazil",
}

def normalize_location(location):
    if not location:
        return None
    loc = clean_text(location).lower()

    for k, v in COUNTRY_MAP.items():
        if k in loc:
            return v  # returns the country only

    return location.title()


# ----------------------------------------------
# DATAFRAME CLEANING (JOBS)
# ----------------------------------------------
def clean_jobs(df):
    df = df.copy()

    df["title"] = df["title"].apply(clean_text)
    df["company_name"] = df["company_name"].apply(clean_text)
    df["location"] = df["location"].apply(clean_text)
    df["description"] = df["description"].apply(clean_text)

    # Normalize country
    df["country"] = df["location"].apply(normalize_location)

    # Deduplicate by job_id
    df = df.drop_duplicates(subset=["job_id"], keep="last")

    # Remove empty rows
    df = df[df["title"].notna() & df["company_name"].notna()]

    return df


# ----------------------------------------------
# CLEAN SKILLS TABLE
# ----------------------------------------------
#def clean_skills(df_skills, df_jobs):
    #df_skills = df_skills.copy()

    # Normalizar textos
    #if "skill_name" in df_skills.columns:
       # df_skills["skill_name"] = df_skills["skill_name"].apply(clean_text)

    #if "skill_category" in df_skills.columns:
        #df_skills["skill_category"] = df_skills["skill_category"].apply(clean_text)

    # Mantener solo skills con job_id válido (no vacío)
    #df_skills = df_skills[df_skills["job_id"].notna()]
    #df_skills = df_skills[df_skills["job_id"].astype(str).str.strip() != ""]

    # 🔥 FILTRAR skills cuya job_id sí exista en df_jobs_clean
    v#alid_job_ids = set(df_jobs["job_id"].astype(str))
    #df_skills["job_id"] = df_skills["job_id"].astype(str)
    #df_skills = df_skills[df_skills["job_id"].isin(valid_job_ids)]

    # Quitar duplicados por job_id + skill_name
    #if "skill_name" in df_skills.columns:
        #df_skills = df_skills.drop_duplicates(subset=["job_id", "skill_name"])

    #return df_skills
