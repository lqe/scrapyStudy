#coding:utf-8
import sys
sys.path.insert(0, '..')
import codecs
from models import BaseModels

db = BaseModels().get_db()

cur = db.cursor()
cur.execute("select count(1) from news;")
total = cur.fetchone()[0]

skip, length = 0, 500
finished = 0
f = codecs.open('newsData.txt', 'wb', 'utf-8')
try:
    while finished != total:
        resNum = cur.execute('''select `url`, `title`, `dateline`,`source`,`content`, `cut_words`
                                from news
                                order by `dateline`
                                Limit %s,%s''', (skip, length))
        for url, title, dateline, source, content, cut_words in cur.fetchall():
            tmp = []
            tmp.append(url)
            tmp.append(title or "NULL")
            if dateline:
                tmp.append(dateline.strftime("%Y-%m-%d %H:%M-%S"))
            else:
                tmp.append("NULL")
            tmp.append(source or "NULL")
            tmp.append(content or "NULL")
            tmp.append(cut_words or "NULL")
            f.write(u'\t'.join(ele.decode('utf-8') for ele in tmp)+u"\r\n")
        finished += resNum
        skip = finished
        print "has export news %d, total=%d" % (finished, total)
finally:
    f.close()
    cur.close()
    db.close()


