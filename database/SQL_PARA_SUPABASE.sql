-- Esquema SQL para Supabase (tablas 'jobs', 'skills', 'companies', 'trends')

-- Tabla de Compañías (companies)
CREATE TABLE public.companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    industry TEXT,
    country TEXT,
    website TEXT,
    description TEXT,
    size TEXT,
    type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public companies are viewable by all." ON public.companies FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert companies." ON public.companies FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to update companies." ON public.companies FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to delete companies." ON public.companies FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');


-- Tabla de Trabajos (jobs)
CREATE TABLE public.jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT NOT NULL, -- ID único de la plataforma (ej. LinkedIn Job ID)
    source_platform TEXT NOT NULL, -- Plataforma de origen (LinkedIn, Computrabajo, Indeed)
    title TEXT NOT NULL,
    company_name TEXT NOT NULL, -- Nombre de la compañía directamente (podría ser FK a companies.id)
    location TEXT,
    country TEXT,
    job_type TEXT,
    seniority_level TEXT,
    sector TEXT,
    role_category TEXT,
    description TEXT,
    requirements TEXT,
    salary_range TEXT,
    posted_date DATE,
    source_url TEXT UNIQUE NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    is_active BOOLEAN DEFAULT TRUE,
    company_id uuid REFERENCES public.companies(id) ON DELETE SET NULL, -- Clave foránea a la tabla de compañías
    
    -- Campos de enriquecimiento directo para simplificar la consulta desde `jobs`
    company_size TEXT,
    company_industry TEXT,
    company_hq_country TEXT,
    company_type TEXT,
    company_website TEXT,

    CONSTRAINT unique_job_platform UNIQUE (job_id, source_platform) -- Deduplicación clave
);

ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public jobs are viewable by all." ON public.jobs FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert jobs." ON public.jobs FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to update jobs." ON public.jobs FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to delete jobs." ON public.jobs FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Índices para mejorar rendimiento de búsqueda
CREATE INDEX jobs_company_name_idx ON public.jobs (company_name);
CREATE INDEX jobs_country_idx ON public.jobs (country);
CREATE INDEX jobs_sector_idx ON public.jobs (sector);
CREATE INDEX jobs_seniority_idx ON public.jobs (seniority_level);
CREATE INDEX jobs_posted_date_idx ON public.jobs (posted_date DESC);
CREATE INDEX jobs_scraped_at_idx ON public.jobs (scraped_at DESC);


-- Tabla de Habilidades (skills)
CREATE TABLE public.skills (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL, -- FK a la tabla jobs
    skill_name TEXT NOT NULL,
    skill_category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    
    CONSTRAINT unique_job_skill UNIQUE (job_id, skill_name) -- Para evitar duplicados de habilidades por trabajo
);

ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public skills are viewable by all." ON public.skills FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert skills." ON public.skills FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to update skills." ON public.skills FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to delete skills." ON public.skills FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE INDEX skills_skill_name_idx ON public.skills (skill_name);


-- Tabla de Tendencias (trends)
CREATE TABLE public.trends (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    metric_name TEXT NOT NULL, -- Ej. 'most_demanded_skill', 'growing_skill', 'sector_distribution'
    metric_value TEXT NOT NULL, -- Ej. 'Python', 'Fintech', 'Software Engineer'
    count INTEGER, -- Valor asociado a la métrica (ej. frecuencia)
    sector TEXT, -- Filtro opcional por sector
    country TEXT, -- Filtro opcional por país
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),

    CONSTRAINT unique_trend_day_metric UNIQUE (date, metric_name, metric_value, sector, country)
);

ALTER TABLE public.trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public trends are viewable by all." ON public.trends FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to insert trends." ON public.trends FOR INSERT WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to update trends." ON public.trends FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Allow authenticated users to delete trends." ON public.trends FOR DELETE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE INDEX trends_date_idx ON public.trends (date DESC);
CREATE INDEX trends_metric_name_idx ON public.trends (metric_name);