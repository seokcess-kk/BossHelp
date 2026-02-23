-- Add Dark Souls series to games table
-- Version: 1.1
-- Date: 2026-02-23

INSERT INTO games (id, title, genre, subreddit, wiki_base_url, is_active) VALUES
    ('dark-souls', 'Dark Souls: Remastered', 'soulslike', 'r/darksouls', 'https://darksouls.wiki.fextralife.com', true),
    ('dark-souls-2', 'Dark Souls II: SOTFS', 'soulslike', 'r/DarkSouls2', 'https://darksouls2.wiki.fextralife.com', true),
    ('dark-souls-3', 'Dark Souls III', 'soulslike', 'r/darksouls3', 'https://darksouls3.wiki.fextralife.com', true)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    wiki_base_url = EXCLUDED.wiki_base_url,
    is_active = true,
    updated_at = now();
