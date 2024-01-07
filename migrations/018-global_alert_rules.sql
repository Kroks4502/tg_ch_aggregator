ALTER TABLE alert_rule
    ALTER COLUMN category_id DROP NOT NULL;

ALTER TABLE alert_history
    ALTER COLUMN category_id DROP NOT NULL;
