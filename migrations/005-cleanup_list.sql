ALTER TABLE "source"
    ADD "cleanup_regex" json DEFAULT '[]' NOT NULL,
    ADD "is_rewrite" bool DEFAULT FALSE NOT NULL;

CREATE TABLE IF NOT EXISTS "global_settings"
(
    "key"   varchar(255) NOT NULL PRIMARY KEY,
    "value" JSON         NOT NULL
);

INSERT INTO "global_settings" (key, value)
VALUES ('cleanup_regex', '[]');
