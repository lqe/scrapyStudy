# coding:utf-8
import re
import datetime
import chardet
from bs4 import UnicodeDammit


timFormat = "%Y-%m-%d %H:%M:%S"

def findGreatestSubArray(L):
    begin, end, max_sum = 0, 0, L[0]
    for i in xrange(1, len(L)):
        tmp_max_sum = 0
        for j in xrange(i, begin - 1, -1):
            tmp_max_sum += L[j]
            if tmp_max_sum > max_sum:
                begin, end, max_sum = j, i, tmp_max_sum
    return begin, end, max_sum


def searchTime(str):
    timRe = re.compile(ur'(?P<year>\d{4})[-\\/年]'
                       ur'(?P<month>\d{1,2})[-\\/月]'
                       ur'(?P<day>\d{1,2})([-\\/日号])?\s?'
                       ur'((?P<hour>\d{1,2})[-\\/:时点]'
                       ur'(?P<minute>\d{1,2})'
                       ur'([-\\/:分](?P<second>\d{1,2})[秒]?)?)?')

    res = timRe.findall(str)
    timStrFormat = "%s-%s-%s %s:%s:%s"
    if len(res) == 1:
        year, month, day, _, _, hour, minute, _, second = map(lambda e: e or "0", res[0])
        return datetime.datetime.strptime(timStrFormat % (year, month, day, hour, minute, second), timFormat)
    else:
        return None

def get_unicode(text, is_html=False):
    if not text:
        return u''
    if isinstance(text, unicode):
        return text
    encoding = chardet.detect(text)['encoding']
    try: return text.decode(encoding)
    except: pass

    if encoding.lower().startswith('gb'):
        try: return text.decode('gbk')
        except: pass

    converted = UnicodeDammit(text, is_html=is_html)
    if not converted.unicode_markup:
        raise Exception(
            'Failed to detect encoding of text: "%s"...,'
            '\ntried encodings: "%s"' %
            (text[:20], ', '.join(converted.tried_encodings)))
    return converted.unicode_markup

class __TEST():
    def searchTime(self):
        strLis = [u"2013年4月2日9:2:1",
                  u"2013年4月2日 9:2:1",
                  u"2013年4月2日 9:2",
                  u"2013年4月2日",
                  u"2013/4/029:2:1",
                  ur"2013\4\2 9:2:1",
                  u"2013-4/2 9:2",
                  u"2013-4-2",
                  u"2016年04月04日11:20"]
        for ele in strLis:
            print searchTime(ele)

    def findGreatestSubArray(self):
        from random import randint
        testL = [randint(-100, 100) for i in xrange(10)]
        print testL
        print findGreatestSubArray(testL)


if __name__ == "__main__":
    test = __TEST()
    test.searchTime()
