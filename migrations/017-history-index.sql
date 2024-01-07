DROP INDEX message_history_source_id;

CREATE INDEX message_history_category_media_group_id_idx
    ON message_history (category_media_group_id);

CREATE INDEX message_history_created_at_idx
    ON message_history (created_at);
