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
        """Test that index page loads with Bulma and no custom CSS"""
        response = app_client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Sentiment Analyzer' in html
        assert '/static/css/bulma.min.css' in html
        assert '<style' not in html.lower()
        assert 'style=' not in html.lower()
        assert 'class="button is-link"' in html
        assert 'class="textarea"' in html
        assert 'class="columns is-multiline"' in html


class TestInputValidation:
    """Test input validation"""
    
    def test_empty_text(self, app_client):
        """Test with empty text"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'empty' in data['error'].lower()
    
    def test_non_string_text(self, app_client):
        """Test with non-string text"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 123}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'string' in data['error'].lower()
    
    def test_oversized_text(self, app_client):
        """Test text exceeding maximum length"""
        long_text = 'a' * 5001
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'text': long_text}),
            content_type='application/json'
        )
        assert response.status_code == 413
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_malformed_json(self, app_client):
        """Test with malformed JSON"""
        response = app_client.post(
            '/api/analyze',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_missing_text_field(self, app_client):
        """Test with missing text field"""
        response = app_client.post(
            '/api/analyze',
            data=json.dumps({'wrong_field': 'value'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestPagination:
    """Test pagination parameters"""
    
    def test_negative_limit(self, app_client):
        """Test with negative limit"""
        response = app_client.get('/api/reviews?limit=-1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 1  # Should clamp to minimum
    
    def test_excessive_limit(self, app_client):
        """Test with excessive limit"""
        response = app_client.get('/api/reviews?limit=200')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 100  # Should clamp to maximum
    
    def test_negative_offset(self, app_client):
        """Test with negative offset"""
        response = app_client.get('/api/reviews?offset=-10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['offset'] == 0  # Should clamp to minimum


class TestStatsAccuracy:
    """Test stats calculation accuracy"""
    
    def test_exact_percentages(self, app_client):
        """Test exact percentage calculations"""
        # Add 2 positive reviews
        app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'This is amazing!'}),
            content_type='application/json'
        )
        app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'I love it!'}),
            content_type='application/json'
        )
        
        # Add 1 negative review
        app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'This is terrible and awful'}),
            content_type='application/json'
        )
        
        # Add 1 neutral review
        app_client.post(
            '/api/analyze',
            data=json.dumps({'text': 'It is a thing'}),
            content_type='application/json'
        )
        
        response = app_client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['total_reviews'] == 4
        assert data['positive_count'] == 2
        assert data['negative_count'] == 1
        assert data['neutral_count'] == 1
        assert data['positive_percentage'] == 50.0
        assert data['negative_percentage'] == 25.0
        assert data['neutral_percentage'] == 25.0
