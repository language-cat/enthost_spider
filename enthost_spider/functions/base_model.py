import peewee
from peewee import Model
import os

from enthost_spider import settings
from enthost_spider.functions.base_connect import connect_to_mongodb

db_settings = settings.DATABASE
db_engine = db_settings.get("engine")
db_params = db_settings.get("params")

mongodb_host = os.getenv("TARGET_DB_HOST")
mongodb_port = int(os.getenv("TARGET_DB_PORT", 27017))
mongodb_password = os.getenv("TARGET_DB_PASSWORD")
mongodb_db_database = os.getenv("TARGET_DB_DATABASE")
mongodb_collections = os.getenv("TARGET_DB_COLLECTION")
mongodb_connect = connect_to_mongodb(mongodb_host, mongodb_port, mongodb_password)

if db_engine.lower() == "mysql":
    mysql_connect = peewee.MySQLDatabase(**db_params)
elif db_engine.lower() == "postgresql":
    pgsql_connect = peewee.PostgresqlDatabase(**db_params)


class MongodbBaseModel(Model):
    class Meta:
        database = mongodb_connect


class PgsqlBaseModel(Model):
    class Meta:
        database = pgsql_connect
