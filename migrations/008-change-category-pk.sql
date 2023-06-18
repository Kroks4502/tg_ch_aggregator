ALTER TABLE source
    ADD category_new_id bigint;

WITH cat AS (SELECT c.id, c.tg_id
             FROM category c)
UPDATE source
SET category_new_id = cat.tg_id
FROM cat
WHERE source.category_id = cat.id;

--

ALTER TABLE category_message_history
    ADD category_new_id bigint;

WITH cat AS (SELECT c.id, c.tg_id
             FROM category c)
UPDATE category_message_history
SET category_new_id = cat.tg_id
FROM cat
WHERE category_message_history.category_id = cat.id;

--

ALTER TABLE source
    DROP CONSTRAINT source_category_id_fkey;

ALTER TABLE category_message_history
    DROP CONSTRAINT categorymessagehistory_category_id_fkey;

--

ALTER TABLE source
    DROP COLUMN category_id;

ALTER TABLE category_message_history
    DROP COLUMN category_id;

--

ALTER TABLE source
    RENAME COLUMN category_new_id TO category_id;

ALTER TABLE category_message_history
    RENAME COLUMN category_new_id TO category_id;

--

DROP INDEX category_tg_id;

ALTER TABLE category
    DROP CONSTRAINT category_pkey;

ALTER TABLE category
    DROP COLUMN id;

--

ALTER TABLE category
    RENAME COLUMN tg_id TO id;

ALTER TABLE category
    ADD CONSTRAINT category_pk
        PRIMARY KEY (id);

--

CREATE INDEX IF NOT EXISTS "source_category_id" ON "source" ("category_id");
CREATE INDEX IF NOT EXISTS "categorymessagehistory_category_id" ON "category_message_history" ("category_id");

--

ALTER TABLE source
    ADD FOREIGN KEY (category_id) REFERENCES category (id)
        ON DELETE CASCADE;

ALTER TABLE category_message_history
    ADD FOREIGN KEY (category_id) REFERENCES category (id)
        ON DELETE CASCADE;

--

ALTER TABLE source
    ALTER COLUMN category_id SET NOT NULL;

ALTER TABLE category_message_history
    ALTER COLUMN category_id SET NOT NULL;
