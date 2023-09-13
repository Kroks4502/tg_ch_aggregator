CREATE TABLE IF NOT EXISTS "alert_rule"
(
    "id"          serial      NOT NULL PRIMARY KEY,
    "user_id"     bigint      NOT NULL,
    "category_id" bigint      NOT NULL,
    "type"        varchar(32) NOT NULL,
    "config"      jsonb        NOT NULL,
    FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE INDEX alert_rule_user_id_idx ON "alert_rule" ("user_id");
CREATE INDEX alert_rule_category_id_idx ON "alert_rule" ("category_id");


CREATE TABLE IF NOT EXISTS "alert_history"
(
    "id"          serial      NOT NULL PRIMARY KEY,
    "category_id" bigint      NOT NULL,
    "fired_at"    timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "data"        jsonb,
    FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE CASCADE
);
CREATE INDEX alert_history_category_id_idx ON "alert_history" ("category_id");
