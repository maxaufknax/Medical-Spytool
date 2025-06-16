"""
Enhanced Result Processor for Medical Spytool v1.4-beta

This module provides intelligent result processing with semantic deduplication,
relevance ranking, and quality scoring.

Features:
- Semantic Deduplication (not just exact matches)
- Relevance Ranking based on search criteria
- Automatic Categorization (Medicine, Biology, etc.)
- Enhanced Metadata Extraction (Impact Factor, Citations)
- Quality Score for each publication
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import hashlib
from datetime import datetime
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class PublicationMetrics:
    """Advanced metrics for publication quality assessment."""
    relevance_score: float = 0.0
    quality_score: float = 0.0
    impact_factor: Optional[float] = None
    citation_count: Optional[int] = None
    author_h_index: Optional[float] = None
    journal_rank: Optional[int] = None
    publication_age_score: float = 0.0
    keyword_match_score: float = 0.0
    title_similarity_score: float = 0.0
    
    @property
    def combined_score(self) -> float:
        """Calculate combined relevance and quality score."""
        weights = {
            'relevance': 0.4,
            'quality': 0.3,
            'citations': 0.15,
            'recency': 0.1,
            'keywords': 0.05
        }
        
        score = (
            weights['relevance'] * self.relevance_score +
            weights['quality'] * self.quality_score +
            weights['recency'] * self.publication_age_score +
            weights['keywords'] * self.keyword_match_score
        )
        
        # Bonus for citations if available
        if self.citation_count is not None:
            citation_score = min(1.0, self.citation_count / 100)  # Normalize to 0-1
            score += weights['citations'] * citation_score
        
        return min(1.0, score)


@dataclass
class ProcessedPublication:
    """Publication with enhanced processing information."""
    original_data: Dict[str, Any]
    normalized_title: str
    normalized_authors: List[str]
    keywords: Set[str]
    category: str
    source_database: str
    fingerprint: str
    metrics: PublicationMetrics = field(default_factory=PublicationMetrics)
    duplicate_group: Optional[str] = None
    processing_timestamp: datetime = field(default_factory=datetime.now)


class CategoryClassifier:
    """Automatic categorization of publications."""
    
    def __init__(self):
        self.medical_keywords = {
            'clinical', 'patient', 'therapy', 'treatment', 'diagnosis', 'disease',
            'medical', 'hospital', 'healthcare', 'medicine', 'pharmaceutical',
            'drug', 'medication', 'surgery', 'therapeutic', 'epidemiology',
            'pathology', 'oncology', 'cardiology', 'neurology', 'psychiatry'
        }
        
        self.biology_keywords = {
            'biological', 'genetic', 'molecular', 'cellular', 'organism',
            'gene', 'protein', 'enzyme', 'mutation', 'evolution',
            'ecology', 'biotechnology', 'microbiology', 'biochemistry',
            'physiology', 'anatomy', 'immunology', 'virology'
        }
        
        self.research_keywords = {
            'study', 'research', 'analysis', 'investigation', 'experiment',
            'methodology', 'statistical', 'data', 'results', 'findings',
            'systematic', 'meta-analysis', 'randomized', 'controlled'
        }
    
    def classify(self, title: str, abstract: str = "", keywords: List[str] = None) -> str:
        """Classify publication into category."""
        text = f"{title} {abstract}".lower()
        if keywords:
            text += " " + " ".join(keywords).lower()
        
        # Count keyword matches
        medical_score = sum(1 for kw in self.medical_keywords if kw in text)
        biology_score = sum(1 for kw in self.biology_keywords if kw in text)
        research_score = sum(1 for kw in self.research_keywords if kw in text)
        
        # Determine category
        scores = {
            'Medical': medical_score,
            'Biology': biology_score,
            'Research': research_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return 'General'
        
        return max(scores, key=scores.get)


class SemanticDeduplicator:
    """Advanced deduplication using semantic similarity."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.processed_publications: List[ProcessedPublication] = []
    
    def calculate_similarity(self, pub1: ProcessedPublication, pub2: ProcessedPublication) -> float:
        """Calculate semantic similarity between two publications."""
        # Title similarity (most important)
        title_sim = SequenceMatcher(None, pub1.normalized_title, pub2.normalized_title).ratio()
        
        # Author similarity
        author_sim = self._calculate_author_similarity(pub1.normalized_authors, pub2.normalized_authors)
        
        # Keyword similarity
        keyword_sim = self._calculate_keyword_similarity(pub1.keywords, pub2.keywords)
        
        # Year similarity (if available)
        year_sim = self._calculate_year_similarity(pub1.original_data, pub2.original_data)
        
        # Weighted combination
        similarity = (
            0.5 * title_sim +
            0.2 * author_sim +
            0.2 * keyword_sim +
            0.1 * year_sim
        )
        
        return similarity
    
    def _calculate_author_similarity(self, authors1: List[str], authors2: List[str]) -> float:
        """Calculate similarity between author lists."""
        if not authors1 or not authors2:
            return 0.0
        
        matches = 0
        for author1 in authors1:
            for author2 in authors2:
                if SequenceMatcher(None, author1, author2).ratio() > 0.8:
                    matches += 1
                    break
        
        return matches / max(len(authors1), len(authors2))
    
    def _calculate_keyword_similarity(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """Calculate similarity between keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_year_similarity(self, data1: Dict, data2: Dict) -> float:
        """Calculate similarity based on publication year."""
        year1 = self._extract_year(data1)
        year2 = self._extract_year(data2)
        
        if year1 is None or year2 is None:
            return 0.0
        
        year_diff = abs(year1 - year2)
        return max(0.0, 1.0 - (year_diff / 5.0))  # Full similarity if same year, 0 if >5 years apart
    
    def _extract_year(self, data: Dict) -> Optional[int]:
        """Extract publication year from data."""
        year_fields = ['year', 'publication_year', 'date', 'published']
        
        for field in year_fields:
            if field in data and data[field]:
                try:
                    year_str = str(data[field])
                    # Extract 4-digit year
                    year_match = re.search(r'\b(19|20)\d{2}\b', year_str)
                    if year_match:
                        return int(year_match.group())
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def find_duplicates(self, publications: List[ProcessedPublication]) -> Dict[str, List[ProcessedPublication]]:
        """Find duplicate groups in publications."""
        duplicate_groups = defaultdict(list)
        processed = set()
        
        for i, pub1 in enumerate(publications):
            if pub1.fingerprint in processed:
                continue
            
            group_id = f"group_{i}"
            duplicate_groups[group_id].append(pub1)
            processed.add(pub1.fingerprint)
            
            for j, pub2 in enumerate(publications[i+1:], i+1):
                if pub2.fingerprint in processed:
                    continue
                
                similarity = self.calculate_similarity(pub1, pub2)
                if similarity >= self.similarity_threshold:
                    duplicate_groups[group_id].append(pub2)
                    processed.add(pub2.fingerprint)
                    pub2.duplicate_group = group_id
            
            if len(duplicate_groups[group_id]) == 1:
                del duplicate_groups[group_id]
            else:
                pub1.duplicate_group = group_id
        
        return dict(duplicate_groups)


class RelevanceRanker:
    """Advanced relevance ranking for search results."""
    
    def __init__(self, search_query: str):
        self.search_query = search_query.lower()
        self.query_terms = self._extract_terms(search_query)
    
    def _extract_terms(self, query: str) -> Set[str]:
        """Extract meaningful terms from search query."""
        # Remove common words and normalize
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        # Extract words (alphanumeric, at least 3 characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        return {word for word in words if word not in stop_words}
    
    def calculate_relevance(self, publication: ProcessedPublication) -> float:
        """Calculate relevance score for a publication."""
        title = publication.normalized_title
        abstract = publication.original_data.get('abstract', '')
        keywords = publication.keywords
        
        # Title matching (highest weight)
        title_score = self._calculate_text_relevance(title, self.query_terms)
        
        # Abstract matching
        abstract_score = self._calculate_text_relevance(abstract, self.query_terms)
        
        # Keyword matching
        keyword_score = len(self.query_terms.intersection(keywords)) / len(self.query_terms) if self.query_terms else 0
        
        # Author matching
        author_score = self._calculate_author_relevance(publication.normalized_authors)
        
        # Weighted combination
        relevance = (
            0.4 * title_score +
            0.3 * abstract_score +
            0.2 * keyword_score +
            0.1 * author_score
        )
        
        return min(1.0, relevance)
    
    def _calculate_text_relevance(self, text: str, query_terms: Set[str]) -> float:
        """Calculate relevance based on text content."""
        if not text or not query_terms:
            return 0.0
        
        text_lower = text.lower()
        
        # Exact phrase matching
        phrase_score = 1.0 if self.search_query in text_lower else 0.0
        
        # Individual term matching
        term_matches = sum(1 for term in query_terms if term in text_lower)
        term_score = term_matches / len(query_terms)
        
        # Position-based scoring (earlier matches are better)
        position_score = 0.0
        for term in query_terms:
            pos = text_lower.find(term)
            if pos >= 0:
                # Score decreases with position
                position_score += max(0.1, 1.0 - (pos / len(text_lower)))
        
        position_score /= len(query_terms)
        
        # Weighted combination
        return 0.5 * phrase_score + 0.3 * term_score + 0.2 * position_score
    
    def _calculate_author_relevance(self, authors: List[str]) -> float:
        """Calculate relevance based on author names."""
        if not authors or not self.query_terms:
            return 0.0
        
        author_text = ' '.join(authors).lower()
        matches = sum(1 for term in self.query_terms if term in author_text)
        
        return matches / len(self.query_terms)


class EnhancedResultProcessor:
    """Enhanced result processor with comprehensive analysis."""
    
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.deduplicator = SemanticDeduplicator()
        self.processed_count = 0
        
        logger.info("Enhanced Result Processor initialized")
    
    def process_results(self, 
                       raw_results: List[Dict],
                       search_query: str = "",
                       source_databases: List[str] = None) -> List[ProcessedPublication]:
        """
        Process raw search results with comprehensive analysis.
        
        Args:
            raw_results: Raw publication data from APIs
            search_query: Original search query for relevance ranking
            source_databases: List of source databases
            
        Returns:
            List of processed and enhanced publications
        """
        logger.info(f"Processing {len(raw_results)} raw results")
        
        # Step 1: Normalize and extract features
        processed_pubs = []
        ranker = RelevanceRanker(search_query) if search_query else None
        
        for result in raw_results:
            try:
                processed_pub = self._process_single_result(result, ranker)
                processed_pubs.append(processed_pub)
            except Exception as e:
                logger.warning(f"Failed to process result: {e}")
                continue
        
        # Step 2: Deduplication
        logger.info("Performing semantic deduplication...")
        duplicate_groups = self.deduplicator.find_duplicates(processed_pubs)
        
        # Step 3: Quality scoring
        self._calculate_quality_scores(processed_pubs)
        
        # Step 4: Sort by combined score
        processed_pubs.sort(key=lambda p: p.metrics.combined_score, reverse=True)
        
        self.processed_count += len(processed_pubs)
        
        logger.info(f"Processing complete. {len(duplicate_groups)} duplicate groups found")
        return processed_pubs
    
    def _process_single_result(self, 
                             result: Dict,
                             ranker: Optional[RelevanceRanker] = None) -> ProcessedPublication:
        """Process a single publication result."""
        # Extract and normalize fields
        title = result.get('title', '')
        authors = result.get('authors', [])
        abstract = result.get('abstract', '')
        keywords = result.get('keywords', [])
        
        # Normalize text
        normalized_title = self._normalize_text(title)
        normalized_authors = [self._normalize_text(author) for author in authors if author]
        
        # Extract keywords
        extracted_keywords = self._extract_keywords(title, abstract, keywords)
        
        # Classify category
        category = self.classifier.classify(title, abstract, keywords)
        
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(normalized_title, normalized_authors)
        
        # Create processed publication
        processed_pub = ProcessedPublication(
            original_data=result,
            normalized_title=normalized_title,
            normalized_authors=normalized_authors,
            keywords=extracted_keywords,
            category=category,
            source_database=result.get('source', 'unknown'),
            fingerprint=fingerprint
        )
        
        # Calculate relevance if ranker available
        if ranker:
            processed_pub.metrics.relevance_score = ranker.calculate_relevance(processed_pub)
        
        # Extract additional metrics
        self._extract_metrics(processed_pub)
        
        return processed_pub
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # Remove special characters, convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_keywords(self, title: str, abstract: str, provided_keywords: List[str]) -> Set[str]:
        """Extract and normalize keywords."""
        keywords = set()
        
        # Add provided keywords
        for keyword in provided_keywords:
            if keyword:
                keywords.add(self._normalize_text(keyword))
        
        # Extract from title
        title_words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
        keywords.update(title_words)
        
        # Extract from abstract (if available)
        if abstract:
            # Extract meaningful terms (4+ letters, not too common)
            abstract_words = re.findall(r'\b[a-zA-Z]{4,}\b', abstract.lower())
            # Take most frequent non-common words
            word_freq = Counter(abstract_words)
            common_words = {
                'this', 'that', 'with', 'from', 'they', 'were', 'been', 'have',
                'their', 'said', 'each', 'which', 'could', 'would', 'there'
            }
            
            for word, freq in word_freq.most_common(10):
                if word not in common_words and len(word) >= 4:
                    keywords.add(word)
        
        return keywords
    
    def _generate_fingerprint(self, title: str, authors: List[str]) -> str:
        """Generate unique fingerprint for deduplication."""
        # Combine normalized title with first author
        fingerprint_text = title
        if authors:
            fingerprint_text += " " + authors[0]
        
        # Create hash
        return hashlib.md5(fingerprint_text.encode()).hexdigest()
    
    def _extract_metrics(self, publication: ProcessedPublication):
        """Extract additional metrics from publication data."""
        data = publication.original_data
        
        # Citation count
        if 'citations' in data:
            try:
                publication.metrics.citation_count = int(data['citations'])
            except (ValueError, TypeError):
                pass
        
        # Impact factor (if available)
        if 'impact_factor' in data:
            try:
                publication.metrics.impact_factor = float(data['impact_factor'])
            except (ValueError, TypeError):
                pass
        
        # Publication age score
        current_year = datetime.now().year
        pub_year = self.deduplicator._extract_year(data)
        if pub_year:
            age = current_year - pub_year
            # Newer publications get higher scores
            publication.metrics.publication_age_score = max(0.0, 1.0 - (age / 20.0))
    
    def _calculate_quality_scores(self, publications: List[ProcessedPublication]):
        """Calculate quality scores for all publications."""
        for pub in publications:
            quality_factors = []
            
            # Title completeness
            if pub.normalized_title:
                title_quality = min(1.0, len(pub.normalized_title.split()) / 10.0)
                quality_factors.append(title_quality)
            
            # Author information
            if pub.normalized_authors:
                author_quality = min(1.0, len(pub.normalized_authors) / 5.0)
                quality_factors.append(author_quality)
            
            # Abstract availability
            if pub.original_data.get('abstract'):
                abstract_len = len(pub.original_data['abstract'])
                abstract_quality = min(1.0, abstract_len / 500.0)
                quality_factors.append(abstract_quality)
            
            # Keywords availability
            if pub.keywords:
                keyword_quality = min(1.0, len(pub.keywords) / 10.0)
                quality_factors.append(keyword_quality)
            
            # Citation information
            if pub.metrics.citation_count is not None:
                citation_quality = min(1.0, pub.metrics.citation_count / 50.0)
                quality_factors.append(citation_quality)
            
            # Calculate average quality
            if quality_factors:
                pub.metrics.quality_score = sum(quality_factors) / len(quality_factors)
            else:
                pub.metrics.quality_score = 0.5  # Default medium quality
    
    def get_duplicate_summary(self, publications: List[ProcessedPublication]) -> Dict[str, Any]:
        """Get summary of duplicate detection."""
        groups = defaultdict(list)
        for pub in publications:
            if pub.duplicate_group:
                groups[pub.duplicate_group].append(pub)
        
        return {
            'total_publications': len(publications),
            'duplicate_groups': len(groups),
            'total_duplicates': sum(len(group) - 1 for group in groups.values()),
            'unique_publications': len(publications) - sum(len(group) - 1 for group in groups.values()),
            'groups': dict(groups)
        }
    
    def get_category_distribution(self, publications: List[ProcessedPublication]) -> Dict[str, int]:
        """Get distribution of publications by category."""
        return Counter(pub.category for pub in publications)
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        return {
            'total_processed': self.processed_count,
            'deduplication_threshold': self.deduplicator.similarity_threshold,
            'categories_available': len(self.classifier.medical_keywords) + len(self.classifier.biology_keywords),
            'processing_features': [
                'Semantic Deduplication',
                'Relevance Ranking',
                'Quality Scoring',
                'Automatic Categorization',
                'Metadata Enhancement'
            ]
        }