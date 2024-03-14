# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy_redis.pipelines import RedisPipeline

from enthost_spider.utils.functions import strip


class EnthostPipeline:
    def process_item(self, item, spider):
        return item


class DropNullTaxpayerIdentificationNumberPipeline(RedisPipeline):

    def _process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if 'taxpayer_identification_number' not in adapter:
            return item
        taxpayer_identification_number = adapter.get('taxpayer_identification_number', None)
        social_credit_code = adapter.get("social_credit_code", None)

        if taxpayer_identification_number != social_credit_code:
            raise DropItem("taxpayer_identification_number not equal to social_credit_code")
        elif len(taxpayer_identification_number) != 15 and len(taxpayer_identification_number) != 18:
            raise DropItem("length of taxpayer_identification_number is not valid")
        elif taxpayer_identification_number is None or not taxpayer_identification_number.strip():
            raise DropItem("Missing taxpayer_identification_number in %s" % item)
        adapter['taxpayer_identification_number'] = str.strip(adapter['taxpayer_identification_number'])
        return item


class StripPipeline(RedisPipeline):

    def _process_item(self, item, spider):
        replace_list = ["-", "_", " ", "略", "/", ""]
        adapter = ItemAdapter(item)
        for key, value in adapter.items():
            adapter[key] = strip(value) or None
            if value is None:
                return item
            if len(value) == 1 and value in replace_list:
                adapter[key] = None
        return item
