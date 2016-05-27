 #coding:utf-8

import codecs
import re
import hashlib
from collections import defaultdict
import jieba
import jieba.analyse
from jieba.analyse import set_stop_words
set_stop_words('stopword.txt')

def gen_keys_word_pbTXT():
    stop_word = set()
    with codecs.open('stopword.txt','rb','utf-8') as f:
        for line in f:
            stop_word.add(line.strip())
    contentLis = []
    an_contentLis = []
    with codecs.open('newsDataBref.txt','rb','utf-8') as f:
        for line in f:
            tmp = line.split('\t')
            if len(tmp) != 2:
                continue
            if tmp[0].strip() == '1':
                contentLis.append(re.sub(r'[<>\w0-9a-zA-Z]','',tmp[1].strip()))
            else:
                an_contentLis.append(re.sub(r'[<>\w0-9a-zA-Z]','',tmp[1].strip()))
    content = ''.join(contentLis)
    wordsGen = jieba.cut(content, cut_all=True)
    wordMap = defaultdict(int)
    for word in wordsGen:
        if word.strip() not in stop_word and len(word) >= 2:
            wordMap[word] += 1
    allVaules = sum(wordMap.values())
    with codecs.open('keys_word_pb.txt', 'wb','utf-8') as f:
        for word, value in sorted(wordMap.iteritems(), key=lambda e:e[1], reverse=True):
            f.write(word+" "+unicode(value)+" "+unicode(value*1.0/allVaules)+"\n")

    an_content = ''.join(an_contentLis)
    wordsGen = jieba.cut(an_content, cut_all=True)
    wordMap = defaultdict(int)
    for word in wordsGen:
        if word.strip() not in stop_word and len(word) >= 2:
            wordMap[word] += 1
    allVaules = sum(wordMap.values())
    with codecs.open('keys_word_pb_an.txt', 'wb','utf-8') as f:
        for word, value in sorted(wordMap.iteritems(), key=lambda e:e[1], reverse=True):
            f.write(word+" "+unicode(value)+" "+unicode(value*1.0/allVaules)+"\n")
    print 'over'

def find():
    wordMap1 = {}
    with codecs.open("keys_word_pb.txt", "rb", 'utf-8') as f:
        for line in f:
            word, count, per = line.strip().split(' ')
            wordMap1[word] = float(per)
    wordMap2 = {}
    with codecs.open("keys_word_pb_an.txt", "rb", 'utf-8') as f:
        for line in f:
            word, count, per = line.strip().split(' ')
            wordMap2[word] = float(per)

    allNews = []
    contentSet= set()
    an_contentSet = set()
    with codecs.open('newsDataBref.txt','rb','utf-8') as f:
        for line in f:
            tmp = line.split('\t')
            if len(tmp) != 2:
                continue
            new = re.sub(r'[<>\w0-9a-zA-Z]','',tmp[1].strip())
            allNews.append(new)
            newsMd5 = hashlib.md5(new.encode('utf-8')).hexdigest()
            if tmp[0].strip() == '1':
                contentSet.add(newsMd5)
            else:
                an_contentSet.add(newsMd5)
    allNewsCut = {}
    for new in allNews:
        res = jieba.analyse.extract_tags(re.sub(ur'[\w\s\.\[\]\{\};:<>,\?\*&^%$#@!-_\+=`|\\]', '', new), topK=100, withWeight=True)
        newsMd5 = hashlib.md5(new.encode('utf-8')).hexdigest()
        allNewsCut[newsMd5] = sorted(list(res), key=lambda e:e[1], reverse=True)

    origin_news_count = len(contentSet)

    infoLis = []
    for topK in xrange(1, 40,1):
        find_news = find_news_cmp= 0
        find_topic_news = find_topic_news_cmp=0
        res = {}
        for newsMd5, new_cut in allNewsCut.iteritems():
            result1 = result2 = 0
            for word , weight in new_cut[:topK]:
                result1 += weight*wordMap1.get(word, 0)
                result2 += weight*wordMap2.get(word, 0)
            res[newsMd5] = (result1,result2)
        for newsMd5, val in res.iteritems():
            result1, result2 = val
            if result1 > result2:
                find_news_cmp += 1
                if newsMd5 in contentSet:
                    find_topic_news_cmp += 1
        for threshold in xrange(1, 101, 1):
            threshold /= 1000.0
            find_news = sum([1 for newsM6d5, val in res.iteritems() if val[0]>val[1] and val[0] >= threshold])
            find_topic_news = sum([1 for newsMd5, val in res.iteritems() if val[0]>val[1] and  val[0] >= threshold and newsMd5 in contentSet])
            if find_news == 0:
                continue
            infoLis.append((topK, threshold, find_news, find_topic_news, origin_news_count))

    bestPoint = []
    variance = 1
    for topK, threshold,find_news,find_topic_news,origin_news_count in sorted(infoLis, key=lambda e:e[3]*1.0/e[4], reverse=True)[:100]:
        a,b = find_topic_news*1.0/origin_news_count,find_topic_news*1.0/find_news
        t = ((1-a)**2 + (1-b)**2)
        if t < variance:
            variance = t
            bestPoint = [(topK, threshold, a, b,find_news,find_topic_news,origin_news_count)]
        elif t == variance:
            bestPoint.append((topK, threshold, a, b,find_news,find_topic_news,origin_news_count))
        print topK, threshold, find_topic_news*1.0/origin_news_count,find_topic_news*1.0/find_news,\
            'find_news=',find_news,'find_top_news=',find_topic_news, 'origin_news_count',origin_news_count

    print '*' * 10
    for topK,threshold,find_news,find_topic_news,origin_news_count in sorted(infoLis, key=lambda e:e[3]*1.0/e[2], reverse=True)[:100]:
        print topK,threshold,find_topic_news*1.0/origin_news_count,find_topic_news*1.0/find_news,\
            'find_news=',find_news,'find_top_news=',find_topic_news, 'origin_news_count',origin_news_count
    print '\n' * 10
    if not bestPoint:
        print "no find"
    for topK, threshold, a, b , find_news,find_topic_news,origin_news_count in bestPoint:
        print topK, threshold, a, b,find_news,find_topic_news,origin_news_count, variance
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('topK')
    ax.set_ylabel('threshold')
    ax.set_zlabel('Y1')
    X = [ele[0] for ele in infoLis]
    Y = [ele[1] for ele in infoLis]
    Z = [e[3]*1.0/e[4] for e in infoLis]

    # ax.set_zlabel('Y3')
    # X = [ele[0] for ele in infoLis]
    # Y = [ele[1] for ele in infoLis]
    # Z = [(1-e[3]*1.0/e[2])**2 + (1-e[3]*1.0/e[4])**2 for e in infoLis]

    ax.plot_trisurf(X, Y, Z)
    # ax.set_zbound(None,1)
    plt.show()
    with codecs.open('ss.txt','ab','utf-8') as f:
        for info in infoLis:
            f.write(' '.join(map(lambda e:unicode(e),info))+'\n')


        # if result1 >= 0.01:
        #     find_news += 1
        #     if newsMd5 in contentSet:
        #         find_topic_news += 1

        # newsMap[new] = result1
    print "ok"

# gen_keys_word_pbTXT()
find()