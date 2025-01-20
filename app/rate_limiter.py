import time
from fastapi import HTTPException
from inspect import iscoroutinefunction
from functools import wraps
import threading

class TokenBucket:
    def __init__(self, rate, capacity):
        """
        Initialize a Token Bucket.

        :param rate: Tokens to refill per second.
        :param capacity: Maximum number of tokens the bucket can hold.
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity  # Start with a full bucket
        self.last_refill_time = time.monotonic()
        self.lock = threading.Lock()

    def _refill_tokens(self):
        """
        Refill tokens based on the time elapsed since the last refill.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill_time = now

    def allow_request(self, tokens_required=1):
        """
        Check if a request can be processed.

        :param tokens_required: Tokens needed for the request.
        :return: True if allowed, False otherwise.
        """
        with self.lock:
            self._refill_tokens()
            if self.tokens >= tokens_required:
                self.tokens -= tokens_required
                return True
            else:
                return False


def rate_limit(bucket: TokenBucket, tokens_required=1):
    """
    A decorator to apply rate limiting to FastAPI routes.

    :param bucket: TokenBucket instance to use for rate limiting.
    :param tokens_required: Number of tokens required to process the request.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not bucket.allow_request(tokens_required):
                raise HTTPException(status_code=429, detail="Too Many Requests")
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not bucket.allow_request(tokens_required):
                raise HTTPException(status_code=429, detail="Too Many Requests")
            return func(*args, **kwargs)

        # Choose the correct wrapper based on whether the function is async
        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator