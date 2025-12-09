from trend_analyzer import load_jobs, jobs_by_country, monthly_trends, top_companies

def generate_report():
    df = load_jobs()

    print("\n==== JOB REPORT ====\n")
    print("Top 20 companies:")
    print(top_companies(df))

    print("\nJobs by country:")
    print(jobs_by_country(df))

    print("\nMonthly new jobs:")
    print(monthly_trends(df))

if __name__ == "__main__":
    generate_report()
