import pytest
import psycopg2
from app import create_app, get_db_connection

TEST_DB_CONFIG = {
    "dbname": "library_test_db",
    "user": "postgres",
    "password": "secret",
    "host": "127.0.0.1",
    "port": "5432"
}

@pytest.fixture(scope="session")
def test_db():
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="secret", host="127.0.0.1")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_CONFIG['dbname']}")
    cur.execute(f"CREATE DATABASE {TEST_DB_CONFIG['dbname']}")
    yield
    cur.execute(f"DROP DATABASE {TEST_DB_CONFIG['dbname']}")
    cur.close()
    conn.close()

@pytest.fixture(scope="session")
def app(test_db):
    app = create_app(TEST_DB_CONFIG)
    return app

@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as client:
        conn = get_db_connection(TEST_DB_CONFIG)
        cur = conn.cursor()
        cur.execute("TRUNCATE books, authors RESTART IDENTITY CASCADE")
        conn.commit()
        cur.close()
        conn.close()
        yield client
