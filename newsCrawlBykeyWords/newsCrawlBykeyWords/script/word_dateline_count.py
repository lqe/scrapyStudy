# coding:utf-8

import sys

sys.path.insert(0, '..')
from models import BaseModels
import json
import codecs


# 插入关键字的 时间出现序列
# 文件每一行的信息 eg 农业机械化	2016-03-30;1/2015-12-10;1
def build_count_data(filename):
    db = BaseModels().get_db()
    cur = db.cursor()
    cur.execute("update inverted_index set countbyday=null, `count`=0;")  # 清空原先的统计的值
    total = sum([1 for i in open(filename, "rb")])
    finished = 0

    f = codecs.open(filename, "rb", "utf-8")
    for line in f:
        line = line.strip()
        tmp = line.split("\t")
        word = tmp[0].strip()
        countInfo = tmp[1].strip()
        wordCount = 0
        for datelineAndCount in countInfo.split('/'):
            wordCount += int(datelineAndCount.split(";")[1])

        cur.execute("select 1 from inverted_index where word=%s", (word,))
        tmp = cur.fetchone()
        # word存在, 添加
        if tmp:
            cur.execute("update inverted_index set countbyday=%s , `count`=%s where word = %s", (countInfo, wordCount, word))
        # word不存在, 需要添加
        else:
            cur.execute("insert into inverted_index(word, countbyday, `count`) "
                        "values(%s, %s, %s)", (word, countInfo, wordCount))
        finished += 1
        if finished % 1000 == 0:
            db.commit()
            print 'has finished %d total=%d' % (finished, total)
    if finished % 1000 != 0:
        print 'has finished %d total=%d' % (finished, total)
    f.close()


def test(word=None):
    db = BaseModels().get_db()
    cur = db.cursor()
    countbyday=""
    count=0
    if word is None:
        cur.execute("select id from inverted_index")
        lis = cur.fetchall()
        if not lis:
            print "no record"
            return
        from random import choice
        cur.execute("select word,  countbyday, `count` from inverted_index where id=%s", (choice(lis),))
        word, info, count = cur.fetchone()
        word = unicode(word, 'utf-8')
        if info:
            countbyday = unicode(info, 'utf-8')
    else:
        word = unicode(word, 'utf-8') if not isinstance(word, unicode) else word
        cur.execute(u"select countbyday, `count`from inverted_index where word=%s", (word,))
        try:
            countbyday, count = cur.fetchone()
            if isinstance(countbyday, str):
                countbyday = unicode(countbyday, 'utf-8')
        except:
            pass
    cur.close()
    db.close()

    print 'word', word
    if countbyday:
        print 'count=', count
        for ele in countbyday.split("/"):
            print ele
    else:
        print "不存在 "


if __name__ == "__main__":
    build_count_data('tmp/word_dateline_count_by_day.txt')
    test(u'新路')
