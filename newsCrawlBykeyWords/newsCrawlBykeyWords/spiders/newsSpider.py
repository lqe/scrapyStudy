# coding:utf-8

import pdb
import hashlib
import urllib
import scrapy
from scrapy import spiders

from ..items import NewsItem
from ..models import NewsHandler
from ..utils.customFun import searchTime, timFormat
from ..utils.newParsed import NewsParse


class NewsSpider(scrapy.spiders.Spider):
    name = "news"
    download_delay = 1

    def __init__(self, name=None, **kwargs):
        super(NewsSpider, self).__init__(name, **kwargs)
        self.maxNewsNum = 1
        self.newsNum = 0

    def start_requests(self):
        urls = []
        base_url = 'http://news.baidu.com/ns?'
        args = {
            "sr": 0, "rn": 20, "tn": "news", "ct": 1, "clk": "sortbyrel"
        }
        args["word"] = "生态"
        urls.append(base_url + urllib.urlencode(args))
        args["word"] = "生态 补偿"
        urls.append(base_url + urllib.urlencode(args))
        # args["word"] = "生态 绿色 发展"
        # urls.append(base_url + urllib.urlencode(args))
        for url in urls:
            print url
            yield self.make_requests_from_url(url)

    def parse(self, response):
        ctx = scrapy.Selector(response)
        singleNew = ctx.xpath("//div[@class='result'][@id]")
        for sel in singleNew:
            try:
                tmp = sel.xpath(".//p[@class='c-author']/text()").extract()[0].split(u"\xa0\xa0")
                source = tmp[0]
                dateline = searchTime(tmp[1])
            except:
                source, dateline = None, None
            title = ''.join(sel.xpath(".//a[@href][1]//text()").extract())
            url = sel.xpath(".//a[@href][1]/@href").extract()[0]
            req = scrapy.Request(url, callback=self.newsParse, meta={"title": title,
                                                                     "dateline": dateline,
                                                                     "source": source})
            yield self.genRequest(req)
            for next_url in ctx.xpath("//p[@id='page']/a[@href][position()>1][@class]/@href").extract():
                req = scrapy.Request('http://news.baidu.com' + next_url, callback=self.parse)
                yield self.genRequest(req, news=False)

    def newsParse(self, response):
        url, meta = response.url, response.meta
        news_parse = NewsParse(response.body, url)
        news_parse.set_dateline(meta["dateline"])
        news_parse.set_source(meta["source"])
        news_parse.set_title(meta["title"])

        kw = {}
        kw["url"] = url
        kw["title"] = news_parse.get_title()
        kw["dateline"] = news_parse.get_dateline()
        kw["source"] = news_parse.get_source()
        kw["content"]  = news_parse.get_content()
        return NewsItem.createNewItem(**kw)

    def genRequest(self, request, news=True):
        # 超出范围
        if self.newsNum > self.maxNewsNum:
            return None
        # 已经抓取
        if hashlib.md5(request.url).hexdigest() in NewsHandler.AllUrlMd5:
            return None
        if news:
            self.newsNum += 1
        return request
