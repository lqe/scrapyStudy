# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem

from models import NewsHandler

class NewsPipeline(object):
    def __init__(self):
        self.news_handler = NewsHandler()

    def process_item(self, item, spider):
        self.news_handler.insert(item)
        return item

class FilterPipeline(object):
    def process_item(self, item, spider):
        url, url_md5  = item['url'], item['url_md5']

        # 过滤掉content是空的item
        if item["content"] is None:
            raise DropItem('content is None, drop it.')
        # 过滤掉已经爬取过的Item
        if item['url_md5'] in NewsHandler.AllUrlMd5:
            raise DropItem('<%s><%s> has crawled.' % (item['url'], item['url_md5']))
        else:
            NewsHandler.AllUrlMd5.add(url_md5)
            return item
