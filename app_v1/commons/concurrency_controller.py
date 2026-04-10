import asyncio
from functools import wraps


# general local async concurrency controller
class AsyncConcurrencyController:

    #TODO: need to improve this- should work with a global concurrency controller - so across service, everything is limited
    def __init__(self, max_concurrent:int):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def limit_concurrency(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self._semaphore:
                return await func(*args, **kwargs)

        return wrapper