-- Initial database schema for Enterprise Architecture Solution

-- User profiles (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users NOT NULL PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    organization TEXT,
    department TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT users_email_unique UNIQUE (email)
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- User Policies
CREATE POLICY "Users can view their own profile"
    ON public.users
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Admin users can update any profile"
    ON public.users
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.users
            WHERE auth.uid() = public.users.id AND role = 'admin'
        )
    );

-- EA Domains Table
CREATE TABLE IF NOT EXISTS public.ea_domains (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_domains_name_unique UNIQUE (name)
);

-- EA Element Types Table
CREATE TABLE IF NOT EXISTS public.ea_element_types (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    domain_id UUID REFERENCES public.ea_domains NOT NULL,
    name TEXT NOT NULL,
    icon TEXT,
    description TEXT,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_element_types_domain_name_unique UNIQUE (domain_id, name)
);

-- EA Relationship Types Table
CREATE TABLE IF NOT EXISTS public.ea_relationship_types (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    source_domain_id UUID REFERENCES public.ea_domains,
    target_domain_id UUID REFERENCES public.ea_domains,
    directional BOOLEAN DEFAULT TRUE NOT NULL,
    icon TEXT,
    description TEXT,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_relationship_types_name_unique UNIQUE (name)
);

-- EA Models Table
CREATE TABLE IF NOT EXISTS public.ea_models (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK (status IN ('draft', 'review', 'approved', 'archived')),
    version TEXT,
    created_by UUID REFERENCES public.users NOT NULL,
    updated_by UUID REFERENCES public.users,
    lifecycle_state TEXT CHECK (lifecycle_state IN ('current', 'target', 'transitional')),
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_models_name_version_unique UNIQUE (name, version)
);

-- EA Elements Table
CREATE TABLE IF NOT EXISTS public.ea_elements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_id UUID REFERENCES public.ea_models NOT NULL,
    type_id UUID REFERENCES public.ea_element_types NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by UUID REFERENCES public.users NOT NULL,
    updated_by UUID REFERENCES public.users,
    external_id TEXT,
    external_source TEXT,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    position_x FLOAT,
    position_y FLOAT,
    status TEXT CHECK (status IN ('draft', 'review', 'approved', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_elements_model_name_unique UNIQUE (model_id, name)
);

-- EA Relationships Table
CREATE TABLE IF NOT EXISTS public.ea_relationships (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_id UUID REFERENCES public.ea_models NOT NULL,
    relationship_type_id UUID REFERENCES public.ea_relationship_types NOT NULL,
    source_element_id UUID REFERENCES public.ea_elements NOT NULL,
    target_element_id UUID REFERENCES public.ea_elements NOT NULL,
    name TEXT,
    description TEXT,
    created_by UUID REFERENCES public.users NOT NULL,
    updated_by UUID REFERENCES public.users,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    status TEXT CHECK (status IN ('draft', 'review', 'approved', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- EA Views Table (for visualizations)
CREATE TABLE IF NOT EXISTS public.ea_views (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_id UUID REFERENCES public.ea_models NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    view_type TEXT NOT NULL CHECK (view_type IN ('diagram', 'matrix', 'heatmap', 'roadmap', 'list')),
    configuration JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_by UUID REFERENCES public.users NOT NULL,
    updated_by UUID REFERENCES public.users,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    
    CONSTRAINT ea_views_model_name_unique UNIQUE (model_id, name)
);

-- Integration Configurations Table
CREATE TABLE IF NOT EXISTS public.integration_configs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    integration_type TEXT NOT NULL CHECK (integration_type IN ('halo_itsm', 'entra_id', 'sharepoint', 'power_bi')),
    configuration JSONB NOT NULL,
    status TEXT CHECK (status IN ('active', 'inactive', 'error')),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES public.users NOT NULL,
    updated_by UUID REFERENCES public.users,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- AI Generated Content Table
CREATE TABLE IF NOT EXISTS public.ai_generated_content (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content_type TEXT NOT NULL CHECK (content_type IN ('suggestion', 'documentation', 'analysis', 'pattern')),
    content TEXT NOT NULL,
    related_element_id UUID REFERENCES public.ea_elements,
    related_model_id UUID REFERENCES public.ea_models,
    prompt TEXT NOT NULL,
    created_by UUID REFERENCES public.users NOT NULL,
    properties JSONB DEFAULT '{}'::jsonb NOT NULL,
    applied BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Insert default domains
INSERT INTO public.ea_domains (name, description)
VALUES 
  ('Performance', 'Performance architecture domain'),
  ('Business', 'Business architecture domain'),
  ('Services', 'Services architecture domain'),
  ('Data', 'Data architecture domain'),
  ('Technology', 'Technology architecture domain')
ON CONFLICT (name) DO NOTHING;