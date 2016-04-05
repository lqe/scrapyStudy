#coding:utf-8

import sys
sys.path.insert(0, '..')
from models import BaseModels
import re
import json
import jieba
import jieba.analyse

db = BaseModels().get_db()
cur = db.cursor()

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
        for id, content, in cur.fetchall():
            res = jieba.analyse.extract_tags(re.sub(ur'[\w\s]', '', content), topK=100, withWeight=True)
            tmp_dic = {}
            for k,v in res:
                tmp_dic[k] = str(v)[:8]
            cur.execute("update news set `cut_words`=%s where id=%s ", (json.dumps(tmp_dic), id))
        db.commit()
        finished += affected_rows
        print 'has finished %d total=%d' % (finished, total)
finally:
    cur.close()
    db.close()
