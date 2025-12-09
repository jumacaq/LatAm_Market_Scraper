# etl/update_data.py
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# Import cleaning helpers
from cleaning import clean_jobs#, clean_skills   

load_dotenv()

# ---------------------------------------------------
# SUPABASE CONNECTION
# ---------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")   # Usamos service key SOLO en backend

client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------
# 🔥 HARD DELETE (Opción A)
# ---------------------------
def wipe_table(table_name):
    """Delete ALL rows from a table."""
    print(f"⚠ Borrando todos los datos de '{table_name}'...")
    client.table(table_name).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"✔ Tabla '{table_name}' vaciada correctamente.\n")


# ---------------------------
# 🔽 Descargar datos crudos
# ---------------------------
def load_raw():
    print("📥 Cargando datos desde Supabase...")

    jobs_raw = client.table("jobs").select("*").execute().data
    
    skills_raw = client.table("skills").select("*").execute().data

    print(f"Jobs cargados: {len(jobs_raw)}")
    print(f"Skills cargadas: {len(skills_raw)}")

    df_jobs = pd.DataFrame(jobs_raw)
    df_skills = pd.DataFrame(skills_raw)

    return df_jobs, df_skills


# ---------------------------
# 🔼 Subir datos limpios
# ---------------------------
def upload_clean_data(df_jobs_clean, df_skills_clean):

    # 1️⃣ BORRAR TABLAS COMPLETAS
    wipe_table("skills")     # primero skills (depende de jobs)
    wipe_table("jobs")

    # 2️⃣ REINSERTAR JOBS
    print("⬆ Subiendo jobs limpios...")
    if len(df_jobs_clean) > 0:
        client.table("jobs").insert(df_jobs_clean.to_dict(orient="records")).execute()
        print(f"✔ Insertados {len(df_jobs_clean)} jobs limpios.\n")
    else:
        print("⚠ No hay jobs limpios para insertar.\n")

    # 3️⃣ REINSERTAR SKILLS
    print("⬆ Subiendo skills limpias...")
    if len(df_skills_clean) > 0:
        client.table("skills").insert(df_skills_clean.to_dict(orient="records")).execute()
        print(f"✔ Insertadas {len(df_skills_clean)} skills limpias.\n")
    else:
        print("⚠ No hay skills limpias para insertar.\n")


# ---------------------------
# 🚀 MAIN ETL PROCESS
# ---------------------------
def run_etl():

    # cargar datos del scraping
    #df_jobs, df_skills = load_raw()

    # limpiar jobs
    #print("\n🧹 Limpiando tabla jobs...")
    #df_jobs_clean = clean_jobs(df_jobs)
    #print(f"Jobs tras limpieza: {len(df_jobs_clean)}")

    # limpiar skills
    #print("\n🧹 (Saltado) No se aplica limpieza de skills...")
    #df_skills_clean = df_skills.copy()
    #print(f"Skills tras limpieza: {len(df_skills_clean)}")


    # subir
    #upload_clean_data(df_jobs_clean, df_skills_clean)

    #print("\n🎯 ETL COMPLETADO CON ÉXITO\n")


if __name__ == "__main__":
    run_etl()