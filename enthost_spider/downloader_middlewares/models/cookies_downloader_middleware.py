from peewee import TextField, DateTimeField, BlobField, IntegerField, AutoField
from enthost_spider.functions.base_model import PgsqlBaseModel
from scrapy_utils.base_time import get_current_time


class LoginUserInfo(PgsqlBaseModel):
    id = AutoField(primary_key=True)
    telephone = TextField("电话")
    password = TextField("密码")
    source = TextField("来源", default="tianyancha")
    is_active = BlobField("是否激活", default=True)
    is_super = BlobField("是否超级用户", default=False)
    created_at = DateTimeField("创建时间", default=get_current_time)
    updated_at = DateTimeField("修改时间", default=get_current_time)

    class Meta:
        db_table = "login_user_info"


class LoginUserInfoDetail(PgsqlBaseModel):
    id = AutoField(primary_key=True)
    user_id = TextField("用户ID")
    source = TextField("来源", default="tianyancha")
    raw_cookies = TextField("raw_cookies")
    cookies = TextField("cookies")
    is_expire = BlobField("是否激活", default=True)
    is_super = BlobField("是否超级用户", default=False)
    counter = IntegerField("使用次数", default=0)
    created_at = DateTimeField("创建时间", default=get_current_time)
    updated_at = DateTimeField("修改时间", default=get_current_time)

    class Meta:
        db_table = "login_user_info_detail"
