ALTER TABLE source
    RENAME COLUMN cleanup_regex TO cleanup_list;

UPDATE global_settings
SET key = 'cleanup_list'
WHERE key = 'cleanup_regex';
