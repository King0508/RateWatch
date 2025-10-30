"""
Named Entity Recognition (NER) for financial news.
Extracts key entities: Fed speakers, economic indicators, Treasury instruments.
"""

import re
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class FinancialEntityExtractor:
    """
    Extract financial entities from news text using pattern matching
    and domain-specific dictionaries.
    """

    # Fed officials and key speakers
    FED_OFFICIALS = {
        "powell", "jerome powell", "j. powell", "chair powell",
        "williams", "john williams",
        "brainard", "lael brainard",
        "waller", "christopher waller",
        "bowman", "michelle bowman",
        "jefferson", "philip jefferson",
        "cook", "lisa cook",
        "barkin", "thomas barkin",
        "bostic", "raphael bostic",
        "daly", "mary daly",
        "kashkari", "neel kashkari",
        "mester", "loretta mester",
        "goolsbee", "austan goolsbee",
        "harker", "patrick harker",
        "logan", "lorie logan",
    }

    # Economic indicators
    ECONOMIC_INDICATORS = {
        "cpi": ["cpi", "consumer price index", "inflation rate"],
        "pce": ["pce", "personal consumption expenditures", "core pce"],
        "nfp": ["nfp", "payrolls", "non-farm payrolls", "jobs report", "employment report"],
        "unemployment": ["unemployment", "jobless rate", "unemployment rate"],
        "gdp": ["gdp", "gross domestic product", "economic growth"],
        "ism": ["ism", "ism manufacturing", "ism services", "pmi"],
        "retail_sales": ["retail sales"],
        "housing": ["housing starts", "home sales", "existing home sales", "new home sales"],
        "fomc": ["fomc", "federal open market committee", "fed meeting", "monetary policy"],
        "ppi": ["ppi", "producer price index"],
        "claims": ["jobless claims", "unemployment claims", "initial claims"],
        "trade": ["trade deficit", "trade balance"],
    }

    # Treasury instruments and related terms
    TREASURY_INSTRUMENTS = {
        "2y": ["2-year", "2y", "two-year", "2 year"],
        "5y": ["5-year", "5y", "five-year", "5 year"],
        "10y": ["10-year", "10y", "ten-year", "10 year"],
        "30y": ["30-year", "30y", "thirty-year", "30 year"],
        "tips": ["tips", "inflation-protected", "treasury inflation"],
        "bills": ["t-bill", "treasury bill"],
        "notes": ["t-note", "treasury note"],
        "bonds": ["t-bond", "treasury bond"],
    }

    # Credit and spread terms
    CREDIT_TERMS = {
        "spread": ["spread", "spreads", "credit spread"],
        "yield_curve": ["yield curve", "curve", "inversion", "inverted"],
        "credit": ["credit", "corporate bonds", "high yield", "investment grade"],
        "mbs": ["mbs", "mortgage-backed", "mortgage securities"],
        "agency": ["agency", "fannie mae", "freddie mac", "ginnie mae"],
    }

    def __init__(self):
        """Initialize the entity extractor with compiled patterns."""
        # Compile regex patterns for yield mentions (e.g., "2.5%", "yields at 4.2%")
        self.yield_pattern = re.compile(r'\b\d+\.?\d*\s*%|\byield[s]?\s+(?:at|to|of)?\s*\d+\.?\d*\s*%', re.IGNORECASE)
        
        # Pattern for basis points
        self.bps_pattern = re.compile(r'\b\d+\s*(?:bp|bps|basis\s+points?)', re.IGNORECASE)

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all financial entities from text.
        
        Args:
            text: News headline and/or summary
            
        Returns:
            Dictionary with entity types as keys and lists of found entities as values:
            {
                "fed_officials": [...],
                "economic_indicators": [...],
                "treasury_instruments": [...],
                "credit_terms": [...],
                "yields": [...],
                "basis_points": [...]
            }
        """
        if not text:
            return self._empty_result()

        text_lower = text.lower()
        
        entities = {
            "fed_officials": self._extract_fed_officials(text_lower),
            "economic_indicators": self._extract_indicators(text_lower),
            "treasury_instruments": self._extract_treasuries(text_lower),
            "credit_terms": self._extract_credit_terms(text_lower),
            "yields": self._extract_yields(text),
            "basis_points": self._extract_basis_points(text),
        }
        
        return entities

    def _empty_result(self) -> Dict[str, List[str]]:
        """Return empty entity result structure."""
        return {
            "fed_officials": [],
            "economic_indicators": [],
            "treasury_instruments": [],
            "credit_terms": [],
            "yields": [],
            "basis_points": [],
        }

    def _extract_fed_officials(self, text_lower: str) -> List[str]:
        """Extract Fed official names from text."""
        found = []
        for official in self.FED_OFFICIALS:
            if official in text_lower:
                # Normalize to title case
                found.append(official.title())
        return list(set(found))  # Remove duplicates

    def _extract_indicators(self, text_lower: str) -> List[str]:
        """Extract economic indicator mentions."""
        found = []
        for indicator_key, patterns in self.ECONOMIC_INDICATORS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found.append(indicator_key.upper())
                    break  # Only add once per indicator type
        return list(set(found))

    def _extract_treasuries(self, text_lower: str) -> List[str]:
        """Extract Treasury instrument mentions."""
        found = []
        for instrument_key, patterns in self.TREASURY_INSTRUMENTS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found.append(instrument_key.upper())
                    break
        return list(set(found))

    def _extract_credit_terms(self, text_lower: str) -> List[str]:
        """Extract credit and spread-related terms."""
        found = []
        for term_key, patterns in self.CREDIT_TERMS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    found.append(term_key.replace("_", " ").title())
                    break
        return list(set(found))

    def _extract_yields(self, text: str) -> List[str]:
        """Extract yield percentages from text."""
        matches = self.yield_pattern.findall(text)
        return [m.strip() for m in matches]

    def _extract_basis_points(self, text: str) -> List[str]:
        """Extract basis point mentions from text."""
        matches = self.bps_pattern.findall(text)
        return [m.strip() for m in matches]

    def get_entity_summary(self, entities: Dict[str, List[str]]) -> str:
        """
        Create a human-readable summary of extracted entities.
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            Comma-separated string of all entities
        """
        all_entities = []
        for entity_type, entity_list in entities.items():
            if entity_list:
                all_entities.extend(entity_list)
        
        return ", ".join(all_entities) if all_entities else "None"

    def has_high_impact_entities(self, entities: Dict[str, List[str]]) -> bool:
        """
        Check if text contains high-impact entities (FOMC, Fed Chair, major indicators).
        
        Args:
            entities: Dictionary of extracted entities
            
        Returns:
            True if high-impact entities are present
        """
        high_impact_indicators = {"FOMC", "NFP", "CPI", "PCE"}
        high_impact_officials = {"Jerome Powell", "Powell"}
        
        has_indicator = any(ind in entities.get("economic_indicators", []) 
                          for ind in high_impact_indicators)
        has_official = any(off in entities.get("fed_officials", []) 
                         for off in high_impact_officials)
        
        return has_indicator or has_official


# Global extractor instance
_extractor = None


def get_extractor() -> FinancialEntityExtractor:
    """Get or create the global entity extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = FinancialEntityExtractor()
    return _extractor


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Convenience function to extract entities from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary of extracted entities
    """
    extractor = get_extractor()
    return extractor.extract(text)

