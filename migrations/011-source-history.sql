CREATE TABLE IF NOT EXISTS "message_history"
(
    "id"                             bigserial NOT NULL PRIMARY KEY,
    "source_id"                      bigint    NOT NULL,
    "source_message_id"              bigint    NOT NULL,
    "source_media_group"             varchar(255),
    "source_forward_from_chat_id"    bigint,
    "source_forward_from_message_id" bigint,
    "category_id"                    bigint    NOT NULL,
    "category_message_id"            bigint,
    "category_media_group"           varchar(255),
    "category_rewritten"             boolean,
    "filter_id"                      integer,
    "created_at"                     timestamp NOT NULL,
    "edited_at"                      timestamp,
    "deleted_at"                     timestamp,
    "data"                           JSONB     NOT NULL DEFAULT '[]'::jsonb,
    FOREIGN KEY ("source_id") REFERENCES "source" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("category_id") REFERENCES "category" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("filter_id") REFERENCES "filter" ("id") ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS "message_history_source_id" ON "message_history" ("source_id");
CREATE INDEX IF NOT EXISTS "message_history_category_id" ON "message_history" ("category_id");
CREATE INDEX IF NOT EXISTS "message_history_filter_id" ON "message_history" ("filter_id");

---

INSERT INTO message_history(source_id, source_message_id, source_media_group, source_forward_from_chat_id,
                            source_forward_from_message_id, category_id, category_message_id, category_media_group,
                            category_rewritten, filter_id, created_at, edited_at, deleted_at)
SELECT *
FROM (SELECT t.source_id,
             t.source_message_id,
             t.source_media_group,
             t.source_forward_from_chat_id,
             t.source_forward_from_message_id,
             t.category_id,
             CASE WHEN ch.deleted THEN NULL ELSE t.category_message_id END AS category_message_id,
             t.category_media_group,
             t.category_rewritten,
             t.filter_id,
             t.created_at,
             t.edited_at,
             t.deleted_at
      FROM (SELECT ch.source_id,
                   ch.source_message_id,
                   ch.media_group             AS source_media_group,
                   ch.forward_from_chat_id    AS source_forward_from_chat_id,
                   ch.forward_from_message_id AS source_forward_from_message_id,
                   ch.category_id,
                   MAX(ch.message_id)         AS category_message_id,
                   NULL                       AS category_media_group,
                   ch.rewritten               AS category_rewritten,
                   MAX(fh.filter_id)          AS filter_id,
                   MIN(ch.date)               AS created_at,
                   MAX(CASE
                           WHEN NOT ch.source_message_deleted
                               AND NOT ch.source_message_edited THEN
                               ch.date
                       END)                   AS edited_at,
                   MAX(CASE
                           WHEN ch.source_message_deleted THEN
                               ch.date
                       END)                   AS deleted_at
            FROM category_message_history ch
                     LEFT JOIN filter_message_history fh
                               ON fh.source_id = ch.source_id AND fh.source_message_id = ch.source_message_id
            GROUP BY ch.source_id,
                     ch.source_message_id,
                     ch.media_group,
                     ch.forward_from_chat_id,
                     ch.forward_from_message_id,
                     ch.category_id,
                     ch.rewritten) t
               LEFT JOIN category_message_history ch
                         ON ch.message_id = t.category_message_id AND ch.category_id = t.category_id

      UNION ALL

      SELECT fh.source_id,
             fh.source_message_id,
             fh.media_group AS source_media_group,
             NULL           AS source_forward_from_chat_id,
             NULL           AS source_forward_from_message_id,
             s.category_id,
             NULL           AS category_message_id,
             NULL           AS category_media_group,
             NULL           AS category_rewritten,
             fh.filter_id,
             fh.date        AS created_at,
             NULL           AS edited_at,
             NULL           AS deleted_at
      FROM filter_message_history fh
               JOIN source s ON s.id = fh.source_id
      WHERE NOT EXISTS(SELECT NULL
                       FROM category_message_history ch
                       WHERE ch.source_message_id = fh.source_message_id
                         AND ch.source_id = fh.source_id)) tt
ORDER BY tt.created_at;

---

DROP TABLE category_message_history;

DROP TABLE filter_message_history;
