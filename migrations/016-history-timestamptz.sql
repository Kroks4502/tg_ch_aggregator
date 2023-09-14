ALTER TABLE message_history
    ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz,
    ALTER COLUMN edited_at TYPE timestamptz USING edited_at::timestamptz,
    ALTER COLUMN deleted_at TYPE timestamptz USING deleted_at::timestamptz;
