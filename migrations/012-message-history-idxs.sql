CREATE INDEX message_history_idx_1
    ON message_history (source_id, source_message_id);

CREATE INDEX message_history_idx_2
    ON message_history (source_forward_from_chat_id, source_forward_from_message_id);
