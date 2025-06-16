"""
Cache Manager for Medical Spytool v1.4-beta

This module provides comprehensive caching mechanisms for repeated queries
to optimize performance and reduce API calls.

Phase 2 - Step 3: Caching Implementation
"""

import hashlib
import json
import pickle
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class CacheStats:
    """Statistics tracking for cache performance."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.writes = 0
        self.evictions = 0
        self.memory_usage = 0
        self.disk_usage = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_hit(self):
        """Record a cache hit."""
        with self._lock:
            self.hits += 1
    
    def record_miss(self):
        """Record a cache miss."""
        with self._lock:
            self.misses += 1
    
    def record_write(self):
        """Record a cache write."""
        with self._lock:
            self.writes += 1
    
    def record_eviction(self):
        """Record a cache eviction."""
        with self._lock:
            self.evictions += 1
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        with self._lock:
            total = self.hits + self.misses
            return (self.hits / total * 100) if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            uptime = time.time() - self.start_time
            hit_rate = self.hits / (self.hits + self.misses) * 100 if (self.hits + self.misses) > 0 else 0.0
            return {
                'hits': self.hits,
                'misses': self.misses,
                'writes': self.writes,
                'evictions': self.evictions,
                'hit_rate': hit_rate,
                'total_requests': self.hits + self.misses,
                'uptime_seconds': uptime,
                'memory_usage_mb': self.memory_usage / (1024 * 1024),
                'disk_usage_mb': self.disk_usage / (1024 * 1024)
            }


class CacheEntry:
    """Individual cache entry with metadata."""
    
    def __init__(self, data: Any, ttl_seconds: int = 3600):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = self.created_at
        self.size_bytes = self._calculate_size(data)
    
    def _calculate_size(self, data: Any) -> int:
        """Calculate approximate size of data in bytes."""
        try:
            if isinstance(data, (list, dict)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            elif isinstance(data, str):
                return len(data.encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """Access the cached data and update metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.data
    
    def extend_ttl(self, additional_seconds: int):
        """Extend the TTL of this cache entry."""
        self.expires_at += timedelta(seconds=additional_seconds)


class MemoryCache:
    """Thread-safe in-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self.stats = CacheStats()
    
    def _generate_key(self, query: str, database: str, **kwargs) -> str:
        """Generate a unique cache key."""
        key_data = {
            'query': query.lower().strip(),
            'database': database.lower(),
            **{k: v for k, v in sorted(kwargs.items())}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, database: str, **kwargs) -> Optional[Any]:
        """Get cached data if available and not expired."""
        key = self._generate_key(query, database, **kwargs)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.is_expired():
                    # Remove expired entry
                    del self._cache[key]
                    self.stats.record_miss()
                    return None
                
                # Move to end (LRU)
                self._cache.move_to_end(key)
                self.stats.record_hit()
                return entry.access()
            
            self.stats.record_miss()
            return None
    
    def put(self, query: str, database: str, data: Any, ttl: Optional[int] = None, **kwargs):
        """Store data in cache."""
        key = self._generate_key(query, database, **kwargs)
        ttl = ttl or self.default_ttl
        entry = CacheEntry(data, ttl)
        
        with self._lock:
            # Check if we need to evict entries
            while len(self._cache) >= self.max_size:
                oldest_key, oldest_entry = self._cache.popitem(last=False)
                self.stats.record_eviction()
                logger.debug(f"Evicted cache entry: {oldest_key}")
            
            self._cache[key] = entry
            self.stats.record_write()
            self._update_memory_usage()
    
    def _update_memory_usage(self):
        """Update memory usage statistics."""
        total_size = sum(entry.size_bytes for entry in self._cache.values())
        self.stats.memory_usage = total_size
    
    def clear_expired(self):
        """Remove all expired entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self.stats.record_eviction()
            
            logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.stats.memory_usage = 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage_bytes': self.stats.memory_usage,
                'entries': [
                    {
                        'key': key[:16] + '...',
                        'created': entry.created_at.isoformat(),
                        'expires': entry.expires_at.isoformat(),
                        'access_count': entry.access_count,
                        'size_bytes': entry.size_bytes
                    }
                    for key, entry in list(self._cache.items())[-10:]  # Last 10 entries
                ]
            }
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern."""
        logger.info(f"Invalidating cache entries matching pattern: {pattern}")
        
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
                self.stats.record_eviction()
            
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries")
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        with self._lock:
            basic_stats = self.stats.get_stats()
            return {
                **basic_stats,
                'cache_size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage_bytes': self.stats.memory_usage,
                'utilization_percentage': (len(self._cache) / self.max_size * 100) if self.max_size > 0 else 0,
                'average_access_count': sum(entry.access_count for entry in self._cache.values()) / len(self._cache) if self._cache else 0
            }


class DiskCache:
    """Persistent disk-based cache for long-term storage."""
    
    def __init__(self, cache_dir: Union[str, Path] = None, max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir or Path.home() / '.medical_spytool' / 'cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = threading.Lock()
        self.stats = CacheStats()
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists and is writable."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            # Test write permissions
            test_file = self.cache_dir / '.test_write'
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            logger.warning(f"Cache directory not writable: {e}")
            # Fall back to temp directory
            self.cache_dir = Path.cwd() / '.cache'
            self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_filename(self, query: str, database: str, **kwargs) -> str:
        """Generate a safe filename for cache entry."""
        key_data = {
            'query': query.lower().strip(),
            'database': database.lower(),
            **{k: v for k, v in sorted(kwargs.items())}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        hash_key = hashlib.md5(key_string.encode()).hexdigest()
        return f"{database}_{hash_key}.cache"
    
    def get(self, query: str, database: str, **kwargs) -> Optional[Any]:
        """Get cached data from disk."""
        filename = self._generate_filename(query, database, **kwargs)
        cache_file = self.cache_dir / filename
        
        with self._lock:
            try:
                if not cache_file.exists():
                    self.stats.record_miss()
                    return None
                
                # Load cache entry
                with open(cache_file, 'rb') as f:
                    entry_data = pickle.load(f)
                
                entry = CacheEntry(
                    data=entry_data['data'],
                    ttl_seconds=3600  # Will be overridden by expires_at
                )
                entry.created_at = entry_data['created_at']
                entry.expires_at = entry_data['expires_at']
                entry.access_count = entry_data.get('access_count', 0)
                
                if entry.is_expired():
                    # Remove expired file
                    cache_file.unlink()
                    self.stats.record_miss()
                    return None
                
                # Update access info and save back
                entry.access()
                self._save_entry(cache_file, entry)
                
                self.stats.record_hit()
                return entry.data
                
            except Exception as e:
                logger.debug(f"Error reading cache file {filename}: {e}")
                # Remove corrupted cache file
                if cache_file.exists():
                    cache_file.unlink()
                self.stats.record_miss()
                return None
    
    def put(self, query: str, database: str, data: Any, ttl: Optional[int] = None, **kwargs):
        """Store data in disk cache."""
        filename = self._generate_filename(query, database, **kwargs)
        cache_file = self.cache_dir / filename
        entry = CacheEntry(data, ttl or 86400)  # Default 24 hours for disk cache
        
        with self._lock:
            try:
                # Check cache size and clean if necessary
                self._ensure_cache_size()
                
                self._save_entry(cache_file, entry)
                self.stats.record_write()
                self._update_disk_usage()
                
            except Exception as e:
                logger.warning(f"Error writing cache file {filename}: {e}")
    
    def _save_entry(self, cache_file: Path, entry: CacheEntry):
        """Save cache entry to disk."""
        entry_data = {
            'data': entry.data,
            'created_at': entry.created_at,
            'expires_at': entry.expires_at,
            'access_count': entry.access_count,
            'last_accessed': entry.last_accessed
        }
        
        with open(cache_file, 'wb') as f:
            pickle.dump(entry_data, f)
    
    def _ensure_cache_size(self):
        """Ensure cache doesn't exceed size limit."""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            if total_size > self.max_size_bytes:
                # Sort by last modified time (oldest first)
                cache_files.sort(key=lambda f: f.stat().st_mtime)
                
                # Remove oldest files until under limit
                for cache_file in cache_files:
                    cache_file.unlink()
                    self.stats.record_eviction()
                    total_size -= cache_file.stat().st_size
                    
                    if total_size <= self.max_size_bytes * 0.8:  # Leave some buffer
                        break
                
                logger.debug(f"Cleaned cache directory, removed {len(cache_files)} files")
                
        except Exception as e:
            logger.warning(f"Error managing cache size: {e}")
    
    def _update_disk_usage(self):
        """Update disk usage statistics."""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            total_size = sum(f.stat().st_size for f in cache_files)
            self.stats.disk_usage = total_size
        except Exception as e:
            logger.debug(f"Error calculating disk usage: {e}")
    
    def clear_expired(self):
        """Remove expired cache files."""
        with self._lock:
            try:
                cache_files = list(self.cache_dir.glob('*.cache'))
                expired_count = 0
                
                for cache_file in cache_files:
                    try:
                        with open(cache_file, 'rb') as f:
                            entry_data = pickle.load(f)
                        
                        if datetime.now() > entry_data['expires_at']:
                            cache_file.unlink()
                            expired_count += 1
                            self.stats.record_eviction()
                            
                    except Exception:
                        # Remove corrupted files
                        cache_file.unlink()
                        expired_count += 1
                        self.stats.record_eviction()
                
                logger.debug(f"Cleared {expired_count} expired disk cache entries")
                self._update_disk_usage()
                
            except Exception as e:
                logger.warning(f"Error clearing expired cache: {e}")
    
    def clear(self):
        """Clear all disk cache."""
        with self._lock:
            try:
                cache_files = list(self.cache_dir.glob('*.cache'))
                for cache_file in cache_files:
                    cache_file.unlink()
                self.stats.disk_usage = 0
                logger.info(f"Cleared {len(cache_files)} disk cache entries")
            except Exception as e:
                logger.warning(f"Error clearing disk cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get disk cache information."""
        try:
            cache_files = list(self.cache_dir.glob('*.cache'))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'cache_dir': str(self.cache_dir),
                'file_count': len(cache_files),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'max_size_mb': self.max_size_mb
            }
        except Exception as e:
            logger.warning(f"Error getting cache info: {e}")
            return {'error': str(e)}

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern."""
        logger.info(f"Invalidating cache entries matching pattern: {pattern}")
        
        with self._lock:
            files_to_remove = list(self.cache_dir.glob(f"*.cache"))
            for cache_file in files_to_remove:
                try:
                    with open(cache_file, 'rb') as f:
                        entry_data = pickle.load(f)
                    
                    # Check if pattern matches in the query data
                    if pattern.lower() in str(entry_data.get('data', '')).lower():
                        cache_file.unlink()
                        self.stats.record_eviction()
                        logger.info(f"Invalidated cache file: {cache_file.name}")
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink()
                    self.stats.record_eviction()
                    logger.warning(f"Removed corrupted cache file: {cache_file.name}")
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed disk cache statistics."""
        with self._lock:
            try:
                basic_stats = self.stats.get_stats()
                total_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
                file_count = len(list(self.cache_dir.glob('*.cache')))
                
                return {
                    **basic_stats,
                    'disk_usage_bytes': total_size,
                    'disk_usage_mb': total_size / (1024 * 1024),
                    'max_size_mb': self.max_size_mb,
                    'file_count': file_count,
                    'utilization_percentage': (total_size / (self.max_size_mb * 1024 * 1024) * 100) if self.max_size_mb > 0 else 0
                }
            except Exception as e:
                logger.warning(f"Error getting detailed cache stats: {e}")
                return {'error': str(e), 'disk_usage_bytes': 0}


class QueryCacheManager:
    """Comprehensive cache manager combining memory and disk caching."""
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 disk_cache_size_mb: int = 100,
                 cache_dir: Union[str, Path] = None,
                 enable_disk_cache: bool = True):
        
        self.memory_cache = MemoryCache(max_size=memory_cache_size)
        self.disk_cache = DiskCache(cache_dir=cache_dir, max_size_mb=disk_cache_size_mb) if enable_disk_cache else None
        self.enable_disk_cache = enable_disk_cache
        
        # Combined statistics
        self.total_stats = CacheStats()
        
        # Cleanup timer and tracking
        self._cleanup_timer = None
        self._last_cleanup = None
        self._start_cleanup_timer()
        
        logger.info(f"Cache manager initialized - Memory: {memory_cache_size} entries, "
                   f"Disk: {disk_cache_size_mb}MB {'enabled' if enable_disk_cache else 'disabled'}")
    
    def get(self, query: str, database: str, **kwargs) -> Optional[Any]:
        """Get cached data, checking memory first, then disk."""
        # Try memory cache first
        result = self.memory_cache.get(query, database, **kwargs)
        if result is not None:
            logger.debug(f"Cache HIT (memory): {database}:{query[:50]}...")
            self.total_stats.record_hit()
            return result
        
        # Try disk cache if enabled
        if self.disk_cache:
            result = self.disk_cache.get(query, database, **kwargs)
            if result is not None:
                # Promote to memory cache
                self.memory_cache.put(query, database, result, **kwargs)
                logger.debug(f"Cache HIT (disk): {database}:{query[:50]}...")
                self.total_stats.record_hit()
                return result
        
        logger.debug(f"Cache MISS: {database}:{query[:50]}...")
        self.total_stats.record_miss()
        return None
    
    def put(self, query: str, database: str, data: Any, ttl: Optional[int] = None, **kwargs):
        """Store data in both memory and disk caches."""
        # Always store in memory cache
        self.memory_cache.put(query, database, data, ttl, **kwargs)
        
        # Store in disk cache if enabled
        if self.disk_cache:
            self.disk_cache.put(query, database, data, ttl, **kwargs)
        
        self.total_stats.record_write()
        logger.debug(f"Cache STORE: {database}:{query[:50]}...")
    
    def invalidate(self, query: str = None, database: str = None):
        """Invalidate specific cache entries or all entries."""
        if query is None and database is None:
            # Clear all caches
            self.memory_cache.clear()
            if self.disk_cache:
                self.disk_cache.clear()
            logger.info("All caches cleared")
        else:
            # For specific invalidation, we'd need to implement pattern matching
            # For now, this is a placeholder for future enhancement
            logger.warning("Specific cache invalidation not yet implemented")
    
    def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern."""
        logger.info(f"Invalidating cache entries matching pattern: {pattern}")
        
        # Memory cache
                # Memory cache
        if self.memory_cache:
            self.memory_cache.invalidate_pattern(pattern)
        
        # Disk cache  
        if self.disk_cache:
            self.disk_cache.invalidate_pattern(pattern)
    
    def cleanup_expired(self):
        """Clean up expired entries from both caches."""
        self.memory_cache.clear_expired()
        
        if self.disk_cache:
            self.disk_cache.clear_expired()
        self._last_cleanup = datetime.now()
        logger.debug("Expired cache entries cleaned up")
    
    def get_hit_rate(self) -> float:
        """Get overall cache hit rate as a decimal between 0 and 1."""
        total_hits = 0
        total_requests = 0
        
        if self.memory_cache:
            mem_stats = self.memory_cache.stats
            total_hits += mem_stats.hits
            total_requests += mem_stats.hits + mem_stats.misses
        
        if self.disk_cache:
            disk_stats = self.disk_cache.stats
            total_hits += disk_stats.hits
            total_requests += disk_stats.hits + disk_stats.misses
        
        return (total_hits / total_requests) if total_requests > 0 else 0.0
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'overall': {
                'hit_rate': self.get_hit_rate(),
                'total_size_bytes': 0,
                'last_cleanup': self._last_cleanup.isoformat() if self._last_cleanup else None
            },
            'memory_cache': None,
            'disk_cache': None
        }
        
        if self.memory_cache:
            mem_stats = self.memory_cache.get_detailed_stats()
            stats['memory_cache'] = mem_stats
            stats['overall']['total_size_bytes'] += mem_stats.get('memory_usage_bytes', 0)
        
        if self.disk_cache:
            disk_stats = self.disk_cache.get_detailed_stats()
            stats['disk_cache'] = disk_stats
            stats['overall']['total_size_bytes'] += disk_stats.get('disk_usage_bytes', 0)
        
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic cache statistics for compatibility."""
        return {
            'hit_rate': self.get_hit_rate(),
            'memory_cache_size': len(self.memory_cache._cache) if self.memory_cache else 0,
            'disk_cache_files': len(list(self.disk_cache.cache_dir.glob('*.cache'))) if self.disk_cache else 0,
            'last_cleanup': self._last_cleanup.isoformat() if self._last_cleanup else None
        }
    
    def _start_cleanup_timer(self):
        """Start the periodic cleanup timer."""
        import threading
        
        def cleanup_task():
            """Periodic cleanup task."""
            try:
                self.cleanup_expired()
                # Schedule next cleanup
                if not hasattr(self, '_shutdown') or not self._shutdown:
                    self._cleanup_timer = threading.Timer(300.0, cleanup_task)  # 5 minutes
                    self._cleanup_timer.start()
            except Exception as e:
                logger.warning(f"Cleanup task failed: {e}")
        
        # Start initial timer
        self._cleanup_timer = threading.Timer(300.0, cleanup_task)  # 5 minutes
        self._cleanup_timer.start()
        self._shutdown = False
        
        logger.debug("Cleanup timer started")
    
    def __del__(self):
        """Cleanup timer on destruction."""
        self._shutdown = True
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
