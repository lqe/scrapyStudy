# coding:utf-8

import os
import MySQLdb

from newsCrawlBykeyWords.items import NewsItem

filePath = os.path.dirname(os.path.abspath(__file__))

class SingleTon(type):
    def __call__(cls, *args, **kwargs):
        if hasattr(cls, '_single'):
            return cls._single
        else:
            cls._single = type.__call__(cls, *args, **kwargs)
            return cls._single


class BaseModels(object):
    def __init__(self):
        conf = {}
        with open(os.path.join(filePath,"conf.txt"), "rb") as f:
            for line in f.readlines():
                key, value = tuple(line.strip().split("="))
                conf[key] = value
        self.db = MySQLdb.connect(
                host=conf['host'], port=int(conf['port']),
                user=conf['user'], passwd=conf['passwd']
        )
        self.db.select_db('scrapy')
        self.db.set_character_set('utf8')

    def get_db(self):
        return self.db

    def close(self):
        self.db.close()


class NewsHandler(BaseModels):
    __metaclass__ = SingleTon

    AllUrlMd5 = set()

    def __init__(self):
        super(NewsHandler, self).__init__()
        NewsHandler.AllUrlMd5 = self.getAllUrlMd5()

    def insert(self, items):
        cur = self.db.cursor()

        def get_values(item):
            url_md5 = item['url_md5']
            url = item['url']
            title = item['title']
            dateline = item['dateline']
            source = item['source']
            return (url_md5, url, title, dateline, source)

        if isinstance(items, NewsItem):
            cur.execute('''insert into news(`url_md5`, `url`, `title`,`dateline`,`source`)
                           values(%s,%s,%s,%s,%s)''', get_values(items))
        else:
            cur.executemany('''insert into news(`url_md5`, `url`, `title`,`dateline`,`source`)
                           values(%s,%s,%s,%s,%s)''', [get_values(items) for item in items])
        cur.close()
        self.db.commit()

    def getAllUrlMd5(self):
        cur = self.db.cursor()
        cur.execute("select `url_md5` from news")
        res = set(url_md5 for url_md5, in cur.fetchall())
        cur.close()
        return res


if __name__ == "__main__":
    handle = NewsHandler()
    print iter(handle.AllUrlMd5).next(), len(handle.AllUrlMd5)
