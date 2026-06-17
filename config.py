import os

REDIS_CONFIG = {
    "host":os.getenv("REDIS_HOST","localhost"),
    "port":os.getenv("REDIS_PORT","6379"),
    "db":0,
    "max_connections":10,
    "decode_responses":True
}

class CONFIG:
    name="Myblog"
    version="1.0"

    
