"""Pytest configuration and fixtures"""
import os
import sqlite3
import tempfile
from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'test_db'
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_pass'


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
    import sqlite3
    
    def get_connection(*args, **kwargs):
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        return conn
    
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
