ALTER TABLE admin
    RENAME CONSTRAINT admin_pk TO user_pk;

ALTER TABLE admin
    RENAME TO "user";

ALTER TABLE "user"
    ADD is_admin bool DEFAULT FALSE NOT NULL;

UPDATE "user"
SET is_admin = TRUE;
