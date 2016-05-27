# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import re
import hashlib


class NewsItem(scrapy.Item):
    # 字段中不含 [\t\r\n]
    url_md5 = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    dateline = scrapy.Field()  # string
    source = scrapy.Field()
    content = scrapy.Field()

    @classmethod
    def createNewItem(cls, **kwargs):
        news = cls()
        fields = ["url", "title", "dateline","source","content"]
        if hasattr(kwargs['dateline'] , 'strftime'):
            kwargs['dateline'] = kwargs['dateline'].strftime('%Y-%m-%d %H:%M:%S')

        for field in fields:
            value = kwargs[field]
            if value:
                news[field] = re.sub(u"[\t\r\n]+", "", value)
        news["url_md5"] = hashlib.md5(news["url"]).hexdigest()
        return news

    def get(self, key, default="NULL"):
        value = super(NewsItem, self).get(key) or "NULL"
        return value

    def __getitem__(self, key):
        try:
            return self._values[key]
        except:
            return None

    def getlineInfoformated(self):
        fields = ["url", "title", "dateline","source","content"]
        res = []
        for field in fields:
            value = self.get(field, "NULL") or "NULL"
            res.append(value)
        return '\t'.join(res) + "\r\n"

if __name__ == "__main__":
    new = NewsItem()
    print new.getlineInfoformated()
