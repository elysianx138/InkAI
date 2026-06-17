from redis import Redis,ConnectionPool
from config import REDIS_CONFIG

pool = ConnectionPool(
    host=REDIS_CONFIG["host"],
    port=REDIS_CONFIG["port"],
    db=REDIS_CONFIG["db"],
    max_connections=REDIS_CONFIG["max_connections"],
    decode_responses=REDIS_CONFIG["decode_responses"]
)

def get_redis():
    return Redis(connection_pool=pool)
