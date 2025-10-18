-- ===============================================
-- Dr. Aunty Health Bot - Complete Database Setup
-- ===============================================
-- Run this ONCE in your Supabase SQL Editor
-- Safe to run multiple times - handles existing objects
-- ===============================================

-- 1. Create tables (if they don't exist)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health_reports (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    test_date DATE,
    lab_data JSONB,
    analysis TEXT,
    response_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS video_summaries (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    script TEXT,
    video_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- NEW: Family Connect - Caregiver relationships
CREATE TABLE IF NOT EXISTS caregivers (
    id SERIAL PRIMARY KEY,
    patient_telegram_id BIGINT NOT NULL,
    caregiver_telegram_id BIGINT NOT NULL,
    caregiver_name TEXT,
    relationship TEXT DEFAULT 'family',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (patient_telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    UNIQUE(patient_telegram_id, caregiver_telegram_id)
);

-- 2. Create indexes (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_health_reports_telegram_id ON health_reports(telegram_id);
CREATE INDEX IF NOT EXISTS idx_health_reports_created_at ON health_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_summaries_telegram_id ON video_summaries(telegram_id);
CREATE INDEX IF NOT EXISTS idx_caregivers_patient_id ON caregivers(patient_telegram_id);
CREATE INDEX IF NOT EXISTS idx_caregivers_caregiver_id ON caregivers(caregiver_telegram_id);

-- 3. Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE caregivers ENABLE ROW LEVEL SECURITY;

-- 4. Drop old policies (to avoid "already exists" errors)
DROP POLICY IF EXISTS "Service role can do everything on users" ON users;
DROP POLICY IF EXISTS "Service role can do everything on health_reports" ON health_reports;
DROP POLICY IF EXISTS "Service role can do everything on video_summaries" ON video_summaries;
DROP POLICY IF EXISTS "Service role can do everything on caregivers" ON caregivers;
DROP POLICY IF EXISTS "Anon can insert users" ON users;
DROP POLICY IF EXISTS "Anon can update users" ON users;
DROP POLICY IF EXISTS "Anon can select users" ON users;
DROP POLICY IF EXISTS "Anon can insert health_reports" ON health_reports;
DROP POLICY IF EXISTS "Anon can select health_reports" ON health_reports;
DROP POLICY IF EXISTS "Anon can insert video_summaries" ON video_summaries;
DROP POLICY IF EXISTS "Anon can select video_summaries" ON video_summaries;
DROP POLICY IF EXISTS "Anon can insert caregivers" ON caregivers;
DROP POLICY IF EXISTS "Anon can select caregivers" ON caregivers;
DROP POLICY IF EXISTS "Anon can update caregivers" ON caregivers;
DROP POLICY IF EXISTS "Anon can delete caregivers" ON caregivers;

-- 5. Create policies for service role
CREATE POLICY "service_role_all_users" 
    ON users FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "service_role_all_health_reports" 
    ON health_reports FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "service_role_all_video_summaries" 
    ON video_summaries FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "service_role_all_caregivers" 
    ON caregivers FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

-- 6. Create policies for anon/authenticated (your bot)
CREATE POLICY "anon_insert_users" 
    ON users FOR INSERT 
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "anon_update_users" 
    ON users FOR UPDATE 
    TO anon, authenticated
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "anon_select_users" 
    ON users FOR SELECT 
    TO anon, authenticated
    USING (true);

CREATE POLICY "anon_insert_health_reports" 
    ON health_reports FOR INSERT 
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "anon_select_health_reports" 
    ON health_reports FOR SELECT 
    TO anon, authenticated
    USING (true);

CREATE POLICY "anon_insert_video_summaries" 
    ON video_summaries FOR INSERT 
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "anon_select_video_summaries" 
    ON video_summaries FOR SELECT 
    TO anon, authenticated
    USING (true);

CREATE POLICY "anon_insert_caregivers" 
    ON caregivers FOR INSERT 
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "anon_select_caregivers" 
    ON caregivers FOR SELECT 
    TO anon, authenticated
    USING (true);

CREATE POLICY "anon_update_caregivers" 
    ON caregivers FOR UPDATE 
    TO anon, authenticated
    USING (true) 
    WITH CHECK (true);

CREATE POLICY "anon_delete_caregivers" 
    ON caregivers FOR DELETE 
    TO anon, authenticated
    USING (true);

-- ===============================================
-- ✅ DONE! Verify everything:
-- ===============================================
SELECT 'Tables created:' as status;
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('users', 'health_reports', 'video_summaries', 'caregivers');

SELECT 'Policies created:' as status;
SELECT tablename, policyname FROM pg_policies WHERE tablename IN ('users', 'health_reports', 'video_summaries', 'caregivers') ORDER BY tablename, policyname;

