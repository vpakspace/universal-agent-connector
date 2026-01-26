-- Grant SELECT permissions to cloudbadal user on all tables
-- Run this as a database administrator (e.g., postgres user)

-- Grant permissions on individual tables
GRANT SELECT ON TABLE public.school TO cloudbadal;
GRANT SELECT ON TABLE public.class TO cloudbadal;
GRANT SELECT ON TABLE public.student TO cloudbadal;
GRANT SELECT ON TABLE public.enrollment TO cloudbadal;

-- Alternative: Grant all privileges on all tables in public schema
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cloudbadal;

-- Verify permissions (optional)
SELECT 
    grantee, 
    table_schema, 
    table_name, 
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'cloudbadal'
    AND table_schema = 'public'
    AND table_name IN ('school', 'class', 'student', 'enrollment')
ORDER BY table_name, privilege_type;






