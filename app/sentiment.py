"""Sentiment analysis module using VADER"""
import re
from typing import Dict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def preprocess_text(text: str) -> str:
    """
    Preprocess review text for analysis
    
    Args:
        text: Raw review text
        
    Returns:
        Preprocessed text
    """
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


class SentimentAnalyzer:
    """Sentiment analyzer using VADER"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Preprocessed review text
            
        Returns:
            Dictionary with sentiment label and scores
        """
        scores = self.analyzer.polarity_scores(text)
        
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'compound': compound,
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }
