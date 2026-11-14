"""Tests for sentiment analysis functionality"""
import pytest

from app.sentiment import SentimentAnalyzer, preprocess_text


class TestPreprocessing:
    """Test text preprocessing"""
    
    def test_preprocess_strips_whitespace(self):
        """Test that preprocessing removes leading/trailing whitespace"""
        text = "  Hello world  "
        result = preprocess_text(text)
        assert result == "Hello world"
    
    def test_preprocess_normalizes_spaces(self):
        """Test that multiple spaces are normalized to single space"""
        text = "Hello    world   from   Python"
        result = preprocess_text(text)
        assert result == "Hello world from Python"
    
    def test_preprocess_handles_newlines(self):
        """Test that newlines are converted to spaces"""
        text = "Hello\nworld\nfrom\nPython"
        result = preprocess_text(text)
        assert result == "Hello world from Python"
    
    def test_preprocess_empty_string(self):
        """Test preprocessing empty string"""
        assert preprocess_text("") == ""
    
    def test_preprocess_preserves_punctuation(self):
        """Test that punctuation is preserved"""
        text = "Great! This product is amazing!!!"
        result = preprocess_text(text)
        assert "!" in result
        assert result == "Great! This product is amazing!!!"


class TestSentimentAnalyzer:
    """Test sentiment analysis"""
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        analyzer = SentimentAnalyzer()
        assert analyzer.analyzer is not None
    
    def test_positive_sentiment(self):
        """Test detection of positive sentiment"""
        analyzer = SentimentAnalyzer()
        text = "This is an excellent product! I love it!"
        result = analyzer.analyze(text)
        
        assert result['sentiment'] == 'positive'
        assert result['compound'] > 0.05
        assert 'positive' in result
        assert 'negative' in result
        assert 'neutral' in result
    
    def test_negative_sentiment(self):
        """Test detection of negative sentiment"""
        analyzer = SentimentAnalyzer()
        text = "This is terrible! I hate it! Worst product ever!"
        result = analyzer.analyze(text)
        
        assert result['sentiment'] == 'negative'
        assert result['compound'] < -0.05
    
    def test_neutral_sentiment(self):
        """Test detection of neutral sentiment"""
        analyzer = SentimentAnalyzer()
        text = "This is a product."
        result = analyzer.analyze(text)
        
        assert result['sentiment'] == 'neutral'
        assert -0.05 <= result['compound'] <= 0.05
    
    def test_compound_score_range(self):
        """Test that compound score is in valid range"""
        analyzer = SentimentAnalyzer()
        texts = [
            "Amazing!",
            "Terrible!",
            "Okay",
            "The product exists"
        ]
        
        for text in texts:
            result = analyzer.analyze(text)
            assert -1 <= result['compound'] <= 1
    
    def test_score_components_sum(self):
        """Test that positive, negative, and neutral scores sum to approximately 1"""
        analyzer = SentimentAnalyzer()
        text = "This product is pretty good but has some issues."
        result = analyzer.analyze(text)
        
        total = result['positive'] + result['negative'] + result['neutral']
        assert 0.99 <= total <= 1.01
