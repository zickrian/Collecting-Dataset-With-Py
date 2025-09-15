-- SQL untuk membuat tabel di Supabase
-- Jalankan script ini di SQL Editor Supabase

-- Tabel untuk menyimpan video ID yang sudah diproses
CREATE TABLE IF NOT EXISTS youtube_videos (
    id SERIAL PRIMARY KEY,
    video_id TEXT UNIQUE NOT NULL,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk menyimpan komentar YouTube (sudah Anda buat)
CREATE TABLE IF NOT EXISTS youtube_comments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    author_name TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    like_count INTEGER DEFAULT 0
);

-- Index untuk performa query
CREATE INDEX IF NOT EXISTS idx_youtube_videos_video_id ON youtube_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_youtube_comments_created_at ON youtube_comments(created_at);
CREATE INDEX IF NOT EXISTS idx_youtube_comments_author ON youtube_comments(author_name);

-- Row Level Security (RLS) - Opsional, disable untuk testing
ALTER TABLE youtube_videos DISABLE ROW LEVEL SECURITY;
ALTER TABLE youtube_comments DISABLE ROW LEVEL SECURITY;

-- Fix SERIAL sequence untuk menghindari duplicate key error
-- Sinkronkan sequence dengan nilai id terakhir di tabel, lalu +1 untuk next insert
SELECT setval('youtube_videos_id_seq', (SELECT COALESCE(MAX(id), 0) FROM youtube_videos));
SELECT setval('youtube_comments_id_seq', (SELECT COALESCE(MAX(id), 0) FROM youtube_comments));

-- ALTERNATIF: Ganti ke IDENTITY yang lebih modern (jalankan jika mau upgrade)
-- ALTER TABLE youtube_videos ALTER COLUMN id DROP DEFAULT;
-- DROP SEQUENCE IF EXISTS youtube_videos_id_seq CASCADE;
-- ALTER TABLE youtube_videos ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (START WITH 103);

-- ALTER TABLE youtube_comments ALTER COLUMN id DROP DEFAULT;
-- DROP SEQUENCE IF EXISTS youtube_comments_id_seq CASCADE;
-- ALTER TABLE youtube_comments ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
