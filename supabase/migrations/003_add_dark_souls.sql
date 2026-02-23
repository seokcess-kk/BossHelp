-- Add Dark Souls series to games table
-- Version: 1.0
-- Date: 2026-02-23

INSERT INTO games (id, title, genre, subreddit, wiki_base_url) VALUES
    ('dark-souls', 'Dark Souls: Remastered', 'soulslike', 'r/darksouls', 'https://darksouls.wiki.fextralife.com'),
    ('dark-souls-2', 'Dark Souls II: SOTFS', 'soulslike', 'r/DarkSouls2', 'https://darksouls2.wiki.fextralife.com'),
    ('dark-souls-3', 'Dark Souls III', 'soulslike', 'r/darksouls3', 'https://darksouls3.wiki.fextralife.com')
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    wiki_base_url = EXCLUDED.wiki_base_url,
    updated_at = now();
