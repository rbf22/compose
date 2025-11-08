# compose/cache_system.py
"""
Caching system for performance optimization in Compose.
Provides intelligent caching for expensive operations like math rendering and diagram generation.
"""

import hashlib
import pickle
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import os


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, data: Any, metadata: Dict[str, Any] = None):
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.access_count = 0
        self.last_accessed = time.time()

    def access(self):
        """Mark entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()

    def is_expired(self, max_age: float) -> bool:
        """Check if entry is expired"""
        return time.time() - self.timestamp > max_age

    def size_estimate(self) -> int:
        """Estimate memory size of entry"""
        return len(pickle.dumps(self.data)) + len(pickle.dumps(self.metadata))


class IntelligentCache:
    """
    Intelligent caching system with LRU eviction, TTL, and memory management.
    Optimized for typesetting workloads.
    """

    def __init__(self, max_memory: int = 50 * 1024 * 1024,  # 50MB default
                 max_entries: int = 1000,
                 default_ttl: float = 3600):  # 1 hour default
        self.max_memory = max_memory
        self.max_entries = max_entries
        self.default_ttl = default_ttl

        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.memory_used = 0

        # Cache directory for persistent storage
        self.cache_dir = Path.home() / '.compose_cache'
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key: str, default=None) -> Any:
        """Get item from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired(self.default_ttl):
                entry.access()
                return entry.data
            else:
                # Remove expired entry
                self._remove_entry(key)

        return default

    def set(self, key: str, value: Any, metadata: Dict[str, Any] = None, ttl: float = None) -> None:
        """Set item in cache"""
        if ttl is None:
            ttl = self.default_ttl

        entry = CacheEntry(value, metadata)

        # Check if we need to evict
        if key not in self.cache:
            while (len(self.cache) >= self.max_entries or
                   self.memory_used + entry.size_estimate() > self.max_memory):
                self._evict_lru()

        # Remove old entry if it exists
        if key in self.cache:
            self._remove_entry(key)

        # Add new entry
        self.cache[key] = entry
        self.memory_used += entry.size_estimate()

    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            self._remove_entry(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.memory_used = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        return {
            'entries': len(self.cache),
            'memory_used': self.memory_used,
            'memory_limit': self.max_memory,
            'hit_rate': total_accesses / max(1, len(self.cache)),
            'oldest_entry': min((entry.timestamp for entry in self.cache.values()), default=0),
            'newest_entry': max((entry.timestamp for entry in self.cache.values()), default=0)
        }

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return

        # Find LRU entry
        lru_key = min(self.cache.keys(),
                      key=lambda k: self.cache[k].last_accessed)

        self._remove_entry(lru_key)

    def _remove_entry(self, key: str) -> None:
        """Remove entry and update memory usage"""
        if key in self.cache:
            entry = self.cache[key]
            self.memory_used -= entry.size_estimate()
            del self.cache[key]

    def persistent_get(self, key: str) -> Any:
        """Get item from persistent cache"""
        cache_file = self._cache_file_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    if not entry.is_expired(self.default_ttl):
                        return entry.data
                    else:
                        # Remove expired file
                        cache_file.unlink()
            except Exception:
                # Corrupted cache file, remove it
                cache_file.unlink()
        return None

    def persistent_set(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> None:
        """Set item in persistent cache"""
        entry = CacheEntry(value, metadata)
        cache_file = self._cache_file_path(key)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception:
            # If writing fails, just skip persistent caching
            pass

    def _cache_file_path(self, key: str) -> Path:
        """Get cache file path for key"""
        # Create a safe filename from key hash
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"


class MathExpressionCache:
    """
    Specialized cache for mathematical expressions.
    Caches rendered math images and parsed expressions.
    """

    def __init__(self):
        self.memory_cache = IntelligentCache(max_memory=20 * 1024 * 1024)  # 20MB
        self.render_cache = IntelligentCache(max_memory=30 * 1024 * 1024)  # 30MB

    def get_parsed_expression(self, latex: str) -> Optional[Any]:
        """Get cached parsed expression"""
        key = f"parsed:{latex}"
        return self.memory_cache.get(key)

    def set_parsed_expression(self, latex: str, parsed: Any) -> None:
        """Cache parsed expression"""
        key = f"parsed:{latex}"
        self.memory_cache.set(key, parsed, {'type': 'parsed_expression'})

    def get_rendered_math(self, latex: str, display_style: bool = False) -> Optional[str]:
        """Get cached rendered math image"""
        key = f"render:{latex}:{display_style}"
        return self.render_cache.get(key)

    def set_rendered_math(self, latex: str, display_style: bool, svg_data: str) -> None:
        """Cache rendered math image"""
        key = f"render:{latex}:{display_style}"
        self.render_cache.set(key, svg_data, {
            'type': 'rendered_math',
            'latex': latex,
            'display_style': display_style
        })


class DiagramCache:
    """
    Specialized cache for diagram rendering.
    Caches parsed diagrams and rendered outputs.
    """

    def __init__(self):
        self.cache = IntelligentCache(max_memory=25 * 1024 * 1024)  # 25MB

    def get_parsed_diagram(self, code: str) -> Optional[Tuple]:
        """Get cached parsed diagram"""
        key = f"diagram:{hashlib.md5(code.encode()).hexdigest()}"
        return self.cache.get(key)

    def set_parsed_diagram(self, code: str, nodes: Dict, connections: List) -> None:
        """Cache parsed diagram"""
        key = f"diagram:{hashlib.md5(code.encode()).hexdigest()}"
        self.cache.set(key, (nodes, connections), {'type': 'parsed_diagram'})

    def get_rendered_diagram(self, code: str, format: str) -> Optional[str]:
        """Get cached rendered diagram"""
        key = f"render:{format}:{hashlib.md5(code.encode()).hexdigest()}"
        return self.cache.get(key)

    def set_rendered_diagram(self, code: str, format: str, output: str) -> None:
        """Cache rendered diagram"""
        key = f"render:{format}:{hashlib.md5(code.encode()).hexdigest()}"
        self.cache.set(key, output, {
            'type': 'rendered_diagram',
            'format': format
        })


# Global cache instances
math_cache = MathExpressionCache()
diagram_cache = DiagramCache()


def optimize_memory_usage():
    """
    Memory optimization utilities.
    Can be called periodically to free memory.
    """
    import gc
    gc.collect()

    # Clear expired cache entries
    # This is handled automatically by IntelligentCache, but we can force cleanup
    pass


def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive cache statistics"""
    return {
        'math_cache': math_cache.memory_cache.stats(),
        'diagram_cache': diagram_cache.cache.stats(),
        'render_cache': math_cache.render_cache.stats()
    }


# Performance monitoring
class PerformanceMonitor:
    """Monitor performance of key operations"""

    def __init__(self):
        self.operations: Dict[str, List[float]] = {}

    def time_operation(self, operation_name: str):
        """Decorator to time operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if operation_name not in self.operations:
                    self.operations[operation_name] = []
                self.operations[operation_name].append(duration)

                return result
            return wrapper
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for op, times in self.operations.items():
            if times:
                stats[op] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        return stats


# Global performance monitor
performance_monitor = PerformanceMonitor()
