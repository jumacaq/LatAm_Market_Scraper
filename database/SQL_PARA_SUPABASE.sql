-- FILE: job-market-intelligence/database/SQL_PARA_SUPABASE.sql

-- Jobs Table
CREATE TABLE jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL, -- ID único de la fuente (ej. ID de LinkedIn, GetonBoard)
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    country VARCHAR(100),
    job_type VARCHAR(100), -- Full-time, Part-time, Contract, Remote, Hybrid
    seniority_level VARCHAR(100), -- Junior, Mid, Senior, Lead
    sector VARCHAR(100), -- EdTech, Fintech, Future of Work, Other
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(255),
    posted_date DATE,
    source_url TEXT,
    source_platform VARCHAR(100) NOT NULL, -- LinkedIn, GetonBoard, Computrabajo, Torre
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(job_id, source_platform) -- Asegura que no haya duplicados para la misma vacante en la misma plataforma
);

-- Companies Table (para enriquecimiento futuro)
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

-- Skills Table (extraídas de las descripciones de las vacantes)
CREATE TABLE skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE, -- Clave foránea a la tabla 'jobs'
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100), -- Programming, Framework, Tool, Soft Skill
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, skill_name) -- Evita habilidades duplicadas para la misma vacante
);

-- Trends Table (para insights agregados)
CREATE TABLE trends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL, -- e.g., "most_demanded_skill", "growing_role"
    metric_value VARCHAR(255) NOT NULL,
    count INTEGER,
    sector VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, metric_name, metric_value, sector, country) -- Asegura unicidad para las tendencias
);

-- Índices para mejorar el rendimiento de las consultas
CREATE INDEX idx_jobs_country ON jobs(country);
CREATE INDEX idx_jobs_sector ON jobs(sector);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX idx_jobs_company_name ON jobs(company_name);
CREATE INDEX idx_skills_name ON skills(skill_name);
CREATE INDEX idx_trends_date ON trends(date);

-- Habilitar Row Level Security (RLS) para un control de acceso más granular
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE trends ENABLE ROW LEVEL SECURITY;

-- Políticas de lectura pública (cualquiera puede leer)
CREATE POLICY "Public read access on jobs" ON jobs FOR SELECT USING (true);
CREATE POLICY "Public read access on companies" ON companies FOR SELECT USING (true);
CREATE POLICY "Public read access on skills" ON skills FOR SELECT USING (true);
CREATE POLICY "Public read access on trends" ON trends FOR SELECT USING (true);
