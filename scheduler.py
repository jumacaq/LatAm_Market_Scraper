import schedule
import time
import subprocess
import logging

logging.basicConfig(filename='scheduler.log', level=logging.INFO)

def job_scrape():
    logging.info("Starting scheduled scrape...")
    subprocess.run(["python", "main.py", "scrape"])

def job_enrich():
    logging.info("Starting scheduled enrichment...")
    subprocess.run(["python", "main.py", "enrich"])

# Schedule daily runs
schedule.every().day.at("08:00").do(job_scrape)

if __name__ == "__main__":
    print("Scheduler running... Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)