-- Run this SQL in your Supabase SQL Editor to update your database schema
-- and erase the old task data.

-- 1. Erase old tasks entirely
DELETE FROM station_tasks;

-- 2. Add new columns for daily tasks and details (if they don't already exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='station_tasks' AND column_name='day_of_week') THEN
        ALTER TABLE station_tasks ADD COLUMN day_of_week TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='station_tasks' AND column_name='details') THEN
        ALTER TABLE station_tasks ADD COLUMN details TEXT;
    END IF;
END $$;
