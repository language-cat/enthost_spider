import os

import pymongo
import redis

from enthost_spider import settings

db_settings = settings.DATABASE
db_engine = db_settings.get("engine")
db_params = db_settings.get("params")

redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_password = os.getenv("REDIS_PASSWORD")

mongodb_host = os.getenv("TARGET_DB_HOST")
mongodb_port = int(os.getenv("TARGET_DB_PORT", 27017))
mongodb_password = os.getenv("TARGET_DB_PASSWORD")
mongodb_db_database = os.getenv("TARGET_DB_DATABASE")
mongodb_collections = os.getenv("TARGET_DB_COLLECTION")


def connect_to_redis(redis_host, redis_port, redis_password):
    if not redis_password:
        pool = redis.ConnectionPool(host=redis_host, port=redis_port, password=redis_password)
    else:
        pool = redis.ConnectionPool(host=redis_host, port=redis_port)
    redis_connect = redis.Redis(connection_pool=pool)
    return redis_connect


def connect_to_mongodb(mongodb_host, mongodb_port, mongodb_password):
    mongodb_connect = pymongo.MongoClient(
        host=mongodb_host, port=mongodb_port, password=mongodb_password
    )
    return mongodb_connect
