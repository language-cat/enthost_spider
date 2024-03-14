import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import peewee
import psycopg2
from scrapy import signals
import jsonpath
import requests
from more_itertools import first
from twisted.enterprise import adbapi

from enthost_spider.downloader_middlewares.models.proxy_downloader_middleware import ProxyInfo

logger = logging.getLogger(__name__)


class ProxyDownloaderMiddleware:
    """
    替换代理
    """

    def __init__(self, project, db_settings):
        self.db_settings = db_settings
        self.project = project
        self.db_engine = self.db_settings.get("engine")
        self.db_params = self.db_settings.get("params")

    def _connect_db(self):
        if self.db_settings is None:
            raise ValueError("DATABASE is not set")
        if self.db_engine.lower() == "sqlite":
            adapter = self.db_settings.get("adapter", "sqlite3")
            self.db = peewee.SqliteDatabase(**self.db_params)
        elif self.db_engine.lower() == "mysql":
            adapter = self.db_settings.get("adapter", "pymysql")
            self.db = peewee.MySQLDatabase(**self.db_params)
        elif self.db_engine.lower() == "postgresql":
            adapter = self.db_settings.get("adapter", "psycopg2")
            self.db = peewee.PostgresqlDatabase(**self.db_params)
        else:
            raise ValueError("DATABASE engine is not supported")
        self.db_pool = adbapi.ConnectionPool(adapter, **self.db_params, cp_reconnect=True)

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
        self._connect_db()

    def spider_closed(self):
        self.db.close()
        self.db_pool.close()

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(
            project=crawler.settings.get('BOT_NAME'),
            db_settings=crawler.settings.get('DATABASE')
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def get_proxies(self):
        """获取代理（快代理）"""
        proxy = None
        proxy_time_out = "0"
        secret_id = os.getenv("PROXY_SECRET_ID")
        signature = os.getenv("PROXY_SIGNATURE")

        query_params = {
            "secret_id": secret_id,
            "num": "1",
            "signature": signature,
            "pt": "1",
            "f_et": "1",
            "dedup": "1",
            "format": "json",
            "sep": "1",
        }

        response = requests.get(f"https://dps.kdlapi.com/api/getdps/?{urlencode(query_params)}")

        msg = jsonpath.jsonpath(response.json(), "$..msg")
        code = jsonpath.jsonpath(response.json(), "$..code")

        order_left_count = first(jsonpath.jsonpath(response.json(), "$..data..order_left_count"), 0)

        if code != 0:
            logger.warning(f"状态码: {code}, 消息: {msg} 请求代理失败")
            return proxy, proxy_time_out

        if order_left_count <= 50:
            logger.warning(f"当前请求次数剩下{order_left_count}次")

        raw_proxy_list = first([i for i in jsonpath.jsonpath(response, "$..data..proxy_list[0]")], "None,0")
        proxy, proxy_time_out = raw_proxy_list.split(",")
        return proxy, proxy_time_out

    def add_or_update_proxy_record(self, spider, raw_new_proxy, proxy_time_out):
        """
        录入代理 统计每日消耗数, 延迟时间
        :return:
        """
        if not raw_new_proxy:
            return
        data = {
            "user": spider.name,
            "proxy": raw_new_proxy,
            "proxy_time_out": proxy_time_out,
        }

        with self.db.cursor() as cursor:
            if self.db_engine.lower() != "postgresql":
                logger.warning(f"current db engine: {self.db_engine} is not support")
                return
            elif self.db_engine.lower() == "postgresql":
                sql = ProxyInfo.insert(
                    **data
                ).on_conflict(
                    conflict_target=[ProxyInfo.user.name, ProxyInfo.proxy.name],
                    preserve=list(data),
                    update={
                        "counter": ProxyInfo.counter + 1,
                        "modify_date": datetime.now(),
                    }
                ).sql()
            try:
                cursor.execute(*sql)
            except psycopg2.InterfaceError as e:
                connection = psycopg2.connect(**self.db_params)
                cursor = connection.cursor()
                cursor.execute(*sql)

        return

    # TODO
    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        """
        检查响应url是否在verify_urls
        如果是则替换代理, 然后重新将response.requests.url 插到队列中, 否则直接return response 给一下一个中间件
        判断当前是否是空代理, 如果是空代理就替换一个新的, 如果现在是使用代理的, 同时代理已经过期了就请求一个新代理替换
        :param request:
        :param response:
        :param spider:
        :return:
        """
        response_code = [401, 402, 403, 404]
        current_proxy = request.meta.get("proxy", None)
        proxy_time_out = request.meta.get("proxy_time_out", 0)
        if (current_proxy is not None) and (response.status not in response_code):
            self.add_or_update_proxy_record(spider, current_proxy, proxy_time_out)

        if response.status in response_code:
            raw_new_proxy, proxy_time_out = self.get_proxies()
            if not raw_new_proxy:
                logger.warning(f"爬虫:{spider.name}, url:{request.url}: 因没有代理替换, 失败")
                return request

            if current_proxy is None:
                self.add_or_update_proxy_record(spider, raw_new_proxy, proxy_time_out)
            else:
                raw_query = ProxyInfo.select().where(
                    ProxyInfo.proxy == raw_new_proxy,
                    ProxyInfo.user == spider.name,
                ).first()
                query = raw_query.where(
                    ProxyInfo.create_time > datetime.now() - timedelta(seconds=raw_query.proxy_time_out)
                )
                if not query.exists():
                    raw_new_proxy, proxy_time_out = self.get_proxies()
                    self.add_or_update_proxy_record(spider, raw_new_proxy, proxy_time_out)
                else:
                    query = ProxyInfo.select().order_by(ProxyInfo.create_time.desc(), ProxyInfo.counter.asc()).first()
                    raw_new_proxy = query.proxy
                    proxy_time_out = query.proxy_time_out

            new_proxy = f"https://{raw_new_proxy}"
            request.meta["proxy"] = new_proxy
            request.meta["proxy_time_out"] = proxy_time_out
            request.replace(url=request.url, dont_filter=True)
            return request
        request.dont_filter = False
        return response
