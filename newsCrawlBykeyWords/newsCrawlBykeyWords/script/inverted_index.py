# coding:utf-8

import sys

sys.path.insert(0, '..')
from models import BaseModels
import json


def build_inverted_data():
    db = BaseModels().get_db()
    cur = db.cursor()

    cur.execute('select count(*) from news ;')
    total = cur.fetchone()[0]

    skip, length = 0, 500
    finished = 0
    cur.execute("truncate table inverted_index;") # 清空原先的倒排索引
    try:
        while finished != total:
            affected_rows = cur.execute("select id, content, cut_words from news limit %s,%s", (skip, length))
            for news_id, content, cut_words in cur.fetchall():
                content = content.decode('utf-8')
                for word, weight in json.loads(cut_words).iteritems():
                    position = []
                    word_length = len(word)
                    pos = content.find(word)
                    while pos != -1:
                        position.append(pos)
                        pos = content.find(word, pos + word_length)
                    info = ':'.join([str(news_id), str(weight), '&'.join(map(str, position))])

                    cur.execute("select info from inverted_index where word=%s", (word,))
                    tmp = cur.fetchone()
                    # info存在, 需要追加
                    if tmp:
                        info = ";".join([tmp[0], info])
                        cur.execute("update inverted_index set info = %s where word = %s", (info, word))
                    # info不存在, 需要添加
                    else:
                        cur.execute("insert into inverted_index(word, info) values(%s, %s)", (word, info))
            finished += affected_rows
            skip = finished
            db.commit()
            print 'has finished %d total=%d' % (finished, total)
    finally:
        cur.close()
        db.close()


def test(word=None):
    db = BaseModels().get_db()
    cur = db.cursor()
    if word is None:
        cur.execute("select id from inverted_index")
        lis = cur.fetchall()
        if not lis:
            print "no record"
            return
        from random import choice
        cur.execute("select word, info from inverted_index where id=%s", (choice(lis),))
        word, info = cur.fetchone()
        word = unicode(word, 'utf-8')
        info = unicode(info, 'utf-8')
    else:
        word = unicode(word, 'utf-8') if not isinstance(word, unicode) else word
        cur.execute("select info from inverted_index where word=%s", (word, ))
        info = cur.fetchone()[0]
        info = unicode(info, 'utf-8')
    allNewsLis = []
    for news_info in info.split(u";"):
        news_id, word_weight, positions = tuple(news_info.split(":"))
        positions = map(int, positions.split("&"))
        cur.execute("select content from news where id = %s;", (news_id,))
        content = unicode(cur.fetchone()[0], 'utf-8')
        # 标注
        contentLis = []
        word_length = len(word)
        begin = 0
        for pos in positions:
            contentLis.append(content[begin:pos])
            contentLis.append("<font color='red'>")
            contentLis.append(content[pos:pos+word_length])
            contentLis.append("</font>")
            begin = pos + word_length
        contentLis.append(content[begin:])
        allNewsLis.append((word_weight, news_id, ''.join(contentLis)))
    cur.close()
    db.close()
    allNewsLis.sort(reverse=True)
    print 'word', word
    for word_weight, news_id, content in allNewsLis:
        print word_weight, content
    return allNewsLis


if __name__ == "__main__":
    # build_inverted_data()
    test(u'今日')
    test(u'乐视')
