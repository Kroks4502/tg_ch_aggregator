CREATE INDEX category_message_history_idx_1
    ON category_message_history (category_id, source_id, source_message_id);

CREATE INDEX category_message_history_idx_2
    ON category_message_history (category_id, forward_from_chat_id, forward_from_message_id);
