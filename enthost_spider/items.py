# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# import scrapy

import scrapy_autodb as scrapy


class CompanyInfo(scrapy.OrderedItem):
    company_chs_name = scrapy.Field()  # 中文名
    company_en_name = scrapy.Field()  # 英文名
    source_id = scrapy.Field()  # 来源ID
    source = scrapy.Field()  # 来源
    source_url = scrapy.Field()  # 来源url
    telephone = scrapy.Field()  # 电话
    address = scrapy.Field()  # 地址

    business_term = scrapy.Field()  # 营业期限
    business_status = scrapy.Field()  # 经营状态
    registered_capital = scrapy.Field()  # 注册资本
    paid_capital = scrapy.Field()  # 实缴资本
    social_credit_code = scrapy.Field()  # 统一社会信用代码
    taxpayer_identification_number = scrapy.Field()  # 纳税人识别号
    taxpayer_qualifications = scrapy.Field()  # 纳税人资质
    organization_code = scrapy.Field()  # 组织机构代码
    registration_authorities = scrapy.Field()  # 登记机关
    business_registration_number = scrapy.Field()  # 工商注册号

    business_type = scrapy.Field()  # 企业类型
    industry = scrapy.Field()  # 行业
    personnel_size = scrapy.Field()  # 人员规模
    former_name = scrapy.Field()  # 曾用名
    legal_representative = scrapy.Field()  # 法定代表人

    business_scope = scrapy.Field()  # 经营范围
    email = scrapy.Field()  # 邮箱
    website = scrapy.Field()  # 网址
    company_created_date = scrapy.Field()  # 成立日期
    company_verified_date = scrapy.Field()  # 核准日期

    change_history_info = scrapy.Field()  # 变更信息

    airflow_modify_date = scrapy.Field()

    class Meta:
        indexes = (
            (('source', "source_id"), True),
        )


class CompanyInfoHistory(scrapy.OrderedItem):
    """
    记录历史工商信息
    """
    company_chs_name = scrapy.Field()  # 中文名
    company_en_name = scrapy.Field()  # 英文名
    source_id = scrapy.Field()  # 来源ID
    source = scrapy.Field()  # 来源
    source_url = scrapy.Field()  # 来源url
    telephone = scrapy.Field()  # 电话
    address = scrapy.Field()  # 地址

    business_term = scrapy.Field()  # 营业期限
    business_status = scrapy.Field()  # 经营状态
    registered_capital = scrapy.Field()  # 注册资本
    paid_capital = scrapy.Field()  # 实缴资本
    social_credit_code = scrapy.Field()  # 统一社会信用代码
    taxpayer_identification_number = scrapy.Field()  # 纳税人识别号
    taxpayer_qualifications = scrapy.Field()  # 纳税人资质
    organization_code = scrapy.Field()  # 组织机构代码
    registration_authorities = scrapy.Field()  # 登记机关
    business_registration_number = scrapy.Field()  # 工商注册号

    business_type = scrapy.Field()  # 企业类型
    industry = scrapy.Field()  # 行业
    personnel_size = scrapy.Field()  # 人员规模
    former_name = scrapy.Field()  # 曾用名
    legal_representative = scrapy.Field()  # 法定代表人

    business_scope = scrapy.Field()  # 经营范围
    email = scrapy.Field()  # 邮箱
    website = scrapy.Field()  # 网址
    company_created_date = scrapy.Field()  # 成立日期
    company_verified_date = scrapy.Field()  # 核准日期

    change_history_info = scrapy.Field()  # 变更信息

    origin_id = scrapy.Field()  # 信息同步来源ID

    class Meta:
        indexes = (
            (('source', "source_id", "origin_id"), True),
        )


class CompanyInfoSummary(scrapy.OrderedItem):
    """
    用于记录 工商信息变更信息
    """
    social_credit_code = scrapy.Field()
    company_chs_name = scrapy.Field()

    ent_info_json = scrapy.Field()
    ent_info_md5 = scrapy.Field()

    change_history_info_json = scrapy.Field()
    change_history_info_md5 = scrapy.Field()

    source = scrapy.Field()

    class Meta:
        indexes = (
            (('source', "social_credit_code", "ent_info_md5", "change_history_info_md5"), True),
        )
