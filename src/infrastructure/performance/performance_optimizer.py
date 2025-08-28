"""Performance optimization and caching for <150ms coaching reports (Issue 12)."""
import time
import threading
import asyncio
from typing import Dict, Any, Optional, Callable, List, TypeVar, Generic
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with expiration and hit count."""
    value: T
    timestamp: float
    ttl: float
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """Initialize LRU cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._lock = threading.RLock()
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return None
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            entry.hit_count += 1
            return entry.value
    
    def put(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Remove existing entry
            if key in self._cache:
                if key in self._access_order:
                    self._access_order.remove(key)
            
            # Create new entry
            entry = CacheEntry(value, time.time(), ttl)
            self._cache[key] = entry
            self._access_order.append(key)
            
            # Evict if over size limit
            while len(self._cache) > self.max_size:
                self._evict_lru()
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
    
    @property
    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """Get cache hit rate."""
        total_hits = sum(entry.hit_count for entry in self._cache.values())
        return total_hits / max(1, len(self._cache))


class CacheWarmer:
    """Pre-computes and caches frequently accessed data."""
    
    def __init__(self, cache: LRUCache):
        """Initialize cache warmer."""
        self.cache = cache
        self._warm_functions: Dict[str, Callable] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache_warmer")
        self._running = False
    
    def register_warm_function(self, key: str, func: Callable, interval: float = 60.0) -> None:
        """Register function to warm cache periodically."""
        self._warm_functions[key] = {
            'function': func,
            'interval': interval,
            'last_run': 0.0
        }
    
    def start(self) -> None:
        """Start cache warming."""
        if self._running:
            return
        
        self._running = True
        self._executor.submit(self._warm_loop)
        logger.info("Cache warmer started")
    
    def stop(self) -> None:
        """Stop cache warming."""
        self._running = False
        self._executor.shutdown(wait=True)
        logger.info("Cache warmer stopped")
    
    def warm_now(self, key: str) -> None:
        """Warm specific cache entry immediately."""
        if key in self._warm_functions:
            self._executor.submit(self._warm_function, key)
    
    def _warm_loop(self) -> None:
        """Main warming loop."""
        while self._running:
            try:
                current_time = time.time()
                
                for key, config in self._warm_functions.items():
                    if current_time - config['last_run'] >= config['interval']:
                        self._executor.submit(self._warm_function, key)
                        config['last_run'] = current_time
                
                time.sleep(10.0)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in cache warming loop: {e}")
                time.sleep(30.0)
    
    def _warm_function(self, key: str) -> None:
        """Execute warming function and cache result."""
        try:
            config = self._warm_functions.get(key)
            if not config:
                return
            
            start_time = time.time()
            result = config['function']()
            
            if result is not None:
                self.cache.put(key, result)
                logger.debug(f"Warmed cache for {key} in {(time.time() - start_time)*1000:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error warming cache for {key}: {e}")


class StreamingAggregator:
    """Incremental computation for real-time aggregations."""
    
    def __init__(self):
        """Initialize streaming aggregator."""
        self._aggregations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register_aggregation(self, name: str, initial_value: Any = 0) -> None:
        """Register new aggregation."""
        with self._lock:
            self._aggregations[name] = {
                'value': initial_value,
                'count': 0,
                'last_update': time.time()
            }
    
    def update_sum(self, name: str, value: float) -> None:
        """Update sum aggregation incrementally."""
        with self._lock:
            if name not in self._aggregations:
                self.register_aggregation(name, 0.0)
            
            agg = self._aggregations[name]
            agg['value'] += value
            agg['count'] += 1
            agg['last_update'] = time.time()
    
    def update_average(self, name: str, value: float) -> None:
        """Update average aggregation incrementally."""
        with self._lock:
            if name not in self._aggregations:
                self.register_aggregation(name, {'sum': 0.0, 'count': 0})
            
            agg = self._aggregations[name]
            if isinstance(agg['value'], dict):
                agg['value']['sum'] += value
                agg['value']['count'] += 1
                agg['count'] += 1
                agg['last_update'] = time.time()
    
    def update_max(self, name: str, value: float) -> None:
        """Update maximum aggregation."""
        with self._lock:
            if name not in self._aggregations:
                self.register_aggregation(name, value)
            
            agg = self._aggregations[name]
            agg['value'] = max(agg['value'], value)
            agg['count'] += 1
            agg['last_update'] = time.time()
    
    def get_value(self, name: str) -> Any:
        """Get current aggregated value."""
        with self._lock:
            agg = self._aggregations.get(name)
            if not agg:
                return None
            
            value = agg['value']
            
            # Calculate average if needed
            if isinstance(value, dict) and 'sum' in value and 'count' in value:
                return value['sum'] / max(1, value['count'])
            
            return value
    
    def reset(self, name: str) -> None:
        """Reset aggregation."""
        with self._lock:
            if name in self._aggregations:
                agg = self._aggregations[name]
                if isinstance(agg['value'], dict):
                    agg['value'] = {'sum': 0.0, 'count': 0}
                else:
                    agg['value'] = 0
                agg['count'] = 0
                agg['last_update'] = time.time()


class CircuitBreaker:
    """Circuit breaker for external dependencies."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """Initialize circuit breaker."""
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                
                # Success - reset if was half open
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e
    
    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == "OPEN"


class PerformanceMonitor:
    """Monitors performance metrics and alerts on violations."""
    
    def __init__(self, max_delay_ms: float = 150.0):
        """Initialize performance monitor."""
        self.max_delay_ms = max_delay_ms
        self.delays: List[float] = []
        self.violations: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def record_delay(self, operation: str, delay_ms: float) -> None:
        """Record operation delay."""
        with self._lock:
            self.delays.append(delay_ms)
            
            # Keep only recent delays
            if len(self.delays) > 1000:
                self.delays = self.delays[-500:]
            
            # Check for violation
            if delay_ms > self.max_delay_ms:
                violation = {
                    'operation': operation,
                    'delay_ms': delay_ms,
                    'threshold_ms': self.max_delay_ms,
                    'timestamp': time.time()
                }
                self.violations.append(violation)
                
                # Keep only recent violations
                if len(self.violations) > 100:
                    self.violations = self.violations[-50:]
                
                logger.warning(f"Performance violation: {operation} took {delay_ms:.1f}ms (threshold: {self.max_delay_ms}ms)")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            if not self.delays:
                return {}
            
            recent_delays = self.delays[-100:] if len(self.delays) > 100 else self.delays
            violation_rate = len([d for d in recent_delays if d > self.max_delay_ms]) / len(recent_delays)
            
            return {
                'avg_delay_ms': sum(recent_delays) / len(recent_delays),
                'max_delay_ms': max(recent_delays),
                'violation_rate': violation_rate,
                'total_violations': len(self.violations),
                'recent_violations': len([v for v in self.violations if time.time() - v['timestamp'] < 300])
            }


class PerformanceOptimizer:
    """Main service coordinating all performance optimizations."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.cache = LRUCache[Any](max_size=5000, default_ttl=300.0)
        self.cache_warmer = CacheWarmer(self.cache)
        self.aggregator = StreamingAggregator()
        self.circuit_breaker = CircuitBreaker()
        self.monitor = PerformanceMonitor()
        
        # Register common aggregations
        self.aggregator.register_aggregation('coaching_delays', 0.0)
        self.aggregator.register_aggregation('utility_predictions', 0.0)
        self.aggregator.register_aggregation('bandit_rewards', 0.0)
    
    def start(self) -> None:
        """Start performance optimization services."""
        self.cache_warmer.start()
        logger.info("Performance optimizer started")
    
    def stop(self) -> None:
        """Stop performance optimization services."""
        self.cache_warmer.stop()
        logger.info("Performance optimizer stopped")
    
    def time_operation(self, operation: str):
        """Context manager for timing operations."""
        return TimingContext(operation, self.monitor)
    
    def get_status(self) -> Dict[str, Any]:
        """Get performance optimizer status."""
        return {
            'cache_size': self.cache.size,
            'cache_hit_rate': self.cache.hit_rate,
            'circuit_breaker_state': self.circuit_breaker.state,
            'performance_metrics': self.monitor.get_metrics()
        }


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, operation: str, monitor: PerformanceMonitor):
        """Initialize timing context."""
        self.operation = operation
        self.monitor = monitor
        self.start_time = 0.0
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record delay."""
        delay_ms = (time.time() - self.start_time) * 1000
        self.monitor.record_delay(self.operation, delay_ms)