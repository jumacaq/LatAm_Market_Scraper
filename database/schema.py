SCHEMA_SQL = """
-- Jobs Table
CREATE TABLE jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    country VARCHAR(100),
    job_type VARCHAR(100), -- Full-time, Part-time, Contract
    seniority_level VARCHAR(100), -- Junior, Mid, Senior
    sector VARCHAR(100), -- EdTech, Fintech, Future of Work
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(255),
    posted_date DATE,
    source_url TEXT,
    source_platform VARCHAR(100), -- GetonBoard, Computrabajo, etc.
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(job_id, source_platform)
);

-- Companies Table
CREATE TABLE companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    industry VARCHAR(255),
    size VARCHAR(100), -- Startup, SME, Enterprise
    country VARCHAR(100),
    website TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Skills Table (Extracted from job descriptions)
CREATE TABLE skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100), -- Programming, Framework, Tool, Soft Skill
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trends Table (Aggregated insights)
CREATE TABLE trends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL, -- e.g., "most_demanded_skill", "growing_role"
    metric_value VARCHAR(255) NOT NULL,
    count INTEGER,
    sector VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, metric_name, metric_value, sector)
);

-- Indexes for performance
CREATE INDEX idx_jobs_country ON jobs(country);
CREATE INDEX idx_jobs_sector ON jobs(sector);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_skills_name ON skills(skill_name);
CREATE INDEX idx_trends_date ON trends(date);

-- Enable Row Level Security (RLS) for public read access
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE trends ENABLE ROW LEVEL SECURITY;

-- Public read policy
CREATE POLICY "Public read access" ON jobs FOR SELECT USING (true);
CREATE POLICY "Public read access" ON companies FOR SELECT USING (true);
CREATE POLICY "Public read access" ON skills FOR SELECT USING (true);
CREATE POLICY "Public read access" ON trends FOR SELECT USING (true);
"""

print("✅ Project structure and configuration files ready!")
print("\nNext steps:")
print("1. Create the project folders")
print("2. Set up Supabase account and run schema.sql")
print("3. Install requirements: pip install -r requirements.txt")
print("4. Configure .env with your Supabase credentials")