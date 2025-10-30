"""
Integrated news processing service.
Combines news collection, ML sentiment analysis, and entity extraction.
"""

import time
import yaml
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from .news_collector import NewsCollector
from .ml_sentiment import get_analyzer
from .entity_extraction import get_extractor
from backend.database.local_db import get_database

logger = logging.getLogger(__name__)


class NewsProcessor:
    """
    Main service for processing news with sentiment and entity extraction.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize news processor.
        
        Args:
            config_path: Path to feeds.yaml configuration
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "feeds.yaml"
        
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.collector = NewsCollector(
            feed_urls=self.config.get('feeds', []),
            keywords=self.config.get('keywords', {}).get('must_have_any', []),
            stop_words=self.config.get('stop_words', [])
        )
        
        self.sentiment_analyzer = None  # Lazy load
        self.entity_extractor = None    # Lazy load
        self.db = get_database()
        
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {
                'feeds': [],
                'keywords': {'must_have_any': []},
                'stop_words': []
            }
    
    def _get_sentiment_analyzer(self):
        """Lazy load sentiment analyzer."""
        if self.sentiment_analyzer is None:
            self.sentiment_analyzer = get_analyzer()
        return self.sentiment_analyzer
    
    def _get_entity_extractor(self):
        """Lazy load entity extractor."""
        if self.entity_extractor is None:
            self.entity_extractor = get_extractor()
        return self.entity_extractor
    
    def process_news_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single news item with sentiment and entities.
        
        Args:
            item: Raw news item from feed
            
        Returns:
            Processed news item ready for database
        """
        # Combine title and summary for analysis
        text = f"{item.get('title', '')} {item.get('summary', '')}"
        
        # Sentiment analysis
        try:
            analyzer = self._get_sentiment_analyzer()
            sentiment_score, sentiment_label, confidence = analyzer.analyze(text)
            
            # Map risk-on/risk-off to bullish/bearish for consistency
            if sentiment_label == 'risk-on':
                sentiment_label = 'bullish'
            elif sentiment_label == 'risk-off':
                sentiment_label = 'bearish'
                
        except Exception as e:
            logger.warning(f"ML Sentiment analysis failed, using rule-based: {e}")
            # Fall back to simple rule-based sentiment
            text_lower = text.lower()
            bullish_terms = ['easing', 'stable', 'growth', 'strong', 'beat', 'rally']
            bearish_terms = ['tightening', 'hawkish', 'raises', 'hikes', 'selloff', 'slump']
            
            bullish_count = sum(1 for term in bullish_terms if term in text_lower)
            bearish_count = sum(1 for term in bearish_terms if term in text_lower)
            
            if bullish_count > bearish_count:
                sentiment_score = 0.5
                sentiment_label = 'bullish'
                confidence = 0.6
            elif bearish_count > bullish_count:
                sentiment_score = -0.5
                sentiment_label = 'bearish'
                confidence = 0.6
            else:
                sentiment_score = 0.0
                sentiment_label = 'neutral'
                confidence = 0.5
        
        # Entity extraction
        try:
            extractor = self._get_entity_extractor()
            entities = extractor.extract(text)
            is_high_impact = extractor.has_high_impact_entities(entities)
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            entities = {}
            is_high_impact = False
        
        # Convert timestamp
        if 'ts' in item and item['ts']:
            timestamp = datetime.fromtimestamp(time.mktime(item['ts']), tz=timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Build processed item
        processed = {
            'title': item.get('title', ''),
            'summary': item.get('summary', ''),
            'source': item.get('source', ''),
            'url': item.get('link', ''),
            'timestamp': timestamp,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'confidence': confidence,
            'entities': entities,
            'is_high_impact': is_high_impact
        }
        
        return processed
    
    def collect_and_process(self, hours: int = 24, limit: int = 100) -> Dict[str, Any]:
        """
        Collect news, process with ML, and store in database.
        
        Args:
            hours: How many hours back to collect
            limit: Maximum number of items to process
            
        Returns:
            Summary of collection and processing
        """
        logger.info(f"Starting news collection and processing (last {hours} hours)...")
        
        # Collect news
        raw_items = self.collector.collect_news(hours=hours)
        
        if not raw_items:
            logger.info("No news items found")
            return {
                'status': 'success',
                'collected': 0,
                'processed': 0,
                'stored': 0
            }
        
        # Limit items
        raw_items = raw_items[:limit]
        logger.info(f"Processing {len(raw_items)} items...")
        
        # Process each item
        processed_items = []
        for item in raw_items:
            try:
                processed = self.process_news_item(item)
                processed_items.append(processed)
            except Exception as e:
                logger.error(f"Failed to process item: {e}")
                continue
        
        logger.info(f"Processed {len(processed_items)} items with ML sentiment")
        
        # Store in database
        stored_count = self.db.bulk_insert_news(processed_items)
        logger.info(f"Stored {stored_count} items in database")
        
        # Compute aggregates
        if stored_count > 0:
            agg_count = self.db.compute_sentiment_aggregates(hours_back=hours)
            logger.info(f"Computed {agg_count} sentiment aggregates")
        
        # Calculate summary statistics
        summary = self._calculate_summary(processed_items)
        
        return {
            'status': 'success',
            'collected': len(raw_items),
            'processed': len(processed_items),
            'stored': stored_count,
            'summary': summary
        }
    
    def _calculate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from processed items."""
        if not items:
            return {}
        
        total = len(items)
        bullish = sum(1 for item in items if item['sentiment_label'] == 'bullish')
        bearish = sum(1 for item in items if item['sentiment_label'] == 'bearish')
        neutral = sum(1 for item in items if item['sentiment_label'] == 'neutral')
        high_impact = sum(1 for item in items if item['is_high_impact'])
        
        avg_sentiment = sum(item['sentiment_score'] for item in items) / total
        avg_confidence = sum(item['confidence'] for item in items) / total
        
        return {
            'total_items': total,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'high_impact_count': high_impact,
            'avg_sentiment': round(avg_sentiment, 3),
            'avg_confidence': round(avg_confidence, 3),
            'overall_mood': 'bullish' if avg_sentiment > 0.2 else ('bearish' if avg_sentiment < -0.2 else 'neutral')
        }


# Global processor instance
_processor = None


def get_processor(config_path: str = None) -> NewsProcessor:
    """
    Get or create global news processor instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        NewsProcessor instance
    """
    global _processor
    if _processor is None:
        _processor = NewsProcessor(config_path)
    return _processor

