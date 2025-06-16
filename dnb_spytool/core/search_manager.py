"""
Enhanced Search Manager for Medical Spytool v1.4-beta

This module provides robust search functionality with retry mechanisms,
fallback strategies, and intelligent error handling.

Features:
- Circuit Breaker Pattern for API stability
- Exponential Backoff for failed requests
- Progressive Loading with batch processing
- Parallel Search capabilities
- Intelligent Rate Limiting
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import random

from ..api.database_manager import DatabaseManager, DatabaseType
from .cache_manager import QueryCacheManager

logger = logging.getLogger(__name__)


class SearchState(Enum):
    """Search operation states."""
    IDLE = "idle"
    SEARCHING = "searching"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class SearchProgress:
    """Search progress tracking."""
    total_queries: int
    completed_queries: int
    successful_queries: int
    failed_queries: int
    cached_hits: int
    estimated_time_remaining: float
    current_operation: str
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_queries == 0:
            return 0.0
        return (self.completed_queries / self.total_queries) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.completed_queries == 0:
            return 0.0
        return (self.successful_queries / self.completed_queries) * 100


@dataclass
class SearchRequest:
    """Individual search request."""
    query: str
    database_type: DatabaseType
    max_results: int = 100
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0


class CircuitBreaker:
    """Circuit breaker for API stability."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class RateLimiter:
    """Intelligent rate limiter with adaptive behavior."""
    
    def __init__(self, max_requests_per_second: float = 2.0):
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0
        self.request_history = []
        self.adaptive_delay = 0.0
        self._lock = threading.Lock()
    
    def acquire(self):
        """Acquire permission to make a request."""
        with self._lock:
            current_time = time.time()
            
            # Clean old history
            cutoff = current_time - 60  # Keep last minute
            self.request_history = [t for t in self.request_history if t > cutoff]
            
            # Calculate required delay
            time_since_last = current_time - self.last_request_time
            required_delay = self.min_interval + self.adaptive_delay - time_since_last
            
            if required_delay > 0:
                time.sleep(required_delay)
            
            self.last_request_time = time.time()
            self.request_history.append(self.last_request_time)
    
    def adjust_rate(self, success: bool, response_time: float):
        """Adjust rate based on API response."""
        if success and response_time < 1.0:
            # Speed up if responses are fast
            self.adaptive_delay = max(0, self.adaptive_delay - 0.1)
        elif not success or response_time > 5.0:
            # Slow down if errors or slow responses
            self.adaptive_delay += 0.5


class EnhancedSearchManager:
    """Enhanced search manager with robust error handling."""
    
    def __init__(self, cache_manager: Optional[QueryCacheManager] = None):
        self.db_manager = DatabaseManager()
        self.cache_manager = cache_manager or QueryCacheManager()
        
        # State management
        self.state = SearchState.IDLE
        self.progress = SearchProgress(0, 0, 0, 0, 0, 0.0, "")
        self.search_thread = None
        self.cancel_flag = threading.Event()
        
        # Progress callbacks
        self.progress_callbacks: List[Callable] = []
        self.result_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Rate limiting and circuit breakers
        self.rate_limiters = {
            DatabaseType.DNB: RateLimiter(2.0),
            DatabaseType.PUBMED: RateLimiter(3.0)
        }
        
        self.circuit_breakers = {
            DatabaseType.DNB: CircuitBreaker(failure_threshold=3),
            DatabaseType.PUBMED: CircuitBreaker(failure_threshold=3)
        }
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("Enhanced Search Manager initialized")
    
    def add_progress_callback(self, callback: Callable):
        """Add progress update callback."""
        self.progress_callbacks.append(callback)
    
    def add_result_callback(self, callback: Callable):
        """Add result callback."""
        self.result_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add error callback."""
        self.error_callbacks.append(callback)
    
    def search_with_fallback(self, 
                           queries: List[str],
                           databases: List[DatabaseType] = None,
                           max_results: int = 100,
                           enable_parallel: bool = True) -> List[Dict]:
        """
        Execute search with intelligent fallback strategies.
        
        Args:
            queries: List of search queries
            databases: List of databases to search (None for all)
            max_results: Maximum results per query
            enable_parallel: Enable parallel searching
            
        Returns:
            List of search results
        """
        if self.state in [SearchState.SEARCHING]:
            raise RuntimeError("Search already in progress")
        
        # Prepare search requests
        if databases is None:
            databases = [DatabaseType.DNB, DatabaseType.PUBMED]
        
        requests = []
        for query in queries:
            for db_type in databases:
                requests.append(SearchRequest(
                    query=query,
                    database_type=db_type,
                    max_results=max_results
                ))
        
        # Initialize progress
        self.progress = SearchProgress(
            total_queries=len(requests),
            completed_queries=0,
            successful_queries=0,
            failed_queries=0,
            cached_hits=0,
            estimated_time_remaining=0.0,
            current_operation="Preparing search..."
        )
        
        self.state = SearchState.SEARCHING
        self.cancel_flag.clear()
        
        try:
            if enable_parallel:
                results = self._parallel_search(requests)
            else:
                results = self._sequential_search(requests)
            
            self.state = SearchState.COMPLETED
            return results
            
        except Exception as e:
            self.state = SearchState.FAILED
            self._notify_error(f"Search failed: {str(e)}")
            raise
    
    def _parallel_search(self, requests: List[SearchRequest]) -> List[Dict]:
        """Execute parallel search requests."""
        results = []
        start_time = time.time()
        
        # Submit all requests to thread pool
        future_to_request = {
            self.executor.submit(self._execute_single_request, req): req 
            for req in requests
        }
        
        for future in as_completed(future_to_request):
            if self.cancel_flag.is_set():
                break
                
            request = future_to_request[future]
            
            try:
                result = future.result(timeout=60.0)
                if result:
                    results.extend(result)
                    self.progress.successful_queries += 1
                else:
                    self.progress.failed_queries += 1
                    
            except Exception as e:
                logger.error(f"Search failed for {request.query}: {e}")
                self.progress.failed_queries += 1
            
            # Update progress
            self.progress.completed_queries += 1
            elapsed_time = time.time() - start_time
            
            if self.progress.completed_queries > 0:
                avg_time_per_query = elapsed_time / self.progress.completed_queries
                remaining_queries = self.progress.total_queries - self.progress.completed_queries
                self.progress.estimated_time_remaining = avg_time_per_query * remaining_queries
            
            self.progress.current_operation = f"Processing {request.query}..."
            self._notify_progress()
        
        return results
    
    def _sequential_search(self, requests: List[SearchRequest]) -> List[Dict]:
        """Execute sequential search requests."""
        results = []
        start_time = time.time()
        
        for i, request in enumerate(requests):
            if self.cancel_flag.is_set():
                break
            
            self.progress.current_operation = f"Searching: {request.query}"
            self._notify_progress()
            
            try:
                result = self._execute_single_request(request)
                if result:
                    results.extend(result)
                    self.progress.successful_queries += 1
                else:
                    self.progress.failed_queries += 1
                    
            except Exception as e:
                logger.error(f"Search failed for {request.query}: {e}")
                self.progress.failed_queries += 1
            
            # Update progress
            self.progress.completed_queries += 1
            elapsed_time = time.time() - start_time
            
            if self.progress.completed_queries > 0:
                avg_time_per_query = elapsed_time / self.progress.completed_queries
                remaining_queries = self.progress.total_queries - self.progress.completed_queries
                self.progress.estimated_time_remaining = avg_time_per_query * remaining_queries
            
            self._notify_progress()
        
        return results
    
    def _execute_single_request(self, request: SearchRequest) -> Optional[List[Dict]]:
        """Execute a single search request with retry logic."""
        cache_key = f"{request.database_type.value}:{request.query}:{request.max_results}"
        
        # Check cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            self.progress.cached_hits += 1
            logger.debug(f"Cache hit for: {request.query}")
            return cached_result
        
        # Execute with circuit breaker and rate limiting
        rate_limiter = self.rate_limiters[request.database_type]
        circuit_breaker = self.circuit_breakers[request.database_type]
        
        for attempt in range(request.max_retries + 1):
            if self.cancel_flag.is_set():
                return None
            
            try:
                # Rate limiting
                rate_limiter.acquire()
                
                # Execute with circuit breaker
                start_time = time.time()
                result = circuit_breaker.call(
                    self._perform_database_search,
                    request.query,
                    request.database_type,
                    request.max_results
                )
                
                response_time = time.time() - start_time
                rate_limiter.adjust_rate(True, response_time)
                
                # Cache successful result
                if result:
                    self.cache_manager.put(cache_key, result)
                
                return result
                
            except Exception as e:
                request.retry_count = attempt + 1
                
                if attempt < request.max_retries:
                    # Exponential backoff
                    delay = min(30.0, (2 ** attempt) + random.uniform(0, 1))
                    logger.warning(f"Attempt {attempt + 1} failed for {request.query}, retrying in {delay:.2f}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All attempts failed for {request.query}: {e}")
                    rate_limiter.adjust_rate(False, 0)
                    return None
        
        return None
    
    def _perform_database_search(self, query: str, db_type: DatabaseType, max_results: int) -> List[Dict]:
        """Perform the actual database search."""
        try:
            publications = self.db_manager.search_publications(
                query=query,
                database_type=db_type,
                max_results=max_results
            )
            return [pub.to_dict() for pub in publications]
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            raise
    
    def cancel_search(self):
        """Cancel ongoing search operation."""
        if self.state == SearchState.SEARCHING:
            self.cancel_flag.set()
            self.state = SearchState.CANCELLED
            logger.info("Search cancelled by user")
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get comprehensive search statistics."""
        return {
            "state": self.state.value,
            "progress": {
                "total_queries": self.progress.total_queries,
                "completed_queries": self.progress.completed_queries,
                "successful_queries": self.progress.successful_queries,
                "failed_queries": self.progress.failed_queries,
                "cached_hits": self.progress.cached_hits,
                "progress_percentage": self.progress.progress_percentage,
                "success_rate": self.progress.success_rate,
                "estimated_time_remaining": self.progress.estimated_time_remaining,
                "current_operation": self.progress.current_operation
            },
            "circuit_breakers": {
                db_type.value: {
                    "state": breaker.state.value,
                    "failure_count": breaker.failure_count
                }
                for db_type, breaker in self.circuit_breakers.items()
            },
            "cache_stats": self.cache_manager.get_comprehensive_stats() if self.cache_manager else None
        }
    
    def _notify_progress(self):
        """Notify progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def _notify_error(self, error_message: str):
        """Notify error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        self.cancel_search()
        self.executor.shutdown(wait=True)
        logger.info("Search Manager cleaned up")