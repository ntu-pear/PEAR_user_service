import time
from fastapi import HTTPException, Request
from inspect import iscoroutinefunction
from functools import wraps
import threading
from collections import defaultdict

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
    A normal decorator to apply rate limiting to FastAPI routes.

    :param bucket: TokenBucket instance to use for rate limiting.
    :param tokens_required: Number of tokens required to process the request.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not bucket.allow_request(tokens_required):
                next_token_in = 1 / bucket.rate  # Time in seconds until the next token

                raise HTTPException(status_code=429, detail=f"Too Many Requests. Tokens Left: {bucket.tokens}, "
                           f"Next token in: {round(next_token_in, 2)} seconds.")
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not bucket.allow_request(tokens_required):
                next_token_in = 1 / bucket.rate  # Time in seconds until the next token

                raise HTTPException(status_code=429, detail=f"Too Many Requests. Tokens Left: {bucket.tokens}, "
                           f"Next token in: {round(next_token_in, 2)} seconds.")
            return func(*args, **kwargs)

        # Choose the correct wrapper based on whether the function is async
        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator


# Dictionary to store TokenBucket per IP address
# key => ip address
# value => TokenBucket
# lambda is used so that a new Token Bucket instance is created for each IP and not reused
ip_rate_limiter_dict = defaultdict(lambda: TokenBucket(rate=1, capacity=10))

# token bucket does not need to be passed in the decorator as its tracked by the dictionary
def rate_limit_by_ip(tokens_required=1):
    """
    Rate limiter decorator that applies rate limits per IP address.
    :param tokens_required: Tokens required to process the request.
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            bucket = ip_rate_limiter_dict[client_ip]

            if not bucket.allow_request(tokens_required):
                next_token_in = 1 / bucket.rate  # Time in seconds until the next token
                raise HTTPException(status_code=429, detail=f"Too Many Requests from {client_ip}, "
                        f"Too Many Requests. Tokens Left: {bucket.tokens}, "
                        f"Next token in: {round(next_token_in, 2)} seconds.")
            return await func(request, *args, **kwargs)  # Ensure request is passed explicitly

        @wraps(func)
        def sync_wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            bucket = ip_rate_limiter_dict[client_ip]

            if not bucket.allow_request(tokens_required):
                next_token_in = 1 / bucket.rate  # Time in seconds until the next token
                raise HTTPException(status_code=429, detail=f"Too Many Requests from {client_ip}, "
                        f"Too Many Requests. Tokens Left: {bucket.tokens}, "
                        f"Next token in: {round(next_token_in, 2)} seconds.")
            return func(request, *args, **kwargs)  # Ensure request is passed explicitly

        return async_wrapper if iscoroutinefunction(func) else sync_wrapper

    return decorator
