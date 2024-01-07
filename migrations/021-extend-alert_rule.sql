ALTER TABLE alert_history
    ADD alert_rule_id integer;

UPDATE alert_history
SET alert_rule_id= -1
WHERE alert_rule_id IS NULL;

ALTER TABLE alert_history
    ALTER COLUMN alert_rule_id SET NOT NULL;

CREATE INDEX alert_history_alert_rule_id_index
    ON alert_history (alert_rule_id);
