"""Pytest configuration and fixtures"""
import os
import sqlite3
import tempfile
from typing import Generator
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask.testing import FlaskClient

# Set test environment variables before importing app
# Use setdefault so integration tests can override these
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'test_db')
os.environ.setdefault('DB_USER', 'test_user')
os.environ.setdefault('DB_PASSWORD', 'test_pass')
os.environ.setdefault('WAIT_FOR_DB', '0')  # Disable DB wait for fast tests
os.environ.setdefault('TESTING', '1')  # Allow tests to run without strict password checks


class SQLiteAdapter:
    """Adapter to make SQLite behave more like psycopg2 for testing"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._conn = None
    
    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        return self
    
    def cursor(self, cursor_factory=None):
        """Create cursor, ignoring cursor_factory for SQLite compatibility"""
        return SQLiteCursorAdapter(self._conn.cursor())
    
    def commit(self):
        return self._conn.commit()
    
    def close(self):
        return self._conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()


class SQLiteCursorAdapter:
    """Cursor adapter to convert psycopg2 %s placeholders to SQLite ? syntax"""
    
    def __init__(self, cursor):
        self._cursor = cursor
    
    def execute(self, sql, params=None):
        if params:
            sql = sql.replace('%s', '?')
        return self._cursor.execute(sql, params or ())
    
    def fetchone(self):
        result = self._cursor.fetchone()
        if result is None:
            return None
        if isinstance(result, sqlite3.Row):
            class RowAdapter:
                """Adapter that supports both dict and index access"""
                def __init__(self, row):
                    self._row = row
                    self._dict = dict(row)
                
                def __getitem__(self, key):
                    if isinstance(key, int):
                        return self._row[key]
                    return self._dict[key]
                
                def __iter__(self):
                    return iter(self._dict.values())
                
                def keys(self):
                    return self._dict.keys()
            
            return RowAdapter(result)
        return result
    
    def fetchall(self):
        results = self._cursor.fetchall()
        return [dict(row) if isinstance(row, sqlite3.Row) else row for row in results]
    
    def close(self):
        return self._cursor.close()


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing"""
    db_fd, db_path = tempfile.mkstemp()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            preprocessed_text TEXT NOT NULL,
            sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
            compound_score REAL NOT NULL,
            positive_score REAL NOT NULL,
            negative_score REAL NOT NULL,
            neutral_score REAL NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    
    yield db_path
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def mock_db_connection(mocker, temp_db):
    """Mock database connection to use SQLite for testing"""
    
    def get_connection(*args, **kwargs):
        return SQLiteAdapter(temp_db).connect()
    
    mocker.patch('app.main.get_db_connection', side_effect=get_connection)
    mocker.patch('psycopg2.connect', side_effect=get_connection)
    
    return temp_db


@pytest.fixture
def app_client(mock_db_connection) -> Generator[FlaskClient, None, None]:
    """Create Flask test client with mocked database"""
    from app import app
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client
