ALTER TABLE filter
    ADD source_new_id bigint;

WITH src AS (SELECT s.id, s.tg_id
             FROM source s)
UPDATE filter
SET source_new_id = src.tg_id
FROM src
WHERE filter.source_id = src.id;

-- category_message_history -> source_chat_id
-- filter_message_history -> source_chat_id

ALTER TABLE filter
    DROP CONSTRAINT filter_source_id_fkey;

ALTER TABLE category_message_history
    DROP CONSTRAINT categorymessagehistory_source_id_fkey;

ALTER TABLE filter_message_history
    DROP CONSTRAINT filtermessagehistory_source_id_fkey;

--

ALTER TABLE filter
    DROP COLUMN source_id;

ALTER TABLE category_message_history
    DROP COLUMN source_id;

ALTER TABLE filter_message_history
    DROP COLUMN source_id;

--

ALTER TABLE filter
    RENAME COLUMN source_new_id TO source_id;

ALTER TABLE category_message_history
    RENAME COLUMN source_chat_id TO source_id;

ALTER TABLE filter_message_history
    RENAME COLUMN source_chat_id TO source_id;

--

DROP INDEX source_tg_id;

ALTER TABLE source
    DROP CONSTRAINT source_pkey;

ALTER TABLE source
    DROP COLUMN id;

--

ALTER TABLE source
    RENAME COLUMN tg_id TO id;

ALTER TABLE source
    ADD CONSTRAINT source_pk
        PRIMARY KEY (id);

--

CREATE INDEX IF NOT EXISTS "filtermessagehistory_source_id" ON "filter_message_history" ("source_id");
CREATE INDEX IF NOT EXISTS "categorymessagehistory_source_id" ON "category_message_history" ("source_id");

--

ALTER TABLE filter
    ADD FOREIGN KEY (source_id) REFERENCES source (id)
        ON DELETE CASCADE;

ALTER TABLE category_message_history
    ADD CONSTRAINT categorymessagehistory_source_id_fkey
        FOREIGN KEY (source_id) REFERENCES source (id)
            ON DELETE CASCADE;

ALTER TABLE filter_message_history
    ADD CONSTRAINT filtermessagehistory_source_id_fkey
        FOREIGN KEY (source_id) REFERENCES source (id)
            ON DELETE CASCADE;
