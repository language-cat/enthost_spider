import json
import logging
import re
import time
from urllib.parse import urlencode
import jsonpath
import scrapy
from more_itertools import first

from lxml import etree

from enthost_spider.items import CompanyInfo, CompanyInfoHistory, CompanyInfoSummary
from scrapy_utils.base_spider import RedisBaseSpider
import hashlib

logger = logging.getLogger(__name__)


class TianyanchaSpider(RedisBaseSpider):
    """
    天眼查抓取工商信息
    """
    name = "tianyancha"

    custom_settings = {
        "DOWNLOAD_DELAY": 10,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_IP": 1,
    }

    def parse(self, response, *args, **kwargs):
        force_request = response.request.meta.get("force_request", False)
        url = response.xpath("//a[@class='name link-hover-click']/@href").get()
        if url:
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                dont_filter=force_request,
            )

    def parse_detail(self, response):
        force_request = response.request.meta.get("force_request", False)
        tmp_xpath = "//div[contains(text(), {!r})]/div//text()"
        tmp_xpath1 = "//td[contains(text(), {!r})]/following-sibling::td[position()=1]/text()"
        tmp_xpath2 = "//td[contains(text(), {!r})]/following-sibling::td[position()=1]/span/text()"
        # 中文名
        company_chs_name1 = response.xpath("//div[contains(text(), '企业名称：')]/div/h1//text()").get()

        company_chs_name2 = response.xpath("//h1[@class='index_company-name__LqKlo']/text()").get()
        # 企业税号
        company_tax_num = response.xpath(tmp_xpath.format('企业税号：')).get()
        # 企业地址
        address = response.xpath(tmp_xpath.format('企业地址：')).get()
        # 开户银行
        bank = response.xpath(tmp_xpath.format('开户银行：')).get()
        # 银行账户
        bank_account = response.xpath(tmp_xpath.format('银行账户：')).get()

        # 注册资本
        registered_capital = response.xpath("//td[contains(text(), '注册资本')]/following-sibling::td/div/@title").get()

        # 实缴资本
        paid_capital = response.xpath("//td[contains(text(), '实缴资本')]/following-sibling::td[last()-1]/text()").get()

        # 营业期限
        business_term = response.xpath("//td[contains(text(), '营业期限')]/following-sibling::td/span/text()").get()

        # 经营状态
        business_status = response.xpath(tmp_xpath1.format("经营状态")).get()

        # 纳税人识别号
        taxpayer_identification_number = response.xpath(tmp_xpath1.format('纳税人识别号')).get()

        # 统一社会信用代码
        social_credit_code = response.xpath(
            "//td[contains(text(), '统一社会信用代码')]/following-sibling::td[position()=1]/text()"
        ).get()

        # 纳税人资质
        taxpayer_qualifications = response.xpath(tmp_xpath1.format('纳税人资质')).get()

        # 组织机构代码
        organization_code = response.xpath(tmp_xpath1.format('组织机构代码')).get()

        # 登记机关
        registration_authorities = response.xpath(tmp_xpath1.format("登记机关")).get()

        # 工商注册号
        business_registration_number = response.xpath(tmp_xpath1.format("工商注册号")).get()

        # 企业类型
        business_type = response.xpath(tmp_xpath1.format("公司类型")).get()

        # 行业
        industry = response.xpath(tmp_xpath1.format("行业")).get()

        # 人员规模
        personnel_size = response.xpath(tmp_xpath1.format("人员规模")).get()

        # 曾用名
        former_name = response.xpath(tmp_xpath2.format("曾用名")).get()

        # 英文名
        company_en_name = response.xpath(tmp_xpath1.format("英文名称")).get()

        # 企业电话
        telephone = response.xpath(tmp_xpath.format('企业电话')).get()

        source_id = raw_source_id.group() if (
                (raw_source_id := re.search(r"(?<=https://tax.tianyancha.com/).*", response.url)) is not None
        ) else None

        d = {
            "source": self.name,
            "source_id": source_id,
            "company_chs_name": company_chs_name1 or company_chs_name2,
            "company_en_name": company_en_name,
            "telephone": telephone,

            "address": address,
            "business_term": business_term,
            "business_status": business_status,
            "registered_capital": registered_capital,
            "paid_capital": paid_capital,

            "taxpayer_identification_number": taxpayer_identification_number
            if taxpayer_identification_number is not None and len(taxpayer_identification_number) in [15, 18]
            else social_credit_code,
            "taxpayer_qualifications": taxpayer_qualifications,
            "organization_code": organization_code,
            "registration_authorities": registration_authorities,
            "social_credit_code": social_credit_code,
            "business_registration_number": business_registration_number,

            "business_type": business_type,
            "industry": industry,
            "personnel_size": personnel_size,
            "former_name": former_name,
            "source_url": f"https://www.tianyancha.com/company/{source_id}",
        }

        yield scrapy.Request(
            url=f"https://www.tianyancha.com/company/{source_id}",
            callback=self.supplement_company_data,
            meta={"data": d},
            headers=self.headers,
            dont_filter=force_request,
        )

    def supplement_company_data(self, response):
        force_request = response.request.meta.get("force_request", False)
        d = response.meta.get("data", {})

        # 法定代表人
        legal_representative = response.xpath(
            "//span[contains(text(), '法定代表人')]/following-sibling::span/a/@title"
        ).get()

        # 经营范围
        business_scope = response.xpath("//td[contains(text(), '经营范围')]/following-sibling::td/text()").get()

        # 邮箱
        email = response.xpath("//span[contains(text(), '邮箱：')]/following-sibling::span[position()=1]/text()").get()

        website = response.xpath("//span[contains(text(), '网址：')]/parent::div/a/text()").get()

        # 成立日期
        company_created_date = response.xpath("//td[contains(text(), '成立日期')]/following-sibling::td//text()").get()

        # 核准日期
        company_verified_date = response.xpath("//td[contains(text(), '核准日期')]/following-sibling::td//text()").get()

        d["legal_representative"] = legal_representative
        d["email"] = email
        d["website"] = website
        d["company_created_date"] = company_created_date
        d["company_verified_date"] = company_verified_date
        d["business_scope"] = business_scope

        change_history_params = {
            "_": time.time_ns(),
            "gid": d.get("source_id"),
            "pageNum": 1,
            "pageSize": 100,
            "changeItem": -100,
        }

        yield scrapy.Request(
            url=f"https://capi.tianyancha.com/cloud-company-background/company/changeinfoEm?{urlencode(change_history_params)}",
            headers=self.headers,
            callback=self.get_change_history_data,
            meta={"data": d},
            dont_filter=force_request,
        )

    def get_change_history_data(self, response):
        force_request = response.request.meta.get("force_request", False)
        d = response.meta.get("data", {})
        source_id = d.get("source_id")
        if first(jsonpath.jsonpath(response.json(), "$..state"), "warning") != "ok":
            change_history_info = None
            d["change_history_info"] = change_history_info
        else:
            result = jsonpath.jsonpath(response.json(), "$..data..result")

            change_history_info = [
                {
                    "index": index,
                    "change_item": value.get("changeItem", None),
                    "change_time": value.get("changeTime", None),
                    "change_before": ''.join(raw_change_before.xpath("//p//text()"))
                    if (raw_change_before := etree.HTML(
                        value.get("contentBefore", "<html></html>"))) is not None else None,
                    "change_after": ''.join(raw_change_after.xpath("//p//text()"))
                    if (raw_change_after := etree.HTML(
                        value.get("contentAfter", "<html></html>"))) is not None else None
                }
                for index, value in enumerate(first(result, []), start=1)
            ]
            d["change_history_info"] = json.dumps(change_history_info, ensure_ascii=False)

        yield scrapy.Request(
            url=f"https://nianbao.tianyancha.com/{source_id}/",
            headers=self.headers,
            callback=self.get_annual_report,
            meta={"data": d},
            dont_filter=force_request,
        )

    def get_annual_report(self, response):
        d = response.meta.get("data", {})
        source_id = d.get("source_id")
        legal_representative = response.xpath("//div[contains(text(), '法定代表人：')]/span/text()").get()

        company_created_date = response.xpath("//div[contains(text(), '成立日期')]/span/text()").get()

        raw_telephone1 = response.xpath(
            "//td[contains(text(), '企业联系电话')]/following-sibling::td[position()=1]/text()"
        ).get()
        raw_telephone2 = d.get("telephone", None)

        if raw_telephone2:
            telephone = first([raw_telephone1 for i in ["*", '-', '暂无信息'] if i in raw_telephone2], None)
        else:
            telephone = raw_telephone1

        raw_email1 = response.xpath(
            "//td[contains(text(), '电子邮箱')]/following-sibling::td[position()=1]/text()"
        ).get()
        raw_email2 = d.get("email", None)
        if raw_email2:
            email = first([raw_email1 for i in ["*", '-', '暂无信息'] if i in raw_email2], None)
        else:
            email = raw_email1

        d["legal_representative"] = legal_representative
        d["telephone"] = telephone
        d["email"] = email
        d["company_created_date"] = company_created_date
        dd = {
            **d,
            "origin_id": f'{self.name}_{source_id}_{hashlib.md5(json.dumps(d).encode("utf-8")).hexdigest()}',
        }

        raw_change_history_info = d["change_history_info"]

        if raw_change_history_info is not None:
            change_history_info = raw_change_history_info
        else:
            change_history_info = json.dumps(dict())

        ddd = {
            "source": d["source"],
            "social_credit_code": d["taxpayer_identification_number"],
            "company_chs_name": d["company_chs_name"],
            "ent_info_json": json.dumps(d, ensure_ascii=False),
            "ent_info_md5": hashlib.md5(json.dumps(d).encode("utf-8")).hexdigest(),
            "change_history_info_json": change_history_info,
            "change_history_info_md5": hashlib.md5(change_history_info.encode("utf-8")).hexdigest(),
        }
        yield CompanyInfo(**d)
        yield CompanyInfoHistory(**dd)
        yield CompanyInfoSummary(**ddd)
