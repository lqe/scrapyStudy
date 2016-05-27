#coding:utf-8
import sys
sys.path.insert(0, '..')
import re
import json
import codecs
from models import BaseModels

db = BaseModels().get_db()

cur = db.cursor()
cur.execute("select count(1) from news;")
total = cur.fetchone()[0]

skip, length = 0, 500
finished = 0
f = codecs.open('tmp/newsDataBref.txt', 'ab', 'utf-8')
from collections import defaultdict
words = defaultdict(float)
news_words = []

try:
    while finished != total:
        resNum = cur.execute('''select `content`, `cut_words`
                                from news
                                where content is not null
                                Limit %s,%s''', (skip, length))

        for content, cut_words in cur.fetchall():
            content = content.decode('utf-8')
            cut_words = json.loads(cut_words)
            news_words.append((content,cut_words))
            # if u"补偿" in content and u"生态" in content:
            if u"葬" in content or u"电商" in content or u'小米' in content :
                # news_words.append((content,cut_words))
                for k,v in cut_words.items():
                    words[k] += float(v)
                f.write('0\t'+re.sub(u"[\t\r\n]+", "", content)+'\n')
        finished += resNum
        skip = finished
        print "has export news %d, total=%d" % (finished, total)
finally:
    f.close()
    cur.close()
    db.close()
_words = sorted(words.iteritems(), key=lambda e:e[1], reverse=True)
total_weight = sum(words.values())
with codecs.open('tmp/keys_word.txt', 'wb', "utf-8") as f:
    for word, weight in _words:
        weight = weight/total_weight
        words[word] = weight
        f.write(word +' '+unicode(weight)+u'\n')
res_lis = []
for content, cut_words in news_words:
    res = 0
    for word, weight in cut_words.items():
        res += float(weight)*words[word]
    res_lis.append((res, content, cut_words))
res_lis.sort(reverse=True)
print 1
