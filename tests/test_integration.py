"""Integration tests requiring real PostgreSQL

These tests are marked and should only run when explicitly requested
or when a real PostgreSQL instance is available.
"""
import os

import psycopg2
import pytest


def get_db_password():
    """Get database password from file or environment"""
    password_file = os.environ.get('DB_PASSWORD_FILE', '/run/secrets/db_password')
    if os.path.exists(password_file):
        with open(password_file, 'r') as f:
            return f.read().strip()
    return os.environ.get('DB_PASSWORD', 'changeme')


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get('SKIP_INTEGRATION_TESTS', 'true').lower() == 'true',
    reason="Integration tests require real PostgreSQL"
)
class TestDatabaseIntegration:
    """Integration tests with real PostgreSQL database"""
    
    def test_database_connection(self):
        """Test connection to real database"""
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'db'),
            port=int(os.environ.get('DB_PORT', '5432')),
            database=os.environ.get('DB_NAME', 'sentiment_db'),
            user=os.environ.get('DB_USER', 'sentiment_user'),
            password=get_db_password()
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        
        assert result[0] == 1
        
        cursor.close()
        conn.close()
    
    def test_reviews_table_exists(self):
        """Test that reviews table exists and has correct schema"""
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'db'),
            port=int(os.environ.get('DB_PORT', '5432')),
            database=os.environ.get('DB_NAME', 'sentiment_db'),
            user=os.environ.get('DB_USER', 'sentiment_user'),
            password=get_db_password()
        )
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'reviews'
            ORDER BY ordinal_position
        ''')
        
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        expected_columns = [
            'id', 'original_text', 'preprocessed_text', 'sentiment',
            'compound_score', 'positive_score', 'negative_score',
            'neutral_score', 'created_at'
        ]
        
        for expected in expected_columns:
            assert expected in column_names, f"Missing column: {expected}"
        
        cursor.close()
        conn.close()
