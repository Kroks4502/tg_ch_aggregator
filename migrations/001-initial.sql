CREATE TABLE IF NOT EXISTS "admin"
(
    "id"       SERIAL       NOT NULL PRIMARY KEY,
    "tg_id"    BIGINT       NOT NULL,
    "username" VARCHAR(255) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "admin_tg_id" ON "admin" ("tg_id");

CREATE TABLE IF NOT EXISTS "category"
(
    "id"    SERIAL       NOT NULL PRIMARY KEY,
    "tg_id" BIGINT       NOT NULL,
    "title" VARCHAR(255) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "category_tg_id" ON "category" ("tg_id");

CREATE TABLE IF NOT EXISTS "source"
(
    "id"          SERIAL       NOT NULL PRIMARY KEY,
    "tg_id"       BIGINT       NOT NULL,
    "title"       VARCHAR(255) NOT NULL,
    "category_id" INTEGER      NOT NULL,
    FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "source_tg_id" ON "source" ("tg_id");
CREATE INDEX IF NOT EXISTS "source_category_id" ON "source" ("category_id");

CREATE TABLE IF NOT EXISTS "categorymessagehistory"
(
    "id"                      SERIAL       NOT NULL PRIMARY KEY,
    "date"                    TIMESTAMP    NOT NULL,
    "source_id"               INTEGER      NOT NULL,
    "source_message_id"       BIGINT       NOT NULL,
    "source_message_edited"   BOOLEAN      NOT NULL,
    "source_message_deleted"  BOOLEAN      NOT NULL,
    "media_group"             VARCHAR(255) NOT NULL,
    "forward_from_chat_id"    BIGINT,
    "forward_from_message_id" BIGINT,
    "category_id"             INTEGER      NOT NULL,
    "message_id"              BIGINT       NOT NULL,
    "rewritten"               BOOLEAN      NOT NULL,
    "deleted"                 BOOLEAN      NOT NULL,
    FOREIGN KEY ("source_id") REFERENCES "source" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "categorymessagehistory_source_id" ON "categorymessagehistory" ("source_id");
CREATE INDEX IF NOT EXISTS "categorymessagehistory_category_id" ON "categorymessagehistory" ("category_id");

CREATE TABLE IF NOT EXISTS "filter"
(
    "id"        SERIAL       NOT NULL PRIMARY KEY,
    "pattern"   VARCHAR(255) NOT NULL,
    "type"      SMALLINT     NOT NULL,
    "source_id" INTEGER,
    FOREIGN KEY ("source_id") REFERENCES "source" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "filter_source_id" ON "filter" ("source_id");

CREATE TABLE IF NOT EXISTS "filtermessagehistory"
(
    "id"                     SERIAL       NOT NULL PRIMARY KEY,
    "date"                   TIMESTAMP    NOT NULL,
    "source_id"              INTEGER      NOT NULL,
    "source_message_id"      BIGINT       NOT NULL,
    "source_message_edited"  BOOLEAN      NOT NULL,
    "source_message_deleted" BOOLEAN      NOT NULL,
    "media_group"            VARCHAR(255) NOT NULL,
    "filter_id"              INTEGER      NOT NULL,
    FOREIGN KEY ("source_id") REFERENCES "source" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("filter_id") REFERENCES "filter" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "filtermessagehistory_source_id" ON "filtermessagehistory" ("source_id");
CREATE INDEX IF NOT EXISTS "filtermessagehistory_filter_id" ON "filtermessagehistory" ("filter_id");
