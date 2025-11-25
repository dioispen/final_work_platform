from contextlib import contextmanager
import psycopg2

DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'work_platform',
    'user': 'postgres',
    'password': 'neil930927',
    'port': 5432
}

@contextmanager
def get_db():
    conn = psycopg2.connect(**DATABASE_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()