DROP INDEX admin_tg_id;

ALTER TABLE admin
    DROP CONSTRAINT admin_pkey;

ALTER TABLE admin
    DROP COLUMN id;

ALTER TABLE admin
    RENAME COLUMN tg_id TO id;

ALTER TABLE admin
    ADD CONSTRAINT admin_pk
        PRIMARY KEY (id);
