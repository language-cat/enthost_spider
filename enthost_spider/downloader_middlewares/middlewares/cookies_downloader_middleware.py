import json
import logging
import os
import re
import time
from datetime import datetime
import cv2
import numpy as np
import peewee
import random
from dateutil.utils import today
from more_itertools import first
from playwright.sync_api import sync_playwright
from scrapy import signals
from twisted.enterprise import adbapi

from enthost_spider.downloader_middlewares.models.cookies_downloader_middleware import LoginUserInfoDetail
from scrapy_utils.base_time import get_current_time

logger = logging.getLogger(__name__)


# TODO need to be tested
class CookiesDownloaderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(
            project=crawler.settings.get('BOT_NAME'),
            db_settings=crawler.settings.get('DATABASE')
        )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def __init__(self, project, db_settings):
        self.db_settings = db_settings
        self.project = project
        self.db_engine = self.db_settings.get("engine")
        self.db_params = self.db_settings.get("params")
        self.redirect_times = 2
        self.error_code = [401, 402, 403, 404]
        self.warning_code = [429]
        self.sleep_time = 15
        self.headless = True

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

    def _get_cookies(self, spider):
        """
        获取cookie
        :param spider:
        :return:
        """
        raw_query = LoginUserInfoDetail.select(
            LoginUserInfoDetail.id,
            LoginUserInfoDetail.cookies,
        ).where(
            LoginUserInfoDetail.is_expire == False,
            LoginUserInfoDetail.created_at >= today(),
            LoginUserInfoDetail.source == spider.name,
        )

        if not raw_query:
            return None, None
        obj = random.choice(raw_query)
        _id = obj.id
        cookies = obj.cookies
        return _id, cookies

    def _update_cookies_status(self, _id):
        """
        更新cookie状态
        :param _id:
        :return:
        """

        raw_query = LoginUserInfoDetail.update(
            is_expire=True
        ).where(
            LoginUserInfoDetail.id == _id
        )
        raw_query.execute()

        return

    def _update_cookies_count(self, _id):
        """
        更新cookie使用次数
        :param _id:
        :return:
        """
        raw_query = LoginUserInfoDetail.update(
            counter=LoginUserInfoDetail.counter + 1
        ).where(
            LoginUserInfoDetail.id == _id
        )
        raw_query.execute()

        return

    def update_login_user_info_detail(self, _id, raw_cookies, cookies):

        raw_query = LoginUserInfoDetail.update(
            cookies=cookies,
            raw_cookies=raw_cookies,
            is_expire=False,
            updated_at=datetime.now(),
        ).where(
            LoginUserInfoDetail.id == _id,
        )
        raw_query.execute()
        return

    def format_cookies(self, raw_cookies):
        """

        :return:
        """
        if not raw_cookies:
            return None
        raw_cookies_list = list()
        for raw_cookies_index, raw_cookies_value in enumerate(raw_cookies):
            name = raw_cookies_value.get("name")
            value = raw_cookies_value.get("value")
            raw_cookies_list.insert(raw_cookies_index, f"{name}={value}")
        cookies = '; '.join(raw_cookies_list)
        return cookies

    def get_tracks(self, offset):
        """
        :param offset:
        :return:
        """
        v0 = 0
        tracks_list = []
        current = 0
        print(f"偏移量: {offset}")
        if offset >= 150:
            mid = offset * 0.75
            while current < offset:
                t = 0.1 * random.randint(1, 2)
                if current < mid:
                    a = random.randint(6, 7)
                else:
                    a = -random.randint(7, 8)
                s = (v0 * t) + (0.5 * a * (t ** 2))
                current = s + current
                tracks_list.append(s)
                v0 = v0 + (a * t)
        elif 150 < offset <= 100:
            mid = offset * 0.65
            while current < offset:
                t = 0.1 * random.randint(1, 2)
                if current < mid:
                    a = random.randint(4, 5)
                else:
                    a = -random.randint(6, 7)
                s = (v0 * t) + (0.5 * a * (t ** 2))
                current = s + current
                tracks_list.append(s)
                v0 = v0 + (a * t)
        else:
            mid = offset * 0.65
            while current < offset:
                t = 0.1 * random.randint(1, 2)
                if current < mid:
                    a = random.randint(2, 3)
                else:
                    a = -random.randint(3, 4)
                s = (v0 * t) + (0.5 * a * (t ** 2))
                current = s + current
                tracks_list.append(s)
                v0 = v0 + (a * t)

        mean = np.mean(tracks_list)
        std_dev = np.std(tracks_list)
        normal_distribution = np.random.normal(mean, std_dev, len(tracks_list))
        data_with_random = list(zip(tracks_list, normal_distribution))
        sorted_data = [x[0] for x in sorted(data_with_random, key=lambda x: x[1])]

        return sorted(sorted_data, reverse=True)

    def get_picture_offset(self, gap_screenshot, full_screenshot):
        """
        用于识别图片缺口, 如果缺口标注出来只有一个, 证明没有识别出来, 如果有多个则取面积最大的前两个作为对比 offset是一个定值
        :param full_screenshot:
        :param gap_screenshot:
        :return:
        """

        offset = 60
        raw_area_dict = dict()
        gap_screenshot_image = cv2.imread(gap_screenshot)
        full_screenshot_image = cv2.imread(full_screenshot)
        # 确保两张图片具有相同的尺寸
        if gap_screenshot_image.shape != full_screenshot_image.shape:
            raise ValueError("images must be the same shape")
        # 计算差异图
        difference = cv2.absdiff(gap_screenshot_image, full_screenshot_image)
        gray = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
        # 找到差异的位置
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            axis_x, asis_y, width, height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            cv2.rectangle(gap_screenshot_image, (axis_x, asis_y), (axis_x + width, asis_y + height), (0, 255, 0), 2)
            raw_area_dict[area] = {"axis_x": axis_x, "asis_y": asis_y, "width": width, "height": height}
        raw_area_dict = dict(sorted(raw_area_dict.items(), reverse=True))

        if len(raw_area_dict.keys()) <= 1:
            return offset
        elif len(raw_area_dict.keys()) > 2:
            start_location, gap_location, *_ = raw_area_dict.values()
        else:
            start_location, gap_location = raw_area_dict.values()

        start_x, start_y, start_width, start_height = start_location.values()
        gap_x, gap_y, gap_width, gap_height = gap_location.values()

        offset = abs(gap_x - start_x)
        if offset <= 10:
            offset = offset + 50

        return offset

    def drag_gap_to_location_from_page(self, page, button, timeout):
        """
        拖动滑块到指定位置
        :return:
        """
        wait_for_timeout = 2000
        gap_screenshot = f"./static/images/gap_screenshot/{get_current_time().strftime('%Y-%m-%d-%H-%M-%S')}.png"

        full_screenshot = f"./static/images/full_screenshot/{get_current_time().strftime('%Y-%m-%d-%H-%M-%S')}.png"

        page.wait_for_timeout(wait_for_timeout)
        full_screenshot_instance = page.wait_for_selector(
            "//div[@class='gt_holder gt_custom']", timeout=timeout
        ).screenshot(path=full_screenshot)

        box = button.bounding_box()

        button.hover()
        page.mouse.down()
        page.wait_for_timeout(wait_for_timeout)
        gap_screenshot_instance = page.wait_for_selector(
            "//div[@class='gt_holder gt_custom']", timeout=timeout
        ).screenshot(path=gap_screenshot)
        offset = self.get_picture_offset(full_screenshot=full_screenshot, gap_screenshot=gap_screenshot)
        offset_list = self.get_tracks(offset)
        raw_x = 0
        for index, current_offset in enumerate(offset_list):
            if index == 0:
                x = box['x'] + current_offset + raw_x
            else:
                x = current_offset + raw_x + 0.3
            page.mouse.move(x=x, y=box['y'])
            raw_x = x
        page.mouse.up()

        os.remove(gap_screenshot)
        os.remove(full_screenshot)

        return

    def drag_slider_from_page(self, url, _id, headers):
        count = 0
        entry_times = 5
        timeout = 600000
        wait_for_time_out = 300000
        with sync_playwright() as playwright:
            with playwright.chromium.launch(headless=self.headless) as browser:
                context = browser.new_context()
                context.set_extra_http_headers(headers=headers)
                page = context.new_page()
                page.goto(url)
                page.wait_for_timeout(wait_for_time_out)
                button = page.locator("xpath=//div[@class='gt_slider_knob gt_show']")
                while count < entry_times:
                    self.drag_gap_to_location_from_page(page=page, button=button, timeout=timeout)
                    page.wait_for_timeout(wait_for_time_out)
                    success_msg = re.findall("/usercenter/personalcenter", page.content())
                    if success_msg != list():
                        logger.info("验证成功")
                        raw_cookies = page.context.cookies()
                        cookies = self.format_cookies(raw_cookies)
                        logger.info(f"cookies: {cookies}")
                        self.update_login_user_info_detail(
                            _id=_id,
                            raw_cookies=json.dumps(raw_cookies, ensure_ascii=False),
                            cookies=cookies
                        )
                        return True
                    page.wait_for_timeout(wait_for_time_out)
                    content = re.findall("移动到此开始验证", page.content())
                    if content == list():
                        return False
                    raw_error_type = page.wait_for_selector("xpath=//span[@class='gt_info_type']", timeout=timeout)
                    error_type = raw_error_type.text_content()
                    logger.info(error_type)
                    if error_type in ['验证失败:', "再来一次:"]:
                        page.wait_for_timeout(wait_for_time_out)
                        refresh_button = page.wait_for_selector(
                            "xpath=//a[@class='gt_refresh_button']", timeout=timeout
                        )
                        refresh_button.click()
                        count = count + 1
                    elif error_type in ["出现错误:"]:
                        return False
                return False

    def process_request(self, request, spider):
        _id, raw_cookies = self._get_cookies(spider=spider)
        if raw_cookies:
            self._update_cookies_count(_id=_id)
            request.cookies = {
                i.split("=")[0]: i.split("=")[1]
                for i in raw_cookies.split(";")
            }
            request.meta["cookies_id"] = _id
        return None

    def process_response(self, request, response, spider):
        last_cookies_id = request.meta.get("cookies_id", None)
        _id, raw_cookies = self._get_cookies(spider=spider)
        if response.status in self.error_code:
            request.dont_filter = False
            return response
        time.sleep(self.sleep_time)
        if "请进行身份验证以继续使用" in response.text:
            flag = self.drag_slider_from_page(
                url=response.url,
                _id=_id,
                headers=spider.headers,
            )
            if not flag:
                logger.warning("cookies失效需要验证身份进行")
                self._update_cookies_status(_id=_id)
                request_url = first(request.meta.get("redirect_urls"), None)
                new_request = request.replace(url=request_url, dont_filter=True)
                return new_request
        if "login" in response.url:
            request_url = first(request.meta.get("redirect_urls"), None)
            if raw_cookies is None:
                logger.warning("没有可用的cookies")
                new_request = request.replace(url=request_url, dont_filter=True)
                time.sleep(self.sleep_time)
                return new_request
            else:
                new_request = request.replace(url=request_url, dont_filter=True)
                new_request.cookies = {
                    i.split("=")[0]: i.split("=")[1]
                    for i in raw_cookies.split(";")
                }
                time.sleep(self.sleep_time)
                return new_request
        time.sleep(self.sleep_time)
        request.dont_filter = False
        return response
