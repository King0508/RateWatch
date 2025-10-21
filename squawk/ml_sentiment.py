"""
ML-based sentiment analysis using FinBERT for financial text.
Provides more accurate sentiment scoring compared to rule-based approaches.
"""

from typing import Tuple, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging

logger = logging.getLogger(__name__)


class FinBERTSentimentAnalyzer:
    """
    FinBERT-based sentiment analyzer for financial news.
    Uses pre-trained model fine-tuned on financial sentiment data.
    """

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize the FinBERT sentiment analyzer.
        
        Args:
            model_name: HuggingFace model identifier. Options:
                - "ProsusAI/finbert" (general financial sentiment)
                - "yiyanghkust/finbert-tone" (tone-focused)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            logger.info(f"Loading FinBERT model: {model_name} on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            raise

    def analyze(self, text: str, max_length: int = 512) -> Tuple[float, str, float]:
        """
        Analyze sentiment of financial text.
        
        Args:
            text: Text to analyze (headline + summary)
            max_length: Maximum token length for model input
            
        Returns:
            Tuple of (sentiment_score, label, confidence):
                - sentiment_score: Float between -1 (negative) and 1 (positive)
                - label: One of "risk-on", "risk-off", or "neutral"
                - confidence: Probability of the predicted class (0-1)
        """
        if not text or not text.strip():
            return 0.0, "neutral", 0.0

        try:
            # Tokenize and prepare input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)[0]

            # FinBERT outputs: [positive, negative, neutral] or [negative, neutral, positive]
            # We'll handle both model architectures
            probs = probabilities.cpu().numpy()
            
            # For ProsusAI/finbert: classes are [positive, negative, neutral]
            if "prosusai" in self.model_name.lower():
                pos_prob = float(probs[0])
                neg_prob = float(probs[1])
                neu_prob = float(probs[2])
            else:
                # For yiyanghkust/finbert-tone: classes are [negative, neutral, positive]
                neg_prob = float(probs[0])
                neu_prob = float(probs[1])
                pos_prob = float(probs[2])

            # Calculate sentiment score (-1 to 1)
            sentiment_score = pos_prob - neg_prob
            
            # Determine label and confidence
            max_prob = max(pos_prob, neg_prob, neu_prob)
            
            if pos_prob == max_prob:
                label = "risk-on"
                confidence = pos_prob
            elif neg_prob == max_prob:
                label = "risk-off"
                confidence = neg_prob
            else:
                label = "neutral"
                confidence = neu_prob

            return sentiment_score, label, confidence

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 0.0, "neutral", 0.0

    def batch_analyze(self, texts: list[str], batch_size: int = 8) -> list[Tuple[float, str, float]]:
        """
        Analyze sentiment for multiple texts in batches for efficiency.
        
        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of (sentiment_score, label, confidence) tuples
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                # Tokenize batch
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Get predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=1)

                # Process each result in the batch
                for probs in probabilities:
                    probs = probs.cpu().numpy()
                    
                    if "prosusai" in self.model_name.lower():
                        pos_prob = float(probs[0])
                        neg_prob = float(probs[1])
                        neu_prob = float(probs[2])
                    else:
                        neg_prob = float(probs[0])
                        neu_prob = float(probs[1])
                        pos_prob = float(probs[2])

                    sentiment_score = pos_prob - neg_prob
                    max_prob = max(pos_prob, neg_prob, neu_prob)
                    
                    if pos_prob == max_prob:
                        label = "risk-on"
                        confidence = pos_prob
                    elif neg_prob == max_prob:
                        label = "risk-off"
                        confidence = neg_prob
                    else:
                        label = "neutral"
                        confidence = neu_prob

                    results.append((sentiment_score, label, confidence))

            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                # Append neutral results for failed batch
                results.extend([(0.0, "neutral", 0.0)] * len(batch_texts))

        return results


# Global analyzer instance (lazy-loaded)
_analyzer: Optional[FinBERTSentimentAnalyzer] = None


def get_analyzer(model_name: str = "ProsusAI/finbert") -> FinBERTSentimentAnalyzer:
    """
    Get or create the global FinBERT analyzer instance.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        FinBERTSentimentAnalyzer instance
    """
    global _analyzer
    if _analyzer is None or _analyzer.model_name != model_name:
        _analyzer = FinBERTSentimentAnalyzer(model_name)
    return _analyzer


def sentiment_score_ml(text: str, model_name: str = "ProsusAI/finbert") -> Tuple[float, str, float]:
    """
    Convenience function for ML-based sentiment analysis.
    
    Args:
        text: Text to analyze
        model_name: FinBERT model to use
        
    Returns:
        Tuple of (sentiment_score, label, confidence)
    """
    analyzer = get_analyzer(model_name)
    return analyzer.analyze(text)

