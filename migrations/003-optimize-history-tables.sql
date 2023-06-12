ALTER TABLE category_message_history
    ADD source_chat_id bigint;

UPDATE category_message_history
SET source_chat_id=t.tg_id
FROM (SELECT id, tg_id
      FROM source) t
WHERE category_message_history.source_id = t.id;

ALTER TABLE category_message_history
    ALTER COLUMN source_chat_id SET NOT NULL;



DROP INDEX categorymessagehistory_category_id;

CREATE INDEX category_message_history_idx_1
    ON category_message_history (category_id, source_chat_id, source_message_id);

CREATE INDEX category_message_history_idx_2
    ON category_message_history (category_id, forward_from_chat_id, forward_from_message_id);



ALTER TABLE filter_message_history
    ADD source_chat_id bigint;

UPDATE filter_message_history
SET source_chat_id=t.tg_id
FROM (SELECT id, tg_id
      FROM source) t
WHERE filter_message_history.source_id = t.id;

ALTER TABLE filter_message_history
    ALTER COLUMN source_chat_id SET NOT NULL;


CREATE INDEX filter_message_history_idx
    ON filter_message_history (source_chat_id, source_message_id);
