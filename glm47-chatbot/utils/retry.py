import asyncio
import functools
import logging
import random

import httpx

logger = logging.getLogger(__name__)


def async_retry(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except httpx.TimeoutException as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2**attempt)
                    jitter = delay * 0.2 * (random.random() * 2 - 1)
                    wait_time = delay + jitter
                    logger.warning(
                        f"Timeout after attempt {attempt + 1}/{max_attempts}, "
                        f"retrying in {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                except httpx.ConnectError as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2**attempt)
                    jitter = delay * 0.2 * (random.random() * 2 - 1)
                    wait_time = delay + jitter
                    logger.warning(
                        f"Connection error after attempt {attempt + 1}/{max_attempts}, "
                        f"retrying in {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        last_exception = e
                        if attempt == max_attempts - 1:
                            raise
                        delay = base_delay * 5
                        jitter = delay * 0.2 * (random.random() * 2 - 1)
                        wait_time = delay + jitter
                        logger.warning(
                            f"Rate limited (429) after attempt {attempt + 1}/{max_attempts}, "
                            f"retrying in {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                    elif e.response.status_code in (400, 422):
                        raise
                    else:
                        last_exception = e
                        if attempt == max_attempts - 1:
                            raise
                        delay = base_delay * (2**attempt)
                        jitter = delay * 0.2 * (random.random() * 2 - 1)
                        wait_time = delay + jitter
                        logger.warning(
                            f"HTTP error {e.response.status_code} after attempt "
                            f"{attempt + 1}/{max_attempts}, retrying in {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
            raise last_exception

        return wrapper

    return decorator