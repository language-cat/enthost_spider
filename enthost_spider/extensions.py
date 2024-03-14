from scrapy import signals


class BloomFilterExtensions:
    """
    实现 绕过BloomFilter 重新发起请求
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.process_request, signals.request_scheduled)
        return s

    def process_request(self, request, spider):
        depth = request.meta.get("depth", None)
        if not depth:
            force_request = request.meta.get("force_request", False)
            if force_request:
                request.dont_filter = force_request
        else:
            request.meta["force_request"] = request.dont_filter
        return None
