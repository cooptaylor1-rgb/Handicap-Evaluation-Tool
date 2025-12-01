"""Simple in-memory cache middleware for GET requests."""

import json
import hashlib
from typing import Dict
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


class SimpleCacheMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory cache for GET requests.
    
    Caches responses for a configurable TTL (time-to-live).
    Only caches successful GET requests (status 200).
    """
    
    def __init__(self, app, ttl_seconds: int = 300):
        """
        Initialize the cache middleware.
        
        Args:
            app: The FastAPI application
            ttl_seconds: Time-to-live for cached responses in seconds (default: 5 minutes)
        """
        super().__init__(app)
        self.cache: Dict[str, tuple[bytes, dict, datetime]] = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        # Include method, path, and query params
        key_data = {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query),
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, cached_time: datetime) -> bool:
        """Check if a cached entry is expired."""
        return datetime.now() - cached_time > timedelta(seconds=self.ttl_seconds)
    
    def _cleanup_expired(self):
        """Remove expired entries from the cache."""
        expired_keys = [
            key for key, (_, _, cached_time) in self.cache.items()
            if self._is_expired(cached_time)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and potentially return cached response.
        
        Only caches GET requests that return status 200.
        """
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Only cache API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # Clean up expired entries periodically
        if len(self.cache) > 100:  # Arbitrary threshold
            self._cleanup_expired()
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check if we have a cached response
        if cache_key in self.cache:
            body, headers, cached_time = self.cache[cache_key]
            
            if not self._is_expired(cached_time):
                # Return cached response
                return StarletteResponse(
                    content=body,
                    headers={**headers, "X-Cache": "HIT"},
                    media_type="application/json"
                )
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        # Process the request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Cache the response
            self.cache[cache_key] = (
                body,
                dict(response.headers),
                datetime.now()
            )
            
            # Return new response with cached body
            return StarletteResponse(
                content=body,
                status_code=response.status_code,
                headers={**dict(response.headers), "X-Cache": "MISS"},
                media_type=response.media_type
            )
        
        return response
