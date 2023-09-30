ALTER TABLE "user"
    ADD added_at            timestamptz DEFAULT CURRENT_TIMESTAMP,
    ADD last_interaction_at timestamptz DEFAULT CURRENT_TIMESTAMP;

UPDATE "user"
SET added_at=CURRENT_TIMESTAMP
WHERE added_at IS NULL;

UPDATE "user"
SET last_interaction_at=CURRENT_TIMESTAMP
WHERE last_interaction_at IS NULL;

ALTER TABLE "user"
    ALTER COLUMN added_at SET NOT NULL,
    ALTER COLUMN last_interaction_at SET NOT NULL;
