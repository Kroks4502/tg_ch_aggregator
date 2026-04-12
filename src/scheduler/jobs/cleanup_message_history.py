import logging

from peewee import SQL

from db import psql_db
from models import MessageHistory
from settings import MESSAGE_HISTORY_RETENTION_MONTHS

logger = logging.getLogger(__name__)


def _vacuum_message_history() -> None:
    conn = psql_db.connection()
    prev_autocommit = conn.autocommit
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            cursor.execute("VACUUM ANALYZE message_history")
    finally:
        conn.autocommit = prev_autocommit
    logger.info("VACUUM ANALYZE message_history completed")


async def cleanup_message_history_job():
    months = MESSAGE_HISTORY_RETENTION_MONTHS
    deleted = (
        MessageHistory.delete()
        .where(
            MessageHistory.created_at
            < SQL("NOW() - (%s * INTERVAL '1 month')", (months,))
        )
        .execute()
    )
    logger.info(
        "message_history cleanup: deleted %s rows older than %s month(s)",
        deleted,
        months,
    )
    try:
        _vacuum_message_history()
    except Exception:
        logger.exception("message_history cleanup: VACUUM ANALYZE failed")
        raise
