#coding:utf-8

import sys
import codecs
sys.path.insert(0, '..')
from models import BaseModels
import re
import json
import jieba
import jieba.analyse


# 清空所有分词 set cut_word = null
# while cut——word还有null
#    获取文章--分词 -- 更新cut_word字段
#
db = BaseModels().get_db()
cur = db.cursor()


try:
    from jieba.analyse import set_stop_words
    set_stop_words('tmp/stopword.txt')
    print '加载 停用词'
except:
    print 'add stop_words error'
    pass

words=set()
cur.execute("update news set `cut_words` = null;") # 清空所有的分词
cur.execute("select count(1) from news where `cut_words` is null;")
total = cur.fetchone()[0]
skip, length = 0, 100
finished = 0
try:
    while True:
        affected_rows = cur.execute("select id, content from news where cut_words is null limit %s,%s", (skip, length))
        if affected_rows == 0:
            break
        for id, content in cur.fetchall():
            res = jieba.analyse.extract_tags(re.sub(ur'[\w\s\.\[\]\{\};:<>,\?\*&^%$#@!-_\+=`|\\]', '', content), topK=100, withWeight=True)
            tmp_dic = {}
            for k,v in res:
                tmp_dic[k] = str(v)[:8]
                words.add(k)
            cur.execute("update news set `cut_words`=%s where id=%s ", (json.dumps(tmp_dic), id))
        db.commit()
        finished += affected_rows
        print 'has finished %d total=%d' % (finished, total)
finally:
    cur.close()
    db.close()
# 保存词汇

with codecs.open('tmp/cut_words.txt','wb', 'utf-8') as f:
    for word in words:
        f.write(word+'\n')