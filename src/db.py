import logging

from gevent.socket import wait_read, wait_write  # noqa
from playhouse.postgres_ext import PostgresqlExtDatabase
from psycopg2 import extensions

from settings import (
    POSTGRESQL_DATABASE,
    POSTGRESQL_HOST,
    POSTGRESQL_PASSWORD,
    POSTGRESQL_PORT,
    POSTGRESQL_USER,
)


def patch_psycopg2():
    extensions.set_wait_callback(_psycopg2_gevent_callback)


def _psycopg2_gevent_callback(conn, timeout=None):
    while True:
        state = conn.poll()
        if state == extensions.POLL_OK:
            break
        if state == extensions.POLL_READ:
            wait_read(conn.fileno(), timeout=timeout)
        elif state == extensions.POLL_WRITE:
            wait_write(conn.fileno(), timeout=timeout)
        else:
            raise ValueError("poll() returned unexpected result")


def connect():
    con_result = psql_db.connect(reuse_if_open=True)
    if not con_result:
        logging.warning("Connection already opened.")


psql_db = PostgresqlExtDatabase(
    POSTGRESQL_DATABASE,
    user=POSTGRESQL_USER,
    password=POSTGRESQL_PASSWORD,
    host=POSTGRESQL_HOST,
    port=POSTGRESQL_PORT,
)
