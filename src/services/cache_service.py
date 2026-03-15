import json
import time
from typing import Optional, Dict, Any

class CacheService:
    """Simple in-memory cache service"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.enabled = True
        print("[LiteEdGPT] In-memory cache initialized")
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached response if not expired"""
        if not self.enabled:
            return None
        
        if key in self.cache:
            # Check if expired (default 1 hour)
            if time.time() - self.timestamps[key] < 3600:
                print(f"[Cache] Hit for key: {key[:20]}...")
                return self.cache[key]
            else:
                # Remove expired entry
                del self.cache[key]
                del self.timestamps[key]
        
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600) -> bool:
        """Set cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            # Clean old entries if cache gets too large
            if len(self.cache) > 100:
                self._cleanup_old_entries()
            
            return True
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            return False
    
    def _cleanup_old_entries(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if current_time - timestamp > 3600
        ]
        
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]