DO
$$
    DECLARE
        mh_row record;
        item   record;

    BEGIN
        FOR mh_row IN SELECT mh.id, mh.data FROM message_history mh
            LOOP
                FOR item IN (WITH t_data AS (SELECT t.position, t.item_object, t.exception
                                             FROM (SELECT arr.position,
                                                          arr.item_object,
                                                          COUNT(*) OVER ()                                                   AS cnt,
                                                          CASE WHEN arr.item_object -> 'exception' IS NULL THEN 0 ELSE 1 END AS exception,
                                                          MAX(CASE
                                                                  WHEN arr.item_object -> 'exception' IS NOT NULL
                                                                      THEN arr.position END)
                                                          OVER ()                                                            AS last_edit_msg_is_exc,
                                                          MAX(CASE
                                                                  WHEN arr.item_object -> 'exception' IS NULL
                                                                      THEN arr.position END)
                                                          OVER ()                                                            AS last_edit_msg_without_exc
                                                   FROM JSONB_ARRAY_ELEMENTS(mh_row.data) WITH ORDINALITY arr(item_object, position)) t
                                             WHERE t.position = 1
                                                OR t.position = t.last_edit_msg_without_exc AND t.position != 1
                                                OR t.position = t.last_edit_msg_is_exc AND t.position != 1)
                             SELECT JSONB_STRIP_NULLS(JSONB_BUILD_OBJECT(
                                     'first_message',
                                     (SELECT t_data.item_object AS data
                                      FROM t_data
                                      WHERE t_data.position = 1),
--
                                     'last_message_without_error',
                                     (SELECT t_data.item_object AS data
                                      FROM t_data
                                      WHERE t_data.position != 1
                                        AND t_data.exception = 0),
--
                                     'last_message_with_error',
                                     (SELECT t_data.item_object AS data
                                      FROM t_data
                                      WHERE t_data.position != 1
                                        AND t_data.exception = 1)
                                 )) AS new_data)
                    LOOP
                        UPDATE message_history SET data = item.new_data WHERE id = mh_row.id;
                    END LOOP;
            END LOOP;
    END
$$;

ALTER TABLE message_history
    ALTER COLUMN data SET DEFAULT '{}'::jsonb;
