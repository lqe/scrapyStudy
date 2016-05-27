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
    name = "newsTest"
    download_delay = 1

    def __init__(self, name=None, **kwargs):
        super(NewsSpider, self).__init__(name, **kwargs)

    start_urls = [
        'http://www.csunews.com/news/dt/31832.html'
    ]


    def parse(self, response):
        news_parse = NewsParse(response.body, response.url)

        kw = {}
        kw["url"] = response.url
        kw["title"] = news_parse.get_title()
        kw["dateline"] = news_parse.get_dateline()
        kw["source"] = news_parse.get_source()
        kw["content"]  = news_parse.get_content()
        return NewsItem.createNewItem(**kw)


