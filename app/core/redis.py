import json
import redis
from typing import Any, Optional
from app.core.config import settings
from app.core.logger import logger

# Initialize Redis client
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_cache(key: str) -> Optional[Any]:
    try:
        data = redis_client.get(key)
        if data:
            logger.info("CACHE_HIT", extra={"cache_key": key})
            return json.loads(data)
        else:
            logger.info("CACHE_MISS", extra={"cache_key": key})
            return None
    except (redis.exceptions.RedisError, ConnectionError) as e:
        logger.error(f"Redis get error: {str(e)}", extra={"cache_key": key})
        return None

def set_cache(key: str, value: Any, ex: int = 60) -> bool:
    try:
        redis_client.set(key, json.dumps(value), ex=ex)
        return True
    except (redis.exceptions.RedisError, ConnectionError) as e:
        logger.error(f"Redis set error: {str(e)}", extra={"cache_key": key})
        return False

def delete_cache(key: str) -> bool:
    try:
        result = redis_client.delete(key)
        if result > 0:
            logger.info("CACHE_INVALIDATED", extra={"cache_key": key})
        return True
    except (redis.exceptions.RedisError, ConnectionError) as e:
        logger.error(f"Redis delete error: {str(e)}", extra={"cache_key": key})
        return False
