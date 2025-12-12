# LatAm_Market_Scraper
# 🌎 LatAm Job Market Intelligence - MVP Setup Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup](#setup)
5. [Running the System](#running)
6. [Deployment](#deployment)
7. [Team Workflow](#team-workflow)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**Goal**: Build an intelligent scraping system to collect and analyze job market data from LatAm tech sectors (EdTech, Fintech, Future of Work).

**Target**: 500+ processed records daily, focusing on Mexico, Colombia, Argentina, Chile, Peru, and Brazil.

**Value Proposition**: Help job simulation participants understand market demands, emerging roles, and required skills.

---

## 🏗️ Architecture

---

## Project Structure

```
job-market-intelligence/
├── scrapers/
│   ├── __init__.py
│   ├── spiders/
│   │   ├── linkedin_spider.py
│   │   ├── computrabajo_spider.py
│   │   └── company_enrichment_spider.py
│   ├── items.py
│   ├── pipelines.py
│   ├── middlewares.py
│   └── settings.py
├── etl/
│   ├── cleaners.py
│   ├── normalizers.py
│   └── enrichment.py
|   └── sector_classifier.py
|   └── skill_extractor.py
├── database/
│   ├── supabase_client.py     #Config supabase
│   └── SQL_PARA_SUPABASE.sql  #Supabase tables structure
├── analysis/
│   ├── trend_analyzer.py
│   └── report_generator.py
├── notebooks/
│   └── exploratory_analysis.ipynb
├── config/
│   ├── config.yaml
│   └── geo.py
├── dashboard.py
├── main.py
└── requirements.txt
└── .gitignore
└── README.md
```

---

## 📦 Prerequisites

### Required Accounts (All Free!)
1. **GitHub Account** - For code hosting and automation
2. **Supabase Account** - Database (500MB free)
3. **Streamlit Cloud Account** - Dashboard hosting link:



### Local Development Requirements
- Python 3.9 or higher
- Git
- Text editor (VS Code recommended)
- Terminal/Command Line access

---

## 🚀 Step-by-Step Setup

### Phase 1: Local Environment Setup (30 minutes)

#### 1. Clone and Setup Project
```bash
# Create project directory
mkdir latam-job-intelligence
cd latam-job-intelligence

# Initialize git
git init

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Create project structure
mkdir -p scrapers/jobscraper/spiders
mkdir -p etl database analysis dashboard/pages config notebooks tests
mkdir -p .github/workflows
```

#### 2. Install Dependencies
Create `requirements.txt`:
```txt
scrapy==2.11.0
beautifulsoup4==4.12.2
selenium==4.15.2
requests==2.31.0
supabase==2.3.0
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.26.2
plotly==5.18.0
streamlit==1.29.0
pyyaml==6.0.1
fake-useragent==1.4.0
python-dateutil==2.8.2
```

Install:
```bash
pip install -r requirements.txt
```

#### 3. Create Environment Variables
Create `.env` file:
```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

Create `.env.example` (for team):
```env
SUPABASE_URL=
SUPABASE_KEY=
```

#### 4. Create .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
*.egg-info/

# Environment
.env

# Scrapy
.scrapy/
httpcache/

# IDE
.vscode/
.idea/

# Logs
*.log
scraper.log

# Data
*.csv
*.json
data/
```

---

### Phase 2: Database Setup (15 minutes)

#### 1. Create Supabase Project
1. Go to [https://supabase.com](https://supabase.com)
2. Sign up with GitHub
3. Click "New Project"
4. Fill in:
   - **Name**: latam-job-intelligence
   - **Database Password**: (save this securely!)
   - **Region**: Choose closest to LatAm (US East recommended)
5. Wait 2-3 minutes for project creation

#### 2. Run Database Schema
1. In Supabase dashboard, go to **SQL Editor**
2. Copy the schema from `database/schema.sql` (from the artifacts I created)
3. Click **Run**
4. Verify tables created: Go to **Table Editor**

#### 3. Get API Credentials
1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public key** (long string starting with `eyJ...`)
3. Add to your `.env` file

#### 4. Test Connection
Create `test_connection.py`:
```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

client = create_client(url, key)
response = client.table('jobs').select('*').limit(1).execute()

print("✅ Connection successful!" if response else "❌ Connection failed")
```

Run:
```bash
python test_connection.py
```

---

### Phase 3: Scrapy Configuration (20 minutes)

#### 1. Initialize Scrapy Project
```bash
cd scrapers
scrapy startproject jobscraper
cd jobscraper
```

#### 2. Add Files
Copy the following files from the artifacts I created:
- `items.py` - Data models
- `pipelines.py` - ETL logic
- `settings.py` - Scrapy configuration
- `spiders/getonboard_spider.py`
- `spiders/torre_spider.py`
- `spiders/computrabajo_spider.py`

#### 3. Test a Spider
```bash
# Test GetonBoard spider (most reliable)
scrapy crawl getonboard -o test_output.json

# Check output
cat test_output.json
```

Expected output: JSON array with job data

---

### Phase 4: Dashboard Setup (15 minutes)

#### 1. Create Dashboard Files
Copy `dashboard/app.py` from artifacts.

#### 2. Test Dashboard Locally
```bash
streamlit run dashboard/app.py
```

Opens browser at `http://localhost:8501`

**Expected**: Dashboard loads (may show "no data" if scrapers haven't run yet)

---

### Phase 5: Automation Setup (20 minutes)

#### 1. Create GitHub Actions Workflow
Copy `.github/workflows/scrape_daily.yml` from artifacts.

#### 2. Add Orchestrator Script
Copy `run_scraper.py` to project root.

#### 3. Test Locally
```bash
python run_scraper.py
```

This should run all three scrapers sequentially.

---

## 🎮 Running the System

### Local Development

#### Run Single Spider
```bash
cd scrapers/jobscraper
scrapy crawl getonboard
```

#### Run All Scrapers
```bash
python run_scraper.py
```

#### Generate Report
```bash
python analysis/report_generator.py
```

#### Start Dashboard
```bash
streamlit run dashboard/app.py
```

---

## 🚀 Deployment (All Free!)

### 1. Deploy to GitHub

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: LatAm Job Intelligence MVP"

# Create GitHub repo (via GitHub website)
# Then push:
git remote add origin https://github.com/YOUR-USERNAME/latam-job-intelligence.git
git push -u origin main
```

### 2. Configure GitHub Secrets

1. Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon key

### 3. Enable GitHub Actions

1. Go to **Actions** tab
2. You should see "Daily Job Scraping" workflow
3. Click **Enable workflow**
4. Optionally, click **Run workflow** to test immediately

**Schedule**: Runs automatically every day at 6 AM UTC (1-3 AM LatAm time)

### 4. Deploy Dashboard to Streamlit Cloud

1. Go to [Link Streamlit](https://proyecto-no-country-suy3cnnrkvzkdja5rfhovq.streamlit.app/)
2. Sign in with GitHub
3. Click **New app**
4. Select:
   - **Repository**: your-username/latam-job-intelligence
   - **Branch**: main
   - **Main file**: dashboard/app.py
5. Click **Advanced settings** → Add secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
6. Click **Deploy**


---

## 👥 Team Workflow

### Daily Operations

1. **Automated Scraping**: Runs daily via GitHub Actions
2. **Data Updates**: Automatically flows to Supabase
3. **Dashboard**: Auto-updates (refresh browser)
4. **Monitoring**: Check GitHub Actions logs

### Team Roles

#### Developer 1: Spiders & ETL
- Maintain spider code
- Fix broken scrapers
- Add new data sources
- Improve extraction logic

#### Developer 2: Data & Analysis
- Monitor data quality
- Create analysis notebooks
- Generate insights
- Update trend algorithms

#### Developer 3: Dashboard & Reporting
- Improve visualizations
- Add new dashboard features
- Generate weekly reports
- User experience improvements

### Weekly Tasks

**Monday**:
- Review weekend scraping logs
- Check data quality metrics
- Plan weekly improvements

**Wednesday**:
- Mid-week data analysis
- Test new features locally
- Update documentation

**Friday**:
- Deploy improvements
- Generate weekly report
- Team knowledge sharing session

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Scrapers Failing
```bash
# Check logs
cat scraper.log

# Test single spider with verbose mode
scrapy crawl getonboard -L DEBUG

# Check if site structure changed
scrapy shell "https://www.getonbrd.com/jobs"
```

**Solution**: Update CSS selectors in spider code.

#### 2. Database Connection Errors
```python
# Test connection
python test_connection.py

# Check credentials
cat .env
```

**Solution**: Verify Supabase URL and key are correct.

#### 3. GitHub Actions Failing
1. Go to **Actions** tab
2. Click failed workflow
3. Check error logs
4. Common fixes:
   - Verify secrets are set correctly
   - Check requirements.txt is complete
   - Ensure scrapy project structure is correct

#### 4. Dashboard Not Showing Data
```bash
# Check if data exists in Supabase
# Go to Supabase → Table Editor → jobs table

# Test locally
streamlit run dashboard/app.py
```

**Solution**: Run scrapers first if no data exists.

---

## 📊 Success Metrics

Track these to verify MVP success:

- ✅ **500+ jobs** scraped weekly
- ✅ **3+ countries** covered
- ✅ **3+ sectors** (EdTech, Fintech, Future of Work)
- ✅ **50+ skills** extracted
- ✅ **95%+ uptime** on GitHub Actions
- ✅ **Daily dashboard updates**

---

## 🎓 Learning Resources

### For Team Members

**Scrapy**:
- [Official Docs](https://docs.scrapy.org/)
- [Scrapy Tutorial](https://docs.scrapy.org/en/latest/intro/tutorial.html)

**Supabase**:
- [Quickstart](https://supabase.com/docs/guides/getting-started)
- [Python Client](https://supabase.com/docs/reference/python/introduction)

**Streamlit**:
- [Get Started](https://docs.streamlit.io/library/get-started)
- [Dashboard Examples](https://streamlit.io/gallery)

---

## 🚦 Next Steps After MVP

### Phase 2 (Optional Enhancements)
1. Add email notifications for daily reports
2. Implement salary prediction ML model
3. Add more job boards (LinkedIn API alternatives)
4. Create mobile-responsive dashboard
5. Add user authentication for personalized insights
6. Implement job matching algorithm

---

## 📞 Support

**Issues**: Create GitHub issue in repository  
**Questions**: Team Slack channel  
**Documentation**: Check `docs/` folder

---

## 📄 License

This project is for educational purposes as part of job simulation training.

---

**Built with ❤️ for LatAm Tech Talent**

Last updated: December 2025