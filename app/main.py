"""Sentiment Analyzer for Reviews - Main Application"""
import os
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

from .sentiment import SentimentAnalyzer, preprocess_text

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'database': os.environ.get('DB_NAME', 'sentiment_db'),
    'user': os.environ.get('DB_USER', 'sentiment_user'),
}

SECRET_FILE = os.environ.get('DB_PASSWORD_FILE', '/run/secrets/db_password')
if os.path.exists(SECRET_FILE):
    with open(SECRET_FILE, 'r') as f:
        DB_CONFIG['password'] = f.read().strip()
else:
    DB_CONFIG['password'] = os.environ.get('DB_PASSWORD', 'changeme')

analyzer = SentimentAnalyzer()


def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready with retry logic"""
    print(f"Waiting for database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...", flush=True)
    
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            print(f"✓ Database connection successful on attempt {attempt}", flush=True)
            return True
        except (psycopg2.OperationalError, Exception) as e:
            if attempt < max_retries:
                print(f"Database not ready (attempt {attempt}/{max_retries}): {str(e)[:100]}", flush=True)
                time.sleep(delay)
            else:
                print(f"✗ Failed to connect to database after {max_retries} attempts", flush=True)
                print(f"Last error: {e}", flush=True)
                return False
    
    return False


# Wait for database at startup
if __name__ != '__main__':
    # Running under gunicorn
    print("=" * 60, flush=True)
    print("Starting Sentiment Analyzer API", flush=True)
    print("=" * 60, flush=True)
    if not wait_for_db():
        print("WARNING: Database not available at startup", flush=True)
    else:
        print("✓ Database ready", flush=True)
    print("=" * 60, flush=True)


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'analyzer': 'loaded'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_review():
    """Analyze sentiment of a review"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text field'}), 400
    
    text = data['text']
    if not text.strip():
        return jsonify({'error': 'Empty text'}), 400
    
    preprocessed = preprocess_text(text)
    result = analyzer.analyze(preprocessed)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO reviews (original_text, preprocessed_text, sentiment, 
           compound_score, positive_score, negative_score, neutral_score, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id''',
        (text, preprocessed, result['sentiment'], result['compound'], 
         result['positive'], result['negative'], result['neutral'], datetime.utcnow())
    )
    review_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({
        'id': review_id,
        'text': text,
        'preprocessed': preprocessed,
        **result
    }), 201


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Get all reviews with pagination"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT COUNT(*) as total FROM reviews')
    total = cursor.fetchone()['total']
    
    cursor.execute(
        '''SELECT id, original_text, sentiment, compound_score, 
           positive_score, negative_score, neutral_score, created_at
           FROM reviews ORDER BY created_at DESC LIMIT %s OFFSET %s''',
        (limit, offset)
    )
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'reviews': reviews
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get sentiment statistics"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_reviews,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
            AVG(compound_score) as avg_compound
        FROM reviews
    ''')
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    
    total = stats['total_reviews'] or 0
    positive = stats['positive_count'] or 0
    negative = stats['negative_count'] or 0
    neutral = stats['neutral_count'] or 0
    
    return jsonify({
        'total_reviews': total,
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'positive_percentage': round((positive / total * 100) if total > 0 else 0, 2),
        'negative_percentage': round((negative / total * 100) if total > 0 else 0, 2),
        'neutral_percentage': round((neutral / total * 100) if total > 0 else 0, 2),
        'average_compound': round(stats['avg_compound'] or 0, 4)
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)
