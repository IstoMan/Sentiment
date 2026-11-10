"""Tests for Flask API endpoints"""
import json

import pytest


class TestHealthEndpoint:
    """Test /health endpoint"""
    
    def test_health_check(self, app_client):
        """Test health check returns 200"""
        response = app_client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'database' in data
        assert 'analyzer' in data


class TestAnalyzeEndpoint:
    """Test /api/analyze endpoint"""
    
    def test_analyze_positive_review(self, app_client):
        """Test analyzing a positive review"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'This product is amazing! I love it!'}),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'id' in data
        assert data['sentiment'] == 'positive'
        assert 'compound' in data
        assert data['compound'] > 0
    
    def test_analyze_negative_review(self, app_client):
        """Test analyzing a negative review"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'This is terrible! Worst product ever!'}),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert data['sentiment'] == 'negative'
        assert data['compound'] < 0
    
    def test_analyze_missing_text(self, app_client):
        """Test error when text is missing"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_empty_text(self, app_client):
        """Test error when text is empty"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': '   '}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestReviewsEndpoint:
    """Test /api/reviews endpoint"""
    
    def test_get_reviews_empty(self, app_client):
        """Test getting reviews when none exist"""
        response = app_client.get('/api/reviews')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['total'] == 0
        assert data['reviews'] == []
    
    def test_get_reviews_with_data(self, app_client):
        """Test getting reviews after adding some"""
        app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'Great product!'}),
            content_type='application/json'
        )
        
        response = app_client.get('/api/reviews')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['total'] == 1
        assert len(data['reviews']) == 1
        assert 'sentiment' in data['reviews'][0]
    
    def test_get_reviews_pagination(self, app_client):
        """Test pagination parameters"""
        for i in range(5):
            app_client.post(
                '/api/analyze',
                data=json.dumps({'text': f'Review number {i}'}),
                content_type='application/json'
            )
        
        response = app_client.get('/api/reviews?limit=2&offset=1')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['limit'] == 2
        assert data['offset'] == 1
        assert len(data['reviews']) == 2


class TestStatsEndpoint:
    """Test /api/stats endpoint"""
    
    def test_stats_empty(self, app_client):
        """Test stats when no reviews exist"""
        response = app_client.get('/api/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['total_reviews'] == 0
        assert data['positive_count'] == 0
        assert data['negative_count'] == 0
        assert data['positive_percentage'] == 0
        assert data['negative_percentage'] == 0
    
    def test_stats_with_reviews(self, app_client):
        """Test stats calculation with reviews"""
        reviews = [
            'This is amazing!',
            'I love this product!',
            'Terrible experience',
            'Just okay'
        ]
        
        for review in reviews:
            app_client.post(
                '/api/analyze',
                data=json.dumps({'text': review}),
                content_type='application/json'
            )
        
        response = app_client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['total_reviews'] == 4
        assert data['positive_count'] >= 1
        assert 'positive_percentage' in data
        assert 'negative_percentage' in data
        assert 'average_compound' in data


class TestIndexPage:
    """Test main page"""
    
    def test_index_page(self, app_client):
        """Test that index page loads"""
        response = app_client.get('/')
        assert response.status_code == 200
        assert b'Sentiment Analyzer' in response.data
