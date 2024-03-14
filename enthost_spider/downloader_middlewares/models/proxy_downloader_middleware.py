from datetime import datetime

from peewee import TextField, DateTimeField, IntegerField

from enthost_spider.functions.base_model import PgsqlBaseModel


class ProxyInfo(PgsqlBaseModel):
    """
    代理信息
    """
    user = TextField("代理使用者")
    proxy = TextField("代理IP")
    counter = IntegerField("代理使用次数", default=1)
    proxy_time_out = IntegerField("代理有效时间")
    create_time = DateTimeField("代理新增时间", default=datetime.now)
    modify_date = DateTimeField("代理修改时间", default=datetime.now)

    class Meta:
        indexes = (
            (("user", "proxy"), True),
        )
        db_table = "proxy_info"
