# coding:utf-8
import re
from dateutil.parser import parse
from customFun import findGreatestSubArray, searchTime, get_unicode


class RE():
    comment_re = re.compile(ur"<\s*!--.*?--\s*>")
    head_re = re.compile(ur"<\s*head[^>]*>.*?<\s*/\s*head[^>]*>")
    script_re = re.compile(ur"<\s*script[^>]*>.*?<\s*/\s*script[^>]*>")
    style_re = re.compile(ur"<\s*style[^>]*>.*?<\s*/\s*style[^>]*>")
    whitespace_re = re.compile(ur"\s+")
    label_re = staticmethod(lambda e: re.compile("<\s*/?\s*%s[^>]*>" % e))
    url_date_re = re.compile(
            ur'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?')


class NewsParse(object):
    MIN_WORD_COUNT = 300
    KEY_LABEL = set([u'、', u'，', u'。'])
    KEY_WORD = set([u'记者', u'专电', u'发生',u'电', u'据', u'摘要', u'讯', u'消息', u'报道'])

    def __init__(self, html, url):
        self.url = url
        try:
            self.html = get_unicode(html, is_html=True)
        except Exception:
            self.html = html
        self.htmlClean = self.clean_html(self.html)
        self.htmlSeq = self.convert_seq(self.htmlClean)
        self.title = None
        self.dateline = None
        self.source = None
        self.content = None
        self.KEY_WORD = set([i for i in NewsParse.KEY_WORD])

    def set_title(self, title):
        self.title = get_unicode(title)

    def set_dateline(self, dateline):
        if isinstance(dateline, basestring):
            self.dateline = parse(dateline)
        else:
            self.dateline = dateline

    def set_source(self, source):
        self.source = get_unicode(source)

    def get_title(self):
        if self.title is not None:
            return self.title
        return self.title

    def get_source(self):
        if self.source is not None:
            return self.source
        return self.source

    def get_url(self):
        return self.url

    def get_dateline(self):
        """3 strategies for publishing date extraction. The strategies
        are descending in accuracy and the next strategy is only
        attempted if a preferred one fails.

        1. Pubdate from URL
        2. Pubdate from metadata
        3. Raw regex searches in the HTML + added heuristics
        """
        if self.dateline is not None:
            return self.dateline

        # 在htmlSeq中, 正文开始索引为content_begin, 从content-begin --> 0 方向上找时间
        if self.content is None:
            self.get_content()
        # 正文存在的话
        if self.content:
            for ele, weight in reversed(self.htmlSeq[:self.content_begin]):
                if weight < 0: continue
                self.dateline = searchTime(ele)
                if self.dateline:
                    return self.dateline

        def parse_date_str(date_str):
            try:
                datetime_obj = parse(date_str)
                return datetime_obj
            except:
                # near all parse failures are due to URL dates without a day
                # specifier, e.g. /2014/04/
                return None

        date_match = RE.url_date_re.search(self.url)
        if date_match:
            date_str = date_match.group(0)
            datetime_obj = parse_date_str(date_str)
            if datetime_obj:
                return datetime_obj
        return None

    def get_content(self):
        if self.content is not None:
            return self.content
        begin, end, sum = findGreatestSubArray([ele[1] for ele in self.htmlSeq])
        if sum < self.MIN_WORD_COUNT:
            return None
        text = []
        for ele, value in self.htmlSeq[begin:end + 1]:
            if value < 0:
                if re.search("<\s*/?(p)|(br)[^>]*>", ele):
                    text.append("<br/>")
            else:
                text.append(ele)
        self.content_begin, self.content_end = begin, end
        self.content = ''.join(text)
        return self.content

    def convert_seq(self, html):
        res = re.split('(<[^>]*>)', html)
        seq = []
        for ele in res:
            ele = ele.strip()
            if not ele:
                continue
            elif ele.startswith("<") and ele.endswith(">"):
                seq.append((ele, -len(ele)))
            else:
                seq.append((ele, self.get_weight(ele)))
        # 合并
        seqIter = iter(seq)
        htmlSeq = []
        tmp = [seqIter.next()]
        while True:
            try:
                ele, value = seqIter.next()
            except StopIteration:
                eleLis, valueLis = zip(*tmp)
                htmlSeq.append((''.join(eleLis), sum(valueLis)))
                break
            if tmp[-1][-1] * value > 0:
                tmp.append((ele, value))
            else:
                eleLis, valueLis = zip(*tmp)
                htmlSeq.append((''.join(eleLis), sum(valueLis)))
                tmp = [(ele, value)]

        return htmlSeq

    def get_weight(self, ele):
        wight = len(ele)
        # return wight
        for char in ele:
            if char in self.KEY_WORD:
                self.KEY_WORD.remove(char)
                wight += 1000
            elif char in self.KEY_LABEL:
                wight += 512
        return wight

    def clean_html(self, html):
        html = RE.whitespace_re.sub('', html)
        html = RE.head_re.sub('', html)
        html = RE.script_re.sub('', html)
        html = RE.style_re.sub('', html)
        html = RE.comment_re.sub('', html)
        # 以下标签容易把分割同一句话,需要剔除
        html = RE.label_re('font').sub('', html)
        html = RE.label_re('em').sub('', html)
        html = RE.label_re('strong').sub('', html)
        html = RE.label_re('span').sub('', html)
        return html


def getHtml():
    return u'''<html><head><avalon ms-skip="1" class="avalonHide">X<style id="avalonStyle">.avalonHide{ display: none!important }</style><div class="fjxz" ms-if="''!=''">
            <h4>附件下载：</h4>
            <ul>

            </ul>
        </div></avalon>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>2016年我省重点流域生态补偿资金规模进一步增加_部门动态_中国福建--福建省人民政府门户网站</title>
<meta name="description" content="2016年我省重点流域生态补偿资金规模进一步增加，重点流域;生态补偿资金，中国福建，福建省人民政府官方网站；福建省人民政府门户网站（简称中国福建政府网），是福建省人民政府和省人民政府各部门，以及各设区市、县（市、区）人民政府在国际互联网上发布政务信息、提供在线服务和公众参与的综合服务平台。">
 <meta name="keyword" content="2016年我省重点流域生态补偿资金规模进一步增加，重点流域;生态补偿资金，福建省，福建，闽，八闽，八闽大地，海峡西岸经济区，海峡西岸，海西，台湾海峡，台海，海峡两岸，两岸，闽台缘，闽台交流，福建要闻，海上丝稠之路核心区，海上丝稠之路，海丝，中国（福建）自由贸易试验区，福建自贸试验区，福建自贸区，清新福建，福建旅游，福建省人民政府，福建省政府，福建省人民政府办公厅，福建省政府办公厅，福建省经济信息中心，福建省信息中心，中国福建，中国福建网站，中国福建政府网，福建省人民政府门户网站，福建省人民政府官方网站，福建省政府门户网站，福建省政府官方网站，福建省政府网站">
<meta content="no-cache" http-equiv="Pragma">
<meta name="robots" content="all">
<link href="../../../../images/20160115szf-gfxl.css" rel="stylesheet" type="text/css">
<link href="../../../../images/2016_szf_golbal.css" rel="stylesheet" type="text/css">
<link href="../../../../images/2016fujian.css" rel="stylesheet" type="text/css">
<style>

</style>
<script src="http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion=405442"></script><style type="text/css">/*!
* ui-dialog.css
* Date: 2014-07-03
* https://github.com/aui/artDialog
* (c) 2009-2014 TangBin, http://www.planeArt.cn
*
* This is licensed under the GNU LGPL, version 2.1 or later.
* For details, see: http://www.gnu.org/licenses/lgpl-2.1.html
*/
.ui-dialog {
*zoom:1;
_float: left;
position: relative;
background-color: #FFF;
border: 1px solid #999;
border-radius: 6px;
outline: 0;
background-clip: padding-box;
font-family: Helvetica, arial, sans-serif;
font-size: 14px;
line-height: 1.428571429;
color: #333;
opacity: 0;
-webkit-transform: scale(0);
transform: scale(0);
-webkit-transition: -webkit-transform .15s ease-in-out, opacity .15s ease-in-out;
transition: transform .15s ease-in-out, opacity .15s ease-in-out;
}
.ui-popup-show .ui-dialog {
opacity: 1;
-webkit-transform: scale(1);
transform: scale(1);
}
.ui-popup-focus .ui-dialog {
box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
}
.ui-popup-modal .ui-dialog {
box-shadow: 0 0 8px rgba(0, 0, 0, 0.1), 0 0 256px rgba(255, 255, 255, .3);
}
.ui-dialog-grid {
width: auto;
margin: 0;
border: 0 none;
border-collapse:collapse;
border-spacing: 0;
background: transparent;
}
.ui-dialog-header,
.ui-dialog-body,
.ui-dialog-footer {
padding: 0;
border: 0 none;
text-align: left;
background: transparent;
}
.ui-dialog-header {
white-space: nowrap;
border-bottom: 1px solid #E5E5E5;
}
.ui-dialog-close {
position: relative;
_position: absolute;
float: right;
top: 13px;
right: 13px;
_height: 26px;
padding: 0 4px;
font-size: 21px;
font-weight: bold;
line-height: 1;
color: #000;
text-shadow: 0 1px 0 #FFF;
opacity: .2;
filter: alpha(opacity=20);
cursor: pointer;
background: transparent;
_background: #FFF;
border: 0;
-webkit-appearance: none;
}
.ui-dialog-close:hover,
.ui-dialog-close:focus {
color: #000000;
text-decoration: none;
cursor: pointer;
outline: 0;
opacity: 0.5;
filter: alpha(opacity=50);
}
.ui-dialog-title {
margin: 0;
line-height: 1.428571429;
min-height: 16.428571429px;
padding: 15px;
overflow:hidden;
white-space: nowrap;
text-overflow: ellipsis;
font-weight: bold;
cursor: default;
}
.ui-dialog-body {
padding: 20px;
text-align: center;
}
.ui-dialog-content {
display: inline-block;
position: relative;
vertical-align: middle;
*zoom: 1;
*display: inline;
text-align: left;
}
.ui-dialog-footer {
padding: 0 20px 20px 20px;
}
.ui-dialog-statusbar {
float: left;
margin-right: 20px;
padding: 6px 0;
line-height: 1.428571429;
font-size: 14px;
color: #888;
white-space: nowrap;
}
.ui-dialog-statusbar label:hover {
color: #333;
}
.ui-dialog-statusbar input,
.ui-dialog-statusbar .label {
vertical-align: middle;
}
.ui-dialog-button {
float: right;
white-space: nowrap;
}
.ui-dialog-footer button+button {
margin-bottom: 0;
margin-left: 5px;
}
.ui-dialog-footer button {
width:auto;
overflow:visible;
display: inline-block;
padding: 6px 12px;
_margin-left: 5px;
margin-bottom: 0;
font-size: 14px;
font-weight: normal;
line-height: 1.428571429;
text-align: center;
white-space: nowrap;
vertical-align: middle;
cursor: pointer;
background-image: none;
border: 1px solid transparent;
border-radius: 4px;
-webkit-user-select: none;
 -moz-user-select: none;
  -ms-user-select: none;
   -o-user-select: none;
      user-select: none;
}

.ui-dialog-footer button:focus {
outline: thin dotted #333;
outline: 5px auto -webkit-focus-ring-color;
outline-offset: -2px;
}

.ui-dialog-footer button:hover,
.ui-dialog-footer button:focus {
color: #333333;
text-decoration: none;
}

.ui-dialog-footer button:active {
background-image: none;
outline: 0;
-webkit-box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
      box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
}
.ui-dialog-footer button[disabled] {
pointer-events: none;
cursor: not-allowed;
opacity: 0.65;
filter: alpha(opacity=65);
-webkit-box-shadow: none;
      box-shadow: none;
}

.ui-dialog-footer button {
color: #333333;
background-color: #ffffff;
border-color: #cccccc;
}

.ui-dialog-footer button:hover,
.ui-dialog-footer button:focus,
.ui-dialog-footer button:active {
color: #333333;
background-color: #ebebeb;
border-color: #adadad;
}

.ui-dialog-footer button:active{
background-image: none;
}

.ui-dialog-footer button[disabled],
.ui-dialog-footer button[disabled]:hover,
.ui-dialog-footer button[disabled]:focus,
.ui-dialog-footer button[disabled]:active {
background-color: #ffffff;
border-color: #cccccc;
}

.ui-dialog-footer button.ui-dialog-autofocus {
color: #ffffff;
background-color: #428bca;
border-color: #357ebd;
}

.ui-dialog-footer button.ui-dialog-autofocus:hover,
.ui-dialog-footer button.ui-dialog-autofocus:focus,
.ui-dialog-footer button.ui-dialog-autofocus:active {
color: #ffffff;
background-color: #3276b1;
border-color: #285e8e;
}

.ui-dialog-footer button.ui-dialog-autofocus:active {
background-image: none;
}
.ui-popup-top-left .ui-dialog,
.ui-popup-top .ui-dialog,
.ui-popup-top-right .ui-dialog {
top: -8px;
}
.ui-popup-bottom-left .ui-dialog,
.ui-popup-bottom .ui-dialog,
.ui-popup-bottom-right .ui-dialog {
top: 8px;
}
.ui-popup-left-top .ui-dialog,
.ui-popup-left .ui-dialog,
.ui-popup-left-bottom .ui-dialog {
left: -8px;
}
.ui-popup-right-top .ui-dialog,
.ui-popup-right .ui-dialog,
.ui-popup-right-bottom .ui-dialog {
left: 8px;
}

.ui-dialog-arrow-a,
.ui-dialog-arrow-b {
position: absolute;
display: none;
width: 0;
height: 0;
overflow:hidden;
_color:#FF3FFF;
_filter:chroma(color=#FF3FFF);
border:8px dashed transparent;
}
.ui-popup-follow .ui-dialog-arrow-a,
.ui-popup-follow .ui-dialog-arrow-b{
display: block;
}
.ui-popup-top-left .ui-dialog-arrow-a,
.ui-popup-top .ui-dialog-arrow-a,
.ui-popup-top-right .ui-dialog-arrow-a {
bottom: -16px;
border-top:8px solid #7C7C7C;
}
.ui-popup-top-left .ui-dialog-arrow-b,
.ui-popup-top .ui-dialog-arrow-b,
.ui-popup-top-right .ui-dialog-arrow-b {
bottom: -15px;
border-top:8px solid #fff;
}
.ui-popup-top-left .ui-dialog-arrow-a,
.ui-popup-top-left .ui-dialog-arrow-b  {
left: 15px;
}
.ui-popup-top .ui-dialog-arrow-a,
.ui-popup-top .ui-dialog-arrow-b  {
left: 50%;
margin-left: -8px;
}
.ui-popup-top-right .ui-dialog-arrow-a,
.ui-popup-top-right .ui-dialog-arrow-b {
right: 15px;
}
.ui-popup-bottom-left .ui-dialog-arrow-a,
.ui-popup-bottom .ui-dialog-arrow-a,
.ui-popup-bottom-right .ui-dialog-arrow-a {
top: -16px;
border-bottom:8px solid #7C7C7C;
}
.ui-popup-bottom-left .ui-dialog-arrow-b,
.ui-popup-bottom .ui-dialog-arrow-b,
.ui-popup-bottom-right .ui-dialog-arrow-b {
top: -15px;
border-bottom:8px solid #fff;
}
.ui-popup-bottom-left .ui-dialog-arrow-a,
.ui-popup-bottom-left .ui-dialog-arrow-b {
left: 15px;
}
.ui-popup-bottom .ui-dialog-arrow-a,
.ui-popup-bottom .ui-dialog-arrow-b {
margin-left: -8px;
left: 50%;
}
.ui-popup-bottom-right .ui-dialog-arrow-a,
.ui-popup-bottom-right .ui-dialog-arrow-b {
right: 15px;
}
.ui-popup-left-top .ui-dialog-arrow-a,
.ui-popup-left .ui-dialog-arrow-a,
.ui-popup-left-bottom .ui-dialog-arrow-a {
right: -16px;
border-left:8px solid #7C7C7C;
}
.ui-popup-left-top .ui-dialog-arrow-b,
.ui-popup-left .ui-dialog-arrow-b,
.ui-popup-left-bottom .ui-dialog-arrow-b {
right: -15px;
border-left:8px solid #fff;
}
.ui-popup-left-top .ui-dialog-arrow-a,
.ui-popup-left-top .ui-dialog-arrow-b {
top: 15px;
}
.ui-popup-left .ui-dialog-arrow-a,
.ui-popup-left .ui-dialog-arrow-b {
margin-top: -8px;
top: 50%;
}
.ui-popup-left-bottom .ui-dialog-arrow-a,
.ui-popup-left-bottom .ui-dialog-arrow-b {
bottom: 15px;
}
.ui-popup-right-top .ui-dialog-arrow-a,
.ui-popup-right .ui-dialog-arrow-a,
.ui-popup-right-bottom .ui-dialog-arrow-a {
left: -16px;
border-right:8px solid #7C7C7C;
}
.ui-popup-right-top .ui-dialog-arrow-b,
.ui-popup-right .ui-dialog-arrow-b,
.ui-popup-right-bottom .ui-dialog-arrow-b {
left: -15px;
border-right:8px solid #fff;
}
.ui-popup-right-top .ui-dialog-arrow-a,
.ui-popup-right-top .ui-dialog-arrow-b {
top: 15px;
}
.ui-popup-right .ui-dialog-arrow-a,
.ui-popup-right .ui-dialog-arrow-b {
margin-top: -8px;
top: 50%;
}
.ui-popup-right-bottom .ui-dialog-arrow-a,
.ui-popup-right-bottom .ui-dialog-arrow-b {
bottom: 15px;
}


@-webkit-keyframes ui-dialog-loading {
0% {
    -webkit-transform: rotate(0deg);
}
100% {
    -webkit-transform: rotate(360deg);
}
}
@keyframes ui-dialog-loading {
0% {
    transform: rotate(0deg);
}
100% {
    transform: rotate(360deg);
}
}

.ui-dialog-loading {
vertical-align: middle;
position: relative;
display: block;
*zoom: 1;
*display: inline;
overflow: hidden;
width: 32px;
height: 32px;
top: 50%;
margin: -16px auto 0 auto;
font-size: 0;
text-indent: -999em;
color: #666;
}
.ui-dialog-loading {
width: 100%\9;
text-indent: 0\9;
line-height: 32px\9;
text-align: center\9;
font-size: 12px\9;
}

.ui-dialog-loading::after {
position: absolute;
content: '';
width: 3px;
height: 3px;
margin: 14.5px 0 0 14.5px;
border-radius: 100%;
box-shadow: 0 -10px 0 1px #ccc, 10px 0px #ccc, 0 10px #ccc, -10px 0 #ccc, -7px -7px 0 0.5px #ccc, 7px -7px 0 1.5px #ccc, 7px 7px #ccc, -7px 7px #ccc;
-webkit-transform: rotate(360deg);
-webkit-animation: ui-dialog-loading 1.5s infinite linear;
transform: rotate(360deg);
animation: ui-dialog-loading 1.5s infinite linear;
display: none\9;
}
.pgStyle{text-align:center;padding:10px;}
.pgStyle a{text-decoration:none;border:1px solid #eee;color:#036cb4;margin:2px;padding:2px 5px;}
.pgStyle a:hover,.pgStyle a:active{color:#666;border:1px solid #999;}
.pgStyle .cur,.pgStyle a.cur,.pgStyle a.cur:visited{border:1px solid #036cb4;color:#fff;background-color:#036cb4;font-weight:bolder;margin:2px;padding:2px 5px;}
.pgStyle .disab{border:#eee 1px solid;color:#ddd;margin:2px;padding:2px 5px;}
.pgStyle input{ width:20px;}
.pgStyle span{margin:2px;padding:2px 5px;border:1px solid #eee;}
.pgStyle6{text-align:center;padding:10px;}
.pgStyle6 a{text-decoration:none;border:1px solid #ddd;color:#ff9900;margin:2px;padding:2px 5px;}
.pgStyle6 a:hover,.pgStyle6 a:active{color:#638425;border:1px solid #FFBE5D;background-color:#FFE3B9}
.pgStyle6 .cur,.pgStyle6 a.cur,.pgStyle6 a.cur:visited{border:1px solid #ff9900;color:#fff;background-color:#ff9900;font-weight:bolder;margin:2px;padding:2px 5px;}
.pgStyle6 .disab{border:#f3f3f3 1px solid;color:#ccc;margin:2px;padding:2px 5px;}
.pgStyle6 input{ width:20px;}
.pgStyle6 span{ margin:2px;padding:2px 5px;border:1px solid #eee;}
/*绿色分页条 add by lqy 2015-8-17 14:20:30*/
.pgStyle_green{text-align:center;padding:10px;}
.pgStyle_green a{text-decoration:none;border:1px solid #ddd;color:#62be35!important;margin:2px;padding:2px 5px;}
.pgStyle_green a:hover,.pgStyle_green a:active{color:#638425;border:1px solid #FFBE5D!important;background-color:#FFE3B9}
.pgStyle_green .cur,.pgStyle_green a.cur,.pgStyle_green a.cur:visited{border:1px solid #62be35;color:#fff!important;background-color:#62be35;font-weight:bolder;margin:2px;padding:2px 5px;}
.pgStyle_green .disab{border:#f3f3f3 1px solid;color:#ccc;margin:2px;padding:2px 5px;}
.pgStyle_green input{ width:20px;}
.pgStyle_green span{ margin:2px;padding:2px 5px;border:1px solid #eee;}
/*红色分页条 add by lqy 2015-8-17 14:20:30*/
.pgStyle_red{text-align:center;padding:10px;}
.pgStyle_red a{text-decoration:none;border:1px solid #ddd;color:#da0300!important;margin:2px;padding:2px 5px;}
.pgStyle_red a:hover,.pgStyle_red a:active{color:#638425;border:1px solid #FFBE5D!important;background-color:#FFE3B9!important;}
.pgStyle_red .cur,.pgStyle_red a.cur,.pgStyle_red a.cur:visited{border:1px solid #da0300;color:#fff!important;background-color:#da0300;font-weight:bolder;margin:2px;padding:2px 5px;}
.pgStyle_red .disab{border:#f3f3f3 1px solid;color:#ccc;margin:2px;padding:2px 5px;}
.pgStyle_red input{ width:20px;}
.pgStyle_red span{ margin:2px;padding:2px 5px;border:1px solid #eee;}

.pgStyle1{text-align:center;padding:10px;}
.pgStyle1 a{text-decoration:none;border:1px solid #eee;color:#000;margin:2px;padding:2px 5px;border-radius: 3px;}
.pgStyle1 a:hover,.pgStyle1 a:active{color:#666;border:1px solid #999;}
.pgStyle1 .cur,.pgStyle1 a.cur,.pgStyle1 a.cur:visited{border:1px solid #d91616;color:#fff;background-color:#d91616;font-weight:bolder;margin:2px;padding:2px 5px;}
.pgStyle1 .disab{border:#eee 1px solid;color:#ddd;margin:2px;padding:2px 5px;}
.pgStyle1 input{ width:20px;}
.pgStyle1 span{margin:2px;padding:2px 5px;border:1px solid #eee;}</style><style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style><link rel="stylesheet" href="http://bdimg.share.baidu.com/static/api/css/share_style0_16.css?v=6aba13f0.css"></head>
<body onmouseup="getWord()" avalonctrl="windowRoot">
<!--top-->
<div class="top_link" style="filter:alpha(opacity=93); -moz-opacity:0.93;  -khtml-opacity: 0.93; opacity: 0.93;">
<div class="top_link_main">
    <p class="fr"><a class="sj_link_icon" target="_blank" href="http://www.fujian.gov.cn/yy/sjmh/">手机门户</a><a class="sj_link_icon2" target="_blank" href="http://www.fujian.gov.cn/yy/wbwx/">微信微博</a><a class="sj_link_icon3" target="_blank" href="https://218.85.73.167/">邮箱</a><!--<a class="sj_link_icon4"  target="_blank" href="../fw/bmxxcx/wzdh/">网站导游</a>--><span>|</span><fjtignoreurl><a href="http://www.fujian.gov.cn">简体版</a></fjtignoreurl><span>|</span><fjtignoreurl><a href="http://www.fujian.gov.cn:82/gate/big5/www.fujian.gov.cn">繁體版</a></fjtignoreurl><span>|</span><a href="http://www.fujian.gov.cn/english/">English</a><span>|</span><a target="_blank" href="http://www.fujian.gov.cn/wzaweb/">无障碍浏览</a></p>


    <!--<p class="fr"><fjtignoreurl><a href="http://www.fujian.gov.cn">简体版</a></fjtignoreurl><span>|</span><fjtignoreurl><a href="http://www.fujian.gov.cn:82/gate/big5/www.fujian.gov.cn">繁體版</a></fjtignoreurl><span>|</span><a
    href="http://www.fujian.gov.cn/english/">English</a><span>|</span><a target="_blank"  href="http://www.fujian.gov.cn/wzaweb/" >无障碍浏览</a><span>|</span><a target="_blank" href="http://www.fujian.gov.cn/yy/sjmh/">手机门户</a><span>|</span><a target="_blank"  href='http://www.fujian.gov.cn/yy/wbwx/'>微信微博</a><span>|</span><a target="_blank" href="https://mail.fujian.gov.cn/">邮箱</a><!--<span>|</span><a target="_blank"
    href="../fw/bmxxcx/wzdh/">网站导游</a>  </p>-->
    <p class="datep fl">
        <i class="fl">2016年04月02日</i>
        <i class="fl mar-L5">星期六</i>
        </p><div class="tqyb fl mar-L5" id="tqyb" style="width:300px;"><fjtignoreurl><iframe src="http://www.fujian.gov.cn/inc/tqyb.htm" width="285" height="22" marginwidth="0" marginheight="0" frameborder="0" scrolling="no" allowtransparency="true" ignoreapd="1"></iframe></fjtignoreurl></div>
    <p></p>
</div>
</div>
<div class="xl_gb">
<div class="content">
    <!--头部嵌套 begin-->
    <div class="xl_banner clearflx">
<div class="xl_logo"><a href="/"><img src="/images/20160117logo001_03.png" width="134" height="42" alt="中国福建--福建省人民政府门户网站" data-bd-imgshare-binded="1"></a></div>
<div class="xl_nav">
    <ul class="clearflx" avalonctrl="tabMenu">
        <li><a href="/szf/">省政府</a></li>
        <li class="xl_curr"><a href="/xw/">新闻</a></li>
        <li><a href="/zc/">政策</a></li>
        <li class=""><a href="/xm/">项目</a></li>
        <li><a href="/fw/">服务</a></li>
    </ul>
</div>
<div class="xl_seach_box"><form method="get" action="/was5/web/search">
    <input type="hidden" name="channelid" value="200043"><input type="hidden" name="templet" value="fj_web_2012.jsp"><input type="hidden" name="sortfield" value="-docreltime">
    <input type="text" name="searchword" placeholder="请输入关键字" required="true" class="inp_text veralign-mid"><input type="submit" value="" class="inp_btn veralign-mid"><input type="button" class="inp_btn2 veralign-mid" onclick="advsearch()" value="搜索平台"></form>
</div>
</div>
    <!--头部嵌套 end-->
    <!--主体内容 begin-->
    <div class="gl-main clearflx">
        <!--当前位置 begin-->
        <div class="top-news clearflx">
            <span>当前位置：<a href="../../../../" title="首页" class="CurrChnlCls">首页</a>&nbsp;&gt;&nbsp;<a href="../../../" title="新闻" class="CurrChnlCls">新闻</a>&nbsp;&gt;&nbsp;<a href="../../" title="工作动态" class="CurrChnlCls">工作动态</a>&nbsp;&gt;&nbsp;<a href="../" title="部门动态" class="CurrChnlCls">部门动态</a></span>
        </div>
        <!--当前位置 end-->
        <div class="xl-bk clearflx">
            <!--正文 begin-->
            <div class="xl-nr clearflx">
                <h3>2016年我省重点流域生态补偿资金规模进一步增加</h3>

                <h5 class="ly">
                    <span ms-if="省发改委">[省发改委]</span>&nbsp;&nbsp;
                    2016-04-01&nbsp;&nbsp;
                    字号：<a href="#" class="font0 active">T</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a class="font1" href="#">T</a></h5>
                <div class="htmlcon font0">
                    <div class="TRS_Editor"><p>　　2015年，我省出台实施《福建省重点流域生态补偿办法》，坚持省市共筹、责任共担、水质优先、区别对待，用标准化方式筹措、用因素法公式分配生态补偿金，建立起与财政收入增长挂钩的生态补偿长效机制。2015年，我省共统筹重点流域生态补偿资金9.15亿元，比之前每年约3亿元的省重点流域水环境综合整治专项资金增加了2倍。2016年，我省重点流域生态补偿资金规模进一步增加，共筹集10.16亿元，比上年增长11%，切实加大了闽江、九龙江、敖江等流域的地区间横向生态补偿力度，将进一步调动各市、县保护水生态环境的积极性。</p></div>
                </div>
            </div>
            <!--附件下载 begin-->
            <!--ms-if-->
        <!--附件下载 end-->
        <!--相关链接 begin-->
        <div class="xglj">
            <h4>相关链接：</h4>
            <ul>
                <li>查看“<a href="/was5/web/search?channelid=281033&amp;templet=fj_web_2012.jsp&amp;searchword=%E9%87%8D%E7%82%B9%E6%B5%81%E5%9F%9F%E7%94%9F%E6%80%81%E8%A1%A5%E5%81%BF%E8%B5%84%E9%87%91" target="_blank"><span>重点流域;生态补偿资金</span></a> ”相关链接</li>
            </ul>
        </div>
        <!--相关链接 end-->

        <!--正文 end-->
    </div>
    <div class="fxan clearflx">
        <div class="xl_btn_icon fl">
            <div class="bdsharebuttonbox bdshare-button-style0-16" style="width:140px;float:left" data-bd-bind="1459595798227">
                <a class="bds_more" href="#" data-cmd="more"></a>
                <a title="分享到QQ空间" class="bds_qzone" href="#" data-cmd="qzone"></a>
                <a title="分享到新浪微博" class="bds_tsina" href="#" data-cmd="tsina"></a>
                <a title="分享到腾讯微博" class="bds_tqq" href="#" data-cmd="tqq"></a>
                <a title="分享到人人网" class="bds_renren" href="#" data-cmd="renren"></a>
                <a title="分享到微信" class="bds_weixin" href="#" data-cmd="weixin"></a>
            </div>
            <script>
                window._bd_share_config={
                    "common":{
                        "bdSnsKey":{},
                        "bdText":"",
                        "bdMini":"2",
                        "bdMiniList":false,
                        "bdPic":"",
                        "bdStyle":"0",
                        "bdSize":"16"},
                    "share":{},
                    "image":{"viewList":["qzone","tsina","tqq","renren","weixin"],
                        "viewText":"分享到：",
                        "viewSize":"16"},
                    "selectShare":{"bdContainerClass":null,"bdSelectMiniList":["qzone","tsina","tqq","renren","weixin"]}};
                with(document)0[(getElementsByTagName('head')[0]||body).appendChild(createElement('script')).src='http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion='+~(-new Date()/36e5)];
            </script>
        </div>
        <div class="ymjc fl" style=" width:250px;">
            <span><a class="ymjc radius5" href="javascript:void(0);" onclick="finderror();">页面纠错</a></span>
            <input type="hidden" name="Errortxt" id="Errortxt">
            <span><a class="wzjs radius5" href="../../../ztzl/zfwzjsygl/lyb/" target="_blank">网站建设意见</a></span>
        </div>
        <div class="tjpy fl">
            <span class="fl">推荐给您的朋友:</span>
            <form name="Form2000" method="post" action="" enctype="text/plain" onsubmit="return validate_form()">
                <input type="text" class="tjpy_text radius5" name="FriendEmail" value="您朋友的E-mail" onclick="this.value=''"><input type="hidden" name="Context">
                <input type="submit" class="tjpy_btn radius5" value="确定">
            </form>
        </div>
        <div class="scdy fr">
            <a href="javascript:addFav(window.location,document.title)">【收藏】</a>
            <a href="javascript:window.print()">【打印】</a>
            <a href="javascript:window.close();">【关闭】</a>
        </div>

    </div>
</div>
</div>

<!--主体内容 end-->
</div>
<!--content end-->
<!--

-->
<div class="footer mar-T30">
<div class="content">
    <div class="pad-T25">
        <select class="fl1" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>省政府部门</option>

                 <option value="http://www.fjdpc.gov.cn/">省发改委</option>

                 <option value="http://www.fjetc.gov.cn/">省经信委</option>

                 <option value="http://www.fjhfpc.gov.cn/">省卫计委</option>

                 <option value="http://www.fjedu.gov.cn/html/index.html">省教育厅</option>

                 <option value="http://www.fjkjt.gov.cn/">省科技厅</option>

                 <option value="http://www.fjmzzj.gov.cn/">省民族宗教厅</option>

                 <option value="http://www.fjgat.gov.cn/">省公安厅</option>

                 <option value="http://www.fjcdi.gov.cn/">省监察厅</option>

                 <option value="http://www.fjsmzt.gov.cn/">省民政厅</option>

                 <option value="http://www.fjsf.gov.cn/">省司法厅</option>

                 <option value="http://www.fjcz.gov.cn/">省财政厅</option>

                 <option value="http://www.fjrs.gov.cn">省人社厅</option>

                 <option value="http://www.fjgtzy.gov.cn/">省国土厅</option>

                 <option value="http://www.fjepb.gov.cn/">省环保厅</option>

                 <option value="http://www.fjjs.gov.cn/">省住建厅</option>

                 <option value="http://www.fjjt.gov.cn/">省交通运输厅</option>

                 <option value="http://www.fjagri.gov.cn/html/">省农业厅</option>

                 <option value="http://www.fjforestry.gov.cn/">省林业厅</option>

                 <option value="http://www.fjwater.gov.cn/">省水利厅</option>

                 <option value="http://www.fjof.gov.cn/">省海洋渔业厅</option>

                 <option value="http://www.fiet.gov.cn/">省商务厅</option>

                 <option value="http://www.fjwh.gov.cn/">省文化厅</option>

                 <option value="http://www.fjaudit.gov.cn/">省审计厅</option>

                 <option value="http://www.fjfao.gov.cn/">省外办</option>

                 <option value="http://www.fjgzw.gov.cn/">省国资委</option>

                 <option value="http://www.fj-l-tax.gov.cn">省地税局</option>

                 <option value="http://www.fjaic.gov.cn/">省工商局</option>

                 <option value="http://www.fjqi.gov.cn/">省质监局</option>

                 <option value="http://www.fjxwgd.gov.cn/">省新闻出版广电局</option>

                 <option value="http://www.fjty.gov.cn/">省体育局</option>

                 <option value="http://www.fjsafety.gov.cn/">省安监局</option>

                 <option value="http://www.fjfda.gov.cn/">省食品药品监管局</option>

                 <option value="http://www.stats-fj.gov.cn/">省统计局</option>

                 <option value="http://www.fjta.gov.cn/">省旅游局</option>

                 <option value="http://www.fjgrain.gov.cn/">省粮食局</option>

                 <option value="http://www.fjjg.gov.cn/fjwjj/index.htm">省物价局</option>

                 <option value="http://www.fjqw.gov.cn/">省侨办</option>

                 <option value="http://www.fjrf.gov.cn/">省人防办</option>

                 <option value="http://www.fjfzb.gov.cn/">省法制办</option>

                 <option value="http://www.fjjghq.gov.cn/">省机关事务管理局</option>

                 <option value="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/sydbwzdh/szfbm/201402/t20140210_697591.htm">省金融办</option>

                 <option value="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/sydbwzdh/szfbm/201212/t20121203_550109.htm">省监狱局</option>

                 <option value="http://gwy.fjrs.gov.cn/">省公务员局</option>

        </select>

        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>市、县（区）</option>



                <option value="http://www.fuzhou.gov.cn/" style="color:red">福州市</option>


                    <option value="http://www.gl.gov.cn/">鼓楼区</option>

                    <option value="http://www.taijiang.gov.cn/">台江区</option>

                    <option value="http://www.fzcangshan.gov.cn/">仓山区</option>

                    <option value="http://www.jinan-fz-fj.gov.cn/">晋安区</option>

                    <option value="http://www.mawei.gov.cn/">马尾区</option>

                    <option value="http://www.fuqing.gov.cn/">福清市</option>

                    <option value="http://www.fjcl.gov.cn/">长乐市</option>

                    <option value="http://www.minhou.gov.cn/">闽侯县</option>

                    <option value="http://www.yongtai.gov.cn/">永泰县</option>

                    <option value="http://www.fjmq.gov.cn/mqzfw/index.htm">闽清县</option>

                    <option value="http://www.fjlj.gov.cn/">连江县</option>

                    <option value="http://www.luoyuan.gov.cn/Index.html">罗源县</option>




                <option value="http://www.xm.gov.cn/" style="color:red">厦门市</option>


                    <option value="http://www.siming.gov.cn/">思明区</option>

                    <option value="http://www.huli.gov.cn/">湖里区</option>

                    <option value="http://www.jimei.gov.cn/">集美区</option>

                    <option value="http://www.haicang.gov.cn/">海沧区</option>

                    <option value="http://www.xmta.gov.cn/">同安区</option>

                    <option value="http://www.xiangan.gov.cn/">翔安区</option>

                    <option value="http://www.xmtorch.gov.cn/">厦门火炬高技术产业开发区</option>

                    <option value="http://www.xmftz.xm.fj.cn/">厦门象屿保税区</option>

                    <option value="http://www.gly.cn/">鼓浪屿-万石山风景名胜区</option>




                <option value="http://www.zhangzhou.gov.cn/" style="color:red">漳州市</option>


                    <option value="http://www.xc.gov.cn/">芗城区</option>

                    <option value="http://www.lwq.gov.cn/">龙文区</option>

                    <option value="http://www.longhai.gov.cn/">龙海市</option>

                    <option value="http://www.zhangpu.gov.cn/">漳浦县</option>

                    <option value="http://www.yunxiao.gov.cn/">云霄县</option>

                    <option value="http://www.zhaoan.gov.cn/">诏安县</option>

                    <option value="http://www.dongshanisland.gov.cn/">东山县</option>

                    <option value="http://www.pinghe.gov.cn/">平和县</option>

                    <option value="http://www.fjnj.gov.cn/">南靖县</option>

                    <option value="http://www.changtai.gov.cn/">长泰县</option>

                    <option value="http://www.huaan.gov.cn/">华安县</option>




                <option value="http://www.fjqz.gov.cn/" style="color:red">泉州市</option>


                    <option value="http://www.qzlc.gov.cn/">鲤城区</option>

                    <option value="http://www.qzfz.gov.cn/">丰泽区</option>

                    <option value="http://www.qzlj.gov.cn/">洛江区</option>

                    <option value="http://www.qg.gov.cn/">泉港区</option>

                    <option value="http://www.shishi.gov.cn/sszfwms/wwwroot/index.jsp">石狮市</option>

                    <option value="http://www.jinjiang.gov.cn/">晋江市</option>

                    <option value="http://www.nanan.gov.cn/">南安市</option>

                    <option value="http://www.huian.gov.cn/">惠安县</option>

                    <option value="http://www.fjax.gov.cn/">安溪县</option>

                    <option value="http://www.dehua.gov.cn/">德化县</option>

                    <option value="http://www.fjyc.gov.cn/">永春县</option>

                    <option value="http://www.qzts.gov.cn/">泉州台商投资区</option>

                    <option value="http://www.qingmeng.gov.cn/">泉州经济技术开发区</option>




                <option value="http://www.sm.gov.cn/" style="color:red">三明市</option>


                    <option value="http://www.smsy.gov.cn/main/">三元区</option>

                    <option value="http://www.ml.gov.cn/Main/main.asp">梅列区</option>

                    <option value="http://www.ya.gov.cn/">永安市</option>

                    <option value="http://www.fjql.gov.cn/main/">清流县</option>

                    <option value="http://www.fjnh.gov.cn/">宁化县</option>

                    <option value="http://www.fjjn.gov.cn/">建宁县</option>

                    <option value="http://www.fjtn.gov.cn/">泰宁县</option>

                    <option value="http://www.fjmx.gov.cn/main/indexdynamic.asp">明溪县</option>

                    <option value="http://www.jiangle.gov.cn/">将乐县</option>

                    <option value="http://www.fjsx.gov.cn/Index.html">沙　县</option>

                    <option value="http://www.fjyx.gov.cn/">尤溪县</option>

                    <option value="http://www.datian.gov.cn/">大田县</option>




                <option value="http://www.putian.gov.cn/" style="color:red">莆田市</option>


                    <option value="http://www.xianyou.gov.cn/gov/index.htm">仙游县</option>

                    <option value="http://www.ptlc.gov.cn/">荔城区</option>

                    <option value="http://www.chengxiang.gov.cn/">城厢区</option>

                    <option value="http://www.pthj.gov.cn/">涵江区</option>

                    <option value="http://www.ptxy.gov.cn/">秀屿区</option>

                    <option value="http://www.ptmzwba.gov.cn/">湄洲湾北岸经济开发区</option>

                    <option value="http://www.mzd.gov.cn/">湄洲岛国家旅游度假区</option>




                <option value="http://www.np.gov.cn/" style="color:red">南平市</option>


                    <option value="http://www.ypzf.gov.cn:8080/">延平区</option>

                    <option value="http://www.jyszfw.gov.cn/">建阳区</option>

                    <option value="http://www.shaowu.gov.cn/index.aspx">邵武市</option>

                    <option value="http://www.wys.gov.cn/">武夷山市</option>

                    <option value="http://www.jianou.gov.cn/">建瓯市</option>

                    <option value="http://www.fjsc.gov.cn/">顺昌县</option>

                    <option value="http://110.76.42.59/">浦城县</option>

                    <option value="http://www.guangze.gov.cn/">光泽县</option>

                    <option value="http://www.songxi.gov.cn/">松溪县</option>

                    <option value="http://www.zhenghe.gov.cn">政和县</option>




                <option value="http://www.longyan.gov.cn/" style="color:red">龙岩市</option>


                    <option value="http://www.fjxinluo.gov.cn/">新罗区</option>

                    <option value="http://www.fjyd.gov.cn/index.aspx">永定区</option>

                    <option value="http://www.shanghang.gov.cn/">上杭县</option>

                    <option value="http://www.wp.gov.cn/">武平县</option>

                    <option value="http://www.changting.gov.cn/">长汀县</option>

                    <option value="http://www.fjlylc.gov.cn/">连城县</option>

                    <option value="http://www.zp.gov.cn/">漳平市</option>




                <option value="http://www.ningde.gov.cn/" style="color:red">宁德市</option>


                    <option value="http://www.jiaocheng.gov.cn/">蕉城区</option>

                    <option value="http://www.fjfa.gov.cn/">福安市</option>

                    <option value="http://www.fuding.gov.cn/">福鼎市</option>

                    <option value="http://www.fjxp.gov.cn/">霞浦县</option>

                    <option value="http://www.fjsn.gov.cn/">寿宁县</option>

                    <option value="http://www.zhouning.gov.cn/">周宁县</option>

                    <option value="http://www.fjzr.gov.cn/">柘荣县</option>

                    <option value="http://www.gutian.gov.cn/">古田县</option>

                    <option value="http://www.pingnan.gov.cn/">屏南县</option>




                <option value="http://www.pingtan.gov.cn/" style="color:red">平潭综合实验区</option>



        </select>
        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>国家部委</option>

                 <option value="http://www.mfa.gov.cn/">外交部</option>

                 <option value="http://www.mod.gov.cn/">国防部</option>

                 <option value="http://www.ndrc.gov.cn/">发展改革委</option>

                 <option value="http://www.moe.edu.cn/">教育部</option>

                 <option value="http://www.most.gov.cn/">科技部</option>

                 <option value="http://www.miit.gov.cn/">工业和信息化部</option>

                 <option value="http://www.seac.gov.cn/">国家民委</option>

                 <option value="http://www.mps.gov.cn/n16/index.html">公安部</option>

                 <option value="http://www.ccdi.gov.cn/">监察部</option>

                 <option value="http://www.mca.gov.cn/">民政部</option>

                 <option value="http://www.moj.gov.cn/">司法部</option>

                 <option value="http://www.mof.gov.cn/">财政部</option>

                 <option value="http://www.mohrss.gov.cn/">人力资源社会保障部</option>

                 <option value="http://www.mlr.gov.cn/">国土资源部</option>

                 <option value="http://www.mep.gov.cn/">环境保护部</option>

                 <option value="http://www.mohurd.gov.cn/">住房城乡建设部</option>

                 <option value="http://www.moc.gov.cn/">交通运输部</option>

                 <option value="http://www.mwr.gov.cn/">水利部</option>

                 <option value="http://www.agri.gov.cn/">农业部</option>

                 <option value="http://www.mofcom.gov.cn/">商务部</option>

                 <option value="http://www.ccnt.gov.cn/">文化部</option>

                 <option value="http://www.nhfpc.gov.cn/">卫生计生委</option>

                 <option value="http://www.pbc.gov.cn/">人民银行</option>

                 <option value="http://www.audit.gov.cn/n1992130/index.html">审计署</option>

                 <option value="http://www.sasac.gov.cn/n1180/index.html">国资委</option>

                 <option value="http://www.customs.gov.cn/publish/portal0/">海关总署</option>

                 <option value="http://www.chinatax.gov.cn">税务总局</option>

                 <option value="http://www.saic.gov.cn/">工商总局</option>

                 <option value="http://www.aqsiq.gov.cn/">质检总局</option>

                 <option value="http://www.sarft.gov.cn/">新闻出版广电总局</option>

                 <option value="http://www.gapp.gov.cn/">版权局</option>

                 <option value="http://www.sport.gov.cn/">体育总局</option>

                 <option value="http://www.chinasafety.gov.cn/newpage/">安全监管总局</option>

                 <option value="http://www.sda.gov.cn/">食品药品监管总局</option>

                 <option value="http://www.stats.gov.cn/">统计局</option>

                 <option value="http://www.forestry.gov.cn/">林业局</option>

                 <option value="http://www.sipo.gov.cn/">知识产权局</option>

                 <option value="http://www.cnta.gov.cn/">旅游局</option>

                 <option value="http://www.sara.gov.cn/">宗教局</option>

                 <option value="http://www.counsellor.gov.cn/">参事室</option>

                 <option value="http://www.ggj.gov.cn/">国管局</option>

                 <option value="http://www.gqb.gov.cn/">侨办</option>

                 <option value="http://www.hmo.gov.cn/">港澳办</option>

                 <option value="http://www.chinalaw.gov.cn/">法制办</option>

                 <option value="http://www.drcnet.com.cn/www/integrated/">国研室</option>

                 <option value="http://www.gwytb.gov.cn/">台办</option>

                 <option value="http://www.scio.gov.cn/">新闻办</option>

                 <option value="http://www.xinhua.org/">新华社</option>

                 <option value="http://www.cas.cn/">中科院</option>

                 <option value="http://cass.cssn.cn/">社科院</option>

                 <option value="http://www.cae.cn/">工程院</option>

                 <option value="http://www.drc.gov.cn/">发展研究中心</option>

                 <option value="http://www.nsa.gov.cn/web/index.html">行政学院</option>

                 <option value="http://www.cea.gov.cn/">地震局</option>

                 <option value="http://www.cma.gov.cn/">气象局</option>

                 <option value="http://www.cbrc.gov.cn/index.html">银监会</option>

                 <option value="http://www.csrc.gov.cn/pub/newsite/">证监会</option>

                 <option value="http://www.circ.gov.cn/web/site0/">保监会</option>

                 <option value="http://www.ssf.gov.cn/">社保基金会</option>

                 <option value="http://www.nsfc.gov.cn/Portal0/default152.htm">自然科学基金会</option>

                 <option value="http://www.gjxfj.gov.cn/">信访局</option>

                 <option value="http://www.chinagrain.gov.cn/n16/index.html">粮食局</option>

                 <option value="http://www.nea.gov.cn/">能源局</option>

                 <option value="http://www.tobacco.gov.cn/html/index.html">烟草局</option>

                 <option value="http://www.safea.gov.cn/">外专局</option>

                 <option value="http://www.soa.gov.cn/soa/index.htm">海洋局</option>

                 <option value="http://www.sbsm.gov.cn/">测绘地信局</option>

                 <option value="http://www.caac.gov.cn/">民航局</option>

                 <option value="http://www.chinapost.gov.cn/">邮政局</option>

                 <option value="http://www.sach.gov.cn/">文物局</option>

                 <option value="http://www.satcm.gov.cn/">中医药局</option>

                 <option value="http://www.safe.gov.cn/">外汇局</option>

                 <option value="http://www.chinasafety.gov.cn/zhuantipindao/meikuanganquan.htm">煤矿安监局</option>

                 <option value="http://www.saac.gov.cn/">档案局</option>

                 <option value="http://www.oscca.gov.cn/">密码局</option>

                 <option value="http://www.cnsa.gov.cn/n1081/index.html">航天局</option>

                 <option value="http://www.caea.gov.cn/n16/index.html">原子能机构</option>

                 <option value="http://www.china-language.gov.cn/">国家语委</option>

                 <option value="http://www.cpad.gov.cn/">国务院扶贫办</option>

                 <option value="http://www.3g.gov.cn/index.ycs">国务院三峡办</option>

                 <option value="http://www.locpg.gov.cn/">驻港联络办</option>

                 <option value="http://www.zlb.gov.cn/">驻澳门联络办</option>


        </select>
        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>中央驻闽机构</option>

                 <option value="http://fuzhou.pbc.gov.cn/">中国人民银行福州中心支行</option>

                 <option value="http://www.fj-n-tax.gov.cn/">福建省国家税务局</option>

                 <option value="http://fuzhou.customs.gov.cn/publish/portal123/">中华人民共和国福州海关</option>

                 <option value="http://xiamen.customs.gov.cn/default.aspx">中华人民共和国厦门海关</option>

                 <option value="http://www.fjciq.gov.cn/">中华人民共和国福建出入境检验检疫局</option>

                 <option value="http://www.xmciq.gov.cn/">中华人民共和国厦门出入境检验检疫局</option>

                 <option value="http://www.fjmsa.gov.cn/">中华人民共和国福建海事局</option>

                 <option value="http://xmhsfy.gov.cn/">中华人民共和国厦门海事法院</option>

                 <option value="http://www.fjqx.gov.cn/">福建省气象局</option>

                 <option value="http://www.fjea.gov.cn/">福建省地震局</option>

                 <option value="http://www.fjca.gov.cn/">福建省通信管理局</option>

                 <option value="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/sydbwzdh/gjbwmjg/201212/t20121204_550781.htm">福建省专用通信局</option>

                 <option value="http://fj.spb.gov.cn/">福建省邮政管理局</option>

                 <option value="http://www.fjycw.com/">福建省烟草专卖局</option>

                 <option value="http://hd.caac.gov.cn/fjjgj/">中国民用航空福建安全监督管理局</option>

                 <option value="http://www.fjsafety.gov.cn/">福建煤矿安全监察局</option>

                 <option value="http://www.fjirsm.ac.cn/">中国科学院福建物质结构研究所</option>

                 <option value="http://fj.mof.gov.cn/">财政部驻福建省财政监察专员办事处</option>

                 <option value="http://fztb.mofcom.gov.cn/">商务部驻福州特派员办事处</option>

                 <option value="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/sydbwzdh/gjbwmjg/201508/t20150821_1050742.htm">国家林业局驻福州森林资源监督专员办事处</option>

                 <option value="http://fjb.nea.gov.cn/">国家能源局福建监管办公室</option>

                 <option value="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/sydbwzdh/gjbwmjg/201212/t20121204_550753.htm">中国银行业监督管理委员会福建监管局</option>

                 <option value="http://www.csrc.gov.cn/pub/fujian/">中国证券监督管理委员会福建监管局</option>

                 <option value="http://fujian.circ.gov.cn/web/site13/">中国保险监督管理委员会福建监管局</option>

                 <option value="http://www.chinaykej.com/">中国冶金地质总局二局</option>

                 <option value="http://xiamen.pbc.gov.cn/">中国人民银行厦门市中心支行</option>

                 <option value="http://www.cbrc.gov.cn/xiamen/index.html">中国银行业监督管理委员会厦门监管局</option>

                 <option value="http://www.csrc.gov.cn/pub/xiamen/">中国证券监督管理委员会厦门监管局</option>

                 <option value="http://xiamen.circ.gov.cn/">中国保险监督管理委员会厦门监管局</option>

        </select>
        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>各省区市</option>

                 <option value="http://www.beijing.gov.cn/">北京</option>

                 <option value="http://www.tj.gov.cn/">天津</option>

                 <option value="http://www.hebei.gov.cn/">河北</option>

                 <option value="http://www.shanxigov.cn/">山西</option>

                 <option value="http://www.nmg.gov.cn/">内蒙古</option>

                 <option value="http://www.ln.gov.cn/">辽宁</option>

                 <option value="http://www.jl.gov.cn/">吉林</option>

                 <option value="http://www.hlj.gov.cn/">黑龙江</option>

                 <option value="http://www.shanghai.gov.cn/shanghai/node2314/index.html">上海</option>

                 <option value="http://www.jiangsu.gov.cn/">江苏</option>

                 <option value="http://www.zhejiang.gov.cn/">浙江</option>

                 <option value="http://www.ah.gov.cn/">安徽</option>

                 <option value="http://www.fujian.gov.cn/">福建</option>

                 <option value="http://www.jiangxi.gov.cn/">江西</option>

                 <option value="http://www.shandong.gov.cn/">山东</option>

                 <option value="http://www.henan.gov.cn/">河南</option>

                 <option value="http://www.hubei.gov.cn/">湖北</option>

                 <option value="http://www.hunan.gov.cn/">湖南</option>

                 <option value="http://www.gd.gov.cn/">广东</option>

                 <option value="http://www.gxzf.gov.cn/">广西</option>

                 <option value="http://www.hainan.gov.cn/code/html/">海南</option>

                 <option value="http://www.cq.gov.cn/">重庆</option>

                 <option value="http://www.sc.gov.cn/">四川</option>

                 <option value="http://www.gzgov.gov.cn/">贵州</option>

                 <option value="http://www.yn.gov.cn/">云南</option>

                 <option value="http://www.xizang.gov.cn/index.jhtml">西藏</option>

                 <option value="http://www.shaanxi.gov.cn/">陕西</option>

                 <option value="http://www.gansu.gov.cn/">甘肃</option>

                 <option value="http://www.qh.gov.cn/">青海</option>

                 <option value="http://www.nx.gov.cn">宁夏</option>

                 <option value="http://www.xinjiang.gov.cn/">新疆</option>

                 <option value="http://www.gov.hk/sc/residents/">香港</option>

                 <option value="http://portal.gov.mo/web/guest/welcomepage;jsessionid=8193C7ABC6F6B27121A3C8E6D3D6417D">澳门</option>

                 <option value="javascript:void(0);">台湾</option>

                 <option value="http://www.xjbt.gov.cn/">新疆生产建设兵团</option>

        </select>
        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>新闻媒体</option>

                 <option value="http://fjrb.fjsen.com/">福建日报</option>

                 <option value="http://www.fjsen.com/">东南网</option>

                 <option value="http://www.fjtv.net/">福建省广播影视集团</option>

                 <option value="http://www.fj.xinhuanet.com/">新华网福建频道</option>

                 <option value="http://www.haixinews.com.cn/">海西网</option>

                 <option value="http://fujian.people.com.cn/">人民网福建频道</option>

                 <option value="http://fj.rmlt.com.cn/">人民论坛网福建资讯</option>

                 <option value="http://www.fj.chinanews.com/">福建新闻网</option>

                 <option value="http://fj.ce.cn/">福建经济网</option>

                 <option value="http://www.cnr.cn/">中国广播网</option>

                 <option value="http://www.xhyb.net.cn/">新华月报</option>

                 <option value="http://www.hxnews.com/">海峡都市报</option>

                 <option value="http://www.taihainet.com/">海峡导报</option>

                 <option value="http://hxjyb.fjsen.com/">海峡教育报</option>

                 <option value="http://www.icn.cn/">海峡消费报</option>

                 <option value="http://www.fzjb.net.cn/">法制今报</option>

                 <option value="http://www.ssrb.com.cn/">石狮日报</option>

                 <option value="http://www.jjjjb.com.cn">晋江经济报</option>

                 <option value="http://www.dnkb.com.cn/">东南快报</option>

                 <option value="http://www.hjyfz.com/">环境与发展报</option>

                 <option value="http://www.fjwsb.net.cn/">福建卫生报</option>

                 <option value="http://www.fjlnw.com/">福建老年报</option>

                 <option value="http://www.txxxb.com/">通信信息报</option>

                 <option value="http://www.hxcjdb.com/">海峡财经导报</option>

                 <option value="http://www.fznews.com.cn/">福州日报</option>

                 <option value="http://www.xmnn.cn/dzbk/xmrb/">厦门日报</option>

                 <option value="http://www.mnrb.net/">闽南日报</option>

                 <option value="http://www.qzwb.com/">泉州晚报</option>

                 <option value="http://dzb.ptweb.com.cn/">湄洲日报</option>

                 <option value="http://smrb.smnet.com.cn/">三明日报</option>

                 <option value="http://www.greatwuyi.com/mbrb/">闽北日报</option>

                 <option value="http://www.mxrb.cn/">闽西日报</option>

                 <option value="http://www.ndwww.cn/">闽东日报</option>

                 <option value="http://fj.sina.com.cn/">新浪福建</option>

                 <option value="http://www.163.com/">网易</option>

                 <option value="http://www.sohu.com/">搜狐</option>

        </select>
        <select class="fl1 mar-L10" name="navURL" onchange="window.open(this.options[this.selectedIndex].value);this.selectedIndex=0">
            <option>其他</option>

                 <option value="http://www.fjic.gov.cn">福建省经济信息中心</option>

                 <option value="http://www.fjbs.gov.cn/">福建省网上办事大厅</option>

                 <option value="http://www.618.gov.cn">6·18虚拟研究院</option>

                 <option value="http://www.fjbid.gov.cn/">福建招标与采购网</option>

                 <option value="http://www.fjcredit.gov.cn/">信用福建</option>

                 <option value="http://www.fjeport.gov.cn/">福建电子口岸</option>

                 <option value="http://www.fjfdi.com/">福建国际投资促进网</option>

                 <option value="http://www.fdi.gov.cn/index.htm">中国投资指南</option>

                 <option value="http://www.21fj.com/">福建企业信息</option>

                 <option value="http://www.fj-hitech.com/">福建高科技与产业</option>

                 <option value="http://fgj.fuzhou.gov.cn/">福州房地产联合信息网</option>

                 <option value="http://www.fj12333.gov.cn/">福建12333公共服务网</option>

                 <option value="http://www.fjszgjj.com/">福建省直公积金网</option>

                 <option value="http://www.fjcdc.com.cn/">福建省疾病预防控制中心</option>

                 <option value="http://www.fjhi.gov.cn/">福建卫生监督网</option>

                 <option value="http://www.fj12315.gov.cn/index.aspx">福建12315消费者权益保护网</option>

                 <option value="http://xszz.fjedu.gov.cn/">福建省学生资助网</option>

                 <option value="http://www.eeafj.cn/">福建省教育考试院</option>

                 <option value="http://www.fjbys.gov.cn/">福建省毕业生就业公共网</option>

                 <option value="http://www.hxrc.com/">中国海峡人才市场</option>

                 <option value="http://www.fjpta.com/">福建省人事考试网</option>

                 <option value="http://www.fjkl.gov.cn/">福建省公务员考试录用网</option>

                 <option value="http://zp.fjkl.gov.cn/">福建省委托招聘报名网</option>

                 <option value="http://www.fjsq.gov.cn/">福建省情资料库</option>

                 <option value="http://www.fjnj.cn/">福建年鉴</option>

                 <option value="http://mil.fjsen.com/">福建国防教育网</option>

                 <option value="http://www.cc.gov.cn/">福建省商用密码网</option>

                 <option value="http://www.guwenchang.net/">谷文昌纪念馆</option>

                 <option value="http://www.fjlib.net/">福建省图书馆</option>

                 <option value="http://www.fjwh.net/">海西文化信息网</option>

                 <option value="http://www.clair.org.cn/cn/">日本自治体国际化协会北京事务所</option>

                 <option value="http://fj.wenming.cn">中国文明网福建站</option>

                 <option value="http://www.fj-ci.com">福建文化产业网</option>

                 <option value="http://www.fjppzw.gov.cn">福建省品牌政务网</option>

        </select>
    </div>
    <div class="footer_link">
        <p><a href="http://218.85.73.169:8080/portal/" target="_blank">个性化门户</a>&nbsp;|&nbsp;
<!--<a  href="http://www.fujian.gov.cn/bz/sybz/" target="_blank">使用帮助</a>&nbsp;|&nbsp;-->
<a href="http://www.fujian.gov.cn/yy/rss/" target="_blank">RSS信息订阅</a>&nbsp;|&nbsp;
<a href="javascript:setHome(window.location)">设为首页</a>&nbsp;|&nbsp;
<a href="javascript:addFav(window.location, document.title)">收藏本站</a>&nbsp;|&nbsp;
<a href="http://www.fujian.gov.cn/bz/flsm/" target="_blank">法律声明</a>&nbsp;|&nbsp;
<a href="http://www.fujian.gov.cn/bz/gywm/" target="_blank">关于我们</a>&nbsp;|&nbsp;
<a href="http://www.fujian.gov.cn/bz/lxwm/" target="_blank">联系我们</a>&nbsp;|&nbsp;
<a href="http://www.fujian.gov.cn/bz/zddt/" target="_blank">站点地图</a>&nbsp;|&nbsp;
<a href="http://www.fujian.gov.cn/fw/bmxxcx/wzdh/" target="_blank">网站导航</a>
</p>
    </div>
    <div class="footer_bottom clearflx">
        <div class="footer_l"><img src="/images/2016szf_footer_l.png" width="71" height="72" alt="" data-bd-imgshare-binded="1"></div>
        <div class="footer_c">
            <p>主办：福建省人民政府办公厅 承办：福建省经济信息中心</p>

            <p>闽ICP备15003084号 版权所有：© Fujian Provincial People's Government. </p>

            <p>(建议使用1024×768分辨率IE8.0以上版本浏览器)</p>
        </div>
        <div class="footer_r"><script type="text/javascript">document.write(unescape("%3Cspan id='_ideConac' %3E%3C/span%3E%3Cscript src='http://dcs.conac.cn/js/14/000/0000/40445163/CA140000000404451630001.js' type='text/javascript'%3E%3C/script%3E"));</script><span id="_ideConac"><a href="//bszs.conac.cn/sitename?method=show&amp;id=07BBE32157290F90E053022819AC8A23" target="_blank"><img id="imgConac" vspace="0" hspace="0" border="0" src="//dcs.conac.cn/image/red.png" data-bd-imgshare-binded="1"></a></span><script src="http://dcs.conac.cn/js/14/000/0000/40445163/CA140000000404451630001.js" type="text/javascript"></script><span id="_ideConac"></span></div>
    </div>
</div>
</div>
<script src="../../../../images/avalon.min.js"></script>
<script src="../../../../images/main-built.js"></script>
<script src="../../../../images/szf2016top.js"></script>
<script>
function validate_form() {

var str0,str1,str2,str3,str4,str;
validity = true; // assume valid

if (!check_email(document.Form2000.FriendEmail.value)){
    validity = false; alert(' 朋友的Email可能打错了或为空的！');
}

if (validity){
    str0="◆◆◆中国福建--福建省人民政府网站◆◆◆"
    str1="您好!";
    str2="您的朋友向您推荐中国福建网站信息:";
    str3="“"+document.title+"”"+"\n链接网址是：";
    str4=this.location;
    str="\n"+str1+"\n"+str2+"\n"+str3+"\n"+str4+"\n";
    //document.Form2000.Context.value=str;
    document.Form2000.action="mailto:"+document.Form2000.FriendEmail.value+"?Subject=中国福建网站信息推荐&body="+str;
    //document.Form2000.Errortxt.value="";
}
return validity;
}
function check_email(address) {
if ((address == "")
|| (address.indexOf ('@') == -1)
|| (address.indexOf ('.') == -1))
return false;
return true;
}
//鼠标取词
function getWord(){
var txt = '';
var foundIn = '';
if (window.getSelection){
    txt = window.getSelection();
}
else if (document.getSelection){
    txt = document.getSelection();
}
else if (document.selection){
    txt = document.selection.createRange().text;
}

if(txt!=""){
    document.getElementById("Errortxt").value=txt;
    console.log(document.getElementById("Errortxt").value);
}
}

function finderror() {
if(document.getElementById("Errortxt").value==""){
    alert("请先用鼠标选择网页上您认为有错的内容!");
}
else{
    var str0,str1,str2,str3,str4,str5,str;
    str0="“中国福建”网站管理员："
    str1="您好!";
    str2="我在浏览:";
    str3="“"+document.title+"”"+"\n链接网址是：";
    str4=this.location;
    str5=document.getElementById("Errortxt").value;
    str=str0+"\n"+str1+"\n"+str2+"\n"+str3+"\n"+str4+"\n"+"其中"+"\n"+"“"+str5+"”"+"\n"+"有错误，请您更正!";
    //document.Form2000.Context.value=str;
    document.Form2000.action="mailto:webmaster@mail.fjgov.cn?Subject=中国福建网站纠错&body="+str;
    //document.Form2000.Errortxt.value="";
    document.Form2000.submit();
}
}


</script>
<!--全站嵌套的代码-->
<script>
var PageInfo = {
    docid : '1157395',
    chnlid : '103',
    siteid : '2',
    title : "2016年我省重点流域生态补偿资金规模进一步增加",
    chnlname : "部门动态",
    sitename : "中国福建"
}
if( PageInfo.title == "" ){
    PageInfo.title = PageInfo.chnlname;
}
if( PageInfo.title == "" ){
    PageInfo.title = PageInfo.sitename;
}

require(["pageview"],function( objModel ){
    var pageview = objModel( PageInfo );
    pageview.add4arg( PageInfo , function(d){
        if( !d.error ){
            windowRootVm.pvCount = d.pvt ;
            windowRootVm.siteCount = d.pvst ;
        }
    });
})

</script>
<!--全站嵌套的代码-->

<audio controls="controls" style="display: none;"></audio><iframe frameborder="0" id="bdSharePopup_selectshare1459595798237bg" class="bdselect_share_bg" style="display:none;"></iframe><div id="bdSharePopup_selectshare1459595798237box" style="display:none;" share-type="selectshare" class="bdselect_share_box" data-bd-bind="1459595798236"><div class="selectshare-mod-triangle"><div class="triangle-border"></div><div class="triangle-inset"></div></div><div class="bdselect_share_head"><span>分享到</span><a href="http://www.baidu.com/s?wd=&amp;tn=SE_hldp08010_vurs2xrp" class="bdselect_share_dialog_search" target="_blank"><i class="bdselect_share_dialog_search_i"></i><span class="bdselect_share_dialog_search_span">百度一下</span></a><a class="bdselect_share_dialog_close"></a></div><div class="bdselect_share_content"><ul class="bdselect_share_list bdshare-button-style0-16"><div class="bdselect_share_partners"></div><a href="#" class="bds_more" data-cmd="more"></a></ul></div></div><div id="bdimgshare_1459595798271" class="sr-bdimgshare sr-bdimgshare-list sr-bdimgshare-16 sr-bdimgshare-black" style="height:36px;line-height:26px;font-size:12px;width:autopx;display:none;" data-bd-bind="1459595798270"><div class="bdimgshare-bg"></div><div class="bdimgshare-content bdsharebuttonbox bdshare-button-style0-16"><label class="bdimgshare-lbl">分享到：</label><a href="#" onclick="return false;" class="bds_qzone" data-cmd="qzone" hidefocus=""></a><a href="#" onclick="return false;" class="bds_tsina" data-cmd="tsina" hidefocus=""></a><a href="#" onclick="return false;" class="bds_tqq" data-cmd="tqq" hidefocus=""></a><a href="#" onclick="return false;" class="bds_renren" data-cmd="renren" hidefocus=""></a><a href="#" onclick="return false;" class="bds_weixin" data-cmd="weixin" hidefocus=""></a><a href="#" onclick="return false;" class="bds_more" data-cmd="more" hidefocus=""></a></div></div></body></html>'''


def getHtml1():
    return u'''<html><head><script id="sinaads-ck-script" charset="utf-8" src="//d7.sina.com.cn/litong/zhitou/sinaads/src/spec/sinaads_ck.js"></script><script id="sinaere-script" charset="utf-8" src="//d6.sina.com.cn/litong/zhitou/sinaads/test/e-recommendation/release/sinaere.js"></script>
    <link rel="mask-icon" sizes="any" href="http://www.sina.com.cn/favicon.svg" color="red">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta charset="utf-8">
<meta name="sudameta" content="urlpath:roll/; allCIDs:56673,257,51894,51070,258">
<title>辽宁鞍山：生态树葬带起文明祭祀之风_新浪财经_新浪网</title>
<meta name="keywords" content="辽宁鞍山：生态树葬带起文明祭祀之风">
<meta name="tags" content="">
<meta name="description" content="新华社沈阳4月4日专电（记者王炳坤）不修墓穴、不立碑，将逝者骨灰葬于绿树红花之下——辽宁省鞍山市近年来倡导的生态树葬，如今成为广受市民接受的殡葬方式。在鼓励逝者家属减少浪费、植树造林的同时，生态树葬还带起一股文明祭祀之风。位于鞍山市大孤山镇">

<meta property="og:type" content="article">
<meta property="og:title" content="辽宁鞍山：生态树葬带起文明祭祀之风">
<meta property="og:description" content="辽宁鞍山：生态树葬带起文明祭祀之风">
<meta property="og:url" content="http://finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml">
<meta property="og:image" content="">
<meta name="weibo: article:create_at" content="2016-04-04 11:20:28">

<!--news_web_article_v2014_meta -->


<meta name="stencil" content="PGLS000526">
<meta name="publishid" content="fxqxcnz9093681">
<meta name="comment" content="cj:comos-fxqxcnz9093681">
<meta name="sudameta" content="comment_channel:cj;comment_id:comos-fxqxcnz9093681">



<meta name="mediaid" content="新华网">
<meta name="sudameta" content="sinaog:0">
<meta name="mobile-agent" content="format=html5; url=http://doc.sina.cn/?id=comos:fxqxcnz9093681">
<meta name="mobile-agent" content="format=xhtml; url=http://doc.sina.cn/?id=comos:fxqxcnz9093681">
<meta name="mobile-agent" content="format=wml; url=http://doc.sina.cn/?id=comos:fxqxcnz9093681">



<!-- 栏目名： 56673 滚动新闻 --><!-- id： fxqxcnz9093681 URL： http://finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml -->



<meta name="jspreload" content="jspreload">
	<meta property="article:published_time" content="2016-04-04T11:20:30+08:00">
<meta property="article:author" content="新华网">


    <!-- js 预载-->
    <meta name="jspreload" content="jspreload">
    <script id="sinaads-script" charset="utf-8" src="//d0.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js"></script><script type="text/javascript">
        (function(){
            if(navigator.userAgent.indexOf('MSIE') === -1){return};
            var list = ["http://i1.sinaimg.cn/home/sinaflash.js","http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=js","http://news.sina.com.cn/js/87/content2014/common.js","http://news.sina.com.cn/268/2015/0112/jquery.newest.js","http://pfp.sina.com.cn/dcs/js/dc_video_svv.js","http://d1.sina.com.cn/litong/zhitou/sspnew.js","http://d2.sina.com.cn/d1images/button/rotator.js","http://i.sso.sina.com.cn/js/ssologin.js","http://i.sso.sina.com.cn/js/outlogin_layer.js","http://i.sso.sina.com.cn/js/user_panel_new_version_v2.js","http://i1.sinaimg.cn/unipro/pub/suda_m_v629.js","http://n.sinaimg.cn/17e36822/20150708/topnav20150708_min.js","http://finance.sina.com.cn/text/1007/2015-07-02/licaishi.js","http://static.bshare.cn/b/buttonLite.js#style=-1&amp;uuid=2c330a9c-c99a-4bb0-8919-7ea66c5025cc&amp;pophcol=2&amp;lang=zh","http://static.bshare.cn/b/bshareC0.js","http://news.sina.com.cn/268/2014/0919/bshare_update.js","http://finance.sina.com.cn/text/1007/2015-07-02/lcs1tg.js","http://news.sina.com.cn/js/87/content2014/d_location.js","http://pfp.sina.com.cn/js/17/2013/0621/tb/59.js","http://d2.sina.com.cn/d1images/button/rotator.js","http://pfp.sina.com.cn/iframe/14/2011/0517/47zhongshiwangmeng.js","http://pfp.sina.com.cn/js/17/2013/0401/finance00_300x500.js","http://pfp.sina.com.cn/js/17/2013/0621/tb/58.js","http://i3.sinaimg.cn/ty/sinaui/scrollpic/scrollpic2012070701.min.js","http://d5.sina.com.cn/litong/xianwei/taobao0827.js","http://d3.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js","http://d0.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js","http://d5.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js","http://tech.sina.com.cn/js/717/20140827/index2014/top.js","http://news.sina.com.cn/js/87/20140926/comment.3.min.js","http://news.sina.com.cn/js/87/content2014/feed.relatedNews.js","http://ent.sina.com.cn/js/470/2013/0506/collect.js","http://hq.sinajs.cn/list=sh601857","http://n.sinaimg.cn/780c44e8/20150819/stock_v4_130723_0819.js","http://i1.sinaimg.cn/unipro/pub/suda_m_v629.js","http://finance.sina.com.cn/text/1007/2015-07-02/sidead.js"];
            for(var i=0;i<list.length;i++){(new Image()).src = list[i]}
        })();
    </script>

    <!-- /js 预载-->
    <script type="text/javascript" src="http://i1.sinaimg.cn/home/sinaflash.js"></script>
    <!--http://finance.sina.com.cn/basejs/suggestServer.js -->

    <script type="text/javascript" src="http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=js"></script>
    <link rel="stylesheet" href="http://tech.sina.com.cn/css/717/20140911/index2014/feed.1.1.7.css" type="text/css">
    <link rel="stylesheet" href="http://news.sina.com.cn/268/2014/0919/bshare_update.css" type="text/css">
    <link rel="stylesheet" type="text/css" href="http://news.sina.com.cn/css/87/20140926/comment.3.css">
    <link rel="stylesheet" type="text/css" href="http://finance.sina.com.cn/text/1007/2015-07-02/common.min.css">
    <link rel="stylesheet" type="text/css" href="http://n2.sinaimg.cn/finance/zwy/style_finance1116.css">
	<!--http://n.sinaimg.cn/fed3bc0b/20151023/style_finance1023.css-->
	<!-- http://finance.sina.com.cn/text/1007/2015-07-02/style_finance.css-->
    <script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/common.js"></script>
    <script src="http://news.sina.com.cn/268/2015/0112/jquery.newest.js" charset="utf-8"></script>
    <script type="text/javascript">
        (function(){
            //var isTouchDevice = 'ontouchstart' in window;
            var _doc = document;
            var head, meta;
            if(SINA_ARTICLE_PAGE_SETTINGS.isPad){
                head = _doc.querySelector('head');
                meta = document.createElement('meta');
                meta.setAttribute('name', 'viewport');
                meta.setAttribute('content', 'initial-scale=1.0,maximum-scale=1.0,minimum-scale=1.0,user-scalable=no');
                head.appendChild(meta);

                _doc.write('<link rel="stylesheet" href="http://finance.sina.com.cn/text/1007/2015-07-02/ipad.css">');

            } else {
                _doc.write('<link rel="stylesheet" href="http://n2.sinaimg.cn/finance/9e20dd37/20160226/desktop.css">');

            }
        })();
    </script><link rel="stylesheet" href="http://n2.sinaimg.cn/finance/9e20dd37/20160226/desktop.css">
    <script>try{document.domain='sina.com.cn'}catch(e){}</script>
    <script type="text/javascript" src="http://pfp.sina.com.cn/dcs/js/dc_video_svv.js"></script>
    <script type="text/javascript" src="http://d1.sina.com.cn/litong/zhitou/sspnew.js"></script>
    <script language="javascript" type="text/javascript" src="http://d2.sina.com.cn/d1images/button/rotator.js"></script>
    <script>
        (function (d, s, id) {
            var s, n = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            s = d.createElement(s);
            s.id = id;
            s.setAttribute('charset', 'utf-8');
            s.src = '//d' + Math.floor(0 + Math.random() * (9 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js';
            n.parentNode.insertBefore(s, n);
        })(document, 'script', 'sinaads-script');
    </script>
    <script language="javascript" charset="utf-8" src="http://i.sso.sina.com.cn/js/ssologin.js"></script>
    <script type="text/javascript" src="http://i.sso.sina.com.cn/js/outlogin_layer.js" charset="utf-8"></script>
    <script type="text/javascript" src="http://i.sso.sina.com.cn/js/user_panel_new_version_v2.js" charset="utf-8"></script>
<iframe src="http://beacon.sina.com.cn/ckctl.html" id="ckctlFrame" scrolling="no" style="height: 0px; width: 1px; overflow: hidden;"></iframe><iframe src="http://beacon.sina.com.cn/ckctl.html" id="ckctlFrame" scrolling="no" style="height: 0px; width: 1px; overflow: hidden;"></iframe><script src="http://static.bshare.cn/b/components/bsStatic.js?v=20160206" type="text/javascript" charset="utf-8"></script><script src="http://d1.sina.com.cn/litong/zhitou/sinaads/demo/changwy/link/cj_left_hzh_20160122.js"></script><script src="http://d9.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js"></script><script src="http://comment5.news.sina.com.cn/page/info?version=1&amp;format=js&amp;channel=cj&amp;newsid=comos-fxqxcnz9093681&amp;group=&amp;compress=0&amp;ie=utf-8&amp;oe=utf-8&amp;page=1&amp;page_size=20&amp;jsvar=loader_1459744667532_53298454"></script><script src="http://wp.news.sina.com.cn/?s=api&amp;a=get_group_vuser&amp;group_id=35&amp;format=json&amp;callback=jsonp14597446"></script><style id="style_adcode" type="text/css">.side-ad-20150402 {width:110px;bottom: 300px;_bottom:expression(document.documentElement.scrollTop + document.documentElement.clientHeight - 300);left: 50%;margin: 0 0 0 520px;position: fixed;_position:absolute;z-index:10000;overflow: hidden; font: 12px/22px Arial;color:#333;}
 .side-ad-20150402 img{border: 0;display: block; margin:0 auto;padding: 0;}
 .side-ad-20150402:hover .side-ad-20150402-img-01{border: 0;display: none; margin:0 auto;padding: 0;}
 .side-ad-20150402 .side-ad-20150402-img-02{border: 0;display: none; margin:0 auto;padding: 0;}
 .side-ad-20150402:hover .side-ad-20150402-img-02{border: 0;display: block; margin:0 auto;padding: 0;}
 .side-ad-20150402-close{width:40px;height: 18px;line-height: 80px;margin:0 0 0 70px;display:block;overflow: hidden;background: url(http://i0.sinaimg.cn/dy/deco/2013/0912/close.png) no-repeat;}
 .side-ad-20150402-resize{display: none !important;}</style><script charset="gb2312" src="http://news.sina.com.cn/js/694/2012/0830/realtime.js?ver=1.5.1"></script><style type="text/css">.outlogin_layerbox_bylx,
.outlogin_layerbox_bylx p,
.outlogin_layerbox_bylx div,
.outlogin_layerbox_bylx li,
.outlogin_layerbox_bylx input{font: 12px/1.125 "Simsun", "Arial Narrow", "HELVETICA"!important;}
.outlogin_layerbox_bylx{width:292px!important;position:absolute;border-width:1px!important;border-style:solid!important;text-align:left!important;z-index:1000;overflow:visible!important;}
.outlogin_layerbox_bylx .cur_move{position:relative!important;width:477px!important;height:17px!important;cursor:move;left:0!important;clear:both!important;overflow:visible!important;}
.outlogin_layerbox_bylx a.layerbox_close{position:absolute!important;right:8px!important;top:8px!important;width:12px!important;height:11px!important;padding:5px!important;font:700 12px "Simsun"!important;text-decoration:none!important;overflow:hidden!important;z-index:10!important;}
.outlogin_layerbox_bylx .close_loginname{position:absolute!important;width:11px!important;height:11px!important;padding:5px!important;left:182px!important;top:4px!important;font:700 12px "Simsun"!important;text-decoration:none!important;overflow:hidden!important;background:#fff;}
.outlogin_layerbox_bylx a.layerbox_close:hover{text-decoration:none!important;}
.outlogin_layerbox_bylx .layerbox_left{width:259px!important;display:inline!important;float:right!important;margin-top:-17px!important;height:260px;padding:17px 0 17px 30px!important;border-right-width:1px!important;border-right-style:solid!important;}
.outlogin_layerbox_bylx .layerbox_left .titletips{padding:8px 0 35px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist{list-style:none!important;padding:0!important;margin:0!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li{width:260px!important; clear:both!important; padding-bottom:12px!important;*padding-bottom:11px!important; vertical-align:top;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist .sub_wrap_r{height:20px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist .ndrelativewrap{position:relative!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li .btn_wrap{float:left!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li input.styles{margin:0!important;border-style:solid!important;border-width:1px!important;width: 178px!important;height:14px!important;padding:6px 20px 7px 4px!important;outline-style:none!important;vertical-align:middle!important;overflow:hidden!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li input.styles::-ms-clear{display:none!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist input.styles:focus::-webkit-input-placeholder {color:transparent!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist input.styles:focus::-moz-placeholder {color:transparent!important;}
.outlogin_layerbox_bylx .layerbox_left .pre_name{display:block!important;;padding-top:50px!important;width:205px!important;; white-space:nowrap!important;text-overflow:ellipsis!important;overflow:hidden!important;font-size:18px!important;height:25px!important;}
.outlogin_layerbox_bylx .layerbox_left .chg_ac{display:block!important;height:16px!important;font-size:14px!important;text-decoration:none!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li.loginform_yzm{height:28px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li.loginform_yzm input.styles{width:90px!important; float:left!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li.loginform_yzm .disability_voice{display:inline-block;
width:35px;height:29px;vertical-align:middle!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li.loginform_yzm img.yzm{float:left!important;margin-left:12px!important;height:28px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li.loginform_yzm .reload-code{float:left!important;margin:7px 0 0 5px!important;width:24px!important;height:18px!important;cursor:pointer!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist a.login_btn{float:left!important;margin-right:6px!important;padding:7px 18px!important;text-decoration:none!important;font-size:14px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist a.register_lnk{text-decoration:none;vertical-align:middle;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist a.register_lnk:hover{text-decoration:underline; }
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist .auto_checkbox{vertical-align:-2px!important;_vertical-align:-1px!important;margin:0 5px 0 0!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist label{margin:0 0 0 0!important;vertical-align:middle!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist a.forget_Pwd{margin-right:10px!important;text-decoration:none!important;vertical-align:middle!important;_vertical-align:-1px!important;}
.outlogin_layerbox_bylx .layerbox_left .log_option{float:left!important;padding:7px 20px 0 0!important;*padding-top:12px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist a.forget_Pwd:hover{text-decoration:underline!important;}
.outlogin_layerbox_bylx .association{position:absolute!important;left:30px;top:94px;margin:0;border-width:1px!important;border-style:solid!important;width:230px;overflow:hidden!important;padding:0;clear:both!important;}
.outlogin_layerbox_bylx .association li{margin:0 1px!important;padding:3px!important;line-height:1.2!important;list-style:none!important;white-space:nowrap!important;}
.outlogin_layerbox_bylx .association li.note_item{margin:4px!important;padding:0!important;}
.outlogin_layerbox_bylx .association li a{display:block!important;text-decoration:none!important;}
.outlogin_layerbox_bylx .login_error_tips{position:absolute; top:42px; left:215px; z-index:10; border:1px #797979 solid; background:#ffffcc; margin:0 0 10px 0!important;width:225px!important;padding:5px!important;}
.outlogin_layerbox_bylx .login_recom_tips{position:absolute; top:42px; left:215px; z-index:10; border:1px #797979 solid; background:#ffffcc; margin:0 0 10px 0!important;padding:5px; white-space:nowrap;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li .rmb_login{float:left;padding:8px 0 0 10px;}
.outlogin_LoginBtn:hover{text-decoration:underline!important;}
.outlogin_LoginBtn .LoginIcon{display:inline-block!important;height:15px!important;width:16px!important;vertical-align:middle!important;}
.outlogin_LoginBtn .LoginTx{vertical-align:middle!important;padding-left:5px!important;cursor:pointer!important;}
.outlogin_layerbox_bylx .otwo_d_wrap{width:185px!important;height:260px!important;_width:182px!important;}
.outlogin_layerbox_bylx .otwo_d_wrap .otwo_tl{height:40px!important;padding:8px 0 0 26px!important;}
.outlogin_layerbox_bylx .otwo_d_wrap .td_wrap{border-right:1px solid #ededed!important;height:128px!important;padding-right:30px!important;text-align:right!important;overflow:visible!important;}
.outlogin_layerbox_bylx .otwo_d_wrap .td_wrap img{border:none!important;display:inline!important;}
.outlogin_layerbox_bylx .otwo_d_wrap .thumb{float:right;;border:2px solid #dfdfdf;-webkit-border-radius:60px;-moz-border-radius:60px;border-radius:60px;width:120px;height:120px;overflow:hidden; box-shadow:0 0 2px 3px hsla(0,0%,20%,.05)}
.outlogin_layerbox_bylx .otwo_d_wrap .thumb img{width:120px;height:120px;-webkit-border-radius:60px;-moz-border-radius:60px;border-radius:60px;}
.outlogin_layerbox_bylx .otwo_hlp{position:absolute!important;left:175px!important;top:59px!important;width:229px!important;height:329px!important;background:#ebebeb!important;background:hsla(0,0%,0%,.08)!important;z-index:16!important;}
.outlogin_layerbox_bylx .otwo_hlp .hlp_cnt{margin:3px!important;border:1px solid #dadada!important;height:302px!important;padding:19px 0 0 15px!important;background:#fff;!important}
.outlogin_layerbox_bylx .otwo_hlp .otwo_hlp_tl{height:23px!important;line-height:1!important;}
.outlogin_layerbox_bylx .otwo_hlp .ot_arrow{position:absolute!important;top:68px!important;left:-7px!important;width:11px!important;height:16px!important;background:url(http://i.sso.sina.com.cn/images/login/arrow.png) no-repeat 0 0!important;}
.outlogin_layerbox_bylx .swip_check{position:absolute!important;left:10px!important;top:25px!important;border:1px solid #ccc!important;width:204px!important;height:46px!important;background:#fffae1!important; box-shadow:0 0 3px hsla(0,0%,0%,.2)!important; border-radius:3px!important;}
.outlogin_layerbox_bylx .swip_check_cls,
.outlogin_layerbox_bylx .swip_check_icon,
.outlogin_layerbox_bylx .swip_check_btmarow{background-image:url(http://i.sso.sina.com.cn/images/login/swip_icon.gif)!important;background-repeat:no-repeat!important;overflow:hidden!important;}
.outlogin_layerbox_bylx .swip_check_cls{float:right!important;display:inline!important;margin:9px!important;width:10px!important;height:10px!important;background-position:1px -27px!important;}
.outlogin_layerbox_bylx .swip_check_icon{float:left!important;margin:5px!important;width:15px!important;height:15px!important;background-position:0 -8px!important; }
.outlogin_layerbox_bylx .swip_check_txt{ margin:4px 0 0!important;overflow:hidden!important;line-height:18px!important;}
.swip_check_btmarow{position:absolute!important;bottom:-6px!important;left:50%!important;margin-left:-3px!important;width:10px!important;height:6px!important;background-position:0 0!important;}
.outlogin_layerbox_bylx{width:477px!important;border-color:#ffc525;color:#434242;box-shadow:4px 4px 0 rgba(0,0,0,.1);background-color:#fff;}
.outlogin_layerbox_bylx a.layerbox_close{color:#666;}
.outlogin_layerbox_bylx a.layerbox_close:hover{color:#3f7bc1;}
.outlogin_layerbox_bylx .close_loginname{color:#666;}
.outlogin_layerbox_bylx .close_loginname:hover{color:#DA0000;}
.outlogin_layerbox_bylx .layerbox_left{border-right-color:#fff;background:#fff;}
.outlogin_layerbox_bylx .layerbox_left input.styles{border-color:#d0d0d0;background:#FFF;}
.outlogin_layerbox_bylx .layerbox_left .disability_voice{background:url(http://i.sso.sina.com.cn/images/login/voice.gif) no-repeat 50% 50%;}
.outlogin_layerbox_bylx .layerbox_left a.login_btn{background:#ff8500;color:#fff;}
.outlogin_layerbox_bylx .layerbox_left a.login_btn:hover{background:#ff931d;}
.outlogin_layerbox_bylx .layerbox_left a.register_lnk{color:#a87a2c;}
.outlogin_layerbox_bylx .layerbox_left a.login_lnk:hover{color:#a87a2c;}
.outlogin_layerbox_bylx .layerbox_left a.forget_Pwd{color:#a87a2c;}
.outlogin_layerbox_bylx .association{border-color:#ddd;background:#fff;}
.outlogin_layerbox_bylx .association .note_item{color:#999;}
.outlogin_layerbox_bylx .association a{color:#999;}
.outlogin_layerbox_bylx .association .current{background:#f4f5f7;}
.outlogin_layerbox_bylx .login_error_tips{color:#DA0000; }
.outlogin_layerbox_bylx .login_recom_tips{color:#000; }
.outlogin_LoginBtn .LoginIcon{background:url(http://i.sso.sina.com.cn/images/login/loginButton_16a.png) no-repeat 0 0;}
.outlogin_layerbox_bylx li.loginform_yzm .reload-code{background:url(http://i.sso.sina.com.cn/images/login/verify_refresh.png) no-repeat 0 0;}
.outlogin_layerbox_bylx li.loginform_yzm .reload-code:hover{background-position:0 -18px;}
.outlogin_layerbox_bylx .chg_ac{color:#ff8500;}
.outlogin_layerbox_bylx .layerbox_left .qq_spanoption{float:left!important;padding:8px 20px 0 0!important;*padding-top:8px!important;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li span a.qq_login_h{margin-right:10px!important;text-decoration:none;vertical-align:middle!important;_vertical-align:-1px!important;color:#000;}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li span a.qq_login_h:hover{color:#ff8500;text-decoration:underline !important}
.outlogin_layerbox_bylx .layerbox_left ul.loginformlist li span a span.qq_login_logo {display: inline-block;width: 16px;height: 16px;margin-right: 5px;background-image: url(http://i.sso.sina.com.cn/images/login/qq.png);background-repeat: no-repeat;vertical-align: middle;}</style><link charset="utf-8" rel="stylesheet" media="screen" type="text/css" id="14597446659562" href="http://i.sso.sina.com.cn/css/outlogin/v1/outlogin_skin_reversion.css"><script src="http://static.bshare.cn/js/libs/fingerprint2.min.js" type="text/javascript" charset="utf-8"></script><script src="http://static.bshare.cn/b/engines/bs-engine.js?v=20160206" type="text/javascript" charset="utf-8"></script><style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style><script src="http://bdimg.share.baidu.com/static/js/logger.js?cdnversion=405485"></script><style type="text/css">a.bshareDiv,#bsPanel,#bsMorePanel,#bshareF{border:none;background:none;padding:0;margin:0;font:12px Helvetica,Calibri,Tahoma,Arial,宋体,sans-serif;line-height:14px;}#bsPanel div,#bsMorePanel div,#bshareF div{display:block;}.bsRlogo .bsPopupAwd,.bsRlogoSel .bsPopupAwd,.bsLogo .bsPopupAwd,.bsLogoSel .bsPopupAwd{line-height:16px !important;}a.bshareDiv div,#bsFloatTab div{*display:inline;zoom:1;display:inline-block;}a.bshareDiv img,a.bshareDiv div,a.bshareDiv span,a.bshareDiv a,#bshareF table,#bshareF tr,#bshareF td{text-decoration:none;background:none;margin:0;padding:0;border:none;line-height:1.2}a.bshareDiv span{display:inline;float:none;}div.buzzButton{cursor:pointer;font-weight:bold;}.buzzButton .shareCount a{color:#333}.bsStyle1 .shareCount a{color:#fff}span.bshareText{white-space:nowrap;}span.bshareText:hover{text-decoration:underline;}a.bshareDiv .bsPromo,div.bshare-custom .bsPromo{display:none;position:absolute;z-index:100;}a.bshareDiv .bsPromo.bsPromo1,div.bshare-custom .bsPromo.bsPromo1{width:51px;height:18px;top:-18px;left:0;line-height:16px;font-size:12px !important;font-weight:normal !important;color:#fff;text-align:center;background:url(http://static.bshare.cn/frame/images/bshare_box_sprite2.gif) no-repeat 0 -606px;}div.bshare-custom .bsPromo.bsPromo2{background:url(http://static.bshare.cn/frame/images/bshare_promo_sprite.gif) no-repeat;cursor:pointer;}</style><style type="text/css">.bsBox{display:none;z-index:100000001;font-size:12px;background:url(http://static.bshare.cn/frame/images//background-opaque-dark.gif) !important;padding:6px !important;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}.bsClose{_overflow:hidden;cursor:pointer;position:absolute;z-index:10000000;color:#666;font-weight:bold;font-family:Helvetica,Arial;font-size:14px;line-height:20px;}.bsTop{color:#666;background:#f2f2f2;height:24px;line-height:24px;border-bottom:1px solid #e8e8e8;}.bsTop span{float:left;}.bsFrameDiv,#bsMorePanel{border:none;background:#fff;}.bsReturn{float:right;*margin-right:20px;margin-right:36px;text-align:right;cursor:pointer;line-height:24px;color:#666;opacity:0.5;}#bsReturn:hover{text-decoration:underline;opacity:1;}</style><script src="http://static.bshare.cn/b/components/bsMore.js?v=20160206" type="text/javascript" charset="utf-8"></script><script src="http://bshare.optimix.asia/bshare_share_count?Callback=bShare.showCount&amp;url=http%3A%2F%2Ffinance.sina.com.cn%2Froll%2F2016-04-04%2Fdoc-ifxqxcnz9093681.shtml" type="text/javascript" charset="utf-8"></script><style type="text/css">.bshare-custom{font-size:13px;line-height:16px !important;}.bshare-custom.icon-medium{font-size:14px;line-height:20px !important;}.bshare-custom.icon-medium-plus,.bshare-custom.icon-large{font-size:16px;line-height:26px !important;}.bshare-custom.icon-large{line-height:44px !important;}.bshare-custom a{padding-left:19px;height:16px;_height:18px;text-decoration:none;display:none;zoom:1;vertical-align:middle;cursor:pointer;color:#333;margin-right:3px;-moz-opacity:1;-khtml-opacity:1;opacity:1;}.bshare-custom a:hover{text-decoration:underline;-moz-opacity:0.75;-khtml-opacity:0.75;opacity:0.75;}.bshare-custom.icon-medium a{padding-left:27px;height:24px;}.bshare-custom.icon-medium-plus a{padding-left:35px;height:32px;}.bshare-custom.icon-large a{padding-left:53px;height:50px;}.bshare-custom .bshare-more{padding-left:0 !important;color:#333 !important;*display:inline;display:inline-block;}.bshare-custom #bshare-shareto{color:#333;text-decoration:none;font-weight:bold;margin-right:8px;*display:inline;display:inline-block;}.bshare-custom .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/s4/115.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/m2/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/mp2/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/l3/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/s4/139mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/m2/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/mp2/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/l3/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/s4/9dian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/m2/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/mp2/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/l3/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/s4/baiducang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/m2/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/mp2/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/l3/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/s4/baiduhi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/m2/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/mp2/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/l3/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/s4/bgoogle.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/m2/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/mp2/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/l3/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -18px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -26px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -34px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -52px;*display:inline;display:inline-block;}.bshare-custom .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/s4/caimi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/m2/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/mp2/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/l3/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/s4/cfol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/m2/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/mp2/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/l3/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/s4/chouti.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/m2/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/mp2/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/l3/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/s4/clipboard.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/m2/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/mp2/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/l3/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/s4/cyolbbs.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/m2/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/mp2/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/l3/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/s4/cyzone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/m2/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/mp2/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/l3/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/s4/delicious.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/m2/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/mp2/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/l3/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/s4/dig24.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/m2/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/mp2/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/l3/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/s4/digg.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/m2/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/mp2/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/l3/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/s4/diglog.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/m2/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/mp2/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/l3/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/s4/diigo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/m2/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/mp2/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/l3/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -36px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -52px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -68px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -104px;*display:inline;display:inline-block;}.bshare-custom .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/s4/dream.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/m2/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/mp2/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/l3/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/s4/duitang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/m2/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/mp2/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/l3/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/s4/eastdaymb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/m2/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/mp2/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/l3/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/s4/email.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/m2/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/mp2/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/l3/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/s4/evernote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/m2/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/mp2/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/l3/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -54px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -78px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -102px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -156px;*display:inline;display:inline-block;}.bshare-custom .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/s4/fanfou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/m2/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/mp2/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/l3/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/s4/favorite.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/m2/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/mp2/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/l3/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -72px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -104px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -136px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -208px;*display:inline;display:inline-block;}.bshare-custom .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/s4/friendfeed.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/m2/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/mp2/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/l3/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/s4/fwisp.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/m2/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/mp2/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/l3/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/s4/ganniu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/m2/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/mp2/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/l3/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/s4/gmail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/m2/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/l3/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/s4/gmw.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/m2/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/l3/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/s4/gtranslate.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/m2/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/mp2/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/l3/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/s4/hemidemi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/m2/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/mp2/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/l3/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/s4/hexunmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/m2/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/l3/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/s4/huaban.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/m2/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/mp2/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/l3/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/s4/ifengkb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/m2/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/mp2/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/l3/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -90px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -130px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -170px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -260px;*display:inline;display:inline-block;}.bshare-custom .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/s4/ifensi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/m2/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/mp2/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/l3/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/s4/instapaper.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/m2/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/mp2/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/l3/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -108px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -156px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -204px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -312px;*display:inline;display:inline-block;}.bshare-custom .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/s4/joinwish.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/m2/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/mp2/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/l3/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -126px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -182px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -238px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -364px;*display:inline;display:inline-block;}.bshare-custom .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/s4/laodao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/m2/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/mp2/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/l3/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/s4/leihou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/m2/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/mp2/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/l3/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/s4/leshou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/m2/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/mp2/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/l3/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/s4/linkedin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/m2/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/mp2/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/l3/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/s4/livespace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/m2/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/mp2/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/l3/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/s4/mala.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/m2/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/mp2/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/l3/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/s4/masar.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/m2/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/mp2/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/l3/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/s4/meilishuo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/m2/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/mp2/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/l3/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/s4/miliao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/m2/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/mp2/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/l3/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/s4/mister_wong.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/m2/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/mp2/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/l3/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/s4/mogujie.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/m2/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/mp2/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/l3/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/s4/moptk.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/m2/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/mp2/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/l3/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -144px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -208px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -272px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -416px;*display:inline;display:inline-block;}.bshare-custom .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/s4/myshare.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/m2/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/mp2/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/l3/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/s4/myspace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/m2/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/mp2/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/l3/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -162px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -234px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -306px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -468px;*display:inline;display:inline-block;}.bshare-custom .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/s4/netvibes.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/m2/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/mp2/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/l3/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -180px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -260px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -340px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -520px;*display:inline;display:inline-block;}.bshare-custom .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/s4/pinterest.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/m2/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/mp2/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/l3/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/s4/poco.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/m2/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/mp2/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/l3/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/s4/printer.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/m2/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/mp2/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/l3/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/s4/printf.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/m2/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/mp2/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/l3/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -198px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -286px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -374px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -572px;*display:inline;display:inline-block;}.bshare-custom .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/s4/qqshuqian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/m2/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/mp2/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/l3/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -216px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -312px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -408px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -624px;*display:inline;display:inline-block;}.bshare-custom .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -234px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -338px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -442px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -676px;*display:inline;display:inline-block;}.bshare-custom .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/s4/readitlater.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/m2/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/mp2/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/l3/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/s4/reddit.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/m2/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/mp2/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/l3/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/s4/redmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/m2/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/l3/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/s4/renjian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/m2/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/mp2/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/l3/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/s4/renmaiku.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/m2/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/mp2/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/l3/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -252px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -364px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -476px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -728px;*display:inline;display:inline-block;}.bshare-custom .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/s4/shouji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/m2/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/mp2/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/l3/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -270px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -390px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -510px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -780px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -288px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -416px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -544px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -832px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/s4/sinavivi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/m2/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/mp2/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/l3/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/s4/sohubai.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/m2/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/mp2/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/l3/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -306px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -442px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -578px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -884px;*display:inline;display:inline-block;}.bshare-custom .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/s4/southmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/m2/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/l3/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/s4/stumbleupon.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/m2/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/mp2/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/l3/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/s4/szone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/m2/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/mp2/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/l3/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/s4/taojianghu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/m2/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/mp2/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/l3/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -324px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -468px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -612px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -936px;*display:inline;display:inline-block;}.bshare-custom .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/s4/tongxue.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/m2/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/mp2/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/l3/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/s4/tuita.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/m2/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/mp2/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/l3/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/s4/tumblr.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/m2/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/mp2/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/l3/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -342px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -494px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -646px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -988px;*display:inline;display:inline-block;}.bshare-custom .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/s4/ushi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/m2/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/mp2/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/l3/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/s4/waakee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/m2/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/mp2/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/l3/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/s4/wealink.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/m2/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/mp2/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/l3/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/s4/woshao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/m2/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/mp2/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/l3/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/s4/xianguo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/m2/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/mp2/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/l3/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/s4/xiaomeisns.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/m2/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/mp2/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/l3/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinminmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/m2/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/l3/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/xyweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/s4/yaolanmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/m2/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/l3/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/s4/yijee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/m2/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/mp2/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/l3/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/s4/youdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/m2/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/mp2/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/l3/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/s4/zjol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/m2/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/mp2/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/l3/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinhuamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/m2/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/mp2/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/l3/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/s4/szmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/m2/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/l3/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/s4/changshamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/m2/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/mp2/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/l3/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/s4/hefeimb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/m2/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/mp2/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/l3/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/s4/wansha.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/m2/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/mp2/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/l3/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/s4/189share.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/m2/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/mp2/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/l3/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/s4/diandian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/m2/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/mp2/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/l3/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/s4/tianji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/m2/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/mp2/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/l3/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/s4/jipin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/m2/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/mp2/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/l3/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/s4/chezhumb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/m2/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/mp2/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/l3/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/s4/gplus.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/m2/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/mp2/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/l3/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/yidongweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/s4/youdaonote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/m2/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/mp2/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/l3/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/s4/jschina.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/m2/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/mp2/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/l3/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/s4/mingdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/m2/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/mp2/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/l3/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/s4/jxcn.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/m2/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/mp2/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/l3/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/s4/qileke.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/m2/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/mp2/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/l3/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/s4/sohukan.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/m2/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/mp2/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/l3/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/s4/maikunote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/m2/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/mp2/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/l3/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/s4/lezhimark.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/m2/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/mp2/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/l3/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/s4/189mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/m2/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/mp2/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/l3/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/s4/wo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/m2/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/mp2/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/l3/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/gmweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/jianweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/s4/qingbiji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/m2/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/mp2/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/l3/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/s4/duankou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/m2/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/mp2/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/l3/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/s4/qqim.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/m2/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/mp2/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/l3/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/kdweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/s4/xueqiu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/m2/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/mp2/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/l3/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/s4/weixin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/m2/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/mp2/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/l3/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom #bshare-more-icon,.bshare-custom .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/s4/more.png") no-repeat;padding-left:19px !important;}.bshare-custom.icon-medium #bshare-more-icon,.bshare-custom.icon-medium .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/m2/more.gif") no-repeat;padding-left:27px !important;}.bshare-custom.icon-medium-plus #bshare-more-icon,.bshare-custom.icon-medium-plus .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/mp2/more.gif") no-repeat;padding-left:35px !important;}.bshare-custom.icon-large #bshare-more-icon,.bshare-custom.icon-large .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/l3/more.gif") no-repeat;padding-left:53px !important;}.bshare-custom .bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-android.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-android.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-android.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-android.gif) no-repeat;}.bshare-custom .bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-apple.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-apple.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-apple.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-apple.gif) no-repeat;}.bshare-custom .bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-sharethis.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-sharethis.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-sharethis.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-sharethis.gif) no-repeat;}.bshare-custom .bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-sharethis-orange.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom .bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-addthis.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-addthis.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-addthis.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-addthis.gif) no-repeat;}.bshare-custom .bshare-share-count{width:41px;background:transparent url(http://static.bshare.cn/frame/images/counter_box_18.gif) no-repeat;height:18px;line-height:18px !important;color:#333;text-align:center;font:bold 11px Arial,宋体,sans-serif;zoom:1;_padding-top:2px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-share-count{width:45px;padding:0 0 0 2px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_24.gif) no-repeat;height:24px;color:#444;line-height:24px !important;text-align:center;font:bold 12px Arial,宋体,sans-serif;zoom:1;_padding-top:5px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-share-count{width:60px !important;padding:0 0 0 3px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_32.gif) no-repeat;height:32px;line-height:32px !important;text-align:center;color:#444;font:normal 18px Arial,宋体,sans-serif;zoom:1;_padding-top:6px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-share-count{width:94px !important;padding:0 0 0 5px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_50.gif) no-repeat;height:50px;line-height:50px !important;text-align:center;color:#444;font:normal 22px Arial,宋体,sans-serif;zoom:1;_padding-top:12px;*display:inline;display:inline-block;}</style><script src="http://static.bshare.cn/b/styles/bshareS887.js?v=20160206" type="text/javascript" charset="utf-8"></script><link href="http://bdimg.share.baidu.com/static/css/bdsstyle.css?cdnversion=20131219" rel="stylesheet" type="text/css"><style type="text/css">.rtw2-cfx:after {content:"0";display:block;height:0;clear:both;}
 .rtw2-cfx {zoom:1;}
 .real-time-window {z-index:60000; display:block; height:50px; line-height:50px; overflow:hidden; zoom:1;}
 .real-time-window .rtw2-in { height:50px;line-height:50px;}
 .real-time-window .rtw2-lt { display:inline; float:left; width:61px; height:50px; background:url(http://i3.sinaimg.cn/dy/deco/2013/0331/mmx_tc_ico_main.png) 0 0 no-repeat #f9f5ec; zoom:1; }
 .real-time-window .rtw2-md { display:inline; float:left; background:#f9f5ec; height:48px; line-height:48px; zoom:1; border-top:1px solid #f6e3c9;border-bottom:1px solid #f6e3c9;}
 .real-time-window a.rtw2-md-title { font-family:"Microsoft YaHei","微软雅黑","SimHei","黑体" !important; display:inline-block; height:48px; line-height:48px; padding:0 5px; font-size:16px; }
 .real-time-window a.rtw2-md-title:link { color:#122E67 !important;text-decoration:none !important;}
 .real-time-window a.rtw2-md-title:hover { color:#ff8400 !important;text-decoration:underline !important;}
 .real-time-window a.rtw2-md-title:visited { color:#52687e !important;text-decoration:none !important;}
 .real-time-window a.rtw2-md-detail {font-family:"SimSun","宋体","Arial Narrow" !important; display:inline-block; height:48px; line-height:48px; padding:0 5px; font-size:16px; display:none;}
 .real-time-window a.rtw2-md-detail:link { color:#22c4ff;text-decoration:none;}
 .real-time-window a.rtw2-md-detail:hover { color:#22c4ff;text-decoration:underline !important;}
 .real-time-window a.rtw2-md-detail:visited { color:#22c4ff;text-decoration:none;}
 .real-time-window .rtw2-close { display:inline; width:42px; height:38px; float:left; background:url(http://i3.sinaimg.cn/dy/deco/2013/0331/mmx_tc_ico_main.png) -61px 0 no-repeat; padding-top:12px; _filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(enabled=true,sizingMethod=scale, src="http://i0.sinaimg.cn/dy/deco/2013/0331/mmx_tc_ico_right.png"); _background:none; zoom:1;}
 .real-time-window .rtw2-close-btn{ width:26px; height:25px; display:block;background:url(http://i3.sinaimg.cn/dy/deco/2013/0331/mmx_tc_ico_main.png) no-repeat -103px 0 #f9f5ec;}
 .real-time-window .rtw2-close-btn:hover{ background-position: right 0; }</style><style type="text/css">div.bsClear{clear:both;height:0;line-height:0;overflow:hidden;font-size:0;}.bsSearchDiv{padding:5px 15px;background-color:#fafafa;}.bFind-wrapper-top{background:#fff;border-color:#ccc #aaa #aaa #ccc;border-style:solid;border-width:1px;height:16px;padding:4px;margin:0;}.bFind-wrapper-top input{padding:0 !important;border:none !important;box-shadow:none !important;line-height:16px !important;}.bFind-placeholder{background:url("http://static.bshare.cn/css/images/search-icon.gif") no-repeat;display:block;float:left;height:16px;width:16px;}.bFind{background:none;border:none;float:left;font-size:11px !important;height:16px !important;margin-left:3px;outline:none;padding:0;width:400px;}.bsPlatDiv{height:322px;background:#fff;overflow:auto;padding:0 15px;}#bsLogoList{display:block;list-style:none;overflow:hidden;margin:0;padding:0;}#bsLogoList li{float:left;display:inline-block;width:71px;text-align:center;font-size:12px;height:80px;margin:0 !important;}#bsLogoList .bsPlatIcon{cursor:pointer;display:block !important;text-align:center;}#bsLogoList .bsPlatImg{width:32px;height:32px;border:none !important;display:inline-block;}#bsLogoList .bsPlatImg:hover{-moz-border-radius:7px;-webkit-border-radius:7px;border-radius:7px;box-shadow:0 0 15px #a7a8ac;}#bsLogoList .bsPlatName{white-space:nowrap;text-overflow:ellipsis;overflow:hidden;text-align:center;color:#333 !important;margin-top:2px;line-height:140%;*width:70px;}#bsLogoList .bsPromoM{text-align:center;}.bsFooterDiv{height:24px;line-height:24px;padding:0 15px;border-top:1px solid #e8e8e8;background:#f2f2f2;text-align:right;}a.bsLogoLink{color:#666;}.bsLogoLink:hover{text-decoration:underline;}.bsPromoM{background:url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;}.bsNew,.bsHot,.bsRec,.bsAwd{background-position:0 -552px;width:19px;margin:5px auto 1px;line-height:16px;height:18px;font-size:12px;color:#fff;overflow:hidden;}.bsNew{background-position:0 -570px;}.bsRec{width:30px;background-position:0 -588px;}.bsAwd{background:url(http://static.bshare.cn/frame/images//promot/promote.gif) no-repeat;}</style><style type="text/css">.ui-outlogin-shake {-webkit-animation:outlogin-layer-shake 600ms;}
@-webkit-keyframes outlogin-layer-shake {
0% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
10% {-webkit-transform:translateX(-16px);-webkit-animation-timing-function:ease-in;}
20% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
30% {-webkit-transform:translateX(8px);-webkit-animation-timing-function:ease-in;}
40% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
50% {-webkit-transform:translateX(-4px);-webkit-animation-timing-function:ease-in;}
60% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
70% {-webkit-transform:translateX(2px);-webkit-animation-timing-function:ease-in;}
80% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
90% {-webkit-transform:translateX(-1px);-webkit-animation-timing-function:ease-in;}
100% {-webkit-transform:translateX(0px);-webkit-animation-timing-function:ease-out;}
}
</style><style type="text/css">.bshare-custom{font-size:13px;line-height:16px !important;}.bshare-custom.icon-medium{font-size:14px;line-height:20px !important;}.bshare-custom.icon-medium-plus,.bshare-custom.icon-large{font-size:16px;line-height:26px !important;}.bshare-custom.icon-large{line-height:44px !important;}.bshare-custom a{padding-left:19px;height:16px;_height:18px;text-decoration:none;display:none;zoom:1;vertical-align:middle;cursor:pointer;color:#333;margin-right:3px;-moz-opacity:1;-khtml-opacity:1;opacity:1;}.bshare-custom a:hover{text-decoration:underline;-moz-opacity:0.75;-khtml-opacity:0.75;opacity:0.75;}.bshare-custom.icon-medium a{padding-left:27px;height:24px;}.bshare-custom.icon-medium-plus a{padding-left:35px;height:32px;}.bshare-custom.icon-large a{padding-left:53px;height:50px;}.bshare-custom .bshare-more{padding-left:0 !important;color:#333 !important;*display:inline;display:inline-block;}.bshare-custom #bshare-shareto{color:#333;text-decoration:none;font-weight:bold;margin-right:8px;*display:inline;display:inline-block;}.bshare-custom .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/s4/115.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/m2/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/mp2/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/l3/115.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/s4/139mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/m2/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/mp2/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/l3/139mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/s4/9dian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/m2/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/mp2/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/l3/9dian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/s4/baiducang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/m2/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/mp2/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/l3/baiducang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/s4/baiduhi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/m2/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/mp2/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/l3/baiduhi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/s4/bgoogle.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/m2/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/mp2/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/l3/bgoogle.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -18px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -26px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -34px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -52px;*display:inline;display:inline-block;}.bshare-custom .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/s4/caimi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/m2/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/mp2/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/l3/caimi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/s4/cfol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/m2/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/mp2/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/l3/cfol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/s4/chouti.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/m2/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/mp2/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/l3/chouti.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/s4/clipboard.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/m2/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/mp2/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/l3/clipboard.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/s4/cyolbbs.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/m2/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/mp2/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/l3/cyolbbs.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/s4/cyzone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/m2/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/mp2/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/l3/cyzone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/s4/delicious.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/m2/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/mp2/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/l3/delicious.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/s4/dig24.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/m2/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/mp2/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/l3/dig24.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/s4/digg.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/m2/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/mp2/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/l3/digg.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/s4/diglog.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/m2/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/mp2/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/l3/diglog.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/s4/diigo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/m2/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/mp2/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/l3/diigo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -36px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -52px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -68px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -104px;*display:inline;display:inline-block;}.bshare-custom .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/s4/dream.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/m2/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/mp2/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/l3/dream.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/s4/duitang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/m2/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/mp2/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/l3/duitang.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/s4/eastdaymb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/m2/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/mp2/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/l3/eastdaymb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/s4/email.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/m2/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/mp2/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/l3/email.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/s4/evernote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/m2/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/mp2/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/l3/evernote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -54px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -78px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -102px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -156px;*display:inline;display:inline-block;}.bshare-custom .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/s4/fanfou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/m2/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/mp2/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/l3/fanfou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/s4/favorite.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/m2/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/mp2/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/l3/favorite.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -72px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -104px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -136px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -208px;*display:inline;display:inline-block;}.bshare-custom .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/s4/friendfeed.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/m2/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/mp2/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/l3/friendfeed.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/s4/fwisp.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/m2/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/mp2/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/l3/fwisp.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/s4/ganniu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/m2/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/mp2/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/l3/ganniu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/s4/gmail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/m2/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/l3/gmail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/s4/gmw.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/m2/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/l3/gmw.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/s4/gtranslate.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/m2/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/mp2/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/l3/gtranslate.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/s4/hemidemi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/m2/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/mp2/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/l3/hemidemi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/s4/hexunmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/m2/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/l3/hexunmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/s4/huaban.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/m2/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/mp2/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/l3/huaban.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/s4/ifengkb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/m2/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/mp2/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/l3/ifengkb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -90px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -130px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -170px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -260px;*display:inline;display:inline-block;}.bshare-custom .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/s4/ifensi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/m2/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/mp2/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/l3/ifensi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/s4/instapaper.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/m2/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/mp2/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/l3/instapaper.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -108px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -156px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -204px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -312px;*display:inline;display:inline-block;}.bshare-custom .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/s4/joinwish.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/m2/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/mp2/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/l3/joinwish.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -126px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -182px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -238px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -364px;*display:inline;display:inline-block;}.bshare-custom .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/s4/laodao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/m2/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/mp2/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/l3/laodao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/s4/leihou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/m2/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/mp2/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/l3/leihou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/s4/leshou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/m2/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/mp2/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/l3/leshou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/s4/linkedin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/m2/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/mp2/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/l3/linkedin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/s4/livespace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/m2/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/mp2/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/l3/livespace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/s4/mala.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/m2/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/mp2/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/l3/mala.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/s4/masar.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/m2/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/mp2/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/l3/masar.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/s4/meilishuo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/m2/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/mp2/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/l3/meilishuo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/s4/miliao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/m2/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/mp2/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/l3/miliao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/s4/mister_wong.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/m2/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/mp2/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/l3/mister_wong.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/s4/mogujie.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/m2/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/mp2/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/l3/mogujie.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/s4/moptk.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/m2/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/mp2/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/l3/moptk.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -144px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -208px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -272px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -416px;*display:inline;display:inline-block;}.bshare-custom .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/s4/myshare.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/m2/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/mp2/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/l3/myshare.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/s4/myspace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/m2/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/mp2/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/l3/myspace.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -162px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -234px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -306px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -468px;*display:inline;display:inline-block;}.bshare-custom .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/s4/netvibes.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/m2/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/mp2/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/l3/netvibes.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -180px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -260px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -340px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -520px;*display:inline;display:inline-block;}.bshare-custom .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/s4/pinterest.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/m2/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/mp2/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/l3/pinterest.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/s4/poco.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/m2/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/mp2/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/l3/poco.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/s4/printer.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/m2/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/mp2/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/l3/printer.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/s4/printf.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/m2/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/mp2/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/l3/printf.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -198px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -286px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -374px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -572px;*display:inline;display:inline-block;}.bshare-custom .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/s4/qqshuqian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/m2/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/mp2/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/l3/qqshuqian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -216px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -312px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -408px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -624px;*display:inline;display:inline-block;}.bshare-custom .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -234px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -338px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -442px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -676px;*display:inline;display:inline-block;}.bshare-custom .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/s4/readitlater.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/m2/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/mp2/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/l3/readitlater.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/s4/reddit.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/m2/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/mp2/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/l3/reddit.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/s4/redmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/m2/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/l3/redmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/s4/renjian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/m2/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/mp2/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/l3/renjian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/s4/renmaiku.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/m2/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/mp2/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/l3/renmaiku.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -252px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -364px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -476px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -728px;*display:inline;display:inline-block;}.bshare-custom .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/s4/shouji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/m2/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/mp2/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/l3/shouji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -270px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -390px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -510px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -780px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -288px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -416px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -544px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -832px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/s4/sinavivi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/m2/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/mp2/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/l3/sinavivi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/s4/sohubai.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/m2/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/mp2/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/l3/sohubai.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -306px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -442px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -578px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -884px;*display:inline;display:inline-block;}.bshare-custom .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/s4/southmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/m2/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/l3/southmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/s4/stumbleupon.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/m2/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/mp2/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/l3/stumbleupon.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/s4/szone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/m2/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/mp2/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/l3/szone.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/s4/taojianghu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/m2/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/mp2/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/l3/taojianghu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -324px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -468px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -612px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -936px;*display:inline;display:inline-block;}.bshare-custom .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/s4/tongxue.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/m2/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/mp2/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/l3/tongxue.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/s4/tuita.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/m2/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/mp2/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/l3/tuita.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/s4/tumblr.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/m2/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/mp2/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/l3/tumblr.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -342px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/m2/sprite/top_logos_sprite.gif") no-repeat 0 -494px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/mp2/sprite/top_logos_sprite.gif") no-repeat 0 -646px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/l3/sprite/top_logos_sprite.gif") no-repeat 0 -988px;*display:inline;display:inline-block;}.bshare-custom .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/s4/ushi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/m2/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/mp2/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/l3/ushi.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/s4/waakee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/m2/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/mp2/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/l3/waakee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/s4/wealink.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/m2/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/mp2/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/l3/wealink.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/s4/woshao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/m2/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/mp2/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/l3/woshao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/s4/xianguo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/m2/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/mp2/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/l3/xianguo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/s4/xiaomeisns.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/m2/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/mp2/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/l3/xiaomeisns.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinminmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/m2/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/l3/xinminmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/xyweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/xyweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/s4/yaolanmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/m2/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/l3/yaolanmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/s4/yijee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/m2/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/mp2/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/l3/yijee.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/s4/youdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/m2/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/mp2/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/l3/youdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/s4/zjol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/m2/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/mp2/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/l3/zjol.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinhuamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/m2/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/mp2/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/l3/xinhuamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/s4/szmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/m2/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/mp2/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/l3/szmb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/s4/changshamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/m2/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/mp2/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/l3/changshamb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/s4/hefeimb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/m2/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/mp2/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/l3/hefeimb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/s4/wansha.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/m2/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/mp2/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/l3/wansha.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/s4/189share.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/m2/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/mp2/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/l3/189share.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/s4/diandian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/m2/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/mp2/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/l3/diandian.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/s4/tianji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/m2/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/mp2/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/l3/tianji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/s4/jipin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/m2/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/mp2/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/l3/jipin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/s4/chezhumb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/m2/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/mp2/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/l3/chezhumb.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/s4/gplus.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/m2/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/mp2/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/l3/gplus.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/yidongweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/yidongweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/s4/youdaonote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/m2/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/mp2/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/l3/youdaonote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/s4/jschina.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/m2/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/mp2/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/l3/jschina.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/s4/mingdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/m2/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/mp2/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/l3/mingdao.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/s4/jxcn.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/m2/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/mp2/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/l3/jxcn.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/s4/qileke.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/m2/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/mp2/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/l3/qileke.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/s4/sohukan.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/m2/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/mp2/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/l3/sohukan.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/s4/maikunote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/m2/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/mp2/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/l3/maikunote.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/s4/lezhimark.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/m2/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/mp2/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/l3/lezhimark.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/s4/189mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/m2/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/mp2/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/l3/189mail.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/s4/wo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/m2/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/mp2/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/l3/wo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/gmweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/gmweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/jianweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/jianweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/s4/qingbiji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/m2/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/mp2/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/l3/qingbiji.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/s4/duankou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/m2/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/mp2/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/l3/duankou.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/s4/qqim.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/m2/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/mp2/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/l3/qqim.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/kdweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/m2/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/mp2/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/l3/kdweibo.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/s4/xueqiu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/m2/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/mp2/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/l3/xueqiu.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/s4/weixin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/m2/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/mp2/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/l3/weixin.gif") no-repeat;*display:inline;display:inline-block;}.bshare-custom #bshare-more-icon,.bshare-custom .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/s4/more.png") no-repeat;padding-left:19px !important;}.bshare-custom.icon-medium #bshare-more-icon,.bshare-custom.icon-medium .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/m2/more.gif") no-repeat;padding-left:27px !important;}.bshare-custom.icon-medium-plus #bshare-more-icon,.bshare-custom.icon-medium-plus .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/mp2/more.gif") no-repeat;padding-left:35px !important;}.bshare-custom.icon-large #bshare-more-icon,.bshare-custom.icon-large .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/l3/more.gif") no-repeat;padding-left:53px !important;}.bshare-custom .bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-android.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-android.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-android.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-android{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-android.gif) no-repeat;}.bshare-custom .bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-apple.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-apple.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-apple.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-apple{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-apple.gif) no-repeat;}.bshare-custom .bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-sharethis.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-sharethis.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-sharethis.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-sharethis{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-sharethis.gif) no-repeat;}.bshare-custom .bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-sharethis-orange.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-sharethis-orange{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-sharethis-orange.gif) no-repeat;}.bshare-custom .bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/s4/more-style-addthis.png) no-repeat;}.bshare-custom.icon-medium a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/m2/more-style-addthis.gif) no-repeat;}.bshare-custom.icon-medium-plus a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/mp2/more-style-addthis.gif) no-repeat;}.bshare-custom.icon-large a.bshare-more.more-style-addthis{background:url(http://static.bshare.cn/frame/images/logos/l3/more-style-addthis.gif) no-repeat;}.bshare-custom .bshare-share-count{width:41px;background:transparent url(http://static.bshare.cn/frame/images/counter_box_18.gif) no-repeat;height:18px;line-height:18px !important;color:#333;text-align:center;font:bold 11px Arial,宋体,sans-serif;zoom:1;_padding-top:2px;*display:inline;display:inline-block;}.bshare-custom.icon-medium .bshare-share-count{width:45px;padding:0 0 0 2px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_24.gif) no-repeat;height:24px;color:#444;line-height:24px !important;text-align:center;font:bold 12px Arial,宋体,sans-serif;zoom:1;_padding-top:5px;*display:inline;display:inline-block;}.bshare-custom.icon-medium-plus .bshare-share-count{width:60px !important;padding:0 0 0 3px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_32.gif) no-repeat;height:32px;line-height:32px !important;text-align:center;color:#444;font:normal 18px Arial,宋体,sans-serif;zoom:1;_padding-top:6px;*display:inline;display:inline-block;}.bshare-custom.icon-large .bshare-share-count{width:94px !important;padding:0 0 0 5px;vertical-align:bottom;background:transparent url(http://static.bshare.cn/frame/images/counter_box_50.gif) no-repeat;height:50px;line-height:50px !important;text-align:center;color:#444;font:normal 22px Arial,宋体,sans-serif;zoom:1;_padding-top:12px;*display:inline;display:inline-block;}</style><style type="text/css">a.bsSiteLink{text-decoration:none;color:#666;}a.bsSiteLink:hover{text-decoration:underline;}a.bshareDiv{overflow:hidden;height:16px;line-height:18px;font-size:14px;color:#333;padding-left:0;}a.bshareDiv:hover{text-decoration:none;}div.bsTitle{padding:0 8px;border-bottom:1px solid #e8e8e8;color:#666;background:#f2f2f2;text-align:left;}div.buzzButton{cursor:pointer;}div.bsRlogo,div.bsRlogoSel{width:68px;float:left;margin:0;padding:2px 0;}div.bsRlogo a,div.bsRlogoSel a{float:left;}div.bsLogo,div.bsLogoSel{float:left;width:111px;text-align:left;height:auto;padding:2px 4px;margin:2px 0;white-space:nowrap;overflow:hidden;}div.bsLogoSel,div.bsRlogoSel{border:1px solid #ddd;background:#f1f1f1;}div.bsLogo,div.bsRlogo{border:1px solid #fff;background:#fff;}div.bsLogo a,div.bsLogoSel a{display:block;height:16px;line-height:16px;padding:0 0 0 24px;text-decoration:none;float:left;overflow:hidden;}div.bsLogoSel a,div.bsRlogoSel a{color:#000;border:none;}div.bsLogo a,div.bsRlogo a{color:#666;border:none;}div.bsLogoLink{width:121px;overflow:hidden;background:#FFF;float:left;margin:3px 0;}#bsPanel{position:absolute;z-index:100000000;font-size:12px;width:258px;background:url(http://static.bshare.cn/frame/images/background-opaque-dark.png);padding:6px;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}div.bsClear{clear:both;height:0;line-height:0;font-size:0;overflow:hidden;}div.bsPopupAwd{background: url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;background-position:0 -624px;width:18px;padding-left:3px;text-align:center;float:left;margin-left:2px;height:15px;font-size:12px;color:#fff;overflow:hidden;}div.bsRlogo .bsPopupAwd,div.bsRlogoSel .bsPopupAwd{float:left;margin:5px 0 0 -14px;}</style><script src="http://static.bshare.cn/b/components/bsPlatforms.js?v=20160206" type="text/javascript" charset="utf-8"></script><script src="http://bshare.optimix.asia/bshare_view?Callback=bShare.viewcb&amp;url=http%3A%2F%2Ffinance.sina.com.cn%2Froll%2F2016-04-04%2Fdoc-ifxqxcnz9093681.shtml&amp;h=&amp;uuid=2c330a9c-c99a-4bb0-8919-7ea66c5025cc&amp;sc=1&amp;l=17&amp;lite=1&amp;ot=辽宁鞍山：生态树葬带起文明祭祀之风_新浪财经_新浪网&amp;cs=UTF-8&amp;kws=辽宁鞍山：生态树葬带起文明祭祀之风&amp;fp=70f182235e037fcefd896f1c3f8d500a&amp;b=bs1e2414" type="text/javascript" charset="utf-8"></script><style type="text/css">a.bsSiteLink{text-decoration:none;color:#666;}a.bsSiteLink:hover{text-decoration:underline;}a.bshareDiv{overflow:hidden;height:16px;line-height:18px;font-size:14px;color:#333;padding-left:0;}a.bshareDiv:hover{text-decoration:none;}div.bsTitle{padding:0 8px;border-bottom:1px solid #e8e8e8;color:#666;background:#f2f2f2;text-align:left;}div.buzzButton{cursor:pointer;}div.bsRlogo,div.bsRlogoSel{width:68px;float:left;margin:0;padding:2px 0;}div.bsRlogo a,div.bsRlogoSel a{float:left;}div.bsLogo,div.bsLogoSel{float:left;width:111px;text-align:left;height:auto;padding:2px 4px;margin:2px 0;white-space:nowrap;overflow:hidden;}div.bsLogoSel,div.bsRlogoSel{border:1px solid #ddd;background:#f1f1f1;}div.bsLogo,div.bsRlogo{border:1px solid #fff;background:#fff;}div.bsLogo a,div.bsLogoSel a{display:block;height:16px;line-height:16px;padding:0 0 0 24px;text-decoration:none;float:left;overflow:hidden;}div.bsLogoSel a,div.bsRlogoSel a{color:#000;border:none;}div.bsLogo a,div.bsRlogo a{color:#666;border:none;}div.bsLogoLink{width:121px;overflow:hidden;background:#FFF;float:left;margin:3px 0;}#bsPanel{position:absolute;z-index:100000000;font-size:12px;width:258px;background:url(http://static.bshare.cn/frame/images/background-opaque-dark.png);padding:6px;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}div.bsClear{clear:both;height:0;line-height:0;font-size:0;overflow:hidden;}div.bsPopupAwd{background: url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;background-position:0 -624px;width:18px;padding-left:3px;text-align:center;float:left;margin-left:2px;height:15px;font-size:12px;color:#fff;overflow:hidden;}div.bsRlogo .bsPopupAwd,div.bsRlogoSel .bsPopupAwd{float:left;margin:5px 0 0 -14px;}</style></head>
<body class=" sinacMNT_logout"><div id="sinaadToolkitBox0" class="sinaad-toolkit-box" style="position: fixed; width: 300px; height: 250px; z-index: 11000; display: block; left: 879px; top: 77px;"><div style="width: 60px; height: 22px; position: absolute; right: 0px; top: 0px; z-index: 11010; margin: 0px; padding: 0px; cursor: pointer; background: url(&quot;http://d1.sina.com.cn/litong/zhitou/sinaads/60x18_2_close.gif&quot;) no-repeat;"></div><div style="width: 60px; height: 18px; opacity: 0.5; display: none; position: absolute; top: 0px; right: 60px; z-index: 11010; font-size: 12px; font-family: 宋体; background: rgb(0, 0, 0);"><div style="width: 50px; height: 18px; line-height: 18px; padding: 0px 0px 0px 3px; position: absolute; top: 0px; left: 0px; color: rgb(255, 255, 255);"></div><div style="width: 10px; height: 18px; line-height: 18px; overflow: hidden; position: absolute; top: 0px; left: 43px; color: rgb(255, 0, 0);"></div></div><ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000055657" data-ad-status="done" data-ad-offset-left="0" data-ad-offset-top="4484" style="display: block; overflow: hidden; text-decoration: none; padding-top: 0px;"><ins style="text-decoration:none;margin:0px auto;display:block;overflow:hidden;width:300px;height:250px;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NwkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJOWI0N2I5ZWEtMjQxMS00M2QyLTg4NGQtOGM2YzMxODFjYzBiCTM5Njk1Nwk1NzMzMjUyNTEyX1BJTlBBSS1DUEMJMTI2ODIwCTEyMzEwMQkwLjAwMzE3MTgxCTEJdHJ1ZQlQRFBTMDAwMDAwMDU1NjU3CTEwOTMwOTgJUEMJaW1hZ2UJLQkwfDM5Njk1N3xudWxsCW51bGwJMQktMQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=DspHYY6fQreiDkuDG0e%2FtspeMLDjDyETu7Rrtg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMGVjYTQ3NjEtOGU5Zi00MmI3LWEyMGUtNGI4MzFiNDdiZmI2CTE3CVBEUFMwMDAwMDAwNTU2NTcJMTA5MzA5OAkxCVJUQgkt%26id%3D17%26url%3Dhttps%253A%252F%252Fizhongchou.taobao.com%252Fdreamdetail.htm%253Fspm%253Da215p.1472805.0.0.bYhb6h%2526id%253D10069812%2526qq-pf-to%253Dpcqq.c2c%26sina_sign%3D60d6ec8e41f7e8b1&amp;sign=2c6496a891c1ea8c" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NwkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJOWI0N2I5ZWEtMjQxMS00M2QyLTg4NGQtOGM2YzMxODFjYzBiCTM5Njk1Nwk1NzMzMjUyNTEyX1BJTlBBSS1DUEMJMTI2ODIwCTEyMzEwMQkwLjAwMzE3MTgxCTEJdHJ1ZQlQRFBTMDAwMDAwMDU1NjU3CTEwOTMwOTgJUEMJaW1hZ2UJLQkwfDM5Njk1N3xudWxsCW51bGwJMQktMQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=DspHYY6fQreiDkuDG0e%2FtspeMLDjDyETu7Rrtg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMGVjYTQ3NjEtOGU5Zi00MmI3LWEyMGUtNGI4MzFiNDdiZmI2CTE3CVBEUFMwMDAwMDAwNTU2NTcJMTA5MzA5OAkxCVJUQgkt%26id%3D17%26url%3Dhttps%253A%252F%252Fizhongchou.taobao.com%252Fdreamdetail.htm%253Fspm%253Da215p.1472805.0.0.bYhb6h%2526id%253D10069812%2526qq-pf-to%253Dpcqq.c2c%26sina_sign%3D60d6ec8e41f7e8b1&amp;sign=2c6496a891c1ea8c" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d5.sina.com.cn/pfpghc2/201603/30/1e640aac7b48421396bd7f5539e46c61.jpg" style="width:300px;height:250px;border:0" alt="http://d5.sina.com.cn/pfpghc2/201603/30/1e640aac7b48421396bd7f5539e46c61.jpg"></a></ins></ins></div><iframe id="IO_WEBPUSH3_LOCALCONN_IFRAME" src="http://woocall.sina.com.cn/lib/iframe/IO.WebPush3.localConn.htm" style="display: none;"></iframe><div class="real-time-window" style="display: none; position: fixed; left: 0px; bottom: 55px;"></div><iframe frameborder="0" style="display: none;"></iframe><div id="bdshare_s" style="display: block;"><iframe id="bdsIfr" style="position:absolute;display:none;z-index:9999;" frameborder="0"></iframe><div id="bdshare_l" style="display: none;"><div id="bdshare_l_c"><h6>分享到</h6><ul><li><a href="#" class="bds_mshare mshare">一键分享</a></li><li><a href="#" class="bds_qzone qqkj">QQ空间</a></li><li><a href="#" class="bds_tsina xlwb">新浪微博</a></li><li><a href="#" class="bds_bdysc bdysc">百度云收藏</a></li><li><a href="#" class="bds_renren rrw">人人网</a></li><li><a href="#" class="bds_tqq txwb">腾讯微博</a></li><li><a href="#" class="bds_bdxc bdxc">百度相册</a></li><li><a href="#" class="bds_kaixin001 kxw">开心网</a></li><li><a href="#" class="bds_tqf txpy">腾讯朋友</a></li><li><a href="#" class="bds_tieba bdtb">百度贴吧</a></li><li><a href="#" class="bds_douban db">豆瓣网</a></li><li><a href="#" class="bds_tsohu shwb">搜狐微博</a></li><li><a href="#" class="bds_bdhome bdhome">百度新首页</a></li><li><a href="#" class="bds_sqq sqq">QQ好友</a></li><li><a href="#" class="bds_thx thx">和讯微博</a></li><li><a href="#" class="bds_more">更多...</a></li></ul><p><a href="#" class="goWebsite">百度分享</a></p></div></div></div><div id="bdshare_s" style="display: block;"><iframe id="bdsIfr" style="position:absolute;display:none;z-index:9999;" frameborder="0"></iframe><div id="bdshare_l" style="display: none;"><div id="bdshare_l_c"><h6>分享到</h6><ul><li><a href="#" class="bds_mshare mshare">一键分享</a></li><li><a href="#" class="bds_qzone qqkj">QQ空间</a></li><li><a href="#" class="bds_tsina xlwb">新浪微博</a></li><li><a href="#" class="bds_bdysc bdysc">百度云收藏</a></li><li><a href="#" class="bds_renren rrw">人人网</a></li><li><a href="#" class="bds_tqq txwb">腾讯微博</a></li><li><a href="#" class="bds_bdxc bdxc">百度相册</a></li><li><a href="#" class="bds_kaixin001 kxw">开心网</a></li><li><a href="#" class="bds_tqf txpy">腾讯朋友</a></li><li><a href="#" class="bds_tieba bdtb">百度贴吧</a></li><li><a href="#" class="bds_douban db">豆瓣网</a></li><li><a href="#" class="bds_tsohu shwb">搜狐微博</a></li><li><a href="#" class="bds_bdhome bdhome">百度新首页</a></li><li><a href="#" class="bds_sqq sqq">QQ好友</a></li><li><a href="#" class="bds_thx thx">和讯微博</a></li><li><a href="#" class="bds_more">更多...</a></li></ul><p><a href="#" class="goWebsite">百度分享</a></p></div></div></div><div class="side-ad-20150402 side-ad-20150402-resize" style="display: block;"><a class="side-ad-20150402-img" href="http://sax.sina.com.cn/click?type=nonstd&amp;t=REowMDAxMTIyMA%3D%3D&amp;sign=e14173835b1372ce&amp;url=http%3A%2F%2Fwsgs.dxzq.net%3A8080%2Fgaoshou%2Fawards.jsp%23award" target="_blank"><img src="http://n.sinaimg.cn/finance/fed3bc0b/20160316/20160316%EF%BC%88110x145%EF%BC%89.png" width="110" height="145"></a><a href="javascript:;" class="side-ad-20150402-close" title="关闭" suda-uatrack="key=ad_close2015&amp;value=finance_ad_close2015">关闭</a></div><!-- body code begin -->

<!-- SUDA_CODE_START -->
<script type="text/javascript">
//<!--
(function(){var an="V=2.1.16";var ah=window,F=document,s=navigator,W=s.userAgent,ao=ah.screen,j=ah.location.href;var aD="https:"==ah.location.protocol?"https://s":"http://",ay="beacon.sina.com.cn";var N=aD+ay+"/a.gif?",z=aD+ay+"/g.gif?",R=aD+ay+"/f.gif?",ag=aD+ay+"/e.gif?",aB=aD+"beacon.sinauda.com/i.gif?";var aA=F.referrer.toLowerCase();var aa="SINAGLOBAL",Y="FSINAGLOBAL",H="Apache",P="ULV",l="SUP",aE="UOR",E="_s_acc",X="_s_tentry",n=false,az=false,B=(document.domain=="sina.com.cn")?true:false;var o=0;var aG=false,A=false;var al="";var m=16777215,Z=0,C,K=0;var r="",b="",a="";var M=[],S=[],I=[];var u=0;var v=0;var p="";var am=false;var w=false;function O(){var e=document.createElement("iframe");e.src=aD+ay+"/data.html?"+new Date().getTime();e.id="sudaDataFrame";e.style.height="0px";e.style.width="1px";e.style.overflow="hidden";e.frameborder="0";e.scrolling="no";document.getElementsByTagName("head")[0].appendChild(e)}function k(){var e=document.createElement("iframe");e.src=aD+ay+"/ckctl.html";e.id="ckctlFrame";e.style.height="0px";e.style.width="1px";e.style.overflow="hidden";e.frameborder="0";e.scrolling="no";document.getElementsByTagName("head")[0].appendChild(e)}function q(){var e=document.createElement("script");e.src=aD+ay+"/h.js";document.getElementsByTagName("head")[0].appendChild(e)}function h(aH,i){var D=F.getElementsByName(aH);var e=(i>0)?i:0;return(D.length>e)?D[e].content:""}function aF(){var aJ=F.getElementsByName("sudameta");var aR=[];for(var aO=0;aO<aJ.length;aO++){var aK=aJ[aO].content;if(aK){if(aK.indexOf(";")!=-1){var D=aK.split(";");for(var aH=0;aH<D.length;aH++){var aP=aw(D[aH]);if(!aP){continue}aR.push(aP)}}else{aR.push(aK)}}}var aM=F.getElementsByTagName("meta");for(var aO=0,aI=aM.length;aO<aI;aO++){var aN=aM[aO];if(aN.name=="tags"){aR.push("content_tags:"+encodeURI(aN.content))}}var aL=t("vjuids");aR.push("vjuids:"+aL);var e="";var aQ=j.indexOf("#");if(aQ!=-1){e=escape(j.substr(aQ+1));aR.push("hashtag:"+e)}return aR}function V(aK,D,aI,aH){if(aK==""){return""}aH=(aH=="")?"=":aH;D+=aH;var aJ=aK.indexOf(D);if(aJ<0){return""}aJ+=D.length;var i=aK.indexOf(aI,aJ);if(i<aJ){i=aK.length}return aK.substring(aJ,i)}function t(e){if(undefined==e||""==e){return""}return V(F.cookie,e,";","")}function at(aI,e,i,aH){if(e!=null){if((undefined==aH)||(null==aH)){aH="sina.com.cn"}if((undefined==i)||(null==i)||(""==i)){F.cookie=aI+"="+e+";domain="+aH+";path=/"}else{var D=new Date();var aJ=D.getTime();aJ=aJ+86400000*i;D.setTime(aJ);aJ=D.getTime();F.cookie=aI+"="+e+";domain="+aH+";expires="+D.toUTCString()+";path=/"}}}function f(D){try{var i=document.getElementById("sudaDataFrame").contentWindow.storage;return i.get(D)}catch(aH){return false}}function ar(D,aH){try{var i=document.getElementById("sudaDataFrame").contentWindow.storage;i.set(D,aH);return true}catch(aI){return false}}function L(){var aJ=15;var D=window.SUDA.etag;if(!B){return"-"}if(u==0){O();q()}if(D&&D!=undefined){w=true}ls_gid=f(aa);if(ls_gid===false||w==false){return false}else{am=true}if(ls_gid&&ls_gid.length>aJ){at(aa,ls_gid,3650);n=true;return ls_gid}else{if(D&&D.length>aJ){at(aa,D,3650);az=true}var i=0,aI=500;var aH=setInterval((function(){var e=t(aa);if(w){e=D}i+=1;if(i>3){clearInterval(aH)}if(e.length>aJ){clearInterval(aH);ar(aa,e)}}),aI);return w?D:t(aa)}}function U(e,aH,D){var i=e;if(i==null){return false}aH=aH||"click";if((typeof D).toLowerCase()!="function"){return}if(i.attachEvent){i.attachEvent("on"+aH,D)}else{if(i.addEventListener){i.addEventListener(aH,D,false)}else{i["on"+aH]=D}}return true}function af(){if(window.event!=null){return window.event}else{if(window.event){return window.event}var D=arguments.callee.caller;var i;var aH=0;while(D!=null&&aH<40){i=D.arguments[0];if(i&&(i.constructor==Event||i.constructor==MouseEvent||i.constructor==KeyboardEvent)){return i}aH++;D=D.caller}return i}}function g(i){i=i||af();if(!i.target){i.target=i.srcElement;i.pageX=i.x;i.pageY=i.y}if(typeof i.layerX=="undefined"){i.layerX=i.offsetX}if(typeof i.layerY=="undefined"){i.layerY=i.offsetY}return i}function aw(aH){if(typeof aH!=="string"){throw"trim need a string as parameter"}var e=aH.length;var D=0;var i=/(\u3000|\s|\t|\u00A0)/;while(D<e){if(!i.test(aH.charAt(D))){break}D+=1}while(e>D){if(!i.test(aH.charAt(e-1))){break}e-=1}return aH.slice(D,e)}function c(e){return Object.prototype.toString.call(e)==="[object Array]"}function J(aH,aL){var aN=aw(aH).split("&");var aM={};var D=function(i){if(aL){try{return decodeURIComponent(i)}catch(aP){return i}}else{return i}};for(var aJ=0,aK=aN.length;aJ<aK;aJ++){if(aN[aJ]){var aI=aN[aJ].split("=");var e=aI[0];var aO=aI[1];if(aI.length<2){aO=e;e="$nullName"}if(!aM[e]){aM[e]=D(aO)}else{if(c(aM[e])!=true){aM[e]=[aM[e]]}aM[e].push(D(aO))}}}return aM}function ac(D,aI){for(var aH=0,e=D.length;aH<e;aH++){aI(D[aH],aH)}}function ak(i){var e=new RegExp("^http(?:s)?://([^/]+)","im");if(i.match(e)){return i.match(e)[1].toString()}else{return""}}function aj(aO){try{var aL="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";var D="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=";var aQ=function(e){var aR="",aS=0;for(;aS<e.length;aS++){aR+="%"+aH(e[aS])}return decodeURIComponent(aR)};var aH=function(e){var i="0"+e.toString(16);return i.length<=2?i:i.substr(1)};var aP=function(aY,aV,aR){if(typeof(aY)=="string"){aY=aY.split("")}var aX=function(a7,a9){for(var a8=0;a8<a7.length;a8++){if(a7[a8]==a9){return a8}}return -1};var aS=[];var a6,a4,a1="";var a5,a3,a0,aZ="";if(aY.length%4!=0){}var e=/[^A-Za-z0-9\+\/\=]/g;var a2=aL.split("");if(aV=="urlsafe"){e=/[^A-Za-z0-9\-_\=]/g;a2=D.split("")}var aU=0;if(aV=="binnary"){a2=[];for(aU=0;aU<=64;aU++){a2[aU]=aU+128}}if(aV!="binnary"&&e.exec(aY.join(""))){return aR=="array"?[]:""}aU=0;do{a5=aX(a2,aY[aU++]);a3=aX(a2,aY[aU++]);a0=aX(a2,aY[aU++]);aZ=aX(a2,aY[aU++]);a6=(a5<<2)|(a3>>4);a4=((a3&15)<<4)|(a0>>2);a1=((a0&3)<<6)|aZ;aS.push(a6);if(a0!=64&&a0!=-1){aS.push(a4)}if(aZ!=64&&aZ!=-1){aS.push(a1)}a6=a4=a1="";a5=a3=a0=aZ=""}while(aU<aY.length);if(aR=="array"){return aS}var aW="",aT=0;for(;aT<aS.lenth;aT++){aW+=String.fromCharCode(aS[aT])}return aW};var aI=[];var aN=aO.substr(0,3);var aK=aO.substr(3);switch(aN){case"v01":for(var aJ=0;aJ<aK.length;aJ+=2){aI.push(parseInt(aK.substr(aJ,2),16))}return decodeURIComponent(aQ(aP(aI,"binnary","array")));break;case"v02":aI=aP(aK,"urlsafe","array");return aQ(aP(aI,"binnary","array"));break;default:return decodeURIComponent(aO)}}catch(aM){return""}}var ap={screenSize:function(){return(m&8388608==8388608)?ao.width+"x"+ao.height:""},colorDepth:function(){return(m&4194304==4194304)?ao.colorDepth:""},appCode:function(){return(m&2097152==2097152)?s.appCodeName:""},appName:function(){return(m&1048576==1048576)?((s.appName.indexOf("Microsoft Internet Explorer")>-1)?"MSIE":s.appName):""},cpu:function(){return(m&524288==524288)?(s.cpuClass||s.oscpu):""},platform:function(){return(m&262144==262144)?(s.platform):""},jsVer:function(){if(m&131072!=131072){return""}var aI,e,aK,D=1,aH=0,i=(s.appName.indexOf("Microsoft Internet Explorer")>-1)?"MSIE":s.appName,aJ=s.appVersion;if("MSIE"==i){e="MSIE";aI=aJ.indexOf(e);if(aI>=0){aK=window.parseInt(aJ.substring(aI+5));if(3<=aK){D=1.1;if(4<=aK){D=1.3}}}}else{if(("Netscape"==i)||("Opera"==i)||("Mozilla"==i)){D=1.3;e="Netscape6";aI=aJ.indexOf(e);if(aI>=0){D=1.5}}}return D},network:function(){if(m&65536!=65536){return""}var i="";i=(s.connection&&s.connection.type)?s.connection.type:i;try{F.body.addBehavior("#default#clientCaps");i=F.body.connectionType}catch(D){i="unkown"}return i},language:function(){return(m&32768==32768)?(s.systemLanguage||s.language):""},timezone:function(){return(m&16384==16384)?(new Date().getTimezoneOffset()/60):""},flashVer:function(){if(m&8192!=8192){return""}var aK=s.plugins,aH,aL,aN;if(aK&&aK.length){for(var aJ in aK){aL=aK[aJ];if(aL.description==null){continue}if(aH!=null){break}aN=aL.description.toLowerCase();if(aN.indexOf("flash")!=-1){aH=aL.version?parseInt(aL.version):aN.match(/\d+/);continue}}}else{if(window.ActiveXObject){for(var aI=10;aI>=2;aI--){try{var D=new ActiveXObject("ShockwaveFlash.ShockwaveFlash."+aI);if(D){aH=aI;break}}catch(aM){}}}else{if(W.indexOf("webtv/2.5")!=-1){aH=3}else{if(W.indexOf("webtv")!=-1){aH=2}}}}return aH},javaEnabled:function(){if(m&4096!=4096){return""}var D=s.plugins,i=s.javaEnabled(),aH,aI;if(i==true){return 1}if(D&&D.length){for(var e in D){aH=D[e];if(aH.description==null){continue}if(i!=null){break}aI=aH.description.toLowerCase();if(aI.indexOf("java plug-in")!=-1){i=parseInt(aH.version);continue}}}else{if(window.ActiveXObject){i=(new ActiveXObject("JavaWebStart.IsInstalled")!=null)}}return i?1:0}};var ad={pageId:function(i){var D=i||r,aK="-9999-0-0-1";if((undefined==D)||(""==D)){try{var aH=h("publishid");if(""!=aH){var aJ=aH.split(",");if(aJ.length>0){if(aJ.length>=3){aK="-9999-0-"+aJ[1]+"-"+aJ[2]}D=aJ[0]}}else{D="0"}}catch(aI){D="0"}D=D+aK}return D},sessionCount:function(){var e=t("_s_upa");if(e==""){e=0}return e},excuteCount:function(){return SUDA.sudaCount},referrer:function(){if(m&2048!=2048){return""}var e=/^[^\?&#]*.swf([\?#])?/;if((aA=="")||(aA.match(e))){var i=V(j,"ref","&","");if(i!=""){return escape(i)}}return escape(aA)},isHomepage:function(){if(m&1024!=1024){return""}var D="";try{F.body.addBehavior("#default#homePage");D=F.body.isHomePage(j)?"Y":"N"}catch(i){D="unkown"}return D},PGLS:function(){return(m&512==512)?h("stencil"):""},ZT:function(){if(m&256!=256){return""}var e=h("subjectid");e.replace(",",".");e.replace(";",",");return escape(e)},mediaType:function(){return(m&128==128)?h("mediaid"):""},domCount:function(){return(m&64==64)?F.getElementsByTagName("*").length:""},iframeCount:function(){return(m&32==32)?F.getElementsByTagName("iframe").length:""}};var av={visitorId:function(){var i=15;var e=t(aa);if(e.length>i&&u==0){return e}else{return}},fvisitorId:function(e){if(!e){var e=t(Y);return e}else{at(Y,e,3650)}},sessionId:function(){var e=t(H);if(""==e){var i=new Date();e=Math.random()*10000000000000+"."+i.getTime()}return e},flashCookie:function(e){if(e){}else{return p}},lastVisit:function(){var D=t(H);var aI=t(P);var aH=aI.split(":");var aJ="",i;if(aH.length>=6){if(D!=aH[4]){i=new Date();var e=new Date(window.parseInt(aH[0]));aH[1]=window.parseInt(aH[1])+1;if(i.getMonth()!=e.getMonth()){aH[2]=1}else{aH[2]=window.parseInt(aH[2])+1}if(((i.getTime()-e.getTime())/86400000)>=7){aH[3]=1}else{if(i.getDay()<e.getDay()){aH[3]=1}else{aH[3]=window.parseInt(aH[3])+1}}aJ=aH[0]+":"+aH[1]+":"+aH[2]+":"+aH[3];aH[5]=aH[0];aH[0]=i.getTime();at(P,aH[0]+":"+aH[1]+":"+aH[2]+":"+aH[3]+":"+D+":"+aH[5],360)}else{aJ=aH[5]+":"+aH[1]+":"+aH[2]+":"+aH[3]}}else{i=new Date();aJ=":1:1:1";at(P,i.getTime()+aJ+":"+D+":",360)}return aJ},userNick:function(){if(al!=""){return al}var D=unescape(t(l));if(D!=""){var i=V(D,"ag","&","");var e=V(D,"user","&","");var aH=V(D,"uid","&","");var aJ=V(D,"sex","&","");var aI=V(D,"dob","&","");al=i+":"+e+":"+aH+":"+aJ+":"+aI;return al}else{return""}},userOrigin:function(){if(m&4!=4){return""}var e=t(aE);var i=e.split(":");if(i.length>=2){return i[0]}else{return""}},advCount:function(){return(m&2==2)?t(E):""},setUOR:function(){var aL=t(aE),aP="",i="",aO="",aI="",aM=j.toLowerCase(),D=F.referrer.toLowerCase();var aQ=/[&|?]c=spr(_[A-Za-z0-9]{1,}){3,}/;var aK=new Date();if(aM.match(aQ)){aO=aM.match(aQ)[0]}else{if(D.match(aQ)){aO=D.match(aQ)[0]}}if(aO!=""){aO=aO.substr(3)+":"+aK.getTime()}if(aL==""){if(t(P)==""){aP=ak(D);i=ak(aM)}at(aE,aP+","+i+","+aO,365)}else{var aJ=0,aN=aL.split(",");if(aN.length>=1){aP=aN[0]}if(aN.length>=2){i=aN[1]}if(aN.length>=3){aI=aN[2]}if(aO!=""){aJ=1}else{var aH=aI.split(":");if(aH.length>=2){var e=new Date(window.parseInt(aH[1]));if(e.getTime()<(aK.getTime()-86400000*30)){aJ=1}}}if(aJ){at(aE,aP+","+i+","+aO,365)}}},setAEC:function(e){if(""==e){return}var i=t(E);if(i.indexOf(e+",")<0){i=i+e+","}at(E,i,7)},ssoInfo:function(){var D=unescape(aj(t("sso_info")));if(D!=""){if(D.indexOf("uid=")!=-1){var i=V(D,"uid","&","");return escape("uid:"+i)}else{var e=V(D,"u","&","");return escape("u:"+unescape(e))}}else{return""}},subp:function(){return t("SUBP")}};var ai={CI:function(){var e=["sz:"+ap.screenSize(),"dp:"+ap.colorDepth(),"ac:"+ap.appCode(),"an:"+ap.appName(),"cpu:"+ap.cpu(),"pf:"+ap.platform(),"jv:"+ap.jsVer(),"ct:"+ap.network(),"lg:"+ap.language(),"tz:"+ap.timezone(),"fv:"+ap.flashVer(),"ja:"+ap.javaEnabled()];return"CI="+e.join("|")},PI:function(e){var i=["pid:"+ad.pageId(e),"st:"+ad.sessionCount(),"et:"+ad.excuteCount(),"ref:"+ad.referrer(),"hp:"+ad.isHomepage(),"PGLS:"+ad.PGLS(),"ZT:"+ad.ZT(),"MT:"+ad.mediaType(),"keys:","dom:"+ad.domCount(),"ifr:"+ad.iframeCount()];return"PI="+i.join("|")},UI:function(){var e=["vid:"+av.visitorId(),"sid:"+av.sessionId(),"lv:"+av.lastVisit(),"un:"+av.userNick(),"uo:"+av.userOrigin(),"ae:"+av.advCount(),"lu:"+av.fvisitorId(),"si:"+av.ssoInfo(),"rs:"+(n?1:0),"dm:"+(B?1:0),"su:"+av.subp()];return"UI="+e.join("|")},EX:function(i,e){if(m&1!=1){return""}i=(null!=i)?i||"":b;e=(null!=e)?e||"":a;return"EX=ex1:"+i+"|ex2:"+e},MT:function(){return"MT="+aF().join("|")},V:function(){return an},R:function(){return"gUid_"+new Date().getTime()}};function ax(){var aK="-",aH=F.referrer.toLowerCase(),D=j.toLowerCase();if(""==t(X)){if(""!=aH){aK=ak(aH)}at(X,aK,"","weibo.com")}var aI=/weibo.com\/reg.php/;if(D.match(aI)){var aJ=V(unescape(D),"sharehost","&","");var i=V(unescape(D),"appkey","&","");if(""!=aJ){at(X,aJ,"","weibo.com")}at("appkey",i,"","weibo.com")}}function d(e,i){G(e,i)}function G(i,D){D=D||{};var e=new Image(),aH;if(D&&D.callback&&typeof D.callback=="function"){e.onload=function(){clearTimeout(aH);aH=null;D.callback(true)}}SUDA.img=e;e.src=i;aH=setTimeout(function(){if(D&&D.callback&&typeof D.callback=="function"){D.callback(false);e.onload=null}},D.timeout||2000)}function x(e,aH,D,aI){SUDA.sudaCount++;if(!av.visitorId()&&!L()){if(u<3){u++;setTimeout(x,500);return}}var i=N+[ai.V(),ai.CI(),ai.PI(e),ai.UI(),ai.MT(),ai.EX(aH,D),ai.R()].join("&");G(i,aI);if(window.location.host.search("auto.sina.com.cn")>=0){wrating_url="http://m.wrating.com/m.gif?a=&c=860010-2370010112&mcookie="+av.visitorId()+"&"+ai.R()+"=";G(wrating_url)}}function y(e,D,i){if(aG||A){return}if(SUDA.sudaCount!=0){return}x(e,D,i)}function ab(e,aH){if((""==e)||(undefined==e)){return}av.setAEC(e);if(0==aH){return}var D="AcTrack||"+t(aa)+"||"+t(H)+"||"+av.userNick()+"||"+e+"||";var i=ag+D+"&gUid_"+new Date().getTime();d(i)}function aq(aI,e,i,aJ){aJ=aJ||{};if(!i){i=""}else{i=escape(i)}var aH="UATrack||"+t(aa)+"||"+t(H)+"||"+av.userNick()+"||"+aI+"||"+e+"||"+ad.referrer()+"||"+i+"||"+(aJ.realUrl||"")+"||"+(aJ.ext||"");var D=ag+aH+"&gUid_"+new Date().getTime();d(D,aJ)}function aC(aK){var i=g(aK);var aI=i.target;var aH="",aL="",D="";var aJ;if(aI!=null&&aI.getAttribute&&(!aI.getAttribute("suda-uatrack")&&!aI.getAttribute("suda-actrack")&&!aI.getAttribute("suda-data"))){while(aI!=null&&aI.getAttribute&&(!!aI.getAttribute("suda-uatrack")||!!aI.getAttribute("suda-actrack")||!!aI.getAttribute("suda-data"))==false){if(aI==F.body){return}aI=aI.parentNode}}if(aI==null||aI.getAttribute==null){return}aH=aI.getAttribute("suda-actrack")||"";aL=aI.getAttribute("suda-uatrack")||aI.getAttribute("suda-data")||"";sudaUrls=aI.getAttribute("suda-urls")||"";if(aL){aJ=J(aL);if(aI.tagName.toLowerCase()=="a"){D=aI.href}opts={};opts.ext=(aJ.ext||"");aJ.key&&SUDA.uaTrack&&SUDA.uaTrack(aJ.key,aJ.value||aJ.key,D,opts)}if(aH){aJ=J(aH);aJ.key&&SUDA.acTrack&&SUDA.acTrack(aJ.key,aJ.value||aJ.key)}}if(window.SUDA&&Object.prototype.toString.call(window.SUDA)==="[object Array]"){for(var Q=0,ae=SUDA.length;Q<ae;Q++){switch(SUDA[Q][0]){case"setGatherType":m=SUDA[Q][1];break;case"setGatherInfo":r=SUDA[Q][1]||r;b=SUDA[Q][2]||b;a=SUDA[Q][3]||a;break;case"setPerformance":Z=SUDA[Q][1];break;case"setPerformanceFilter":C=SUDA[Q][1];break;case"setPerformanceInterval":K=SUDA[Q][1]*1||0;K=isNaN(K)?0:K;break;case"setGatherMore":M.push(SUDA[Q].slice(1));break;case"acTrack":S.push(SUDA[Q].slice(1));break;case"uaTrack":I.push(SUDA[Q].slice(1));break}}}aG=(function(D,i){if(ah.top==ah){return false}else{try{if(F.body.clientHeight==0){return false}return((F.body.clientHeight>=D)&&(F.body.clientWidth>=i))?false:true}catch(aH){return true}}})(320,240);A=(function(){return false})();av.setUOR();var au=av.sessionId();window.SUDA=window.SUDA||[];SUDA.sudaCount=SUDA.sudaCount||0;SUDA.log=function(){x.apply(null,arguments)};SUDA.acTrack=function(){ab.apply(null,arguments)};SUDA.uaTrack=function(){aq.apply(null,arguments)};U(F.body,"click",aC);window.GB_SUDA=SUDA;GB_SUDA._S_pSt=function(){};GB_SUDA._S_acTrack=function(){ab.apply(null,arguments)};GB_SUDA._S_uaTrack=function(){aq.apply(null,arguments)};window._S_pSt=function(){};window._S_acTrack=function(){ab.apply(null,arguments)};window._S_uaTrack=function(){aq.apply(null,arguments)};window._S_PID_="";if(!window.SUDA.disableClickstream){y()}try{k()}catch(T){}})();
//-->
</script>
<noscript>
&lt;div style='position:absolute;top:0;left:0;width:0;height:0;visibility:hidden'&gt;&lt;img width=0 height=0 src='http://beacon.sina.com.cn/a.gif?noScript' border='0' alt='' /&gt;&lt;/div&gt;
</noscript>
<!-- SUDA_CODE_END -->

<!-- SSO_GETCOOKIE_START -->
<script type="text/javascript">var sinaSSOManager=sinaSSOManager||{};sinaSSOManager.getSinaCookie=function(){function dc(u){if(u==undefined){return""}var decoded=decodeURIComponent(u);return decoded=="null"?"":decoded}function ps(str){var arr=str.split("&");var arrtmp;var arrResult={};for(var i=0;i<arr.length;i++){arrtmp=arr[i].split("=");arrResult[arrtmp[0]]=dc(arrtmp[1])}return arrResult}function gC(name){var Res=eval("/"+name+"=([^;]+)/").exec(document.cookie);return Res==null?null:Res[1]}var sup=dc(gC("SUP"));if(!sup){sup=dc(gC("SUR"))}if(!sup){return null}return ps(sup)};</script>
<!-- SSO_GETCOOKIE_END -->

<script type="text/javascript">new function(r,s,t){this.a=function(n,t,e){if(window.addEventListener){n.addEventListener(t,e,false);}else if(window.attachEvent){n.attachEvent("on"+t,e);}};this.b=function(f){var t=this;return function(){return f.apply(t,arguments);};};this.c=function(){var f=document.getElementsByTagName("form");for(var i=0;i<f.length;i++){var o=f[i].action;if(this.r.test(o)){f[i].action=o.replace(this.r,this.s);}}};this.r=r;this.s=s;this.d=setInterval(this.b(this.c),t);this.a(window,"load",this.b(function(){this.c();clearInterval(this.d);}));}(/http:\/\/www\.google\.c(om|n)\/search/, "http://keyword.sina.com.cn/searchword.php", 250);</script>
<!-- body code end -->
<!-- body code begin 1 -->

<!-- SUDA_CODE_START -->
<script type="text/javascript">
    //<!--
    (function(){var an="V=2.1.15";var ah=window,F=document,s=navigator,W=s.userAgent,ao=ah.screen,j=ah.location.href;var aD="https:"==ah.location.protocol?"https://s":"http://",ay="beacon.sina.com.cn";var N=aD+ay+"/a.gif?",z=aD+ay+"/g.gif?",R=aD+ay+"/f.gif?",ag=aD+ay+"/e.gif?",aB=aD+"beacon.sinauda.com/i.gif?";var aA=F.referrer.toLowerCase();var aa="SINAGLOBAL",Y="FSINAGLOBAL",H="Apache",P="ULV",l="SUP",aE="UOR",E="_s_acc",X="_s_tentry",n=false,az=false,B=(document.domain=="sina.com.cn")?true:false;var o=0;var aG=false,A=false;var al="";var m=16777215,Z=0,C,K=0;var r="",b="",a="";var M=[],S=[],I=[];var u=0;var v=0;var p="";var am=false;var w=false;function O(){var e=document.createElement("iframe");e.src=aD+ay+"/data.html?"+new Date().getTime();e.id="sudaDataFrame";e.style.height="0px";e.style.width="1px";e.style.overflow="hidden";e.frameborder="0";e.scrolling="no";document.getElementsByTagName("head")[0].appendChild(e)}function k(){var e=document.createElement("iframe");e.src=aD+ay+"/ckctl.html";e.id="ckctlFrame";e.style.height="0px";e.style.width="1px";e.style.overflow="hidden";e.frameborder="0";e.scrolling="no";document.getElementsByTagName("head")[0].appendChild(e)}function q(){var e=document.createElement("script");e.src=aD+ay+"/h.js";document.getElementsByTagName("head")[0].appendChild(e)}function h(aH,i){var D=F.getElementsByName(aH);var e=(i>0)?i:0;return(D.length>e)?D[e].content:""}function aF(){var aJ=F.getElementsByName("sudameta");var aR=[];for(var aO=0;aO<aJ.length;aO++){var aK=aJ[aO].content;if(aK){if(aK.indexOf(";")!=-1){var D=aK.split(";");for(var aH=0;aH<D.length;aH++){var aP=aw(D[aH]);if(!aP){continue}aR.push(aP)}}else{aR.push(aK)}}}var aM=F.getElementsByTagName("meta");for(var aO=0,aI=aM.length;aO<aI;aO++){var aN=aM[aO];if(aN.name=="tags"){aR.push("content_tags:"+encodeURI(aN.content))}}var aL=t("vjuids");aR.push("vjuids:"+aL);var e="";var aQ=j.indexOf("#");if(aQ!=-1){e=escape(j.substr(aQ+1))}aR.push("hashtag:"+e);return aR}function V(aK,D,aI,aH){if(aK==""){return""}aH=(aH=="")?"=":aH;D+=aH;var aJ=aK.indexOf(D);if(aJ<0){return""}aJ+=D.length;var i=aK.indexOf(aI,aJ);if(i<aJ){i=aK.length}return aK.substring(aJ,i)}function t(e){if(undefined==e||""==e){return""}return V(F.cookie,e,";","")}function at(aI,e,i,aH){if(e!=null){if((undefined==aH)||(null==aH)){aH="sina.com.cn"}if((undefined==i)||(null==i)||(""==i)){F.cookie=aI+"="+e+";domain="+aH+";path=/"}else{var D=new Date();var aJ=D.getTime();aJ=aJ+86400000*i;D.setTime(aJ);aJ=D.getTime();F.cookie=aI+"="+e+";domain="+aH+";expires="+D.toUTCString()+";path=/"}}}function f(D){try{var i=document.getElementById("sudaDataFrame").contentWindow.storage;return i.get(D)}catch(aH){return false}}function ar(D,aH){try{var i=document.getElementById("sudaDataFrame").contentWindow.storage;i.set(D,aH);return true}catch(aI){return false}}function L(){var aJ=15;var D=window.SUDA.etag;if(!B){return"-"}if(u==0){O();q()}if(D&&D!=undefined){w=true}ls_gid=f(aa);if(ls_gid===false||w==false){return false}else{am=true}if(ls_gid&&ls_gid.length>aJ){at(aa,ls_gid,3650);n=true;return ls_gid}else{if(D&&D.length>aJ){at(aa,D,3650);az=true}var i=0,aI=500;var aH=setInterval((function(){var e=t(aa);if(w){e=D}i+=1;if(i>3){clearInterval(aH)}if(e.length>aJ){clearInterval(aH);ar(aa,e)}}),aI);return w?D:t(aa)}}function U(e,aH,D){var i=e;if(i==null){return false}aH=aH||"click";if((typeof D).toLowerCase()!="function"){return}if(i.attachEvent){i.attachEvent("on"+aH,D)}else{if(i.addEventListener){i.addEventListener(aH,D,false)}else{i["on"+aH]=D}}return true}function af(){if(window.event!=null){return window.event}else{if(window.event){return window.event}var D=arguments.callee.caller;var i;var aH=0;while(D!=null&&aH<40){i=D.arguments[0];if(i&&(i.constructor==Event||i.constructor==MouseEvent||i.constructor==KeyboardEvent)){return i}aH++;D=D.caller}return i}}function g(i){i=i||af();if(!i.target){i.target=i.srcElement;i.pageX=i.x;i.pageY=i.y}if(typeof i.layerX=="undefined"){i.layerX=i.offsetX}if(typeof i.layerY=="undefined"){i.layerY=i.offsetY}return i}function aw(aH){if(typeof aH!=="string"){throw"trim need a string as parameter"}var e=aH.length;var D=0;var i=/(\u3000|\s|\t|\u00A0)/;while(D<e){if(!i.test(aH.charAt(D))){break}D+=1}while(e>D){if(!i.test(aH.charAt(e-1))){break}e-=1}return aH.slice(D,e)}function c(e){return Object.prototype.toString.call(e)==="[object Array]"}function J(aH,aL){var aN=aw(aH).split("&");var aM={};var D=function(i){if(aL){try{return decodeURIComponent(i)}catch(aP){return i}}else{return i}};for(var aJ=0,aK=aN.length;aJ<aK;aJ++){if(aN[aJ]){var aI=aN[aJ].split("=");var e=aI[0];var aO=aI[1];if(aI.length<2){aO=e;e="$nullName"}if(!aM[e]){aM[e]=D(aO)}else{if(c(aM[e])!=true){aM[e]=[aM[e]]}aM[e].push(D(aO))}}}return aM}function ac(D,aI){for(var aH=0,e=D.length;aH<e;aH++){aI(D[aH],aH)}}function ak(i){var e=new RegExp("^http(?:s)?://([^/]+)","im");if(i.match(e)){return i.match(e)[1].toString()}else{return""}}function aj(aO){try{var aL="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";var D="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=";var aQ=function(e){var aR="",aS=0;for(;aS<e.length;aS++){aR+="%"+aH(e[aS])}return decodeURIComponent(aR)};var aH=function(e){var i="0"+e.toString(16);return i.length<=2?i:i.substr(1)};var aP=function(aY,aV,aR){if(typeof(aY)=="string"){aY=aY.split("")}var aX=function(a7,a9){for(var a8=0;a8<a7.length;a8++){if(a7[a8]==a9){return a8}}return -1};var aS=[];var a6,a4,a1="";var a5,a3,a0,aZ="";if(aY.length%4!=0){}var e=/[^A-Za-z0-9\+\/\=]/g;var a2=aL.split("");if(aV=="urlsafe"){e=/[^A-Za-z0-9\-_\=]/g;a2=D.split("")}var aU=0;if(aV=="binnary"){a2=[];for(aU=0;aU<=64;aU++){a2[aU]=aU+128}}if(aV!="binnary"&&e.exec(aY.join(""))){return aR=="array"?[]:""}aU=0;do{a5=aX(a2,aY[aU++]);a3=aX(a2,aY[aU++]);a0=aX(a2,aY[aU++]);aZ=aX(a2,aY[aU++]);a6=(a5<<2)|(a3>>4);a4=((a3&15)<<4)|(a0>>2);a1=((a0&3)<<6)|aZ;aS.push(a6);if(a0!=64&&a0!=-1){aS.push(a4)}if(aZ!=64&&aZ!=-1){aS.push(a1)}a6=a4=a1="";a5=a3=a0=aZ=""}while(aU<aY.length);if(aR=="array"){return aS}var aW="",aT=0;for(;aT<aS.lenth;aT++){aW+=String.fromCharCode(aS[aT])}return aW};var aI=[];var aN=aO.substr(0,3);var aK=aO.substr(3);switch(aN){case"v01":for(var aJ=0;aJ<aK.length;aJ+=2){aI.push(parseInt(aK.substr(aJ,2),16))}return decodeURIComponent(aQ(aP(aI,"binnary","array")));break;case"v02":aI=aP(aK,"urlsafe","array");return aQ(aP(aI,"binnary","array"));break;default:return decodeURIComponent(aO)}}catch(aM){return""}}var ap={screenSize:function(){return(m&8388608==8388608)?ao.width+"x"+ao.height:""},colorDepth:function(){return(m&4194304==4194304)?ao.colorDepth:""},appCode:function(){return(m&2097152==2097152)?s.appCodeName:""},appName:function(){return(m&1048576==1048576)?((s.appName.indexOf("Microsoft Internet Explorer")>-1)?"MSIE":s.appName):""},cpu:function(){return(m&524288==524288)?(s.cpuClass||s.oscpu):""},platform:function(){return(m&262144==262144)?(s.platform):""},jsVer:function(){if(m&131072!=131072){return""}var aI,e,aK,D=1,aH=0,i=(s.appName.indexOf("Microsoft Internet Explorer")>-1)?"MSIE":s.appName,aJ=s.appVersion;if("MSIE"==i){e="MSIE";aI=aJ.indexOf(e);if(aI>=0){aK=window.parseInt(aJ.substring(aI+5));if(3<=aK){D=1.1;if(4<=aK){D=1.3}}}}else{if(("Netscape"==i)||("Opera"==i)||("Mozilla"==i)){D=1.3;e="Netscape6";aI=aJ.indexOf(e);if(aI>=0){D=1.5}}}return D},network:function(){if(m&65536!=65536){return""}var i="";i=(s.connection&&s.connection.type)?s.connection.type:i;try{F.body.addBehavior("#default#clientCaps");i=F.body.connectionType}catch(D){i="unkown"}return i},language:function(){return(m&32768==32768)?(s.systemLanguage||s.language):""},timezone:function(){return(m&16384==16384)?(new Date().getTimezoneOffset()/60):""},flashVer:function(){if(m&8192!=8192){return""}var aK=s.plugins,aH,aL,aN;if(aK&&aK.length){for(var aJ in aK){aL=aK[aJ];if(aL.description==null){continue}if(aH!=null){break}aN=aL.description.toLowerCase();if(aN.indexOf("flash")!=-1){aH=aL.version?parseInt(aL.version):aN.match(/\d+/);continue}}}else{if(window.ActiveXObject){for(var aI=10;aI>=2;aI--){try{var D=new ActiveXObject("ShockwaveFlash.ShockwaveFlash."+aI);if(D){aH=aI;break}}catch(aM){}}}else{if(W.indexOf("webtv/2.5")!=-1){aH=3}else{if(W.indexOf("webtv")!=-1){aH=2}}}}return aH},javaEnabled:function(){if(m&4096!=4096){return""}var D=s.plugins,i=s.javaEnabled(),aH,aI;if(i==true){return 1}if(D&&D.length){for(var e in D){aH=D[e];if(aH.description==null){continue}if(i!=null){break}aI=aH.description.toLowerCase();if(aI.indexOf("java plug-in")!=-1){i=parseInt(aH.version);continue}}}else{if(window.ActiveXObject){i=(new ActiveXObject("JavaWebStart.IsInstalled")!=null)}}return i?1:0}};var ad={pageId:function(i){var D=i||r,aK="-9999-0-0-1";if((undefined==D)||(""==D)){try{var aH=h("publishid");if(""!=aH){var aJ=aH.split(",");if(aJ.length>0){if(aJ.length>=3){aK="-9999-0-"+aJ[1]+"-"+aJ[2]}D=aJ[0]}}else{D="0"}}catch(aI){D="0"}D=D+aK}return D},sessionCount:function(){var e=t("_s_upa");if(e==""){e=0}return e},excuteCount:function(){return SUDA.sudaCount},referrer:function(){if(m&2048!=2048){return""}var e=/^[^\?&#]*.swf([\?#])?/;if((aA=="")||(aA.match(e))){var i=V(j,"ref","&","");if(i!=""){return escape(i)}}return escape(aA)},isHomepage:function(){if(m&1024!=1024){return""}var D="";try{F.body.addBehavior("#default#homePage");D=F.body.isHomePage(j)?"Y":"N"}catch(i){D="unkown"}return D},PGLS:function(){return(m&512==512)?h("stencil"):""},ZT:function(){if(m&256!=256){return""}var e=h("subjectid");e.replace(",",".");e.replace(";",",");return escape(e)},mediaType:function(){return(m&128==128)?h("mediaid"):""},domCount:function(){return(m&64==64)?F.getElementsByTagName("*").length:""},iframeCount:function(){return(m&32==32)?F.getElementsByTagName("iframe").length:""}};var av={visitorId:function(){var i=15;var e=t(aa);if(e.length>i&&u==0){return e}else{return}},fvisitorId:function(e){if(!e){var e=t(Y);return e}else{at(Y,e,3650)}},sessionId:function(){var e=t(H);if(""==e){var i=new Date();e=Math.random()*10000000000000+"."+i.getTime()}return e},flashCookie:function(e){if(e){}else{return p}},lastVisit:function(){var D=t(H);var aI=t(P);var aH=aI.split(":");var aJ="",i;if(aH.length>=6){if(D!=aH[4]){i=new Date();var e=new Date(window.parseInt(aH[0]));aH[1]=window.parseInt(aH[1])+1;if(i.getMonth()!=e.getMonth()){aH[2]=1}else{aH[2]=window.parseInt(aH[2])+1}if(((i.getTime()-e.getTime())/86400000)>=7){aH[3]=1}else{if(i.getDay()<e.getDay()){aH[3]=1}else{aH[3]=window.parseInt(aH[3])+1}}aJ=aH[0]+":"+aH[1]+":"+aH[2]+":"+aH[3];aH[5]=aH[0];aH[0]=i.getTime();at(P,aH[0]+":"+aH[1]+":"+aH[2]+":"+aH[3]+":"+D+":"+aH[5],360)}else{aJ=aH[5]+":"+aH[1]+":"+aH[2]+":"+aH[3]}}else{i=new Date();aJ=":1:1:1";at(P,i.getTime()+aJ+":"+D+":",360)}return aJ},userNick:function(){if(al!=""){return al}var D=unescape(t(l));if(D!=""){var i=V(D,"ag","&","");var e=V(D,"user","&","");var aH=V(D,"uid","&","");var aJ=V(D,"sex","&","");var aI=V(D,"dob","&","");al=i+":"+e+":"+aH+":"+aJ+":"+aI;return al}else{return""}},userOrigin:function(){if(m&4!=4){return""}var e=t(aE);var i=e.split(":");if(i.length>=2){return i[0]}else{return""}},advCount:function(){return(m&2==2)?t(E):""},setUOR:function(){var aL=t(aE),aP="",i="",aO="",aI="",aM=j.toLowerCase(),D=F.referrer.toLowerCase();var aQ=/[&|?]c=spr(_[A-Za-z0-9]{1,}){3,}/;var aK=new Date();if(aM.match(aQ)){aO=aM.match(aQ)[0]}else{if(D.match(aQ)){aO=D.match(aQ)[0]}}if(aO!=""){aO=aO.substr(3)+":"+aK.getTime()}if(aL==""){if(t(P)==""){aP=ak(D);i=ak(aM)}at(aE,aP+","+i+","+aO,365)}else{var aJ=0,aN=aL.split(",");if(aN.length>=1){aP=aN[0]}if(aN.length>=2){i=aN[1]}if(aN.length>=3){aI=aN[2]}if(aO!=""){aJ=1}else{var aH=aI.split(":");if(aH.length>=2){var e=new Date(window.parseInt(aH[1]));if(e.getTime()<(aK.getTime()-86400000*30)){aJ=1}}}if(aJ){at(aE,aP+","+i+","+aO,365)}}},setAEC:function(e){if(""==e){return}var i=t(E);if(i.indexOf(e+",")<0){i=i+e+","}at(E,i,7)},ssoInfo:function(){var D=unescape(aj(t("sso_info")));if(D!=""){if(D.indexOf("uid=")!=-1){var i=V(D,"uid","&","");return escape("uid:"+i)}else{var e=V(D,"u","&","");return escape("u:"+unescape(e))}}else{return""}},subp:function(){return t("SUBP")}};var ai={CI:function(){var e=["sz:"+ap.screenSize(),"dp:"+ap.colorDepth(),"ac:"+ap.appCode(),"an:"+ap.appName(),"cpu:"+ap.cpu(),"pf:"+ap.platform(),"jv:"+ap.jsVer(),"ct:"+ap.network(),"lg:"+ap.language(),"tz:"+ap.timezone(),"fv:"+ap.flashVer(),"ja:"+ap.javaEnabled()];return"CI="+e.join("|")},PI:function(e){var i=["pid:"+ad.pageId(e),"st:"+ad.sessionCount(),"et:"+ad.excuteCount(),"ref:"+ad.referrer(),"hp:"+ad.isHomepage(),"PGLS:"+ad.PGLS(),"ZT:"+ad.ZT(),"MT:"+ad.mediaType(),"keys:","dom:"+ad.domCount(),"ifr:"+ad.iframeCount()];return"PI="+i.join("|")},UI:function(){var e=["vid:"+av.visitorId(),"sid:"+av.sessionId(),"lv:"+av.lastVisit(),"un:"+av.userNick(),"uo:"+av.userOrigin(),"ae:"+av.advCount(),"lu:"+av.fvisitorId(),"si:"+av.ssoInfo(),"rs:"+(n?1:0),"dm:"+(B?1:0),"su:"+av.subp()];return"UI="+e.join("|")},EX:function(i,e){if(m&1!=1){return""}i=(null!=i)?i||"":b;e=(null!=e)?e||"":a;return"EX=ex1:"+i+"|ex2:"+e},MT:function(){return"MT="+aF().join("|")},V:function(){return an},R:function(){return"gUid_"+new Date().getTime()}};function ax(){var aK="-",aH=F.referrer.toLowerCase(),D=j.toLowerCase();if(""==t(X)){if(""!=aH){aK=ak(aH)}at(X,aK,"","weibo.com")}var aI=/weibo.com\/reg.php/;if(D.match(aI)){var aJ=V(unescape(D),"sharehost","&","");var i=V(unescape(D),"appkey","&","");if(""!=aJ){at(X,aJ,"","weibo.com")}at("appkey",i,"","weibo.com")}}function d(e,i){G(e,i)}function G(i,D){D=D||{};var e=new Image(),aH;if(D&&D.callback&&typeof D.callback=="function"){e.onload=function(){clearTimeout(aH);aH=null;D.callback(true)}}SUDA.img=e;e.src=i;aH=setTimeout(function(){if(D&&D.callback&&typeof D.callback=="function"){D.callback(false);e.onload=null}},D.timeout||2000)}function x(e,aH,D){SUDA.sudaCount++;if(!av.visitorId()&&!L()){if(u<3){u++;setTimeout(x,500);return}}var i=N+[ai.V(),ai.CI(),ai.PI(e),ai.UI(),ai.MT(),ai.EX(aH,D),ai.R()].join("&");G(i);if(window.location.host.search("auto.sina.com.cn")>=0){wrating_url="http://m.wrating.com/m.gif?a=&c=860010-2370010112&mcookie="+av.visitorId()+"&"+ai.R()+"=";G(wrating_url)}}function y(e,D,i){if(aG||A){return}if(SUDA.sudaCount!=0){return}x(e,D,i)}function ab(e,aH){if((""==e)||(undefined==e)){return}av.setAEC(e);if(0==aH){return}var D="AcTrack||"+t(aa)+"||"+t(H)+"||"+av.userNick()+"||"+e+"||";var i=ag+D+"&gUid_"+new Date().getTime();d(i)}function aq(aI,e,i,aJ){aJ=aJ||{};if(!i){i=""}else{i=escape(i)}var aH="UATrack||"+t(aa)+"||"+t(H)+"||"+av.userNick()+"||"+aI+"||"+e+"||"+ad.referrer()+"||"+i+"||"+(aJ.realUrl||"")+"||"+(aJ.ext||"");var D=ag+aH+"&gUid_"+new Date().getTime();d(D,aJ)}function aC(aK){var i=g(aK);var aI=i.target;var aH="",aL="",D="";var aJ;if(aI!=null&&aI.getAttribute&&(!aI.getAttribute("suda-uatrack")&&!aI.getAttribute("suda-actrack")&&!aI.getAttribute("suda-data"))){while(aI!=null&&aI.getAttribute&&(!!aI.getAttribute("suda-uatrack")||!!aI.getAttribute("suda-actrack")||!!aI.getAttribute("suda-data"))==false){if(aI==F.body){return}aI=aI.parentNode}}if(aI==null||aI.getAttribute==null){return}aH=aI.getAttribute("suda-actrack")||"";aL=aI.getAttribute("suda-uatrack")||aI.getAttribute("suda-data")||"";sudaUrls=aI.getAttribute("suda-urls")||"";if(aL){aJ=J(aL);if(aI.tagName.toLowerCase()=="a"){D=aI.href}opts={};opts.ext=(aJ.ext||"");aJ.key&&SUDA.uaTrack&&SUDA.uaTrack(aJ.key,aJ.value||aJ.key,D,opts)}if(aH){aJ=J(aH);aJ.key&&SUDA.acTrack&&SUDA.acTrack(aJ.key,aJ.value||aJ.key)}}if(window.SUDA&&Object.prototype.toString.call(window.SUDA)==="[object Array]"){for(var Q=0,ae=SUDA.length;Q<ae;Q++){switch(SUDA[Q][0]){case"setGatherType":m=SUDA[Q][1];break;case"setGatherInfo":r=SUDA[Q][1]||r;b=SUDA[Q][2]||b;a=SUDA[Q][3]||a;break;case"setPerformance":Z=SUDA[Q][1];break;case"setPerformanceFilter":C=SUDA[Q][1];break;case"setPerformanceInterval":K=SUDA[Q][1]*1||0;K=isNaN(K)?0:K;break;case"setGatherMore":M.push(SUDA[Q].slice(1));break;case"acTrack":S.push(SUDA[Q].slice(1));break;case"uaTrack":I.push(SUDA[Q].slice(1));break}}}aG=(function(D,i){if(ah.top==ah){return false}else{try{if(F.body.clientHeight==0){return false}return((F.body.clientHeight>=D)&&(F.body.clientWidth>=i))?false:true}catch(aH){return true}}})(320,240);A=(function(){return false})();av.setUOR();var au=av.sessionId();window.SUDA=window.SUDA||[];SUDA.sudaCount=SUDA.sudaCount||0;SUDA.log=function(){x.apply(null,arguments)};SUDA.acTrack=function(){ab.apply(null,arguments)};SUDA.uaTrack=function(){aq.apply(null,arguments)};U(F.body,"click",aC);window.GB_SUDA=SUDA;GB_SUDA._S_pSt=function(){};GB_SUDA._S_acTrack=function(){ab.apply(null,arguments)};GB_SUDA._S_uaTrack=function(){aq.apply(null,arguments)};window._S_pSt=function(){};window._S_acTrack=function(){ab.apply(null,arguments)};window._S_uaTrack=function(){aq.apply(null,arguments)};window._S_PID_="";y();try{k()}catch(T){}})();
    //-->
</script>
<noscript>
    &lt;div style='position:absolute;top:0;left:0;width:0;height:0;visibility:hidden'&gt;&lt;img width=0 height=0 src='http://beacon.sina.com.cn/a.gif?noScript' border='0' alt='' /&gt;&lt;/div&gt;
</noscript>
<!-- SUDA_CODE_END -->

<!-- SSO_GETCOOKIE_START -->
<script type="text/javascript">var sinaSSOManager=sinaSSOManager||{};sinaSSOManager.getSinaCookie=function(){function dc(u){if(u==undefined){return""}var decoded=decodeURIComponent(u);return decoded=="null"?"":decoded}function ps(str){var arr=str.split("&");var arrtmp;var arrResult={};for(var i=0;i<arr.length;i++){arrtmp=arr[i].split("=");arrResult[arrtmp[0]]=dc(arrtmp[1])}return arrResult}function gC(name){var Res=eval("/"+name+"=([^;]+)/").exec(document.cookie);return Res==null?null:Res[1]}var sup=dc(gC("SUP"));if(!sup){sup=dc(gC("SUR"))}if(!sup){return null}return ps(sup)};</script>
<!-- SSO_GETCOOKIE_END -->

<script type="text/javascript">new function(r,s,t){this.a=function(n,t,e){if(window.addEventListener){n.addEventListener(t,e,false);}else if(window.attachEvent){n.attachEvent("on"+t,e);}};this.b=function(f){var t=this;return function(){return f.apply(t,arguments);};};this.c=function(){var f=document.getElementsByTagName("form");for(var i=0;i<f.length;i++){var o=f[i].action;if(this.r.test(o)){f[i].action=o.replace(this.r,this.s);}}};this.r=r;this.s=s;this.d=setInterval(this.b(this.c),t);this.a(window,"load",this.b(function(){this.c();clearInterval(this.d);}));}(/http:\/\/www\.google\.c(om|n)\/search/, "http://keyword.sina.com.cn/searchword.php", 250);</script>
<!-- body code end 1-->


<!-- sina_text_page_info js配置 start 正文页全局参数-->

<script type="text/javascript">
var SINA_TEXT_PAGE_INFO = {
  entry: 'account',
  channel: 'cj',
  newsid: 'comos-fxqxcnz9093681',
  encoding: 'utf-8',

// 是否隐藏评论入口
  hideComment: false,
  // 是否隐藏评论列表(0,1)
  hideCommentList: 0,

  // 微博分享后面的@用户uid
  uid: '1638782947',//财经

  // 文章docid，用来检测是否已收藏
  docID: 'http://doc.sina.cn/?id=comos:fxqxcnz9093681',

  pagepubtime: '2016-04-04',
  difDay: 180,
  ADIDs: ["PublicRelation1","PublicRelation2","PublicRelation3","PublicRelation4","PublicRelation5","PublicRelation6","PublicRelation7","PublicRelation8","PublicRelation9","PublicRelation10","PublicRelation11","PublicRelation12","PublicRelation14","PublicRelation16"],

  // 底部微博推荐，如果没有，不填即可
  weiboGroupID: 35
};
</script>


<!-- sina_text_page_info js配置 end  正文页全局参数-->

<!-- suda -->
<script type="text/javascript" src="http://i1.sinaimg.cn/unipro/pub/suda_m_v629.js"></script>
<script type="text/javascript">suds_init(3465,100.0000,1015,2);</script>

<!-- 登录 css -->
<link rel="stylesheet" type="text/css" href="http://i.sso.sina.com.cn/css/userpanel/v1/top_account_v2.css">

<!--页面顶导 begin-->
<script charset="utf-8" type="text/javascript" src="http://n.sinaimg.cn/17e36822/20150708/topnav20150708_min.js"></script>
<link rel="stylesheet" href="http://finance.sina.com.cn/text/1007/2015-07-02/main-nav.css" type="text/css">
<div class="top_banner_0" style="">
    <ins class="sinaads sinaads-fail" data-ad-pdps="PDPS000000056985" data-ad-status="done" data-ad-offset-left="0" data-ad-offset-top="0"></ins>
    <script>(sinaads = window.sinaads || []).push({});</script>
</div>
<!-- 扩展对联 begin -->
<ins class="sinaads sinaads-fail" data-ad-pdps="2B7DB6CA8103" data-ad-status="done" data-ad-offset-left="0" data-ad-offset-top="0"></ins>
<script>(sinaads = window.sinaads || []).push({});</script>
<!-- 扩展对联 end -->

<!--主导航-->
<div class="sina15-top-bar-wrap" id="sina15-top-bar-wrap-astro" data-sudaclick="suda_723_daohang">
    <div class="sina15-top-bar-inner">
        <div class="sina15-nav">
            <ul class="sina15-nav-list">
                <li class="sina15-nav-list-first"><a href="http://www.sina.com.cn/">新浪首页</a></li>
                <li><a href="http://news.sina.com.cn/">新闻</a></li>
                <li><a href="http://finance.sina.com.cn/">财经</a></li>
                <li><a href="http://finance.sina.com.cn/stock/">股票</a></li>
                <li><a href="http://tech.sina.com.cn/">科技</a></li>
                <li><a href="http://house.sina.com.cn">房产</a></li>
                <li><a href="http://auto.sina.com.cn">汽车</a></li>
                <li><a href="http://sports.sina.com.cn">体育</a></li>
                <li><a href="http://blog.sina.com.cn/">博客</a></li>

                <li class="sina15-nav-list-last"><a href="#" class="sina15-more" data-action="dropdown" data-target="more">更多<i class="sina15-icon sina15-icon-arrows-a"></i></a></li>
                <!--鼠标滑过更多<a>标签添加class="sina15-on"-->
            </ul>
            <ul id="more" class="sina15-nav-others" style="display: none;">
                <li><a href="http://ent.sina.com.cn/">娱乐</a><a href="http://edu.sina.com.cn/">教育</a><a href="http://fashion.sina.com.cn/">时尚</a><a href="http://eladies.sina.com.cn/">女性</a><a href="http://astro.sina.com.cn/">星座</a><a href="http://health.sina.com.cn/">健康</a></li>
                <li><a href="http://photo.sina.com.cn/">图片</a><a href="http://history.sina.com.cn/">历史</a><a href="http://video.sina.com.cn/">视频</a><a href="http://collection.sina.com.cn/">收藏</a><a href="http://baby.sina.com.cn/">育儿</a><a href="http://book.sina.com.cn/">读书</a></li>
                <li class="sina15-nav-others-last"><a href="http://zhuanlan.sina.com.cn/">专栏</a><a href="http://fo.sina.com.cn/">佛学</a><a href="http://games.sina.com.cn/">游戏</a><a href="http://travel.sina.com.cn/">旅游</a><a href="http://mail.sina.com.cn/">邮箱</a><a href="http://news.sina.com.cn/guide/">导航</a></li>
            </ul>
        </div>
        <!--通行证组件start-->
        <div class="sina15-client">
            <div class="sina15-client-tl"> <a class="sina15-more" href="#" data-action="dropdown" data-target="mobileclient">移动客户端<i class="sina15-icon sina15-icon-arrows-a"></i></a> </div>
            <ul id="mobileclient" class="sina15-dropdown">
                <li><a href="http://m.sina.com.cn/m/weibo.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-weibo"></i>新浪微博</a></li>
                <li><a href="http://news.sina.com.cn/m/sinanews.html" target="_blank"><i class="sina15-ico-client sina15-ico-news"></i>新浪新闻</a></li>
                <li><a href="http://m.sina.com.cn/m/sinasports.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-sports"></i>新浪体育</a></li>
                <li><a href="http://m.sina.com.cn/m/sinaent.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-ent"></i>新浪娱乐</a></li>
                <li><a href="http://finance.sina.com.cn/mobile/comfinanceweb.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-finance"></i>新浪财经</a></li>
                <li><a href="http://video.sina.com.cn/app" target="_blank"><i class="sina15-ico-client sina15-ico-video"></i>新浪视频</a></li>
                <li><a href="http://games.sina.com.cn/o/kb/12392.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-games"></i>新浪游戏</a></li>
                <li><a href="http://m.sina.com.cn/m/weather.shtml" target="_blank"><i class="sina15-ico-client sina15-ico-weather"></i>天气通</a></li>
            </ul>
        </div>
        <div id="SI_User" class="TAP14" style="position: relative;">
            <div class="ac-rgst"> <a href="https://login.sina.com.cn/signup/signup?entry=news" class="msg-link" target="_blank">注册</a> </div>
            <div class="ac-login"><div class="ac-login-cnt" node-type="outer"><a class="ac-login-cnt" node-type="login_btn" href="javascript:;"><span class="thumb"><img src="http://i.sso.sina.com.cn/images/login/thumb_default.png"></span><span class="log-links">登录</span></a></div></div>
        <div node-type="box" class="outlogin_layerbox_bylx outlogin_layerbox_bylx_anrrow" style="visibility: visible; display: none; top: 45px; left: -191px;"><div class="cur_move" node-type="handle"><a node-type="close" href="javascript:;" onclick="return false;" class="layerbox_close">×</a></div><div node-type="root" class="layerbox_left"><div class="titletips" node-type="titletips">新浪微博、博客、邮箱帐号，请直接登录</div><p node-type="tip" class="login_error_tips" style="visibility:hidden;"></p><ul class="loginformlist"><li class="ndrelativewrap" node-type="prelogin_area" style="display:none;"><span class="pre_name" node-type="prelogin_name">加载中...</span><a href="javascript:;" class="chg_ac" node-type="prelogin_changeAccount">换个账号登录</a></li><li class="ndrelativewrap" node-type="loginname_box"><input node-type="loginname" name="loginname" class="styles" type="text" placeholder="微博/博客/邮箱/手机号" tabindex="1" maxlength="128" autocomplete="off" autocapitalize="off"><a node-type="clear" href="javascript:;" class="close_loginname" style="display:none;">×</a></li><li node-type="password_box"><input node-type="password" name="password" class="styles" type="password" placeholder="请输入密码" tabindex="2" maxlength="24"></li><li class="loginform_yzm" node-type="door_box" style="display:none;"><input node-type="door" name="door" class="styles" type="text" tabindex="3" maxlength="6" autocomplete="off" autocapitalize="off"><img node-type="door_img" class="yzm" alt="看不清？换一换"><a node-type="door_change" href="javascript:;" class="reload-code" title="看不清？换一换"></a><a node-type="door_voice" href="javascript:;" class="disability_voice" style="display:none;"></a></li><li node-type="vsn_box" style="display:none;"><input node-type="vsn" name="vsn" class="styles" type="text" tabindex="4" maxlength="6" placeholder="请输入微盾动态码" autocomplete="off" autocapitalize="off"></li><li class="sub_wrap_r"><span class="btn_wrap"><a href="javascript:;" tabindex="5" node-type="submit" class="login_btn" suda-uatrack="key=index_new_menu&amp;value=logon_login">登录</a><label node-type="remember_label" class="rmb_login"><input name="remember" node-type="remember" type="checkbox" class="auto_checkbox" checked="checked" autocomplete="off"><span>下次自动登录</span></label></span></li><li class="sub_wrap_r"><span class="log_option"><a class="forget_Pwd" node-type="forgot_password" href="http://login.sina.com.cn/getpass.html" target="_blank" suda-uatrack="key=index_new_menu&amp;value=logon_forgot">忘记密码</a><a class="register_lnk" node-type="register_button" target="_blank" href="https://login.sina.com.cn/signup/signup.php?entry=account" suda-uatrack="key=index_new_menu&amp;value=logon_register">立即注册</a></span></li><li class="sub_wrap_r"><span class="qq_spanoption"><a class="qq_login_h" node-type="qq_login" href="https://passport.weibo.com/othersitebind/authorize?site=qq&amp;wl=1&amp;entry=account&amp;callback=http%3A%2F%2Ffinance.sina.com.cn%2Froll%2F2016-04-04%2Fdoc-ifxqxcnz9093681.shtml" suda-uatrack="key=index_new_menu&amp;value=logon_qq"><span class="qq_login_logo"></span><span class="qq_login">使用QQ登录</span></a></span></li></ul></div><div class="otwo_d_wrap" node-type="layerleft_qrcode"><div class="otwo_tl">用微博客户端扫描安全登录</div><div class="td_wrap"><a href="javascript:;"><img node-type="qrcode_img" src="http://i.sso.sina.com.cn/images/login/td.png"></a></div></div><div class="otwo_d_wrap" node-type="layerleft_preloginThumb" style="display:none;"><div class="otwo_tl"></div><div class="td_wrap"><span class="thumb"><img node-type="prelogin_img" src="http://i.sso.sina.com.cn/images/login/pre_loading.gif"></span></div></div><div node-type="qrcode_help" class="otwo_hlp" style="display:none;"><div class="hlp_cnt"><div class="otwo_hlp_tl">用此功能扫描二维码快速登录</div><div class="ot_wrap"><img src="http://i.sso.sina.com.cn/images/login/weibo_how_ot.png"></div></div><span class="ot_arrow"></span></div><div node-type="qrcode_tip" class="swip_check" style="display:none;"><span class="swip_check_cls" node-type="qrcode_tip_close"></span><span class="swip_check_icon"></span><p class="swip_check_txt">扫描成功！<br>点击手机上的确认即可登录</p><span class="swip_check_btmarow"></span></div><div node-type="css_check" class="outlogin_checkload" style="display:none;"></div></div></div>

        <!--/通行证组件end-->
    </div>
</div>
<!--/主导航-->
<!--页面顶导 end-->

<div class="wrap-outer clearfix" id="wrapOuter">
    <div class="wrap-inner">
        <div class="site-header clearfix">
            <h2><a href="http://finance.sina.com.cn/">新浪财经</a></h2>

            <div class="bread">
                <!--
                <a href=http://finance.sina.com.cn/column/hyjz.html>会议讲座</a>  &gt
                <a href="http://finance.sina.com.cn/focus/2015cpcic/">2015中国国际石油化工大会</a>
                <span class="bread-spliter">&gt;</span>正文</div>  -->
                <a href="http://finance.sina.com.cn/roll/"> 滚动新闻</a> <!--<span class="bread-spliter">&gt;</span>正文--><span class="bread-spliter">&gt;</span>正文</div>


            <div class="m-s-bar clearfix" id="siteSearch" style="visibility: visible;" data-sudaclick="suda_723_search">
                <form class="clearfix" action="http://biz.finance.sina.com.cn/suggest/lookup_n.php" onsubmit="return checkFormSuggest_0(this);" target="_blank" id="topSearch">
                    <div class="m-sb-select" style="position: relative;">
                        <select onchange="" name="country" class="countrySelect" id="slt_02" style="visibility: hidden;">
                            <option value="" selected="selected">行情</option>
                            <option value="stock">股吧</option>
                            <option value="usstock">新闻</option>
							<option value="forex">外汇</option>

                        </select>
                    <div class="selectView" style="width: 60px; position: absolute; left: 0px; top: 0px;"><div class="ds_cont"><div class="ds_title">行情</div><div class="ds_button"></div></div><div class="ds_list" style="display: none;"><div class="dsl_cont"><p>行情</p><p>股吧</p><p>新闻</p><p>外汇</p></div></div></div></div>
                    <div class="m-sb-input_text">
                        <input type="text" onfocus="if(this.value=='简称/代码/拼音'){this.value='';}" onblur="if(this.value==''){this.value='简称/代码/拼音';}" value="简称/代码/拼音" id="suggest01_input" name="q" autocomplete="off">
                    </div>
                    <input type="submit" value="" id="topSearchSubmit" class="topSearchSubmit">
                    <input type="hidden" name="name">
                    <input type="hidden" name="t" value="keyword">
                    <input type="hidden" name="c" value="all">
					<input type="hidden" name="ie" value="utf-8">
                    <input type="hidden" name="k">
                    <input type="hidden" name="range" value="all">
                    <input type="hidden" name="col" value="1_7">
                    <input type="hidden" name="from" value="channel">
                </form>
            </div>
        </div>
        <div class="d_titlebn adNone">
            <!-- 窄顶通 begin -->

            <!-- 窄顶通 end -->
        </div>
        <div class="page-header">
            <h1 id="artibodyTitle" cid="56673" docid="fxqxcnz9093681">辽宁鞍山：生态树葬带起文明祭祀之风</h1>
        </div>
        <div class="page-info">
      <span class="time-source">
		    2016年04月04日11:20

<span data-sudaclick="media_name"><a href="http://news.xinhuanet.com/local/2016-04/04/c_1118525105.htm" target="_blank" rel="nofollow">新华网</a></span>



      </span>

            <div class="page-tools"> <span class="page-tool-i page-tool-c first-page-tool" title="评论"><!-- comment -->
                <a href="javascript:;" suda-uatrack="key=news_content_2014&amp;value=nav_comment"></a> <span id="commentCount1">0</span> <s class="bottom-border"></s> </span> <span class="page-tool-i page-tool-s" title="分享"><!-- share -->
                <a href="javascript:;" id="shareArticleButton" suda-uatrack="key=news_content_2014&amp;value=nav_share">分享</a> <s class="bottom-border"></s> </span> <span class="page-tool-i page-tool-f" title="添加喜爱"><!-- add favorite -->
                <a href="javascript:;" id="addToFavorite1" suda-uatrack="key=news_content_2014&amp;value=nav_favorite">添加喜爱</a> <s class="bottom-border"></s> </span> <span class="page-tool-i page-tool-p" title="打印"><!-- print -->
                <a href="javascript:;" suda-uatrack="key=news_content_2014&amp;value=nav_print">打印</a> <s class="bottom-border"></s> </span> <span class="page-tool-i page-tool-u"><!-- up font size -->
                <a href="javascript:;" id="adjustFontSizeUp1" suda-uatrack="key=news_content_2014&amp;value=nav_bigger" class="enable" title="加大字号">增大字体</a> <s class="bottom-border"></s> </span> <span class="page-tool-i page-tool-d"><!-- donw font size -->
                <a href="javascript:;" id="adjustFontSizeDown1" suda-uatrack="key=news_content_2014&amp;value=nav_small" class="enable" title="减小字号">减小字体</a> <s class="bottom-border"></s> </span> </div>
        </div>
        <div class="page-content clearfix" id="articleContent">
            <div class="left">
                <!--正文部分-->


<div class="l_banner1">
    <!--正文页小通栏 satrt-->
            <script>
            (function (d, s, id) {
                var s, n = d.getElementsByTagName(s)[0];
                if (d.getElementById(id)) return;
                s = d.createElement(s);
                s.id = id;
                s.setAttribute('charset', 'utf-8');
                s.src = '//d' + Math.floor(0 + Math.random() * (9 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js';
                n.parentNode.insertBefore(s, n);
            })(document, 'script', 'sinaads-script');
        </script>
        <!--$$ 20140801 00:00:00-20140801 12:00:00 张飞 zhangfei1.sina.com.cn  开始 $-->
        <!--$$ 窄通广告 pdps: 1188672F3595 $-->
        <ins class="sinaads sinaads-fail" data-ad-pdps="1188672F3595B" data-ad-status="done" data-ad-offset-left="174" data-ad-offset-top="251"></ins>
        <script>(sinaads = window.sinaads || []).push({});</script>
        <!--$$ 20140801 00:00:00-20140801 12:00:00 张飞 zhangfei1.sina.com.cn 结束 $-->

       <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000056026" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="251" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:640px;display:block;position:relative;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJMmE1MmFhM2YtYjE5ZS00NGFhLTg1MzEtNmM4MTY5ODY4MmIwCTM5NzQyMAk1ODc3NDA1OTI5X1BJTlBBSS1DUEMJMTI5NjU3CTIyODIxOAk2LjM1Mjg4RS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDU2MDI2CTEwOTMyNDcJUEMJaW1hZ2UJLQkwfDM5NzQyMHxudWxsCW51bGwJMQkxNQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=Efm1MiMfSeaMT41ZqShFbyPIchdE%2F3IP7Rp7xg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMTFmOWI1MzItMjMxZi00OWU2LThjNGYtOGQ1OWE5Mjg0NTZmCTE3CVBEUFMwMDAwMDAwNTYwMjYJMTA5MzI0NwkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fzhibo.izdzy.com%252Froom%252F%26sina_sign%3D57ef6034968a56ac&amp;sign=e7241dada863c934&amp;am=%7Bclkx%3A430%2Cclky%3A343%7D" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJMmE1MmFhM2YtYjE5ZS00NGFhLTg1MzEtNmM4MTY5ODY4MmIwCTM5NzQyMAk1ODc3NDA1OTI5X1BJTlBBSS1DUEMJMTI5NjU3CTIyODIxOAk2LjM1Mjg4RS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDU2MDI2CTEwOTMyNDcJUEMJaW1hZ2UJLQkwfDM5NzQyMHxudWxsCW51bGwJMQkxNQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=Efm1MiMfSeaMT41ZqShFbyPIchdE%2F3IP7Rp7xg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMTFmOWI1MzItMjMxZi00OWU2LThjNGYtOGQ1OWE5Mjg0NTZmCTE3CVBEUFMwMDAwMDAwNTYwMjYJMTA5MzI0NwkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fzhibo.izdzy.com%252Froom%252F%26sina_sign%3D57ef6034968a56ac&amp;sign=e7241dada863c934" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d1.sina.com.cn/pfpghc2/201603/30/061f22e8124843b58dae053fba1e1102.gif" style="width:640px;height:90px;border:0" alt="http://d1.sina.com.cn/pfpghc2/201603/30/061f22e8124843b58dae053fba1e1102.gif"></a></ins></ins>
<script>(sinaads = window.sinaads || []).push({});</script>

    <!--正文页小通栏 end-->
</div>
<div class="article article_16" id="artibody">
	    <!--视频播放器start-->




	    <!--视频播放器end -->

	    <!--行情图 start-->

	    <!--行情图 end-->

	    <!--上图片-->

	    <!--广告推广-->



	    <!--文章开头推广-->


	    <!-- 原始正文start -->

    <p>　　新华社沈阳4月4日专电（记者王炳坤）不修墓穴、不立碑，将逝者骨灰葬于绿树红花之下——辽宁省鞍山市近年来倡导的生态树葬，如今成为广受市民接受的殡葬方式。在鼓励逝者家属减少浪费、植树造林的同时，生态树葬还带起一股文明祭祀之风。</p>

<div id="ad_44099" class="otherContent_01" style="display: block; margin: 10px 20px 10px 0px; float: left; overflow: hidden; clear: both; padding: 4px; width: 300px; height: 250px;"><ins class="sinaads sinaads-done" id="Sinads49447" data-ad-pdps="PDPS000000044099" data-ad-status="done" data-ad-offset-left="0" data-ad-offset-top="0" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><iframe width="300px" height="250px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="http://x.jd.com/exsites?spread_type=2&amp;ad_ids=1884:5&amp;location_info=0&amp;callback=getjjsku_callback" name="clickTAG=http%3A%2F%2Fsax.sina.com.cn%2Fmfp%2Fclick%3Ftype%3D3%26t%3DMjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDA0NDA5OQk5ZjliY2I2OS0zZmYyLTQwN2UtOTY4MC1mNTk3YTkzODY4ZDUJMUY4N0REOTUxNUVCCTFGODdERDk1MTVFQglfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwNDQwOTl8dmVyc2lvbjpwYzo0LjAJCTMwMjAwMHwzMDIwMDAJNTYwQURFN0UwREMzCUxZMTUxMjA5NjUJUERQUzAwMDAwMDA0NDA5OQk1NjBBREU3RTBEQzNfcG9ydGFsCUFFCS0JOAktCS0JLQktCS0JLQktCS0JMgkxNAlzdHJhdGVneV90aGV0YQkwCTYJLQ%253D%253D&amp;viewTAG=http%3A%2F%2Fsax.sina.com.cn%2Fmfp%2Fview%3Ftype%3D3%26t%3DMjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDA0NDA5OQk5ZjliY2I2OS0zZmYyLTQwN2UtOTY4MC1mNTk3YTkzODY4ZDUJMUY4N0REOTUxNUVCCTFGODdERDk1MTVFQglfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwNDQwOTl8dmVyc2lvbjpwYzo0LjAJCTMwMjAwMHwzMDIwMDAJNTYwQURFN0UwREMzCUxZMTUxMjA5NjUJUERQUzAwMDAwMDA0NDA5OQk1NjBBREU3RTBEQzNfcG9ydGFsCUFFCS0JOAktCS0JLQktCS0JLQktCS0JMgkxNAlzdHJhdGVneV90aGV0YQkwCTYJLQ%253D%253D%26userid%3D114.251.216.113_1459489959.63940%26viewlog%3Dfalse"></iframe></ins></ins></div><p>　　位于鞍山市大孤山镇的弘莲墓园，是全市最大一处树葬公益园。这里没有一块立碑，而是种满了油松、云杉、梧桐等树木。公墓管理者葛继红介绍，这里不修墓穴，也不保留骨灰盒，而是直接将骨灰埋到土里，在上面栽种树木、花草，树枝上挂有逝者的名字牌和墓志铭。</p>

<p>　　与普通公墓相比，生态树葬收费低廉，而且没有大理石、水泥建筑等硬覆盖物造成的环境污染。祭扫者不仅能从逐年长高的树木中得到安慰，而且将建造公墓与植树造林融为一体，对环境保护也有贡献。</p>

<p>　　在鞍山，生态树葬从最初的无人接受，现在已得到越来越多市民认可。如今，鞍山市已有3000多人选择树葬，还有近千人提前认养树木，打算离世后长眠树下。</p>

<p>　　记者4月3日在弘莲墓园采访，三三两两的祭扫者不烧纸、不放鞭炮，而是带着工具给树木浇水、剪枝。鞍山市冯志国爱心团队10余名成员在队长冯志国带领下，在青草绿树之间拉大提琴、弹吉他，为故去的团队老队员弹奏、合唱曾经爱听的歌曲。冯志国说，故去的队员通过树葬给子孙后代留下繁茂森林，我们也该环保、文明祭祀，精心呵护这片绿色和宁静。</p><div style="font-size: 0px; height: 0px; clear: both;"></div>
<!-- news_keyword_pub,stock, -->






	    <!-- 原始正文end -->

	    <!-- 按美股来源显示图片start -->

	    <!-- 按美股来源显示图片end -->

	    <!-- 按媒体来源显示图片 -->


	    <!--总声明-->












	    <!--调查代码-->




		<!--股吧推广-->
	     <div data-sudaclick="suda_1028_guba"><p>进入<a href="http://guba.sina.com.cn" target="_blank">【新浪财经股吧】</a>讨论</p></div>







</div>



                <!--正文部分end-->

				<!--编辑真实姓名及工作代码begain-->


				<!--编辑真实姓名及工作代码end-->

                <!--正文下部-->

    <div class="fin_art_weixin clearfix"><div class="img_wrapper"><img src="http://www.sinaimg.cn/cj/pc/2015-04-02/32/U10832P31T32D122213F651DT20150402120014.jpg"></div></div>






















<div class="article-info clearfix">
	<!-- 文章关键字-->

	<!-- 文章关键字 end-->
    <div class="article-feedback">
        <a href="http://help.sina.com.cn/commonquestion/subview/20/" target="_blank">我要反馈</a>
        <a href="http://roll.finance.sina.com.cn/savepage/save.php?url=http%3A%2F%2Ffinance.sina.com.cn${column_path}${正文日期}%2F${小时分钟}${docid}${blog_path}.shtml" target="_blank">保存网页</a>
    </div>
</div>
	<!-- 微财富推广-->
    			<link rel="stylesheet" href="http://finance.sina.com.cn/text/1007/2015-07-02/licaishi.css">
	<div id="lcs_wrap" data-furl="http://finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml">                <div class="fnc_lcswcf clearfix">                    <div class="fnc_lcswcf_l">                        <a hidefocus="true" href="http://licaishi.sina.com.cn/?fr=f_news" target="_blank"><s class="fnc_lcs_icon"></s>新浪理财师 让天下没有难理的财</a>                    </div>                    <div class="fnc_lcswcf_r">                        <a hidefocus="true" href="http://www.weicaifu.com/?utm_source=sinacj&amp;utm_medium=free&amp;utm_term=lcslogo&amp;utm_campaign=logo6024" target="_blank"><s class="fnc_wcf_icon"></s>新浪微财富全民理财平台！</a>                    </div>                </div></div>
	<script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/licaishi.js" charset="gb2312"></script>
	<!-- 微财富推广 end-->

<div class="bottom-tool clearfix bottom-tool-fixed" id="bottomTools">
    <div class="page-tools"> <span class="page-tool-i first-page-tool page-tool-s" title="分享"><!-- share -->
                        <a href="javascript:;" suda-uatrack="key=news_content_2014&amp;value=bottom_share">分享</a> </span> </div>
    <div class="page-tool-bshare">
        <!-- dataset项说明: bshareupdate存在则标识渲染; data-mburl为可选参数: 自定义分享链接, 建议填写, 若没有则从meta获取 -->
        <div class="bshare-custom icon-medium" bshareupdate="1" data-mburl="http://doc.sina.cn/?id=comos:fxqxcnz9093681" h5qr="http://comet.blog.sina.com.cn/qr?http://doc.sina.cn/?id=comos:fxqxcnz9093681&amp;fromsinaweb="><div class="bsPromo bsPromo2"></div>
            <div class="bsPromo bsPromo2"></div>
            <a href="javascript:void();" title="分享到新浪微博" class="bshare-sinaminiblog"></a><a href="javascript:void();" class="share_weimi" title="分享到微米"></a><a href="javascript:void();" class="share_laiwang" title="分享到来往"></a><span class="share_weixin_w" title="分享到微信"><span class="share_weixin"></span></span><a href="javascript:void();" title="分享到QQ空间" class="bshare-qzone"></a><a href="javascript:void();" title="分享到人人网" class="bshare-renren"></a><a href="javascript:void();" title="更多平台" class="bshare-more bshare-more-icon more-style-addthis"></a> </div>
        <script type="text/javascript" charset="utf-8" src="http://static.bshare.cn/b/buttonLite.js#style=-1&amp;uuid=2c330a9c-c99a-4bb0-8919-7ea66c5025cc&amp;pophcol=2&amp;lang=zh"></script>
        <script type="text/javascript" charset="utf-8" src="http://static.bshare.cn/b/bshareC0.js"></script>
        <script src="http://news.sina.com.cn/268/2014/0919/bshare_update.js" charset="utf-8"></script>
        <script type="text/javascript">
            bShare.addEntry({
                title: '',
                summary: document.getElementById('artibodyTitle').innerHTML.replace(/<[^<>]*?font[^<>]*?>/gi,"") ,
                url: '',
                pic:[]
            });
            $('#shareArticleButton').on('click', function(e){
                bShare.more();
                e.preventDefault();
            });
        </script>
        <script>
            bShareUpdate();
        </script>
    </div>
    <div class="page-tools"> <span class="page-tool-i page-tool-c" title="评论"><!-- comment -->
                        <a hidefocus="true" href="javascript:;" suda-uatrack="key=news_content_2014&amp;value=bottom_comment"></a> <span id="commentCount2">0</span> </span> <span class="page-tool-i page-tool-f" title="添加喜爱"><!-- add favorite -->
                        <a hidefocus="true" href="javascript:;" id="addToFavorite2" suda-uatrack="key=news_content_2014&amp;value=bottom_favorite">添加喜爱</a> </span> <span class="page-tool-i page-tool-p" title="打印"><!-- print -->
                        <a hidefocus="true" href="javascript:;" suda-uatrack="key=news_content_2014&amp;value=bottom_print">打印</a> </span> <span class="page-tool-i page-tool-u"><!-- up font size -->
                        <a hidefocus="true" href="javascript:;" id="adjustFontSizeUp2" suda-uatrack="key=news_content_2014&amp;value=bottom_bigger" class="enable" title="加大字号">增大字体</a> </span> <span class="page-tool-i page-tool-d"><!-- donw font size -->
                        <a hidefocus="true" href="javascript:;" id="adjustFontSizeDown2" suda-uatrack="key=news_content_2014&amp;value=bottom_small" class="enable" title="减小字号">减小字体</a> </span> </div>
</div>

<!-- 评论上方悬停广告 begin -->
<div id="sinaads_box" class="adNone">
    <div id="sinaads_fixed" style="position: relative;" class=""> <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000055148" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1527" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:640px;display:block;position:relative;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJN2EyNDlkNTQtN2I1Yi00NGY4LTgyODEtYTg4MjZkOGMxMWFjCTM5ODcxNgk1ODc5NTIxNjg1X1BJTlBBSS1DUEMJMTMwMTQ2CTgxNzc3CTUuNjgxODE4RS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDU1MTQ4CTEwOTY1OTEJUEMJaW1hZ2UJLQkwfDM5ODcxNnxudWxsCW51bGwJMQkxMA==&amp;userid=114.251.216.113_1459489959.63940&amp;p=dKSkEf6ZRUm%2BGWEoOsMpqzvPy3tu6LNyL%2FnlbA%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DNzRhNGE0MTEtZmU5OS00NTQ5LWJlMTktNjEyODNhYzMyOWFiCTE3CVBEUFMwMDAwMDAwNTUxNDgJMTA5NjU5MQkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fwww.qishanxia.com%252F%253Fgzid%253DA6.640.90%26sina_sign%3D2993631a78efa0b9&amp;sign=26a773684b7d95d6" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJN2EyNDlkNTQtN2I1Yi00NGY4LTgyODEtYTg4MjZkOGMxMWFjCTM5ODcxNgk1ODc5NTIxNjg1X1BJTlBBSS1DUEMJMTMwMTQ2CTgxNzc3CTUuNjgxODE4RS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDU1MTQ4CTEwOTY1OTEJUEMJaW1hZ2UJLQkwfDM5ODcxNnxudWxsCW51bGwJMQkxMA==&amp;userid=114.251.216.113_1459489959.63940&amp;p=dKSkEf6ZRUm%2BGWEoOsMpqzvPy3tu6LNyL%2FnlbA%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DNzRhNGE0MTEtZmU5OS00NTQ5LWJlMTktNjEyODNhYzMyOWFiCTE3CVBEUFMwMDAwMDAwNTUxNDgJMTA5NjU5MQkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fwww.qishanxia.com%252F%253Fgzid%253DA6.640.90%26sina_sign%3D2993631a78efa0b9&amp;sign=26a773684b7d95d6" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d1.sina.com.cn/pfpghc2/201603/31/dca4b078bf894a26bffbd08af3cfe772.jpg" style="width:640px;height:90px;border:0" alt="http://d1.sina.com.cn/pfpghc2/201603/31/dca4b078bf894a26bffbd08af3cfe772.jpg"></a></ins></ins>
        <div id="sinaads-float-close" style="width:40px;height:18px;position:absolute;right:0;top:0;z-index:9999;cursor:pointer;background:url(http://d9.sina.com.cn/litong/zhitou/test/images/close-h.jpg) 100% 50% no-repeat rgb(235, 235, 235);"></div>
        <script>(sinaads = window.sinaads || []).push({});</script>
        <script>
            var sinaadsClose=document.getElementById("sinaads-float-close");
            var sinaadsBox=document.getElementById("sinaads_fixed");
            sinaadsBox.style.position="relative";
            sinaadsClose.onclick=function(){
                sinaadsBox.style.display="none";
            };
        </script>
    </div>
</div>
<div id="sinaads_box">
    <!-- 推荐代码 -->
    <script>
       (function (d, s, id) {
            var n = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            s = d.createElement(s);
            s.id = id;
            s.setAttribute('charset', 'utf-8');
            s.src = '//d' + Math.floor(0 + Math.random() * (9 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/test/e-recommendation/release/sinaere.js';
            n.parentNode.insertBefore(s, n);
        })(document, 'script', 'sinaere-script');
    </script>
   <ins style="margin-top: 10px; display: block; overflow: hidden; text-decoration: none;" class="sinaere" data-tpl="2" data-pos="P_F_T_2" data-w="600" data-h="150" data-num="3" data-channel="finance" data-status="done"><ins style="text-decoration:none;margin:0px auto;display:block;overflow:hidden;width:600px;height:150px;"><iframe width="600" height="150" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="//d2.sina.com.cn/litong/zhitou/sinaads/test/e-recommendation/tpl/eretpl_2_600_150.html?1459744666804" name="%7B%22status%22%3A%7B%22msg%22%3A%22user%20profile%20failed%22%2C%22code%22%3A0%2C%22total%22%3A60%7D%2C%22data%22%3A%5B%7B%22price%22%3A%22150%22%2C%22info%22%3A%224725d496a4503bdd99e8a6df436b4e5d%7C14%7C1%22%2C%22url%22%3A%22http%3A%2F%2Ffashion.sina.com.cn%2Fcosmetics%2Fproduct%2F3794%3Fcre%3Dad_business%26mod%3Dg%26loc%3D1%26r%3D14%26doct%3D0%26rfunc%3D74%22%2C%22doct%22%3A0%2C%22thumb%22%3A%22http%3A%2F%2Fwww.sinaimg.cn%2Flx%2Fbeauty%2Fchanpinku%2Fhufu%2Fyanbu%2F2006-08-31%2FU3098P8T246D3794F6951DT20081015114345.jpg%22%2C%22reason%22%3A14%2C%22bpic%22%3A0%2C%22meta%22%3A%22mbrand%3D7p7L%26mtype1%3DMeJ%26mtype2%3DSnU%26mprice%3D150%22%2C%22brand%22%3A%22%E4%BD%B0%E8%8D%89%E9%9B%86%2FHERBORIST%22%2C%22uuid%22%3A%224725d496a4503bdd99e8a6df436b4e5d%22%2C%22func%22%3A%22%E7%9C%BC%E9%83%A8%E9%97%AE%E9%A2%98%22%2C%22type1%22%3A%22%E6%8A%A4%E8%82%A4%22%2C%22name%22%3A%22%E7%9C%BC%E9%83%A8%E4%BF%AE%E6%8A%A4%E5%95%AB%E5%96%B1%22%2C%22type2%22%3A%22%E7%9C%BC%E9%83%A8%22%7D%2C%7B%22info%22%3A%22b99599f06f0f3927b78b3b0717d4e61f%7C13%7C2%22%2C%22meta%22%3A%22cbrand%3DE3o%26cseries%3D6Wnu%26ctype%3D1%26cprice%3D9%26country%3D1%22%2C%22doct%22%3A1%2C%22thumb%22%3A%22http%3A%2F%2Fwww.sinaimg.cn%2Fqc%2Fphoto_auto%2Fphoto%2F05%2F10%2F59960510%2F59960510_950.jpg%22%2C%22reason%22%3A13%2C%22bpic%22%3A0%2C%22country%22%3A%22%E5%9B%BD%E5%A4%96%22%2C%22cseries%22%3A%22%E5%AE%9D%E9%A9%ACX3%22%2C%22cbrand%22%3A%22%E5%AE%9D%E9%A9%AC%22%2C%22url%22%3A%22http%3A%2F%2Fdata.auto.sina.com.cn%2F409%3Fcre%3Dad_business%26mod%3Dg%26loc%3D2%26r%3D13%26doct%3D1%26rfunc%3D74%22%2C%22uuid%22%3A%22b99599f06f0f3927b78b3b0717d4e61f%22%2C%22ctype%22%3A%22SUV%22%2C%22cprice%22%3A%2235-50%E4%B8%87%22%7D%2C%7B%22camera1%22%3A800%2C%22doct%22%3A2%2C%22uuid%22%3A%22b16f3b668b4a3cffa15e512a3529e35a%22%2C%22manufactor%22%3A%22vivo%22%2C%22bpic%22%3A0%2C%22url%22%3A%22http%3A%2F%2Ftech.sina.com.cn%2Fmobile%2Fmodels%2F20645.html%3Fcre%3Dad_business%26mod%3Dg%26loc%3D3%26r%3D1%26doct%3D2%26rfunc%3D74%22%2C%22pub_time%22%3A%222015%E5%B9%B411%E6%9C%88%22%2C%22size%22%3A%225.2%22%2C%22thumb%22%3A%22http%3A%2F%2Fwww.sinaimg.cn%2FIT%2Fmobile%2Fmodels%2Fidx%2F2015%2F1201%2FU8906P2T136D20645F3244DT20151201101115.jpg%22%2C%22camera%22%3A1300%2C%22meta%22%3A%22product%3D2%26manufactor%3DT5Z%26price%3D4%26pub_time%3D201511%26os%3DMAo%22%2C%22info%22%3A%22b16f3b668b4a3cffa15e512a3529e35a%7C1%7C3%22%2C%22price%22%3A2598%2C%22reason%22%3A1%2C%22os%22%3A%22Android%22%2C%22name%22%3A%22vivo%20X6%20%E5%85%A8%E7%BD%91%E9%80%9A%22%2C%22product%22%3A2%7D%5D%2C%22referrer%22%3A%22http%3A%2F%2Ffinance.sina.com.cn%2Froll%2F2016-04-04%2Fdoc-ifxqxcnz9093681.shtml%22%2C%22pos%22%3A%22P_F_T_2%22%7D"></iframe></ins></ins>
    <script>
        //推荐启动代码
        (sinaere = window.sinaere || []).push({});
    </script>
    <!-- 推荐代码end -->
</div>
<!-- 评论上方悬停广告 end -->

<!-- 理财师左侧推广 -->
<div class="lcs1_w" id="lcs1_w" data-sudaclick="suda_723_lcstg" style="">
    <div class="lcs1_w_tt">
        <h3><a hidefocus="true" href="http://licaishi.sina.com.cn/" target="_blank">新浪理财师推荐</a></h3>
        <div class="lcs1_tt_r"><a hidefocus="true" href="http://licaishi.sina.com.cn/web/askList" target="_blank" id="lcs1_link">选股难？解套难？问问执业理财师&gt;&gt;</a></div>
    </div>
    <div class="lcs1_c">
        <ul class="lcs1_list clearfix" id="lcs1_list">                        <li class="lcs1_item">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/5154737018/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://s3.licaishi.sina.com.cn/180/160309/1406024542.png" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/5154737018/1" class="lcs1_i_name" target="_blank">许新源</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/5154737018/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">第一创业证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">13592</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">99%</p>                                </div>                            </div>                        </li>                        <li class="lcs1_item">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/1615998150/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://tp3.sinaimg.cn/1615998150/180/5718498424/1" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/1615998150/1" class="lcs1_i_name" target="_blank">柳岸林</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/1615998150/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">金元证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">9788</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">99%</p>                                </div>                            </div>                        </li>                        <li class="lcs1_item lcs1_item_edge">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/5379248802/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://s3.licaishi.sina.com.cn/180/160118/1508526448.jpeg" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/5379248802/1" class="lcs1_i_name" target="_blank">王军</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/5379248802/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">华安证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">1611</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">99%</p>                                </div>                            </div>                        </li>                        <li class="lcs1_item">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/3204122324/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://s3.licaishi.sina.com.cn/180/151225/1056446614.png" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/3204122324/1" class="lcs1_i_name" target="_blank">刘斌</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/3204122324/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">大通证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">1403</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">98%</p>                                </div>                            </div>                        </li>                        <li class="lcs1_item">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/2356466220/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://s3.licaishi.sina.com.cn/180/160303/1023232201.jpeg" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/2356466220/1" class="lcs1_i_name" target="_blank">林声茂</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/2356466220/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">爱建证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">549</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">100%</p>                                </div>                            </div>                        </li>                        <li class="lcs1_item lcs1_item_edge">                            <div class="lcs1_i_hd clearfix">                                <a href="http://licaishi.sina.com.cn/planner/1942139933/1" target="_blank"><img class="lcs1_i_prt" width="50" height="50" src="http://tp2.sinaimg.cn/1942139933/180/5656158318/1" alt=""></a>                                <div class="lcs1_i_hd_r">                                    <p class="lcs1_i_p0">                                        <a href="http://licaishi.sina.com.cn/planner/1942139933/1" class="lcs1_i_name" target="_blank">梁仕强</a>                                        <s class="lcs1_up"></s>                                        <a href="http://licaishi.sina.com.cn/planner/1942139933/3" class="lcs1_i_follow lcs_bgc_orange" target="_blank">向Ta提问</a>                                    </p>                                    <p class="lcs1_i_p1">长城证券</p>                                </div>                            </div>                            <div class="lcs1_i_c clearfix">                                <div class="lcs1_i_c_l">                                    <p class="lcs1_i_p2">回答问题数</p>                                    <p class="lcs1_i_p3">500</p>                                </div>                                <div class="lcs1_i_c_r">                                    <p class="lcs1_i_p2">满意度</p>                                    <p class="lcs1_i_p4">98%</p>                                </div>                            </div>                        </li></ul>
        <a hidefocus="true" href="http://licaishi.sina.com.cn/web/askList" target="_blank" class="lcs1_more" id="lcs1_more">更多理财师</a>
    </div>
</div>
<script src="http://finance.sina.com.cn/text/1007/2015-07-02/lcs1tg.js" charset="utf-8"></script>
<!-- 理财师左侧推广 end -->

<div class="feed-wrap" id="relatedNewsWrap" style="margin-top: 75px;">
    <div class="feed-title">
        <h3>相关阅读</h3>
    </div>
    <div class="feed-c">
        <div id="feedCard" suda-uatrack="key=new_content_relate_click_times20150707&amp;value=1" data-sudaclick="suda_723_xgyd" class="feed-card-fixed"><div class="feed-card-tab" id="feedCardTab"><div class="feed-card-tabs feed-card-clearfix" data-sudaclick="feed_nav"><div class="feed-card-tab-firstTab" style="width:60px;"><span id="feedCardTabFirstTab" style="width:40px;" class="feed-card-tab-tabi feed-card-tab-tabi-selected" data-lid="-2000">最新</span></div><div class="feed-card-tab-tabContainer" style="width: 598px;"><div id="feedCardConfigurableTabs" class="feed-card-tab-ctabs feed-card-clearfix"></div><div id="feedCardMoreTabsTrigger" class="feed-card-tab-more-trigger" style="display:none;">更多<i></i></div></div><div class="feed-card-tab-lastTab" suda-uatrack="key=index_feed&amp;value=float_setting" style="display: none;"><span class="feed-card-tab-tabi" id="feedCardSettingsTrigger">兴趣设置</span></div></div><div class="feed-card-tab-more" id="feedCardMoreTabs" style="display: none; right: 0px;"></div><div class="feed-card-tab-edit" id="feedCardTabEditor" data-sudaclick="posi-setting" style="display:none;"><div class="feed-card-tab-select" id="feedCardEditStep1"><div class="feed-card-tab-edit-col"><div class="feed-card-tab-edit-tit feed-card-clearfix"><h5>我的栏目：</h5><p>请点击选择您所感兴趣的栏目</p></div><div class="feed-card-tab-edit-cols feed-card-clearfix" id="feedCardEditCols"></div></div></div><div class="feed-card-tab-reorder" style="display:none;" id="feedCardEditStep2"><div class="feed-card-tab-edit-tit feed-card-clearfix"><p>您可以拖拽调整显示顺序</p></div><div class="feed-card-tab-reorder-c feed-card-clearfix" id="feedCardEditSelectW"></div></div><div class="feed-card-tab-edit-step feed-card-clearfix"><p id="feedCardEditTip"></p><div class="feed-card-tab-edit-steps"><a href="javascript:;" class="prev" id="feedCardEditPrev" style="display:none;" suda-uatrack="key=index_feed&amp;value=setting_btn_prev">上一步</a><a href="javascript:;" class="next" id="feedCardEditNext" suda-uatrack="key=index_feed&amp;value=setting_btn_next">下一步</a><a href="javascript:;" class="done" id="feedCardEditDone" style="display:none;" suda-uatrack="key=index_feed&amp;value=setting_btn_save">完成</a></div></div></div><div class="feed-card-tab-toast" id="feedCardTabToast" style="display:none;"><div id="feedCardTabToastC"></div><a href="javascript:;" id="feedCardTabToastClose">Close</a><span></span></div><div class="feed-card-tab-labels2" id="feedCardLabels" style="display:none;"><a href="javascript;" class="feed-card-tab-labels-toggle" id="feedCardLabelsToggle">更多</a><div class="feed-card-tab-labels-c feed-card-clearfix" id="feedCardLabelsC"></div></div></div><div class="feed-card-tag-tip" id="feedCardTagTip" suda-uatrack="key=index_feed&amp;value=tag_tip" style="display:none;"><div>喜欢“<em id="feedCardTagTipLabel"></em>”？<a href="javascript;" id="feedCardTagTipAdd">马上订阅</a>欣赏最精彩内容~</div><a href="javascript;" id="feedCardTagTipClose">关闭</a></div><div class="feed-card-select-tag" id="feedCardSelectTag" style="display:none;"><div class="feed-card-select-tag-will">欲添加的的标签：<span id="feedCardSelectWillTag"></span></div><div class="feed-card-select-tag-close"><a href="javascript;" id="feedCardSelectTagClose">关闭</a></div><div class="feed-card-select-tags feed-card-clearfix" id="feedCardSelectTagLabels"></div><div class="feed-card-select-tag-tip feed-card-clearfix"><p id="feedCardSelectTagTip"></p><a href="javascript;" id="feedCardSelectTagDone" class="disable">完成</a></div></div><div class="feed-card-notification2" id="feedCardNotification2" style="display:none;"></div><div class="feed-card-notification" id="feedCardNotification" style="display:none;" suda-uatrack="key=index_feed&amp;value=notification"></div><div class="feed-card-content" id="feedCardContent" data-sudaclick="feed_list"><div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:0:0" class="undefined"><a href="http://finance.sina.com.cn/china/gncj/2016-04-04/doc-ifxqxcnr5256543.shtml?cre=financepagepc&amp;mod=f&amp;loc=1&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">私人海葬渐兴：游艇俱乐部推出天价“撒海”服务</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/china/gncj/2016-04-04/doc-ifxqxcnr5256543.shtml?cre=financepagepc&amp;mod=f&amp;loc=1&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:0:0" target="_blank">私人海葬渐兴 游艇俱乐部天价“撒海”昨日，北京长青园。逝者的骨灰被埋葬在木槿之下，地面不留姓名，每棵木槿会有相应的编号。昨日，北京长青园，骨灰深埋区，摆满祭品。</a><a href="http://finance.sina.com.cn/china/gncj/2016-04-04/doc-ifxqxcnr5256543.shtml?cre=financepagepc&amp;mod=f&amp;loc=1&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:0:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">今天01:40</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/京津冀" target="_blank">京津冀</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/海葬" target="_blank">海葬</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/清明节" target="_blank">清明节</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnr5256543','0', 0, '5', 'http://finance.sina.com.cn/china/gncj/2016-04-04/doc-ifxqxcnr5256543.shtml?cre=financepagepc&amp;mod=f&amp;loc=1&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:0:0" target="_blank">评论(28)</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'私人海葬渐兴：游艇俱乐部推出天价“撒海”服务',url:'http://doc.sina.cn/?id=comos:fxqxcnr5256543'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnr5256543_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnr5256543"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnr5256543_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnr5256543'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:1:0" class="undefined"><a href="http://finance.sina.com.cn/hy/20160329/103824501232.shtml?cre=financepagepc&amp;mod=f&amp;loc=2&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">刘东华：人类文明应朝着绿色发展</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/hy/20160329/103824501232.shtml?cre=financepagepc&amp;mod=f&amp;loc=2&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:1:0" target="_blank"> 新浪财经讯 “2016中国绿公司年会北京媒体见面会”于2016年3月29日举行。上图为中国企业家俱乐部创始人、副理事长、正和岛创始人兼首席架构师刘东华。</a><a href="http://finance.sina.com.cn/hy/20160329/103824501232.shtml?cre=financepagepc&amp;mod=f&amp;loc=2&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:1:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">2016年 3月29日 10:38</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/绿公司年会" target="_blank">绿公司年会</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/中国企业家俱乐部" target="_blank">中国企业家俱乐部</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/绿公司" target="_blank">绿公司</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','31-1-24501232','0', 1, 'undefined', 'http://finance.sina.com.cn/hy/20160329/103824501232.shtml?cre=financepagepc&amp;mod=f&amp;loc=2&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:1:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'刘东华：人类文明应朝着绿色发展',url:'http://doc.sina.cn/?id=gsps:31-1-24501232'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_31-1-24501232_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_31-1-24501232"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_31-1-24501232_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, '31-1-24501232'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:2:0" class="undefined"><a href="http://finance.sina.com.cn/roll/2016-02-25/doc-ifxpvutf3317965.shtml?cre=financepagepc&amp;mod=f&amp;loc=3&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">官方鼓励鼓励家庭成员合葬 高价墓地市场或将降温</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/roll/2016-02-25/doc-ifxpvutf3317965.shtml?cre=financepagepc&amp;mod=f&amp;loc=3&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:2:0" target="_blank">官方鼓励合葬 有助遏制“高价墓地” 中新网2月25日电（财经频道 孙建永）未来，售价数万元甚至上百万元的高价墓地市场可能要降温了。</a><a href="http://finance.sina.com.cn/roll/2016-02-25/doc-ifxpvutf3317965.shtml?cre=financepagepc&amp;mod=f&amp;loc=3&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:2:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">2016年 2月25日 01:02</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/墓地" target="_blank">墓地</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/投资" target="_blank">投资</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/合葬" target="_blank">合葬</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxpvutf3317965','0', 2, '9', 'http://finance.sina.com.cn/roll/2016-02-25/doc-ifxpvutf3317965.shtml?cre=financepagepc&amp;mod=f&amp;loc=3&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:2:0" target="_blank">评论(13)</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'官方鼓励鼓励家庭成员合葬 高价墓地市场或将降温',url:'http://doc.sina.cn/?id=comos:fxpvutf3317965'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxpvutf3317965_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxpvutf3317965"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxpvutf3317965_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxpvutf3317965'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:3:0" class="undefined"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnp8452998.shtml?cre=financepagepc&amp;mod=f&amp;loc=4&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">一场不破坏原有生态的农资生态革命</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnp8452998.shtml?cre=financepagepc&amp;mod=f&amp;loc=4&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:3:0" target="_blank">来源： 农民日报 记者王玉琪 冯克 李纯 “沃农资”运营短短半年，就在山东17个地市“收割”了10900多家村级加盟零售商。农资电商究竟如何落地...</a><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnp8452998.shtml?cre=financepagepc&amp;mod=f&amp;loc=4&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:3:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月2日 11:53</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/齐商银行" target="_blank">齐商银行</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/运营商" target="_blank">运营商</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/公司产业" target="_blank">公司产业</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnp8452998','0', 3, 'undefined', 'http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnp8452998.shtml?cre=financepagepc&amp;mod=f&amp;loc=4&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:3:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'一场不破坏原有生态的农资生态革命',url:'http://doc.sina.cn/?id=comos:fxqxcnp8452998'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnp8452998_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnp8452998"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnp8452998_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnp8452998'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:4:0" class="undefined"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=5&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">苏宁投资集团成“第二总部” 五大产业生态协同</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=5&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:4:0" target="_blank">　　苏宁投资集团成“第二总部” 五大产业生态协同　　屈丽丽　　伴随苏宁互联网零售模式的定型，大消费、大服务生态体系的构建...</a><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=5&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:4:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月2日 04:55</div><div class="feed-card-tags"></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnr5197875','0', 4, 'undefined', 'http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=5&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:4:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'苏宁投资集团成“第二总部” 五大产业生态协同',url:'http://doc.sina.cn/?id=comos:fxqxcnr5197875'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnr5197875_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnr5197875"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnr5197875_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnr5197875'); return false;"><span>╱╲</span> 收起</a></div></div><div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:5:0" class="undefined"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=6&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">苏宁投资集团成“第二总部” 五大产业生态协同</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=6&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:5:0" target="_blank">　　苏宁投资集团成“第二总部” 五大产业生态协同　　屈丽丽　　伴随苏宁互联网零售模式的定型，大消费、大服务生态体系的构建...</a><a href="http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=6&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:5:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月2日 04:55</div><div class="feed-card-tags"></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnr5197875','0', 0, 'undefined', 'http://finance.sina.com.cn/roll/2016-04-02/doc-ifxqxcnr5197875.shtml?cre=financepagepc&amp;mod=f&amp;loc=6&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:0:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'苏宁投资集团成“第二总部” 五大产业生态协同',url:'http://doc.sina.cn/?id=comos:fxqxcnr5197875'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnr5197875_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnr5197875"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnr5197875_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnr5197875'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:6:0" class="undefined"><a href="http://finance.sina.com.cn/money/nmetal/hjzx/2016-04-01/doc-ifxqxcnp8398097.shtml?cre=financepagepc&amp;mod=f&amp;loc=7&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">威尔鑫：金市能量流动正处逆转初期 致力于追求零和游戏生态</a></h2><div class="feed-card-c feed-card-c1 feed-card-clearfix" id="videoPlayerC-1459493484"><div class="feed-card-img" style="width:130px; height:87px;"><a href="http://finance.sina.com.cn/money/nmetal/hjzx/2016-04-01/doc-ifxqxcnp8398097.shtml?cre=financepagepc&amp;mod=f&amp;loc=7&amp;r=9&amp;doct=0&amp;rfunc=74" suda-uatrack="key=index_feed&amp;value=news_click:-2000:6:0" target="_blank"><img src="http://s.img.mix.sina.com.cn/auto/resize?img=http://n.sinaimg.cn/finance/20160309/FM1h-fxqafhk7497483.jpg&amp;size=130_87" alt="威尔鑫：金市能量流动正处逆转初期 致力于追求零和游戏生态" style="width:130px; height:87px;"></a></div><div class="feed-card-txt"><a href="http://finance.sina.com.cn/money/nmetal/hjzx/2016-04-01/doc-ifxqxcnp8398097.shtml?cre=financepagepc&amp;mod=f&amp;loc=7&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:6:0" target="_blank">威尔鑫首席分析师 杨易君 零和游戏市场，没有羊群，哪来的狼群；没有羊群、狼群，哪来的狮群、虎群，哪来的“顺羊者”生态。我们要秉持的是：不与羊群抱团，也不去挑战狮...</a><a href="http://finance.sina.com.cn/money/nmetal/hjzx/2016-04-01/doc-ifxqxcnp8398097.shtml?cre=financepagepc&amp;mod=f&amp;loc=7&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:6:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月1日 14:51</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/威尔鑫" target="_blank">威尔鑫</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/耶伦" target="_blank">耶伦</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/黄金投资" target="_blank">黄金投资</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnp8398097','0', 1, '0', 'http://finance.sina.com.cn/money/nmetal/hjzx/2016-04-01/doc-ifxqxcnp8398097.shtml?cre=financepagepc&amp;mod=f&amp;loc=7&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:1:0" target="_blank">评论(1)</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'威尔鑫：金市能量流动正处逆转初期 致力于追求零和游戏生态',url:'http://doc.sina.cn/?id=comos:fxqxcnp8398097',pic:'http://s.img.mix.sina.com.cn/auto/resize?img=http://n.sinaimg.cn/finance/20160309/FM1h-fxqafhk7497483.jpg&amp;size=130_87'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnp8398097_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnp8398097"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnp8398097_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnp8398097'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:7:0" class="undefined"><a href="http://finance.sina.com.cn/stock/e/20160401/132824522893.shtml?cre=financepagepc&amp;mod=f&amp;loc=8&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">建筑工程业：PPP落地大年与环保转型 荐6股</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/stock/e/20160401/132824522893.shtml?cre=financepagepc&amp;mod=f&amp;loc=8&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:7:0" target="_blank">首次覆盖建筑转型 PPP 模式、环保的公司，给予增持评级。1)PPP 模式实现表外融资，项目施工时经营活动才表现在财务报表内，作为项目公司股东将缓解建筑公司施工环节垫资压...</a><a href="http://finance.sina.com.cn/stock/e/20160401/132824522893.shtml?cre=financepagepc&amp;mod=f&amp;loc=8&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:7:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月1日 13:28</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/建筑" target="_blank">建筑</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/腾达建设" target="_blank">腾达建设</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/投资" target="_blank">投资</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','31-1-24522893','0', 2, 'undefined', 'http://finance.sina.com.cn/stock/e/20160401/132824522893.shtml?cre=financepagepc&amp;mod=f&amp;loc=8&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:2:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'建筑工程业：PPP落地大年与环保转型 荐6股',url:'http://doc.sina.cn/?id=gsps:31-1-24522893'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_31-1-24522893_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_31-1-24522893"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_31-1-24522893_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, '31-1-24522893'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:8:0" class="undefined"><a href="http://finance.sina.com.cn/stock/thirdmarket/2016-04-01/doc-ifxqxcnr5141470.shtml?cre=financepagepc&amp;mod=f&amp;loc=9&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">中喜生态拟5000万元设立子公司 深度挖掘林下经济</a></h2><div class="feed-card-c"><div class="feed-card-txt"><a href="http://finance.sina.com.cn/stock/thirdmarket/2016-04-01/doc-ifxqxcnr5141470.shtml?cre=financepagepc&amp;mod=f&amp;loc=9&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:8:0" target="_blank"> 新浪财经讯 3月31日，中喜生态发布公告称公司拟出资5000万元设立全资子公司喜生有机农业科技有限公司，标的公司主营农业科技信息咨询、家禽、家畜、水产品养殖等。</a><a href="http://finance.sina.com.cn/stock/thirdmarket/2016-04-01/doc-ifxqxcnr5141470.shtml?cre=financepagepc&amp;mod=f&amp;loc=9&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:8:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月1日 10:40</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/中喜生态" target="_blank">中喜生态</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/投资" target="_blank">投资</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnr5141470','0', 3, 'undefined', 'http://finance.sina.com.cn/stock/thirdmarket/2016-04-01/doc-ifxqxcnr5141470.shtml?cre=financepagepc&amp;mod=f&amp;loc=9&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:3:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'中喜生态拟5000万元设立子公司 深度挖掘林下经济',url:'http://doc.sina.cn/?id=comos:fxqxcnr5141470'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnr5141470_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnr5141470"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnr5141470_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnr5141470'); return false;"><span>╱╲</span> 收起</a></div></div> <div class="feed-card-item"><h2 suda-uatrack="key=index_feed&amp;value=news_click:-2000:9:0" class="undefined"><a href="http://finance.sina.com.cn/roll/2016-04-01/doc-ifxqxcnp8352573.shtml?cre=financepagepc&amp;mod=f&amp;loc=10&amp;r=9&amp;doct=0&amp;rfunc=74" target="_blank">三特索道重组标的暴利离谱 实控人抛开妻子暴富？</a></h2><div class="feed-card-c feed-card-c1 feed-card-clearfix" id="videoPlayerC-1459465895"><div class="feed-card-img" style="width:130px; height:87px;"><a href="http://finance.sina.com.cn/roll/2016-04-01/doc-ifxqxcnp8352573.shtml?cre=financepagepc&amp;mod=f&amp;loc=10&amp;r=9&amp;doct=0&amp;rfunc=74" suda-uatrack="key=index_feed&amp;value=news_click:-2000:9:0" target="_blank"><img src="http://image.sinajs.cn/newchart/png/k/cn/sz002159.png" alt="三特索道重组标的暴利离谱 实控人抛开妻子暴富？" style="width:130px; height:87px;"></a></div><div class="feed-card-txt"><a href="http://finance.sina.com.cn/roll/2016-04-01/doc-ifxqxcnp8352573.shtml?cre=financepagepc&amp;mod=f&amp;loc=10&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-summary" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:9:0" target="_blank">中国经济网编者按：三特索道拟 24.82亿元收购枫彩生态100%股权。重组方案发布后令投资者拍案惊奇。方案显示，枫彩生态2015年1-4月实现营业收入7607.50万元，净利润6134...</a><a href="http://finance.sina.com.cn/roll/2016-04-01/doc-ifxqxcnp8352573.shtml?cre=financepagepc&amp;mod=f&amp;loc=10&amp;r=9&amp;doct=0&amp;rfunc=74" class="feed-card-txt-detail" rel="nofollow" suda-uatrack="key=index_feed&amp;value=news_click:-2000:9:0" target="_blank">[详细]</a></div></div><div class="feed-card-a feed-card-clearfix"><div class="feed-card-time">4月1日 07:11</div><div class="feed-card-tags"><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/三特索道" target="_blank">三特索道</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/投资" target="_blank">投资</a><a suda-uatrack="key=index_feed&amp;value=news_label_click" href="http://tags.news.sina.com.cn/财经热点" target="_blank">财经热点</a></div><div class="feed-card-actions"><a href="javascript:;" onclick="__SinaFeedCard__.showComment(this, 'cj','comos-fxqxcnp8352573','0', 4, 'undefined', 'http://finance.sina.com.cn/roll/2016-04-01/doc-ifxqxcnp8352573.shtml?cre=financepagepc&amp;mod=f&amp;loc=10&amp;r=9&amp;doct=0&amp;rfunc=74'); return false;" class="feed-card-comment" suda-uatrack="key=index_feed&amp;value=news_comment_click:4:0" target="_blank">评论</a><span class="feed-card-spliter">|</span><span id="bdshare" class="bdshare_t bds_tools get-codes-bdshare feed-card-share" data="text:'三特索道重组标的暴利离谱 实控人抛开妻子暴富？',url:'http://doc.sina.cn/?id=comos:fxqxcnp8352573',pic:'http://image.sinajs.cn/newchart/png/k/cn/sz002159.png'"><span class="bds_more">分享</span></span></div></div><div style="display:none; margin-top:10px;" class="feed-card-comment-w" data-id="feedCardComment_comos-fxqxcnp8352573_w"><div class="feed-card-comment-top" data-id="feedCardCommentTop_comos-fxqxcnp8352573"><em>◆</em><span>◆</span></div><div class="feed-card-comment-c" data-id="feedCardComment_comos-fxqxcnp8352573_c"></div><a href="javascript:;" class="feed-card-comment-close" onclick="__SinaFeedCard__.hideComment(this, 'comos-fxqxcnp8352573'); return false;"><span>╱╲</span> 收起</a></div></div></div></div><div class="feed-card-loading feed-card-loading0" style="display: none;"><img src="http://i1.sinaimg.cn/home/main/ipadwww14/04/loading.gif" width="30" height="30"></div><div class="feed-card-page" style="display: block;"><span class="pagebox_pre_nolink">上一页</span><span class="pagebox_num_nonce">1</span><span class="pagebox_num" data-page="1"><a href="javascript:void 0;">2</a></span><span class="pagebox_num" data-page="2"><a href="javascript:void 0;">3</a></span><span class="pagebox_num" data-page="3"><a href="javascript:void 0;">4</a></span><span class="pagebox_num" data-page="4"><a href="javascript:void 0;">5</a></span><span class="pagebox_next"><a href="javascript:void 0;">下一页</a></span><span class="pagebox_next next5"><a href="javascript:void 0;">下5页</a></span></div></div></div>
    </div>
</div>

<!-- d_location为悬浮结束定位 -->
<div id="d_location" style="visibility:hidden; height:0px; font-size:0px;"></div>
<!-- 广告位浮动修改js 1005 begin -->
<script charset="gbk" src="http://news.sina.com.cn/js/87/content2014/d_location.js"></script>
<!-- 广告位浮动修改js 1005 end -->

<!-- 微博推荐 begin -->
<link rel="stylesheet" href="http://news.sina.com.cn/css/268/2011/1110/17/weibo-all.css">
<link rel="stylesheet" href="http://news.sina.com.cn/css/87/content2014/weiboGroup.css">
<!-- 微博推荐 end -->

<!-- 正文页下四张图片通栏 begin-->
<iframe class="sina-iframe-content" frameborder="0" height="147" width="660" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-07-02/8.html?from=new_content_4pic"></iframe>
<!-- 正文页下四张图片通栏 end-->



<div class="tb-ad0" style="margin-top:20px;">
             <!-- 评论下方640*180通栏 begin -->
            <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000045745" data-ad-status="done" data-ad-offset-left="99" data-ad-offset-top="1932" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:640px;display:block;position:relative;"><iframe width="640px" height="180px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="javascript:'<html><body style=background:transparent;></body></html>'" id="sinaadtk_sandbox_id_0" style="float:left;" name="sinaadtk_sandbox_id_0"></iframe></ins></ins>
            <script>(sinaads = window.sinaads || []).push({});</script>
            <!-- 评论下方640*180通栏 end -->








</div>
             <!-- 正文页左下画中画广告 begin -->
            <script language="javascript" type="text/javascript" src="http://d2.sina.com.cn/d1images/button/rotator.js"></script>
            <script type="text/javascript">
              (function(){
                var adScript = document.createElement('script');
                adScript.src = 'http://d1.sina.com.cn/litong/zhitou/sinaads/demo/changwy/link/cj_left_hzh_20160122.js';
                document.getElementsByTagName('head')[0].appendChild(adScript);
              })();
            </script>
            <!-- 正文页左下画中画广告 end -->








<!-- 热点商讯 begin -->
<!-- 热点商讯 begin -->
    <div class="Ad_02 adNone" id="PublicRelation11">
      <div id="ztsh">
        <div class="zhitou_sheng">
          <h2><strong>聚焦</strong></h2>
          <dl>
            <dd>
    <script>
        (function (d, s, id) {
            var s, n = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            s = d.createElement(s);
            s.id = id;
            s.setAttribute('charset', 'utf-8');
            s.src = '//d' + Math.floor(0 + Math.random() * (9 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js';
            n.parentNode.insertBefore(s, n);
        })(document, 'script', 'sinaads-script');
    </script>
            <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000021062" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:150px;display:block;position:relative;"><a href="http://sax.sina.com.cn/mfp/click?type=3&amp;t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDAyMTA2MgkwY2UyMzIzMC1jZmFiLTRhZWUtOTEwOC00ZWE5ODYzNGJjMWQJODgxXzI5MTEJMTUwOAlfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwMjEwNjJ8dmVyc2lvbjpwYzo0LjAJdl96b25lOjMwMjAwMCwzMDIwMDAJMzAyMDAwfDMwMjAwMAk1NzQyMjU5OTAzCU5CMTYwMzA2OTIJLQk4ODEJQUUJLQk4CS0JLQktCS0JLQktCS0JLQkyCS0Jc3RyYXRlZ3lfbHJfY3RyCTIJOQlyYkdyb3VwOjU0Nw%3D%3D&amp;url=http%3A%2F%2Fphoto.sina.com.cn%2F&amp;captcha=1069054787944536297&amp;viewlog=false" name="res1333" id="res1333" target="_blank"><img src="http://img.amp.ad.sina.com.cn/rb/client/b4ae08df05ae4c9c93d2f1c8fc74db87.jpg" alt=""><span></span><em></em></a></ins></ins>
            <script>(sinaads = window.sinaads || []).push({
                  params : {
                    sinaads_ad_tpl : '<a href="#{link0}" name="res1333" id="res1333" target="_blank"><img src="#{src0}" alt="#{src1}"><span></span><em>#{src1}</em></a>'
                  }
              });</script>
            </dd>
            <dd>
            <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000021063" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:150px;display:block;position:relative;"><a href="http://sax.sina.com.cn/mfp/click?type=3&amp;t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDAyMTA2MwlkMWEwYjJmNC0zYzZmLTQ2ZjgtODAxYy1kZjBmMDVmYTM3NWUJODgwXzI5MTAJMTUwNglfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwMjEwNjN8dmVyc2lvbjpwYzo0LjAJdl96b25lOjMwMjAwMCwzMDIwMDAJMzAyMDAwfDMwMjAwMAk1NzQyMjU5OTAzCU5CMTYwMzA2OTIJLQk4ODAJQUUJLQk4CS0JLQktCS0JLQktCS0JLQkyCS0Jc3RyYXRlZ3lfbHJfY3RyCTIJOQlyYkdyb3VwOjU0Ng%3D%3D&amp;url=http%3A%2F%2Fphoto.sina.com.cn%2Fwit%2F&amp;captcha=3149126793547676733&amp;viewlog=false" name="res1333" id="res1333" target="_blank"><img src="http://img.amp.ad.sina.com.cn/rb/client/6ad6bda49d4948299134cef2451b2f46.jpg" alt=""><span></span><em></em></a></ins></ins>
            <script>(sinaads = window.sinaads || []).push({
                  params : {
                    sinaads_ad_tpl : '<a href="#{link0}" name="res1333" id="res1333" target="_blank"><img src="#{src0}" alt="#{src1}"><span></span><em>#{src1}</em></a>'
                  }
              });</script>
            </dd>
            <dd>
            <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000055077" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:150px;display:block;position:relative;"><a href="http://sax.sina.com.cn/mfp/click?type=3&amp;t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDA1NTA3NwlmODBjNjM0Zi0xMDU3LTQxNTQtOWRjNi02YmJmNDRlOGJlZDgJODgyXzI5MTIJMTUwOQlfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwNTUwNzd8dmVyc2lvbjpwYzo0LjAJdl96b25lOjMwMjAwMCwzMDIwMDAJMzAyMDAwfDMwMjAwMAk1NzQyMjU5OTAzCU5CMTYwMzA2OTIJLQk4ODIJQUUJLQk4CS0JLQktCS0JLQktCS0JLQkyCS0Jc3RyYXRlZ3lfbHJfY3RyCTIJOQlyYkdyb3VwOjU0OA%3D%3D&amp;url=http%3A%2F%2Faipai.sina.com.cn%2Findex%2Fview%2F&amp;captcha=-7619175459506092490&amp;viewlog=false" name="res1333" id="res1333" target="_blank"><img src="http://img.amp.ad.sina.com.cn/rb/client/d76958c8cef8427280cbaf28f95eb49d.jpg" alt=""><span></span><em></em></a></ins></ins>
            <script>(sinaads = window.sinaads || []).push({
                  params : {
                    sinaads_ad_tpl : '<a href="#{link0}" name="res1333" id="res1333" target="_blank"><img src="#{src0}" alt="#{src1}"><span></span><em>#{src1}</em></a>'
                  }
              });</script>
            </dd>
            <dd>
            <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000055078" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:150px;display:block;position:relative;"><a href="http://sax.sina.com.cn/mfp/click?type=3&amp;t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJaHR0cDovL2ZpbmFuY2Uuc2luYS5jb20uY24vcm9sbC8yMDE2LTA0LTA0L2RvYy1pZnhxeGNuejkwOTM2ODEuc2h0bWwJUERQUzAwMDAwMDA1NTA3OAk5MzdlOTg2NC1jYWRlLTRlZmQtYmUwYy02MjkxM2VhZDk1MGEJODgzXzI5MTQJMTUxMAlfdl96b25lOjMwMjAwMCwzMDIwMDB8dXNlcl9nZW5kZXI6NTAxfHVzZXJfZ3JvdXA6OTAzLDkwNyw5MDgsOTEwfHZfem9uZTozMDIwMDAsMzAyMDAwfHVzZXJfdGFnOjIwMDAxLDIwNTMwLDIwODQ3LDIwOTU0LDIwOTU2LDIxMDYxLDIxMDYyLDIxMjcwfG1vYmlsZV9icmFuZDoxMjA5fG1vYmlsZV9icm93c2VyOjgwNXx2X2lzcDoxMzAwfHdhcF9vczo3MDJ8dXNlcl9hZ2U6NjAzLDYwMiw2MDF8cG9zOlBEUFMwMDAwMDAwNTUwNzh8dmVyc2lvbjpwYzo0LjAJdl96b25lOjMwMjAwMCwzMDIwMDAJMzAyMDAwfDMwMjAwMAk1NzQyMjU5OTAzCU5CMTYwMzA2OTIJLQk4ODMJQUUJLQk4CS0JLQktCS0JLQktCS0JLQkyCS0Jc3RyYXRlZ3lfbHJfY3RyCTIJOQlyYkdyb3VwOjU0OQ%3D%3D&amp;url=http%3A%2F%2Fnews.sina.com.cn%2Fzxt%2F&amp;captcha=-673677357857964383&amp;viewlog=false" name="res1333" id="res1333" target="_blank"><img src="http://img.amp.ad.sina.com.cn/rb/client/1cc904ee611f44c4ad7a3df54f53ed40.jpg" alt=""><span></span><em></em></a></ins></ins>
            <script>(sinaads = window.sinaads || []).push({
                  params : {
                    sinaads_ad_tpl : '<a href="#{link0}" name="res1333" id="res1333" target="_blank"><img src="#{src0}" alt="#{src1}"><span></span><em>#{src1}</em></a>'
                  }
              });</script>
            </dd>
          </dl>
          <dl>
            <dd>
              <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000009825" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="text-decoration: none;"><a href="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNQ%3D%3D&amp;url=http%3A%2F%2Fwww.gdxxb.com%2Fad43%2F%3Fa%3Db%26pos%3D1272&amp;sign=3d626a989e663a3b" target="_blank" data-link="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNQ%3D%3D&amp;url=http%3A%2F%2Fwww.gdxxb.com%2Fad43%2F%3Fa%3Db%26pos%3D1272&amp;sign=3d626a989e663a3b" onmousedown="return sinaadToolkit.url.fortp(this, event);">战神刺影合击纯元宝PK</a></ins><script>(sinaads = window.sinaads || []).push({});</script>
            </dd>
            <dd>
              <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000009826" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="text-decoration: none;"><a href="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNg%3D%3D&amp;url=http%3A%2F%2Fpfpclick.sina.com.cn%2Fclick%2Fcpcclick.php%3Fad%3DEALGHzd%2F925%2FvzwlAc64oqrXV9kOLCgIDQjPj2PQtUHjqqTFAfWC%2Fgsfvqix6z45YHcyQcSCgklyfWtdfgJUXRKEqPiY3q%2F36q7jdGdUHeI%3D&amp;sign=e1310bfaf7f7f709" target="_blank" data-link="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNg%3D%3D&amp;url=http%3A%2F%2Fpfpclick.sina.com.cn%2Fclick%2Fcpcclick.php%3Fad%3DEALGHzd%2F925%2FvzwlAc64oqrXV9kOLCgIDQjPj2PQtUHjqqTFAfWC%2Fgsfvqix6z45YHcyQcSCgklyfWtdfgJUXRKEqPiY3q%2F36q7jdGdUHeI%3D&amp;sign=e1310bfaf7f7f709" onmousedown="return sinaadToolkit.url.fortp(this, event);">冰火至尊轻变精品裁决</a></ins><script>(sinaads = window.sinaads || []).push({});</script>
            </dd>
            <dd>
              <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000009827" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="text-decoration: none;"><a href="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNw%3D%3D&amp;url=http%3A%2F%2Fsms.sina.com.cn%2Fact%2F090819%2Fzazhitoutiao.html&amp;sign=04f7c64237875f6e" target="_blank" data-link="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyNw%3D%3D&amp;url=http%3A%2F%2Fsms.sina.com.cn%2Fact%2F090819%2Fzazhitoutiao.html&amp;sign=04f7c64237875f6e" onmousedown="return sinaadToolkit.url.fortp(this, event);">精彩生活快来看</a></ins><script>(sinaads = window.sinaads || []).push({});</script>
            </dd>
            <dd>
              <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000009828" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="1953" style="text-decoration: none;"><a href="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyOA%3D%3D&amp;url=http%3A%2F%2Fnews.sina.com.cn%2Fc%2F2013-12-31%2F023929122853.shtml&amp;sign=eb0c9ea844c7bb8f" target="_blank" data-link="http://sax.sina.com.cn/click?type=bottom&amp;t=UERQUzAwMDAwMDAwOTgyOA%3D%3D&amp;url=http%3A%2F%2Fnews.sina.com.cn%2Fc%2F2013-12-31%2F023929122853.shtml&amp;sign=eb0c9ea844c7bb8f" onmousedown="return sinaadToolkit.url.fortp(this, event);">手机电子书免费下载</a></ins><script>(sinaads = window.sinaads || []).push({});</script>
            </dd>
          </dl>
      </div>
    </div>
    </div>
    <style type="text/css">
    .zhitou_sheng{width:638px;border:1px #e5e5e5 solid;padding-bottom:14px; font-family:'宋体';margin:10px auto 0;overflow:hidden;}
    .zhitou_sheng h2{height:37px;line-height:37px;border-bottom:1px dashed #e5e5e5;}
    .zhitou_sheng h2 strong{font-size:16px;float:left;padding-left:8px; font-family:'微软雅黑'; color:#333;}
    .zhitou_sheng h2 strong em{ font-family:'宋体';}
    .zhitou_sheng dl{margin:14px auto 0;}
    /*.zhitou_sheng dl dt{float:left;margin-right:8px;display:inline;width:145px;height:105px;border:1px #e5e5e5 solid;position:relative}
    .zhitou_sheng dl dt img{ float:left; border:none;}
    .zhitou_sheng dl dt span{width:145px;height:20px;position:absolute;bottom:0;left:0;background:#586063;filter:alpha(opacity=50);opacity:0.5;}
    .zhitou_sheng dl dt em{width:145px;height:20px;font-size:12px;line-height:20px;text-align:center;z-index:5;color:#fff;position:absolute;bottom:0;left:0;}*/
    .zhitou_sheng dl dd{ list-style-type:none;list-style-image:none;font-size:12px;float:left;line-height:22px;margin-left:7px;width:150px;}
    .zhitou_sheng dl dd a{ color:#666;}
    .zhitou_sheng dl dd a:hover{text-decoration:underline; color:#C00;}
    .clear{height:0;line-height:0;font-size:0;overflow:hidden;clear:both;}
    .Ad_02 {height:190px; display:block;}
    .Ad_02 .Mblk_03 .newAddBlk .list_009_f14{padding-left:10px;}
    .Ad_02 .Mblk_03{float:left;}
    .Ad_02 .adNode{border:1px solid #E5E5E5; width:316px; margin-top:15px; height:190px;}
    .Ad_02 .M_Menu_01 .newAddtit2 {padding-top:4px;float:right;padding-right:10px;}
    .Ad_02 .M_Menu_01 .selected{border-right:1px solid #E5E5E5; padding-right:10px;}
    .Ad_02 .Mblk_03 .newAddBlk li { background: url("http://i0.sinaimg.cn/ent/deco/2012/0907/content/ent_zxh_0816_01v3.png") no-repeat scroll -47px -92px transparent; padding-left: 13px; height: 22px; line-height: 22px;}
    .Ad_02 .Mblk_03 .newAddBlk2{border-top:1px dotted #ccc; margin-top:3px;}
    .Ad_02 .Mblk_03 .conBlk{border-bottom:1px solid #fff; padding-top:10px;}
    .Ad_02 .Mblk_03 .newAddBlk .zypicBlk{padding-top:2px;padding-bottom:0px;}

    .M_Menu_01 .selected {color: #010101; font-family: "微软雅黑"; font-size: 14px; height: 32px; line-height: 32px; padding-left: 14px; float:left;}
    .newAddtit2 {float:left; line-height:32px; padding-left:20px; color:#626262;}
    .conBlk {border-bottom:1px dotted #CCCCCC; border-top:1px dotted #CCCCCC;}
    </style>
    <!-- 热点商讯 end -->
<!-- 热点商讯 end -->
<!-- 通栏 begin -->
<ins class="sinaads sinaads-fail" data-ad-pdps="PDPS000000057948" style="margin-top:15px;" data-ad-status="done" data-ad-offset-left="89" data-ad-offset-top="2167"></ins>
<script>(sinaads = window.sinaads || []).push({});</script>
<!-- 通栏 end -->
<!-- 应用中心、新浪公益、互动活动、热点推荐 begin -->
<style type="text/css">
    #ccont02{display:none;}
    #ccont03{display:none;}
    #ccont04{display:none;}
    #ccont05{display:none;}
</style>
<div class="ad_content ad_06 adNone" id="PublicRelation5">
    <div class="cmenu01">
        <span id="cbtn01">应用中心</span>
        <span id="cbtn02">新浪公益</span>
        <span id="cbtn03">新浪游戏</span>
        <span id="cbtn04">互动活动</span>
        <span id="cbtn05">热点推荐</span>
    </div>
    <div class="ad_cont_03">
        <!-- 应用中心、新浪公益、新浪游戏 begin -->
			<!-- 图铃下载、新浪公益、新浪游戏 begin -->
<div id="ccont01">
	<ul class="clist cpot clearfix">
	<!-- 第一行 应用 -->
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=84472&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">一生良师益友：海词词典</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=117176&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">保护隐私与安全：应用锁</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=84623&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">股民的第一选择：同花顺</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=1237478&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">定位家人的位置：跟屁虫</a></li>
<!-- 第二行 游戏 -->
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2348348&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">私人大游艇：快来造船吧</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2350477&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">一个人狩猎：狙击手猎鹿</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2349239&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">和敌人战斗：萌军飞行队</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2349139&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">恐怖的对决：CS反恐精英</a></li>
<!-- 第三行 应用 -->
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=84453&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">路程全掌握：凯立德导航</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=101351&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">高清图片分享：奇思壁纸</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=118425&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">捕捉精彩瞬间：特效相机</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=127035&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">有热度有态度：人民日报</a></li>
<!-- 第四行 游戏 -->
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2349109&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">飞越天际：飞天滑板高手</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2349154&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">等你征服：叛乱武士之战</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2350985&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">魔幻旅：小小魔兽大战争</a></li>
<li><a rel="nofollow" href="http://app.sina.com.cn/appdetail.php?appID=2351044&amp;f=p_wenjiao&amp;w=p_wenjiao" target="_blank">斗魂：超合体魔术机器人</a></li>
	</ul>
</div>

<div id="ccont02">
	<ul class="clist cpot clearfix">
	<li><a rel="nofollow" href="http://gongyi.weibo.com/together?source=10" target="_blank">微博益起来感恩行动</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/2013yfjhhf/index.shtml" target="_blank">2013捐一元爱心送营养</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/2013yjjgyj/index.shtml" target="_blank">2013壹基金公益映像节</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/slfchina/index.shtml" target="_blank">水立方中国公益平台</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/alishuigongyi/index.shtml" target="_blank">阿里巴巴公益广告大赛</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/syfz/index.shtml" target="_blank">思源方舟防灾减灾</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/z/ayhx2013/index.shtml" target="_blank">2013爱佑慈善晚宴</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/gy/canon2013/index.html" target="_blank">佳能影像公益</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/82.html" target="_blank">贫困儿童图书漂流箱项目</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/62.html" target="_blank">福特汽车环保奖</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/70.html" target="_blank">女童权益保护全球行动</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/77.html" target="_blank">奔驰自然保护项目</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/69.html" target="_blank">佳能希望小学色彩教室</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/81.html" target="_blank">卡夫希望厨房</a></li>
<li><a rel="nofollow" href="http://gongyi.sina.com.cn/project/66.html" target="_blank">妇基会母亲包邮活动</a></li>
<li><a href="http://darentong.weibo.com" target="_blank">微博-达人通</a></li>
	</ul>
</div>

<div id="ccont03">
	<ul class="clist cpot clearfix">
	<li><a rel="nofollow" href="http://ka.sina.com.cn/18046" target="_blank">《九阴真经》唯我独尊礼包</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17458" target="_blank">《梦幻西游手游版》夏日情谊卡 </a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17743" target="_blank">《星际战甲》新浪高级特权礼包 </a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17735" target="_blank">《问道》天书奇谭至尊礼包</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17856" target="_blank">《新倩女幽魂》新浪特权礼包 </a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17974" target="_blank">《热血传奇》15周年专区礼包 </a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/16010" target="_blank">《大话西游2》人气公测礼包 </a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/13979" target="_blank">《倩女幽魂2》新浪1888元白金卡</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/14951" target="_blank">《第三把剑》新浪特权皇钻礼包</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/16573" target="_blank">《奇迹MU》 新浪独家礼包</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/14775" target="_blank">《龙门虎将》新浪定制礼包</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/17474" target="_blank">《虎豹骑》二次测试码</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/index/mmo/6-0-0-0-0-0-0#flist" target="_blank">角色扮演类新手卡</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/index/mmo/8-0-0-0-0-0-0#flist" target="_blank">射击类游戏新手卡</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/index/mmo/7-0-0-0-0-0-0#flist" target="_blank">动作类游戏新手卡</a></li>
<li><a rel="nofollow" href="http://ka.sina.com.cn/index/mmo/10-0-0-0-0-0-0#flist" target="_blank">策略类游戏新手卡</a></li>
	</ul>
</div>
<!-- 图铃下载、新浪公益、新浪游戏 end -->


        <!-- 应用中心、新浪公益、新浪游戏 end -->
        <div id="ccont04">
            <ul class="clist cpot clearfix">
		    <!--互动活动 -->
		    	<li><a href="http://zhuanlan.sina.com.cn/" target="_blank" color="red" rel="nofollow">新浪专栏：读名家知天下</a></li>
	<li><a href="http://home.zhuanlan.sina.com.cn/?p=contribute&amp;s=contri&amp;a=postView" target="_blank" rel="nofollow">想成为专栏作家？戳这里</a></li>

	<li><a href="http://hunan.sina.com.cn/news/b/2014-12-15/detail-iawzunex6480218.shtml" target="_blank" rel="nofollow">强势围观！政务微博大事件！</a> </li>


	<li><a href="http://hunan.sina.com.cn/zt/2014weibo/" target="_blank" rel="nofollow">快来看！湖南微博有大事！</a></li>

	<li><a href="http://blog.sina.com.cn/lm/hotshare/" target="_blank" rel="nofollow">最火博文 大家都在看</a></li>

	<li><a href="http://blog.sina.com.cn/lm/z/taiwanyeshimeishi/" target="_blank" rel="nofollow">一大波台湾美食正在向你逼近！</a></li>
		    <!--互动活动 end-->
            </ul>
        </div>
        <div id="ccont05">
            <ul class="clist cpot clearfix">
				      <li><a href="http://finance.sina.com.cn/stock/?c=spr_web_sina_zhengwen_fin_t001" target="_blank" color="red">[财经]股市行情查询</a></li>

      <li><a href="http://finance.sina.com.cn/calc/?c=spr_web_sina_zhengwen_fin_t002" target="_blank">[财经]理财计算器</a></li>

      <li><a href="http://digi.sina.com.cn?c=spr_web_sina_zhengwen_tech_t001" target="_blank">[科技]数码产品库</a></li>

      <li><a href="http://video.sina.com.cn/movie/?c=spr_web_sina_zhengwen_video_t001" target="_blank">[视频]最热影视大片</a></li>

      <li><a href="http://travel.sina.com.cn/places/?c=spr_web_sina_zhengwen_travel_t001" target="_blank">[旅游]国内外景点查询</a></li>

      <li><a href="http://baby.sina.com.cn/tools/?c=spr_web_sina_zhengwen_baby_t001" target="_blank">[育儿]育儿实用工具库</a></li>

      <li><a href="http://data.auto.sina.com.cn/?c=spr_web_sina_zhengwen_auto_t001" target="_blank">[汽车]车型查询</a></li>

      <li><a href="http://eladies.sina.com.cn/beauty/chanpinku/?c=spr_web_sina_zhengwen_lady_t001" target="_blank">[女性]化妆品产品库</a></li>

      <li><a href="http://astro.sina.com.cn/luck/?c=spr_web_sina_zhengwen_astro_t001" target="_blank">[星座]星座运势查询</a></li>

      <li><a href="http://yingxun.ent.sina.com.cn/?c=spr_web_sina_zhengwen_ent_t001" target="_blank">[娱乐]影讯查询</a></li>

      <li><a href="http://tvguide.ent.sina.com.cn/channel/1/cctv1/wed.html?c=spr_web_sina_zhengwen_ent_t002" target="_blank">[娱乐]电视节目表</a></li>

      <li><a href="http://edu.sina.com.cn/college/?c=spr_web_sina_zhengwen_edu_t001" target="_blank">[教育]大学院校查询</a></li>
            </ul>
        </div>
    </div>
</div>
<!-- 应用中心、新浪公益、互动活动、热点推荐 end -->
<!--竟价开始-->
<style type="text/css">
.M_Menu_01 .selected {color: #010101; font-family: "微软雅黑"; font-size: 14px; height: 32px; line-height: 32px; padding-left: 14px; float:left;}
.newAddtit2 {float:left; line-height:32px; padding-left:20px; color:#626262;}
.conBlk {border-bottom:1px dotted #CCCCCC; border-top:1px dotted #CCCCCC;}
.qyfwBlk .zyconBlk{width:300px;}
.color666 a,.botSxBlk li a,.botSxBlk li { color: #666666!important; }
.color666 a:hover,.botSxBlk li a:hover{color:#CC0000!important;}
.botSxBlk {padding-left:20px;}
.botSxBlk li{width:150px!important; display:inline;padding-left:2px;float:left;}
.qyfwBlk .conBlk li {}
.qyfwBlk .zyconBlk {padding-left:11px!important;}

.ad_07 .M_Menu_01 .newAddtit2 {padding-top:4px;float:left;padding-left:22px;}
.ad_07 .M_Menu_01 .selected{border-right:1px solid #E5E5E5; padding-right:10px;}
</style>

<div class="ad_content ad_07 adNone" id="PublicRelation13">
<!--企业服务 beign-->
<script language="javascript" type="text/javascript" src="http://pfp.sina.com.cn/iframe/14/2011/0517/47zhongshiwangmeng.js"></script>
<!--企业服务 end-->
	<div class="botSxBlk">
		<ul>
			<ul>
			<li>·<!--ADS:begin=PDPS000000004395:{B1E2617B-634E-4C00-843F-10C63241D3DB}--><a href="http://city.finance.sina.com.cn/city/wlmp.html" target="_blank">城市热点节庆活动</a><!--nwy/net/A-->

<!--ADS:end--></li>
			<li>·<!--ADS:begin=PDPS000000004396:{61656FAF-3FCE-480F-B59C-A9E6F62C1D15}--><a href="http://city.finance.sina.com.cn/city/dhcs.html" target="_blank">新浪《对话城市》</a><!--nwy/net/A-->

<!--ADS:end--></li>
			<li>·<!--ADS:begin=PDPS000000004397:{7D0CAE62-0F2A-47E8-BA0B-9AFE528E0032}--><a href="http://mail.sina.net/daili/daili.htm" target="_blank">诚招合作伙伴</a><!--nwy/net/A-->

<!--ADS:end--></li>
			<li>·<!--ADS:begin=PDPS000000004398:{56DFCDD8-ED8A-479A-B44C-AA24C0D7DABA}--><a href="http://www.sinanet.com" target="_blank">新企邮上线更优惠</a><!--ae/net/A-->

<!--ADS:end--></li>
		</ul>
		</ul>
	</div>
</div>




<!--竟价结束-->
                <!--正文下部end-->


            </div>
            <div class="right">
                <!--右侧部分-->
                    <div class="side-c side-c0" data-sudaclick="blk_zhuanlan">
        <!-- zhuanlan -->
        <iframe class="sina-iframe-content" frameborder="0" height="127" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-06-26/5.html?from=new_content_zl"></iframe>
    </div>
    <div class="side-c">
    <!--  画中画00 begin -->
	<div class="ad_05 pip00adNone" id="PublicRelation3">
     <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000042135" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="403" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJN2EyMjcwYjEtYjU2NC00MWU0LWJjMDUtMGU4ZDU0NWU1ODcyCTM5NTE4MAkxODAzMzAyNjc3X1BJTlBBSS1DUEMJMTI4NjIxCTE0ODA1MAkwLjAwMTgxNTQxCTEJdHJ1ZQlQRFBTMDAwMDAwMDQyMTM1CTEwODgwMzYJUEMJaW1hZ2UJLQkwfDM5NTE4MHxudWxsCW51bGwJMQktMQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=RQwZ4qPfQn6uoYI3sWQ8ZQDBqGuu92UUW1nozg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DNDUwYzE5ZTItYTNkZi00MjdlLWFlYTEtODIzN2IxNjQzYzY1CTE3CVBEUFMwMDAwMDAwNDIxMzUJMTA4ODAzNgkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fcp.lvya.com%252Fproduct%252Fdrink%252Fxhlj%252Fstandard%252F%253Fsrc%253Dsina-D-ccss-300500%26sina_sign%3De5422eaa3299cbc9&amp;sign=2f207ef0be4f1723" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJN2EyMjcwYjEtYjU2NC00MWU0LWJjMDUtMGU4ZDU0NWU1ODcyCTM5NTE4MAkxODAzMzAyNjc3X1BJTlBBSS1DUEMJMTI4NjIxCTE0ODA1MAkwLjAwMTgxNTQxCTEJdHJ1ZQlQRFBTMDAwMDAwMDQyMTM1CTEwODgwMzYJUEMJaW1hZ2UJLQkwfDM5NTE4MHxudWxsCW51bGwJMQktMQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=RQwZ4qPfQn6uoYI3sWQ8ZQDBqGuu92UUW1nozg%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DNDUwYzE5ZTItYTNkZi00MjdlLWFlYTEtODIzN2IxNjQzYzY1CTE3CVBEUFMwMDAwMDAwNDIxMzUJMTA4ODAzNgkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fcp.lvya.com%252Fproduct%252Fdrink%252Fxhlj%252Fstandard%252F%253Fsrc%253Dsina-D-ccss-300500%26sina_sign%3De5422eaa3299cbc9&amp;sign=2f207ef0be4f1723" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d4.sina.com.cn/pfpghc2/201603/28/d63b03169066487088227fb9d6f8ac81.jpg" style="width:300px;height:500px;border:0" alt="http://d4.sina.com.cn/pfpghc2/201603/28/d63b03169066487088227fb9d6f8ac81.jpg"></a></ins></ins>
     <script>window._sinaads_kzhzh_order = "PDPS000000042135";(sinaads = window.sinaads || []).push({});</script>
</div>
    <!--  画中画00 end -->








    </div>
    <div class="side-c side-c2" data-sudaclick="blk_photo">
        <!-- photo -->
        <iframe class="sina-iframe-content" frameborder="0" height="190" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-06-24/1.html?from=new_content_tjxw" id="blk_n001_017"></iframe>
    </div>
    <div class="side-c">
    <!--  画中画01 begin -->
    <div class="ad_05 adNone" id="PublicRelation4">
    <script>
                (function (d, s, id) {
                    var s, n = d.getElementsByTagName(s)[0];
                    if (d.getElementById(id)) return;
                    s = d.createElement(s);
                    s.id = id;
                    s.setAttribute('charset', 'utf-8');
                    s.src = '//d' + Math.floor(0 + Math.random() * (9 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js';
                    n.parentNode.insertBefore(s, n);
                })(document, 'script', 'sinaads-script');
    </script>
    <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000028572" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="597" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration: none; margin: 0px auto; width: 300px; display: block; position: relative; opacity: 1;"><!--fakesize:sinaadtk_swf_uid_0|300|250--><embed width="300" height="250" wmode="opaque" flashvars="clickTAG=http%3A%2F%2Fsax.sina.com.cn%2Fdsp%2Fclick%3Ft%3DMjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJNGRjYjU5NTYtYTI2ZS00YzVkLTk3OWItOTFiNTRjOThmYTk3CTM5MTI2NQk1NzY4OTY2ODU1X1BJTlBBSS1DUEMJMTI2ODIzCTY0MjMyNwkzLjQ5NjAxRS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDI4NTcyCTEwNzkxMDYJUEMJZmxhc2gJLQkwfDM5MTI2NXxudWxsCW51bGwJMQkxNQ%3D%3D%26userid%3D114.251.216.113_1459489959.63940%26p%3DIc3DolSUTVWyncGo%252F8kiW5bcKwRq8jrFYh%252FAqQ%253D%253D%26url%3Dhttp%253A%252F%252Fsax.sina.com.cn%252Fclick%253Ftype%253D2%2526t%253DMjFjZGMzYTItNTQ5NC00ZDU1LWIyOWQtYzFhOGZmYzkyMjViCTE3CVBEUFMwMDAwMDAwMjg1NzIJMTA3OTEwNgkxCVJUQgkt%2526id%253D17%2526url%253Dhttp%25253A%25252F%25252Fvdax.youzu.com%25252F%25253Fq%25253D160324MWXB22o%252526SET_A%25253DPDPS000000028572%252526SET_B%25253D391265%252526SET_C%25253D1079106%252526SET_D%25253D4dcb5956-a26e-4c5d-979b-91b54c98fa97%252526SET_E%25253D126823%252526SET_F%25253D1%2526sina_sign%253Db4a483f1764f0ecf%26sign%3D49603329c287fdb9" name="sinaadtk_swf_uid_0" align="middle" src="http://d6.sina.com.cn/pfpghc2/201603/24/4632c61fd73f4dd98a55d2eacd7f533c.swf" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer"><a style="position:absolute;background:#fff;opacity:0;filter:alpha(opacity=0);width:300px;height:250px;left:0;top:0" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJNGRjYjU5NTYtYTI2ZS00YzVkLTk3OWItOTFiNTRjOThmYTk3CTM5MTI2NQk1NzY4OTY2ODU1X1BJTlBBSS1DUEMJMTI2ODIzCTY0MjMyNwkzLjQ5NjAxRS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDI4NTcyCTEwNzkxMDYJUEMJZmxhc2gJLQkwfDM5MTI2NXxudWxsCW51bGwJMQkxNQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=Ic3DolSUTVWyncGo%2F8kiW5bcKwRq8jrFYh%2FAqQ%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMjFjZGMzYTItNTQ5NC00ZDU1LWIyOWQtYzFhOGZmYzkyMjViCTE3CVBEUFMwMDAwMDAwMjg1NzIJMTA3OTEwNgkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fvdax.youzu.com%252F%253Fq%253D160324MWXB22o%2526SET_A%253DPDPS000000028572%2526SET_B%253D391265%2526SET_C%253D1079106%2526SET_D%253D4dcb5956-a26e-4c5d-979b-91b54c98fa97%2526SET_E%253D126823%2526SET_F%253D1%26sina_sign%3Db4a483f1764f0ecf&amp;sign=49603329c287fdb9" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJNGRjYjU5NTYtYTI2ZS00YzVkLTk3OWItOTFiNTRjOThmYTk3CTM5MTI2NQk1NzY4OTY2ODU1X1BJTlBBSS1DUEMJMTI2ODIzCTY0MjMyNwkzLjQ5NjAxRS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDI4NTcyCTEwNzkxMDYJUEMJZmxhc2gJLQkwfDM5MTI2NXxudWxsCW51bGwJMQkxNQ==&amp;userid=114.251.216.113_1459489959.63940&amp;p=Ic3DolSUTVWyncGo%2F8kiW5bcKwRq8jrFYh%2FAqQ%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMjFjZGMzYTItNTQ5NC00ZDU1LWIyOWQtYzFhOGZmYzkyMjViCTE3CVBEUFMwMDAwMDAwMjg1NzIJMTA3OTEwNgkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fvdax.youzu.com%252F%253Fq%253D160324MWXB22o%2526SET_A%253DPDPS000000028572%2526SET_B%253D391265%2526SET_C%253D1079106%2526SET_D%253D4dcb5956-a26e-4c5d-979b-91b54c98fa97%2526SET_E%253D126823%2526SET_F%253D1%26sina_sign%3Db4a483f1764f0ecf&amp;sign=49603329c287fdb9" target="_blank" onmousedown="return sinaadToolkit.url.fortp(this, event);"></a></ins></ins><script>(sinaads = window.sinaads || []).push({});</script>

    </div>
    <!--  画中画01 end -->
	<div style="margin-top:10px;">
    <!-- 画中画01下推荐 -->
    <ins class="sinaere" data-tpl="1" data-pos="P_F_T_1" data-w="300" data-h="150" data-num="1" data-channel="finance" data-status="done" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;display:block;overflow:hidden;width:300px;height:150px;"><iframe width="300" height="150" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="//d5.sina.com.cn/litong/zhitou/sinaads/test/e-recommendation/tpl/eretpl_1_300_150.html?1459744667077" name="%7B%22status%22%3A%7B%22msg%22%3A%22user%20profile%20failed%22%2C%22code%22%3A0%2C%22total%22%3A60%7D%2C%22data%22%3A%5B%7B%22price%22%3A%22240%22%2C%22info%22%3A%225bf927685794348191ecd82c6eccd15e%7C14%7C1%22%2C%22url%22%3A%22http%3A%2F%2Ffashion.sina.com.cn%2Fcosmetics%2Fproduct%2F15930%3Fcre%3Dad_business%26mod%3Dg%26loc%3D1%26r%3D14%26doct%3D0%26rfunc%3D74%22%2C%22doct%22%3A0%2C%22thumb%22%3A%22http%3A%2F%2Fwww.sinaimg.cn%2Flx%2Fbeauty%2Fchanpinku%2Fsofina%2FU5120P8T246D15930F6951DT20120228175256.jpg%22%2C%22reason%22%3A14%2C%22bpic%22%3A0%2C%22meta%22%3A%22mbrand%3D7piG%26mtype1%3DRFu%26mtype2%3DDfB%26mprice%3D240%22%2C%22brand%22%3A%22%E8%8B%8F%E8%8F%B2%E5%A8%9C%2FSOFINA%22%2C%22uuid%22%3A%225bf927685794348191ecd82c6eccd15e%22%2C%22func%22%3A%22%E9%AD%85%E5%8A%9B%E5%BD%A9%E5%A6%86%22%2C%22type1%22%3A%22%E5%BD%A9%E5%A6%86%22%2C%22name%22%3A%22%E6%98%A0%E7%BE%8E%E7%84%95%E9%87%87%E8%B4%B4%E5%90%88%E7%B2%89%E9%A5%BC%22%2C%22type2%22%3A%22%E7%B2%89%E9%A5%BC%22%7D%5D%2C%22referrer%22%3A%22http%3A%2F%2Ffinance.sina.com.cn%2Froll%2F2016-04-04%2Fdoc-ifxqxcnz9093681.shtml%22%2C%22pos%22%3A%22P_F_T_1%22%7D"></iframe></ins></ins>
    <script>
        (sinaere = window.sinaere || []).push({});
    </script>
    </div>








        <div class="sp15"></div>
    </div>
<!-- ad_left_button_300_100 -->

    <div class="side-c side-c4">
    <!-- 右侧300*150矩形 begin -->
    <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000046929" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="597" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><iframe width="300px" height="150px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="javascript:'<html><body style=background:transparent;></body></html>'" id="sinaadtk_sandbox_id_1" style="float:left;" name="sinaadtk_sandbox_id_1"></iframe></ins></ins>
    <script>(sinaads = window.sinaads || []).push({});</script>
    <!-- 右侧300*150矩形 end -->








    </div>
    <div class="side-c side-c5" data-sudaclick="blk_video">
        <!-- video -->
        <iframe class="sina-iframe-content" frameborder="0" height="324" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-07-01/7.html?from=new_content_tjsp"></iframe>
    </div>
	<div class="side-c">
		    <!-- 通发页右侧按300*100按钮 begin -->
    <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000056863" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="891" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><iframe width="300px" height="150px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="javascript:'<html><body style=background:transparent;></body></html>'" id="sinaadtk_sandbox_id_2" style="float:left;" name="sinaadtk_sandbox_id_2"></iframe></ins></ins>
    <script>(sinaads = window.sinaads || []).push({});</script>
    <!-- 通发页右侧按300*100按钮 end -->








        <div class="sp15"></div>
    </div>
    <div class="side-c side-c6" id="PublicRelation10">
        <iframe class="sina-iframe-content" id="blk_n001_014" frameborder="0" height="152" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://d3.sina.com.cn/litong/zhitou/sources/20141016.html"></iframe>
    </div>


    <div class="side-c" data-sudaclick="blk_blog">
        <!-- blog -->
        <iframe class="sina-iframe-content" frameborder="0" height="340" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-06-24/2.html?from=new_content_rdbk" id="blk_n001_018"></iframe>
    </div>
<!-- 右侧理财师推广 -->
             <div class="side-c" id="template-lcs" data-sudaclick="suda_723_r_lcs"><div class="lcs0"><h3><a hidefocus="true" href="http://licaishi.sina.com.cn/web/plan" target="_blank">新浪理财师</a><a hidefocus="true" href="http://licaishi.sina.com.cn/web/plan" target="_blank" class="more">更多</a></h3><div class="lcs0_scrollpics clearfix" id="lcs0_scrollpics" style="width: 300px; overflow: hidden;"><div style="overflow: hidden; zoom: 1; width: 32766px;"><div style="overflow: hidden; zoom: 1; float: left;"><div class="lcs0_item"><div class="lcs0_i_hd clearfix"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/3100796395/133984?fr=finance_tab" target="_blank"><img class="lcs0_i_prt" width="50" height="50" src="http://tp2.sinaimg.cn/3100796395/180/1" alt=""></a><div class="lcs0_i_hd_r"><p class="lcs0_i_p0"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/3100796395/133984?fr=finance_tab" class="lcs0_i_name" target="_blank">何金生</a><s class="lcs0_up"></s><span class="lcs0_i_zq">英达资本</span></p><p class="lcs0_i_p1">24天赚23% 同期大盘仅涨9%</p></div></div><div class="lcs0_i_plan clearfix"><div class="lcs0_i_plan_l clearfix"><h3><a hidefocus="true" href="http://licaishi.sina.com.cn/plan/33984?fr=finance_tab" target="_blank" title="何金生利滚利计划04期">何金生利滚利计划04期</a></h3><div class="lcs0_i_earn">目标收益<br>(3个月)</div><div class="lcs0_i_earn_no">20%</div></div><a hidefocus="true" class="lcs0_i_ask" href="http://licaishi.sina.com.cn/plan/33984?fr=finance_tab" target="_blank">我要加入</a></div></div><div class="lcs0_item"><div class="lcs0_i_hd clearfix"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/5751518553/133133?fr=finance_tab" target="_blank"><img class="lcs0_i_prt" width="50" height="50" src="http://s3.licaishi.sina.com.cn/180/151114/1759274921.jpeg" alt=""></a><div class="lcs0_i_hd_r"><p class="lcs0_i_p0"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/5751518553/133133?fr=finance_tab" class="lcs0_i_name" target="_blank">汪春来</a><s class="lcs0_up"></s><span class="lcs0_i_zq">中信建投证券</span></p><p class="lcs0_i_p1">29天即赚15% 同期大盘跌0.29%</p></div></div><div class="lcs0_i_plan clearfix"><div class="lcs0_i_plan_l clearfix"><h3><a hidefocus="true" href="http://licaishi.sina.com.cn/plan/33133?fr=finance_tab" target="_blank" title="汪春来潜龙冲天计划03期">汪春来潜龙冲天计划03期</a></h3><div class="lcs0_i_earn">目标收益<br>(3个月)</div><div class="lcs0_i_earn_no">25%</div></div><a hidefocus="true" class="lcs0_i_ask" href="http://licaishi.sina.com.cn/plan/33133?fr=finance_tab" target="_blank">我要加入</a></div></div><div class="lcs0_item"><div class="lcs0_i_hd clearfix"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/1358242513/134059?fr=finance_tab" target="_blank"><img class="lcs0_i_prt" width="50" height="50" src="http://tp2.sinaimg.cn/1358242513/180/5635946768/1" alt=""></a><div class="lcs0_i_hd_r"><p class="lcs0_i_p0"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/1358242513/134059?fr=finance_tab" class="lcs0_i_name" target="_blank">车睿</a><s class="lcs0_up"></s><span class="lcs0_i_zq">新浪特约</span></p><p class="lcs0_i_p1">69天即赚20% 同期大盘仅涨3%</p></div></div><div class="lcs0_i_plan clearfix"><div class="lcs0_i_plan_l clearfix"><h3><a hidefocus="true" href="http://licaishi.sina.com.cn/plan/34059?fr=finance_tab" target="_blank" title="车睿择时顺势计划02期">车睿择时顺势计划02期</a></h3><div class="lcs0_i_earn">目标收益<br>(3个月)</div><div class="lcs0_i_earn_no">20%</div></div><a hidefocus="true" class="lcs0_i_ask" href="http://licaishi.sina.com.cn/plan/34059?fr=finance_tab" target="_blank">我要加入</a></div></div></div></div></div><div class="lcs0_dots" id="lcs0_dots"><span class="dotItem" title="��1ҳ"></span><span class="dotItem" title="��2ҳ"></span><span class="dotItemOn" title="��3ҳ"></span></div><div class="lcs0_read"><div class="lcs0_read_i clearfix"><a hidefocus="true" class="lcs0_read_lb0" href="http://licaishi.sina.com.cn/web/index?ind_id=0&amp;fee=paid&amp;fr=finance_tab" target="_blank">付费阅读</a><div class="lcs0_txt"><a hidefocus="true" href="http://licaishi.sina.com.cn/planner/1670404053/0?fr=finance_tab" target="_blank">吴伟光</a>：<a hidefocus="true" class="lcs0_txt_lk" href="http://licaishi.sina.com.cn/view/438460?ind_id=1&amp;fr=finance_tab" target="_blank">吴旺鑫：原油37.70下方高空，黄金难以摆脱震</a></div><span class="lcs0_txt_time">11:24</span></div><div class="lcs0_read_i clearfix"><a hidefocus="true" class="lcs0_read_lb1" href="http://licaishi.sina.com.cn/web/askList?fr=finance_tab" target="_blank">我要问股</a><div class="lcs0_txt"><a hidefocus="true" class="lcs0_txt_lk" href="http://licaishi.sina.com.cn/ask/581775?fr=finance_tab" target="_blank">问：老师那个股票是什么什么价位进比较好您说的老情人股票？</a></div><span class="lcs0_txt_time">已回答</span></div></div></div></div>
<script type="text/javascript" src="http://i3.sinaimg.cn/ty/sinaui/scrollpic/scrollpic2012070701.min.js"></script>

<script>
(function($){
    function lcsTemplate(data){
        var view_data = data.view_data,
            view_plan = data.view_plan;

        var tplArr1 = [];
        $.each(view_plan,function(index,item){
            var temp = [
                '<div class="lcs0_item">',
                    '<div class="lcs0_i_hd clearfix">',
                        '<a hidefocus="true"  href="' + item.name_url + '" target="_blank"><img class="lcs0_i_prt" width="50" height="50" src="' + item.user_img + '" alt=""></a>',
                        '<div class="lcs0_i_hd_r">',
                            '<p class="lcs0_i_p0">',
                                '<a hidefocus="true"  href="' + item.name_url + '" class="lcs0_i_name" target="_blank">' + item.user_name + '</a>',
                                '<s class="lcs0_up"></s>',
                                '<span class="lcs0_i_zq">' + item.company_name + '</span>',
                            '</p>',
                            '<p class="lcs0_i_p1">' + item.recommend_reason + '</p>',
                        '</div>',
                    '</div>',
                    '<div class="lcs0_i_plan clearfix">',
                        '<div class="lcs0_i_plan_l clearfix">',
                            '<h3><a hidefocus="true"  href="' + item.p_url + '" target="_blank" title="' + item.name + '">' + item.name + '</a></h3>',
                            '<div class="lcs0_i_earn">目标收益<br />(' + item.Days + ')</div>',
                            '<div class="lcs0_i_earn_no">' + item.p_ratio + '</div>',
                        '</div>',
                        '<a hidefocus="true"  class="lcs0_i_ask" href="' + item.p_url + '" target="_blank">我要加入</a>',
                    '</div>',
                '</div>'
            ].join('');
            tplArr1.push(temp);
        });

        var tplArr2 = [
            '<div class="lcs0">',
                '<h3><a hidefocus="true"  href="http://licaishi.sina.com.cn/web/plan" target="_blank">新浪理财师</a><a hidefocus="true"  href="http://licaishi.sina.com.cn/web/plan" target="_blank" class="more">更多</a></h3>',
                '<div class="lcs0_scrollpics clearfix" id="lcs0_scrollpics">',
                    tplArr1.join(''),
                '</div>',
                '<div class="lcs0_dots" id="lcs0_dots"></div>',
                '<div class="lcs0_read">',
                    '<div class="lcs0_read_i clearfix">',
                        '<a hidefocus="true"  class="lcs0_read_lb0" href="http://licaishi.sina.com.cn/web/index?ind_id=0&fee=paid&fr=finance_tab" target="_blank">付费阅读</a>',
                        '<div class="lcs0_txt"><a hidefocus="true"  href="' + view_data.vname_url + '" target="_blank">' + view_data.vname + '</a>：<a hidefocus="true"  class="lcs0_txt_lk" href="' + view_data.vtitle_url + '" target="_blank">' + view_data.vtitle + '</a></div><span class="lcs0_txt_time">' + view_data.vtime + '</span>',
                    '</div>',
                    '<div class="lcs0_read_i clearfix">',
                        '<a hidefocus="true"  class="lcs0_read_lb1" href="http://licaishi.sina.com.cn/web/askList?fr=finance_tab" target="_blank">我要问股</a>',
                        '<div class="lcs0_txt"><a hidefocus="true"  class="lcs0_txt_lk" href="' + view_data.q_url + '" target="_blank">' + view_data.q_title + '？</a></div><span class="lcs0_txt_time">已回答</span>',
                    '</div>',
                '</div>',
            '</div>'
        ];

        return tplArr2.join('');
    }

    var sp0 = new ScrollPic();
    sp0.scrollContId = 'lcs0_scrollpics';
    sp0.dotListId = 'lcs0_dots';
    sp0.pageWidth = 300;
    sp0.frameWidth = 300;
    sp0.upright = false;
    sp0.circularly = false;
    sp0.autoPlay = true;
    sp0.listEvent = 'onmouseover';
    var lcs_scroll_dom=function(){
        var lcs_dom={
           ajax_url:'http://licaishi.sina.com.cn/api/financeIndex2',
           template:lcsTemplate,
           dom:$('#template-lcs'),
           get_data:function(){
              var that=this;
              $.ajax({
                   url:that.ajax_url,
                   dataType:'jsonp',
                   data:{get_planner:1},
                   success:function(d){
                       var plan_list=[];
                       var random=parseInt(Math.random()*3);
                       var i1=0;
                       while(i1<3)
                       {
                          if(random>d.data.plan.length-1)
                          {
                             random=0;
                          }

                          plan_list.push(d.data.plan[random]);
                          random++;
                          i1++;

                       }
                       that.YWP(d.data.view,d.data.question,plan_list);
                   }
              });
           },
           YWP:function(view,question,plan){
                  var view_data={},view_plan_list=[],all_view={};
                  view_data.vtitle=view.title||'';
                  view_data.vname=view.p_name||'';
                  view_data.vname_url='http://licaishi.sina.com.cn/planner/'+view.p_uid+'/0?fr=finance_tab';
                  view_data.vtitle_url='http://licaishi.sina.com.cn/view/'+view.v_id+'?ind_id=1&fr=finance_tab';
                  view_data.vtime=view.time_format;
                  view_data.q_title='问：'+clipString(question.content,0,52)||'';
                  view_data.q_url='http://licaishi.sina.com.cn/ask/'+question.q_id+'?fr=finance_tab';

                for(var i=0;i<plan.length;i++)
                {
                var view_plan={};
                view_plan.name=plan[i].new_plan_info.name||'';
                view_plan.user_name=plan[i].planner_info.name||'';
                view_plan.name_url='http://licaishi.sina.com.cn/planner/'+plan[i].planner_info.p_uid+'/1'+plan[i].new_plan_info.pln_id+'?fr=finance_tab';
                view_plan.p_url='http://licaishi.sina.com.cn/plan/'+plan[i].new_plan_info.pln_id+'?fr=finance_tab';
                view_plan.recommend_reason=plan[i].recommend_reason||'';
                view_plan.company_name=plan[i].planner_info.company_name||'';
                view_plan.user_img=plan[i].planner_info.image||'';
                var _sttime=_plantime(plan[i].new_plan_info.start_date);
                var _retime=_plantime(plan[i].new_plan_info.end_date);
                var start_time=new Date(_sttime[0],_sttime[1],_sttime[2]).getTime(),
                    real_end_time=new Date(_retime[0],_retime[1],_retime[2]).getTime();
                var cha_date_s=real_end_time-start_time;
                var cha_date_m=Math.ceil((cha_date_s/1000)/(86400*30));
                view_plan.Days=cha_date_m+'个月';
                view_plan.ratio=(plan[i].curr_ror*100).toFixed(2)+'%';
                view_plan.p_ratio=(plan[i].new_plan_info.target_ror*100).toFixed(0)+'%';
                view_plan_list.push(view_plan);
                }

                all_view={view_data:view_data,view_plan:view_plan_list};
                this.dom.html(this.template(all_view));
                sp0.initialize();//轮播
           },
           init:function(){
               this.get_data();
           }

        };
        return lcs_dom;
    }().init();
    function _toPercent (num) {
            var ret;
            num = Math.round(num * 100);
            ret = num + '%';
            return ret;
        }
    function _plantime(start){
        var str_start=start,str_end=end;
        var start={},end={};
        var arr_start=str_start.split(/-|\s|:/g);

        var plantime=_str_0(arr_start);
        return plantime;

    }
    function _str_0(arr_str){

       var arr_str=arr_str;
       for(var i=0;i<arr_str.length;i++)
       {
          arr_str[i].replace('0','');
       }
       return arr_str;
    }
    function clipString(str, a, b) {
            var s = str.replace(/([^\x00-\xff])/g, "\x00$1");
            return (s.length < b) ? str : (s.substring(a, b - 3).replace(/\x00/g, '') + '...');
       }

})(jQuery);
</script>
<!-- 右侧理财师推广 end-->

    <div class="side-c">
    <!-- 右侧300*250矩形 begin -->
    <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000043766" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="1401" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><iframe width="300px" height="250px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="javascript:'<html><body style=background:transparent;></body></html>'" id="sinaadtk_sandbox_id_3" style="float:left;" name="sinaadtk_sandbox_id_3"></iframe></ins></ins>
    <script>(sinaads = window.sinaads || []).push({});</script>
    <!-- 右侧300*250矩形 end -->








        <div class="sp15"></div>
    </div>
    <!-- 自选股, 最近访问股 -->
    <div class="side-c" data-sudaclick="suda_723_zxg">
        <iframe class="sina-iframe-content" frameborder="0" height="389" width="300" marginheight="0" marginwidth="0" scrolling="no" src="http://finance.sina.com.cn/iframe/1008/2015-06-25/3.html"></iframe>
    </div>
    <!-- 自选股, 最近访问股 end -->
    <div class="side-c">
    <!-- 画中画button start -->
    <span id="PublicRelation18" class="adNone">
    <script async="" charset="utf-8" src="http://d1.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js"></script><ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000052110" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="1694" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><iframe width="300px" height="150px" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" src="http://img.adbox.sina.com.cn/ad/1505759360-1386562732590-8419.html" name="viewTAG=http%3A%2F%2Fsax.sina.com.cn%2Fview%3Ftype%3Dbottom%26t%3DUERQUzAwMDAwMDA1MjExMA%253D%253D%26am%3D%257Bds%253A800x600%252Cfv%253A21%252Cov%253AMacIntel%257D"></iframe></ins></ins><script>(sinaads = window.sinaads || []).push({});</script>
    <!-- 画中画button end -->
	</span>








    </div>
    <div class="side-c">
        <div class="adNone pip02gn" id="PublicRelation4">
    <!-- 画中画02 start -->
    <!-- new change 2014-8-25 start -->
    <style>
    .right_fixed {position: fixed;top: 0;width: 300px;}
    .right_fixed a img{ padding: 0px;}
    </style>
    <div class="right_fixed_area_new right_fixed_area" id="rightFixedArea">
    <div id="ad_04452">
    <script async="" charset="utf-8" src="http://d0.sina.com.cn/litong/zhitou/sinaads/release/sinaads.js"></script><ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000005425" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="1694" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJZTNmNzkwOWYtZDNkNC00MzY3LWJlMGYtZTBhNTUyNTVmZTdkCTM0OTc0Mwk1ODI2ODMxMTQ4X1BJTlBBSS1DUEMJMTA3NzEzCTEyNzU1Mgk3LjYyNjgyRS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDA1NDI1CTEwOTI0OTcJUEMJaW1hZ2UJLQkwfDM0OTc0M3xudWxsCW51bGwJMQkxNg==&amp;userid=114.251.216.113_1459489959.63940&amp;p=N1fiMueWS5G2%2FSxcnqGbV8D94JB8qRfBnAZ5tQ%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMzc1N2UyMzItZTc5Ni00YjkxLWI2ZmQtMmM1YzllYTE5YjU3CTE3CVBEUFMwMDAwMDAwMDU0MjUJMTA5MjQ5NwkxCVJUQgkt%26id%3D17%26url%3Dhttps%253A%252F%252Fdessmann.tmall.com%252Fp%252Frd720140.htm%253Fspm%253Da1z10.1-b.w5001-3086128028.4.3QWzuf%26sina_sign%3D7212640f3b381efa&amp;sign=5763b5fa8af1921f" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJZTNmNzkwOWYtZDNkNC00MzY3LWJlMGYtZTBhNTUyNTVmZTdkCTM0OTc0Mwk1ODI2ODMxMTQ4X1BJTlBBSS1DUEMJMTA3NzEzCTEyNzU1Mgk3LjYyNjgyRS00CTEJdHJ1ZQlQRFBTMDAwMDAwMDA1NDI1CTEwOTI0OTcJUEMJaW1hZ2UJLQkwfDM0OTc0M3xudWxsCW51bGwJMQkxNg==&amp;userid=114.251.216.113_1459489959.63940&amp;p=N1fiMueWS5G2%2FSxcnqGbV8D94JB8qRfBnAZ5tQ%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMzc1N2UyMzItZTc5Ni00YjkxLWI2ZmQtMmM1YzllYTE5YjU3CTE3CVBEUFMwMDAwMDAwMDU0MjUJMTA5MjQ5NwkxCVJUQgkt%26id%3D17%26url%3Dhttps%253A%252F%252Fdessmann.tmall.com%252Fp%252Frd720140.htm%253Fspm%253Da1z10.1-b.w5001-3086128028.4.3QWzuf%26sina_sign%3D7212640f3b381efa&amp;sign=5763b5fa8af1921f" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d3.sina.com.cn/pfpghc2/201604/01/131f48c292fa494aae7b34751e92496f.gif" style="width:300px;height:250px;border:0" alt="http://d3.sina.com.cn/pfpghc2/201604/01/131f48c292fa494aae7b34751e92496f.gif"></a></ins></ins><script>(sinaads = window.sinaads || []).push({});</script>
    </div>
    </div>
    <!-- new change 2014-8-25 end -->
    <!-- 画中画02 end -->








        </div>
        <div class="sp15"></div>
    </div>
    <div class="side-c" data-sudaclick="suda_723_fy">
		<!--新浪智投-->
		   <!--  新浪智投 begin -->
                <style type="text/css">
        .zhitou-wrap{overflow: hidden; border-top:1px solid #d0d0d0;}
        .zhitou-header{overflow:hidden;padding:16px 0 0;}
        .zhitou-header .text{float:left;color:#000;font-size:18px;font-weight: bold;}
        .zhitou-header .more{float:right;margin-top: 4px;}
        .zhitou-content .title {overflow:hidden;display:block;color:#333;height:18px; font-size: 14px; font-weight: normal; margin:15px 0px 10px 0px;text-overflow: ellipsis;white-space: nowrap;}
        .zhitou-content .detail {overflow:hidden;display:block;color:#999;height:18px; font-size: 14px; font-weight: normal; margin:15px 0px 10px 0px;text-overflow: ellipsis;white-space: nowrap;}
        .zhitou-content .title:hover {color:#1976e8;}
        .zhitou-content .detail:hover {color:#1976e8;}
    </style>
                <div class="zhitou-wrap" id="rightSinaFuyiArea">
                    <div class="zhitou-header"> <span class="text"><a href="http://sea.sina.com.cn" target="_blank">新浪扶翼</a></span> <span class="more"><a href="http://sea.sina.com.cn" target="_blank">行业专区</a></span> </div>
                    <div class="zhitou-content">
					        <!--新浪扶翼tuigraph leitao Start-->
        <ins class="sinaads sinaads-done" data-ad-pdps="PDPS000000057665" data-ad-status="done" data-ad-offset-left="789" data-ad-offset-top="1737" style="display: block; overflow: hidden; text-decoration: none;"><ins style="text-decoration:none;margin:0px auto;width:300px;display:block;position:relative;"><a style="display:block;" href="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJODkyZmI3ZGQtNmU1OC00MDM2LWFmODQtYjE4OTNlODRjOGE2CTM4MTg4MwkxNjU5NTAyMzI0X1BJTlBBSS1DUEMJMTIxODkyCTc5ODYzCTYuMjVFLTQJMQl0cnVlCVBEUFMwMDAwMDAwNTc2NjUJMTA2OTQyOAlQQwlpbWFnZQktCTB8MzgxODgzfG51bGwJbnVsbAkxCTA=&amp;userid=114.251.216.113_1459489959.63940&amp;p=JJldbk0NS5ajPdCgwDLb2imwg8KPbSHcLQ1SiA%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMjQ5OTVkNmUtNGQwZC00Yjk2LWEzM2QtZDBhMGMwMzJkYmRhCTE3CVBEUFMwMDAwMDAwNTc2NjUJMTA2OTQyOAkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fwww.meitianying.net%252Findex.php%252Flive%252Froom%252F26%253Fsina_caijing2%26sina_sign%3D83b4040a3c18cdd3&amp;sign=0ea8ea1eba9a0dc4" target="_blank" data-link="http://sax.sina.com.cn/dsp/click?t=MjAxNi0wNC0wNCAxMjozNzo0NgkxLjIwMi4xODcuOTYJMTE0LjI1MS4yMTYuMTEzXzE0NTk0ODk5NTkuNjM5NDAJODkyZmI3ZGQtNmU1OC00MDM2LWFmODQtYjE4OTNlODRjOGE2CTM4MTg4MwkxNjU5NTAyMzI0X1BJTlBBSS1DUEMJMTIxODkyCTc5ODYzCTYuMjVFLTQJMQl0cnVlCVBEUFMwMDAwMDAwNTc2NjUJMTA2OTQyOAlQQwlpbWFnZQktCTB8MzgxODgzfG51bGwJbnVsbAkxCTA=&amp;userid=114.251.216.113_1459489959.63940&amp;p=JJldbk0NS5ajPdCgwDLb2imwg8KPbSHcLQ1SiA%3D%3D&amp;url=http%3A%2F%2Fsax.sina.com.cn%2Fclick%3Ftype%3D2%26t%3DMjQ5OTVkNmUtNGQwZC00Yjk2LWEzM2QtZDBhMGMwMzJkYmRhCTE3CVBEUFMwMDAwMDAwNTc2NjUJMTA2OTQyOAkxCVJUQgkt%26id%3D17%26url%3Dhttp%253A%252F%252Fwww.meitianying.net%252Findex.php%252Flive%252Froom%252F26%253Fsina_caijing2%26sina_sign%3D83b4040a3c18cdd3&amp;sign=0ea8ea1eba9a0dc4" onmousedown="return sinaadToolkit.url.fortp(this, event);"><img border="0" src="http://d3.sina.com.cn/pfpghc2/201603/22/69a1c3bfaa384b08b58bfba0071ab3a3.jpg" style="width:300px;height:250px;border:0" alt="http://d3.sina.com.cn/pfpghc2/201603/22/69a1c3bfaa384b08b58bfba0071ab3a3.jpg"></a></ins></ins>
		<script>(sinaads = window.sinaads || []).push({});</script>
        <!--新浪扶翼tuigraph leitao End-->
                    </div>
                </div>

     <!--  新浪智投 end -->

    </div>

                <!--右侧部分 end-->
            </div>

            <div class="comment-wrap comment-wrap-fixed" id="articleCommentWrap"> <a hidefocus="true" href="javascript:;" class="comment-close" id="sinaTextPageCommentClose">close</a>
                <div class="sina-comment-wrap" id="sinaTextPageComment" style="height: 327px;"><div class="sina-comment-form sina-comment-top" comment-type="form"><div class="hd clearfix"><span comment-type="count" href="#url" class="count"><em><a href="http://comment5.news.sina.com.cn/comment/skin/default.html?channel=cj&amp;newsid=comos-fxqxcnz9093681">0</a></em>条评论<span>|</span><em><a href="http://comment5.news.sina.com.cn/comment/skin/default.html?channel=cj&amp;newsid=comos-fxqxcnz9093681">0</a></em>人参与</span><span class="tip">我有话说</span></div><div class="bd"><div class="editor"><div class="inner"><textarea comment-type="cont" class="box" autocomplete="off" placeholder="请输入评论" value=""></textarea></div><span class="arrow"></span></div><!-- 登录信息 start --><div class="user"><div class="form-head" comment-type="head"><a href="http://weibo.com/" target="_blank" title=""><img src="http://img.t.sinajs.cn/t5/style/images/face/male_180.png" alt=""></a></div><span class="name" comment-type="name"></span><a comment-type="logout" class="logout" href="javascript:;" onclick="return false;" title="退出">退出</a></div><div class="user user-default"><div class="form-head" comment-type="head"><a href="http://weibo.com/" target="_blank"><img width="80" height="80" src="http://img.t.sinajs.cn/t5/style/images/face/male_180.png"></a></div><a action-type="login" class="login-lnk" href="javascript:;" onclick="return false;" title="登录">登录</a>|<a class="register-lnk" target="_blank" href="https://login.sina.com.cn/signup/signup.php" onclick="try{if(window._S_uaTrack){_S_uaTrack('entcomment', 'logon');}}catch(e){}">注册</a></div><!-- 登录信息 end --></div><div class="ft clearfix"><div class="face"><a href="javascript:;" class="trigger" action-type="face-toggle">表情</a></div><div comment-type="weibo" class="weibo sina-comment-chkbox" action-type="checkbox-toggle"> <i></i><span>分享到微博</span></div><!-- 发布 start --><a comment-type="submit" href="javascript:;" action-type="tip-toggle" class="comment btn btn-red btn-disabled">发布</a><!-- 发布 end --><!-- 登录与注册 start --><div class="login"></div><!-- 登录与注册前 end --></div></div> <div class="sina-comment-list " comment-type="list"><div class="hot-wrap" comment-type="hotWrap"><div class="title"><span class="name">最热评论</span> <a action-type="reflash" action-data="type=hot" class="reflash" href="javascript:;" comment-type="hotReflash">刷新</a> </div><div class="hot-loading loading"><a href="javascript:;"></a></div><div class="list" comment-type="hotList"></div></div><div class="latest-wrap" comment-type="latestWrap"><div class="title"><span class="name">最新评论</span> <a action-type="reflash" action-data="type=latest" class="reflash" href="javascript:;" comment-type="latestReflash">刷新</a> </div><div class="latest-loading loading"><a href="javascript:;"></a></div><div class="list" comment-type="latestList"></div><div class="more" action-type="" action-data="type=latest" comment-type="latestMore"><a target="_blank" href="http://comment5.news.sina.com.cn/comment/skin/default.html?channel=cj&amp;newsid=comos-fxqxcnz9093681&amp;group=0">更多精彩评论&gt;&gt;</a></div></div><div class="all-loading loading"><a href="javascript:;"></a></div></div></div>
            </div>
        </div>

        <!-- footer -->
        <div class="page-footer">
            <p><a hidefocus="true" href="http://corp.sina.com.cn/chn/" target="_blank">新浪简介</a><span class="spliter">┊</span><a hidefocus="true" href="http://corp.sina.com.cn/eng/" target="_blank">About Sina</a><span class="spliter">┊</span><a href="http://emarketing.sina.com.cn/" target="_blank">广告服务</a><span class="spliter">┊</span><a hidefocus="true" href="http://www.sina.com.cn/contactus.html" target="_blank">联系我们</a><span class="spliter">┊</span><a hidefocus="true" href="http://corp.sina.com.cn/chn/sina_job.html" target="_blank">招聘信息</a><span class="spliter">┊</span><a hidefocus="true" href="http://www.sina.com.cn/intro/lawfirm.shtml" target="_blank">网站律师</a><span class="spliter">┊</span><a hidefocus="true" href="http://english.sina.com/" target="_blank">SINA English</a><span class="spliter">┊</span><a hidefocus="true" href="https://login.sina.com.cn/signup/signup.php" target="_blank">通行证注册</a><span class="spliter">┊</span><a hidefocus="true" href="http://help.sina.com.cn/" target="_blank">产品答疑</a></p>
            <p>Copyright <span style="font-family:arial;">©</span>1996-2020 SINA Corporation, All Rights Reserved</p>
            <p>新浪公司 <a hidefocus="true" href="http://www.sina.com.cn/intro/copyright.shtml" target="_blank">版权所有</a></p>
        </div>
        <!-- /footer -->

    </div>
</div>
<!--底部部分start-->
<div class="desktop-side-tool" style="display: block;" id="desktopSideTools">
	<span class="side-tool side-tool-small comment-small" suda-uatrack="key=news_content_2014&amp;value=right_home">
		<a hidefocus="true" class="icon" href="http://www.sina.com.cn/"></a> </span> <span class="side-tool side-tool-small comment2-small" suda-uatrack="key=news_content_2014&amp;value=right_feedback"> <a hidefocus="true" class="icon" href="javascript:;"></a> </span> <span class="side-tool side-tool-small related-news-small" suda-uatrack="key=news_content_2014&amp;value=right_related"> <a hidefocus="true" class="icon" href="#relatedNewsWrap"></a> </span> <span class="side-tool side-tool-small to-top-small" suda-uatrack="key=news_content_2014&amp;value=right_top"> <a hidefocus="true" class="icon" onclick="window.scrollTo(0,1); window.location.hash=''; return false;" href="javascript:;"></a> </span> </div>
<div class="ipad-side-tool" style="display:none;"> <a hidefocus="true" href="#articleCommentWrap" class="side-tool comment" suda-uatrack="key=news_content_2014&amp;value=pad_right_cmt"> <span class="icon"></span> <span class="title" id="ipadCommentCount"></span> </a> <a hidefocus="true" href="javascript:;" class="side-tool share" id="ipadShareArticleButton" suda-uatrack="key=news_content_2014&amp;value=pad_right_share"> <span class="icon"></span> </a> <a hidefocus="true" href="javascript:;" class="side-tool favorite" id="addToFavorite3" suda-uatrack="key=news_content_2014&amp;value=pad_right_fav"> <span class="icon"></span> </a> <a hidefocus="true" href="http://comment5.news.sina.com.cn/comment/skin/feedback_1.html?channel=ly&amp;newsid=3" target="_blank" class="side-tool feedback" suda-uatrack="key=news_content_2014&amp;value=pad_right_feedback"> <span class="icon"></span> </a> <a hidefocus="true" class="side-tool related-news" href="#relatedNewsWrap" suda-uatrack="key=news_content_2014&amp;value=pad_right_related"> <span class="icon"></span> </a> <a hidefocus="true" href="javascript:;" class="side-tool to-top" onclick="window.scrollTo(0,1); window.location.hash=''; return false;" suda-uatrack="key=news_content_2014&amp;value=pad_right_totop"> <span class="icon"></span> </a> </div>
<script type="text/javascript">
    $('#ipadShareArticleButton').on('click', function(){
        bShare.more();
        return false;
    });
</script>


<!-- 收藏form -->
<div style="display:none;">
    <iframe name="scChCreateForm" style="display:none;"></iframe>
    <form id="sc_ch_form" action="" target="scChCreateForm" method="post" style="display:none;">
        <input id="scdocid" type="hidden" name="docid" value="">
        <input type="hidden" name="category" value="1">
        <input type="hidden" name="source" value="1">
        <input id="sc_ch_form_id" type="hidden" name="id" value="">
        <input id="scChCreateFormSub" type="submit">
    </form>
    <span id="sc_ch_total">0</span> </div>
<!-- /收藏form -->

<script type="text/javascript" src="http://tech.sina.com.cn/js/717/20140827/index2014/top.js"></script>
<script src="http://news.sina.com.cn/js/87/20140926/comment.3.min.js"></script>

<script type="text/javascript">
___sinacMNT___.cmnt.config.encoding = 'utf-8';
</script>

<!-- Add bdshare -->
<script type="text/javascript" id="bdshare_js" data="type=tools&amp;uid=483253" src="http://bdimg.share.baidu.com/static/js/bds_s_v2.js?cdnversion=405485"></script>

<script type="text/javascript">
    (function(exports){
        exports.bds_config = {
            // appkey
            "snsKey": {
                'tsina': 'false',
                'tqq': '',
                't163': '',
                'tsohu': ''
            },
            //  id
            'wbUid':'1618051664',
            'searchPic':false,
            'review':'off'
        };
        document.getElementById("bdshell_js").src = "http://bdimg.share.baidu.com/static/js/shell_v2.js?cdnversion=" + Math.ceil(new Date()/3600000);
    })(window);
</script>
<style type="text/css">
    #bdshare{float:none !important;font-size:13px !important;padding-bottom:0 !important;}
    #bdshare span.bds_more{display:inline !important;padding:0 !important;float:none !important;font-family:"Microsoft YaHei","微软雅黑" !important;background-image:none !important;}
    #bdshare span.bds_more:hover{color:#1976e8;}
</style>

<!--相关阅读Feed流设置-->

<script type="text/javascript">
    var FEED_CARD_INFO = {
        containerID: 'feedCard', // 容器ID
        containerWidth: 660, // 默认宽度是660
        loadType: 1, // 加载类型 1表示点击更多加载, 2表示自动加载
        autoLoadDistance: function(){
            //return $('#wb_rec').height() + 740;
            return $(document).height() - $('#relatedNewsWrap').height() - $('#relatedNewsWrap').offset().top + 100;
        }, // 如果是自动加载, 有时候feed流并没有放在最下面, 所以scrollEnd的时候要判断这个距离
        clickLoadText: '点击加载更多',
        summaryKey: 'summary', // 摘要使用字段

        supportNotification: false,// 最左边的列表是否添加提醒功能
        notificationTemplate: '有{n}条消息，点击查看',// 提醒的格式
        notificationTimeout: 1000 * 30,// 提醒的事件间隔
        pageSize: 5, // 每次加载条数

        stepSize: 2, // 加载三次之后出分页
        moreTagTemplate: '点击查看更多关于“{n}”的文章',

        /*
         * 评论相关配置
         */
        // 1. 是否支持当前页展开评论
        enablePageComment: true,
        // 2. 评论组件编码,默认是gbk
        pageCommentEncoding: 'utf-8',
        // 3. 是否显示盖楼,默认0,还可以为1
        pageCommentShowReply: 0,
        // 4. 评论显示字数
        pageCommentMaxWordCount: 110,
        // 5. 最热评论默认显示条数
        pageCommentHotPageNum: 3,
        // 6. 最新评论默认显示条数
        pageCommentFirstPageNum: 10,

        supportTabEdit: false, //是否支持兴趣设置

        toFilterNews: [], // 过滤从feed系统走，此处可置空

        isTabFixed: true,
        fixedTop: 0,

        supportKeywords: false, // 是否支持热词定制
        hotKeywords: [],
        keywords: [], // 默认选定的关键词
        maxKeywordsCount: 15,
        maxKeywordLength: 14,
        searchQuery: '',
        tagURL: 'http://tags.news.sina.com.cn',

        hotNewsCount: 200, //评论超过该数字显示热icon

        yPosition: 'auto', // 如果不固定，则给一个auto，自动计算
        tabHeight: 50,

        noDataText: '没有相关新闻',

        // 最左边固定tab
        firstTab: {
            txt: '最新',
            lid: -2000,
            css_width: 40
        },

        // 栏目分类配置
        columnInfos: {
        },
        tabs: [],
        allTabs: [],

        tabInfos: {
            'tab_-2000': {
                txt: '最新',
                lid: -2000,
                css_width: 40,

                url: 'http://cre.mix.sina.com.cn/api/v3/get?rfunc=105&fields=url&feed_fmt=1&cateid=y&cre=financepagepc&mod=f&merge=3&statics=1&this_page=1&dedup=32&pageurl=http://finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml'+ __getQuery()
            }
        },
        requireLogin: function(){
        },
        isLogin: function(){
        }
    };
</script>

<!--相关阅读Feed流设置-->

<!-- 桌面和ipad共用的js -->
<script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/feed.relatedNews.js"></script>
<!-- /桌面和ipad共用的js -->

<!-- 桌面浏览器需要的js -->
<script type="text/javascript">
    (function(){
        //var isTouchDevice = 'ontouchstart' in window;
        var _doc = document;
        if(SINA_ARTICLE_PAGE_SETTINGS.isPad){
            _doc.write('<' + 'script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/ipad.js"></' + 'script>');

        } else {
            _doc.write('<' + 'script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/slider.js"></' + 'script>');

            //if(SINA_TEXT_PAGE_INFO.weiboGroupID){
                _doc.write('<' + 'script type="text/javascript" src="http://news.sina.com.cn/js/87/20110714/205/sinalib.js"></' + 'script>');
                _doc.write('<' + 'script type="text/javascript" src="http://news.sina.com.cn/js/268/2011/1110/16/weibo-all.js"></' + 'script>');
                _doc.write('<' + 'script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/weibocard2013.js"></' + 'script>');
                _doc.write('<' + 'script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/weiboReco.js"></' + 'script>');
            //}

            _doc.write('<' + 'script type="text/javascript" src="http://n.sinaimg.cn/finance/zwy/suggestSever_cs_20151124.js"></' + 'script>');
            _doc.write('<' + 'script type="text/javascript" src="http://n.sinaimg.cn/finance/zwy/fnc_top_search_0827_20151125.js" charset="utf-8" ></' + 'script>');
            _doc.write('<' + 'script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/application.src.js"></' + 'script>');
        }
    })();
</script><script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/slider.js"></script><script type="text/javascript" src="http://news.sina.com.cn/js/87/20110714/205/sinalib.js"></script><script type="text/javascript" src="http://news.sina.com.cn/js/268/2011/1110/16/weibo-all.js"></script><script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/weibocard2013.js"></script><script type="text/javascript" src="http://news.sina.com.cn/js/87/content2014/weiboReco.js"></script><script type="text/javascript" src="http://n.sinaimg.cn/finance/zwy/suggestSever_cs_20151124.js"></script><script type="text/javascript" src="http://n.sinaimg.cn/finance/zwy/fnc_top_search_0827_20151125.js" charset="utf-8"></script><script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/application.src.js"></script>
<!-- /桌面浏览器需要的js -->


<script src="http://ent.sina.com.cn/js/470/2013/0506/collect.js"></script>

<!--股票关键字替换js-->
<link href="http://i2.sinaimg.cn/cj/news_keyword/stock.css" rel="stylesheet" type="text/css">
<script language="JavaScript" id="hq_data_id" src="http://hq.sinajs.cn/list="></script>
<script language="JavaScript" src="http://n.sinaimg.cn/780c44e8/20150819/stock_v4_130723_0819.js " charset="UTF-8"></script><span id="s_chart" style="z-index: 100;"></span>
<!-- http://finance.sina.com.cn/js/2013/0723/stock_v4_130723.js-->
<script language="JavaScript">
    var strCode = "";
    show_quote(strCode,"stock");
</script>
<!-- 正文底部点击地图 -->
		<!--点击地图 begin-->
		<script type="text/javascript" src="http://www.sinaimg.cn/unipro/pub/suda_m_v629.js"></script>
		<script type="text/javascript">suds_init(2303,20.0000,990,2);</script>
		<!--点击地图 end-->

<script type="text/javascript">
    (function(){
        var rate=1;
        var r_num=Math.floor(Math.random()*100);
        var _getScript = function(url,dispose){
            var scriptNode = document.createElement("script");
            scriptNode.type = "text/javascript";
            scriptNode.onreadystatechange = scriptNode.onload = function(){
                if (!this.readyState || this.readyState == "loaded" || this.readyState == "complete"){
                    if(dispose){dispose()};
                    scriptNode.onreadystatechange = scriptNode.onload = null;
                    scriptNode.parentNode.removeChild(scriptNode);
                }
            };
            scriptNode.src = url;
            document.getElementsByTagName("head")[0].appendChild(scriptNode);
        };
        if(r_num < rate){
            _getScript('http://image2.sina.com.cn/unipro/pub/suda_scroll.min.js', function(){
                SUDA.monitorScroll(100, '2151');
            });
        };
    })();
</script>
<!-- ${第三方监测广告位} -->
<!-- ${新闻内容浮层广告} -->

<!-- 浮层广告 begin -->

<script>(sinaads = window.sinaads || []).push({
    params:{
        sinaads_ad_delay: 5,
        sinaads_pop_position:"right bottom"
    }
});</script>
<!-- 浮层广告 end -->








<!-- 侧边广告 -->
<script type="text/javascript" src="http://finance.sina.com.cn/text/1007/2015-07-02/sidead.js"></script>
<!--底浮流媒体 begin-->
<ins class="sinaads sinaads-fail" data-ad-pdps="PDPS000000056987" data-ad-status="done" data-ad-offset-left="0" data-ad-offset-top="4484"></ins>
<script>(sinaads = window.sinaads || []).push({});</script>
<!--底浮流媒体 end-->
<!--底部部分end-->
<!-- body code end -->
<!-- body code begin -->
<script type="text/javascript">
(function(){
    if(window.top !== window.self || window._thereIsNoRealTimeMessage){return};
    var script = document.createElement('script');
    script.setAttribute('charset', 'gb2312');
    script.src = 'http://news.sina.com.cn/js/694/2012/0830/realtime.js?ver=1.5.1';
    document.getElementsByTagName('head')[0].appendChild(script);
})();
</script>

<!-- SSO_UPDATECOOKIE_START -->
<script type="text/javascript">var sinaSSOManager=sinaSSOManager||{};sinaSSOManager.q=function(b){if(typeof b!="object"){return""}var a=new Array();for(key in b){a.push(key+"="+encodeURIComponent(b[key]))}return a.join("&")};sinaSSOManager.es=function(f,d,e){var c=document.getElementsByTagName("head")[0];var a=document.getElementById(f);if(a){c.removeChild(a)}var b=document.createElement("script");if(e){b.charset=e}else{b.charset="gb2312"}b.id=f;b.type="text/javascript";d+=(/\?/.test(d)?"&":"?")+"_="+(new Date()).getTime();b.src=d;c.appendChild(b)};sinaSSOManager.doCrossDomainCallBack=function(a){sinaSSOManager.crossDomainCounter++;document.getElementsByTagName("head")[0].removeChild(document.getElementById(a.scriptId))};sinaSSOManager.crossDomainCallBack=function(a){if(!a||a.retcode!=0){return false}var d=a.arrURL;var b,f;var e={callback:"sinaSSOManager.doCrossDomainCallBack"};sinaSSOManager.crossDomainCounter=0;if(d.length==0){return true}for(var c=0;c<d.length;c++){b=d[c];f="ssoscript"+c;e.scriptId=f;b=b+(/\?/.test(b)?"&":"?")+sinaSSOManager.q(e);sinaSSOManager.es(f,b)}};sinaSSOManager.updateCookieCallBack=function(c){var d="ssoCrossDomainScriptId";var a="http://login.sina.com.cn/sso/crossdomain.php";if(c.retcode==0){var e={scriptId:d,callback:"sinaSSOManager.crossDomainCallBack",action:"login",domain:"sina.com.cn"};var b=a+"?"+sinaSSOManager.q(e);sinaSSOManager.es(d,b)}else{}};sinaSSOManager.updateCookie=function(){var g=1800;var p=7200;var b="ssoLoginScript";var h=3600*24;var i="sina.com.cn";var m=1800;var l="http://login.sina.com.cn/sso/updatetgt.php";var n=null;var f=function(e){var r=null;var q=null;switch(e){case"sina.com.cn":q=sinaSSOManager.getSinaCookie();if(q){r=q.et}break;case"sina.cn":q=sinaSSOManager.getSinaCookie();if(q){r=q.et}break;case"51uc.com":q=sinaSSOManager.getSinaCookie();if(q){r=q.et}break}return r};var j=function(){try{return f(i)}catch(e){return null}};try{if(g>5){if(n!=null){clearTimeout(n)}n=setTimeout("sinaSSOManager.updateCookie()",g*1000)}var d=j();var c=(new Date()).getTime()/1000;var o={};if(d==null){o={retcode:6102}}else{if(d<c){o={retcode:6203}}else{if(d-h+m>c){o={retcode:6110}}else{if(d-c>p){o={retcode:6111}}}}}if(o.retcode!==undefined){return false}var a=l+"?callback=sinaSSOManager.updateCookieCallBack";sinaSSOManager.es(b,a)}catch(k){}return true};sinaSSOManager.updateCookie();</script>
<!-- SSO_UPDATECOOKIE_END -->

<!-- Start  Wrating  -->
<script language="javascript">
var wrUrl="//sina.wrating.com/";var wrDomain="sina.com.cn";var wratingDefaultAcc="860010-0323010000";var wratingAccArray={"history.sina.com.cn":"860010-0334010000","health.sina.com.cn":"860010-0330010000","fashion.sina.com.cn":"860010-0311010000","collection.sina.com.cn":"860010-0331010000","2014.sina.com.cn":"860010-0308160000","2012.sina.com.cn":"860010-0308150000","torch.2008.sina.com.cn":"860010-0308070000","video.sina.com.cn":"860010-0309010000","ent.sina.com.cn":"860010-0312010000","tech.sina.com.cn":"860010-0313010000","mobile.sina.com.cn":"860010-0313020000","house.sina.com.cn":"860010-0315010000","bj.house.sina.com.cn":"860010-0315020000","auto.sina.com.cn":"860010-0316010000","eladies.sina.com.cn":"860010-0317010000","woman.sina.com.cn":"860010-0317010000","games.sina.com.cn":"860010-0318010000","edu.sina.com.cn":"860010-0307010000","baby.sina.com.cn":"860010-0320010000","astro.sina.com.cn":"860010-0321020000","news.sina.com.cn":"860010-0310010000","weather.news.sina.com.cn":"860010-0310020000","mil.news.sina.com.cn":"860010-0310030000","www.sina.com.cn":"860010-0322010000","home.sina.com.cn":"860010-0322010000","sports.sina.com.cn":"860010-0308010000","shidefc.sina.com.cn":"860010-0308020000","weiqi.sina.com.cn":"860010-0308030000","f1.sina.com.cn":"860010-0308040000","golf.sina.com.cn":"860010-0308050000","2002.sina.com.cn":"860010-0308060000","2004.sina.com.cn":"860010-0308060000","2006.sina.com.cn":"860010-0308060000","2008.sina.com.cn":"860010-0308070000","yayun2002.sina.com.cn":"860010-0308060000","yayun2006.sina.com.cn":"860010-0308060000","book.sina.com.cn":"860010-0319010000","cul.book.sina.com.cn":"860010-0319020000","comic.book.sina.com.cn":"860010-0319030000","finance.sina.com.cn":"860010-0314010000","money.sina.com.cn":"860010-0314020000","yue.sina.com.cn":"860010-0324010000","www.sina.com":"860010-0322010000"};function vjTrack(){var U=1800;var T=false;var S=false;var R="";var Q="0";var P="";var N;var L;var K;var J;var I;var H="expires=Fri, 1 Jan 2038 00:00:00 GMT;";var G=0;if(document.location.protocol=="file:"){return }T=navigator.cookieEnabled?"1":"0";S=navigator.javaEnabled()?"1":"0";var F="0";var E;var C=-1;var D=document.cookie;if(T=="1"){C=D.indexOf("vjuids=");if(C<0){E=vjVisitorID();document.cookie="vjuids="+escape(E)+";"+H+";domain="+wrDomain+";path=/;";if(document.cookie.indexOf("vjuids=")<0){T="0"}else{Q="1"}}else{E=vjGetCookie("vjuids")}}L=document.referrer;if(!L||L==""){L=""}R=vjFlash();if(self.screen){N=screen.width+"x"+screen.height+"x"+screen.colorDepth}else{if(self.java){var M=java.awt.Toolkit.getDefaultToolkit();var O=M.getScreenSize();N=O.width+"x"+O.height+"x0"}}if(navigator.language){K=navigator.language.toLowerCase()}else{if(navigator.browserLanguage){K=navigator.browserLanguage.toLowerCase()}else{K="-"}}I="";var B;var X;X=new Date();J=X.getTimezoneOffset()/-60;J=X.getTimezoneOffset()/-60;B="&s="+N+"&l="+K+"&z="+J+"&j="+S+"&f="+R;if(T=="1"){C=document.cookie.indexOf("vjlast=");if(C<0){G=0}else{G=parseInt(vjGetCookie("vjlast"))}}if((X.getTime()/1000)-G>U){F="1";document.cookie="vjlast="+Math.round(X.getTime()/1000)+";"+H+";domain="+wrDomain+";path=/;"}if(L!=""){B=B+"&r="+escape(L)}if(F!="0"){B=B+"&n="+G}if(Q!="0"){B=B+"&u="+Q}var V;var A=vjGetAcc();var W=vjGetDomain();V=wrUrl+"a.gif?a="+X.getTime().toString(16)+"&t="+escape(I)+"&i="+escape(E)+"&b="+escape(document.location)+"&c="+A+B+"&ck="+W;document.write('<img src="'+V+'" width="1" height="1" style="visibility:hidden;position:absolute;left:0px;top:0px;z-index:-1" />')}function vjGetAcc(){var B=document.location.toString().toLowerCase();var C=(B.split("/"))[2];var A=wratingAccArray[C];if(typeof (A)=="undefined"){A=wratingDefaultAcc}return A}function vjFlash(){var _wr_f="-",_wr_n=navigator;if(_wr_n.plugins&&_wr_n.plugins.length){for(var ii=0;ii<_wr_n.plugins.length;ii++){if(_wr_n.plugins[ii].name.indexOf("Shockwave Flash")!=-1){_wr_f=_wr_n.plugins[ii].description.split("Shockwave Flash ")[1];break}}}else{if(window.ActiveXObject){for(var ii=10;ii>=2;ii--){try{var fl=eval("new ActiveXObject('ShockwaveFlash.ShockwaveFlash."+ii+"');");if(fl){_wr_f=ii+".0";break}}catch(e){}}}}return _wr_f}function vjHash(B){if(!B||B==""){return 0}var D=0;for(var C=B.length-1;C>=0;C--){var A=parseInt(B.charCodeAt(C));D=(D<<5)+D+A}return D}function vjVisitorID(){var B=vjHash(document.location+document.cookie+document.referrer).toString(16);var A;A=new Date();return B+"."+A.getTime().toString(16)+"."+Math.random().toString(16)}function vjGetCookieVal(B){var A=document.cookie.indexOf(";",B);if(A==-1){A=document.cookie.length}return unescape(document.cookie.substring(B,A))}function vjGetCookie(C){var B=C+"=";var F=B.length;var A=document.cookie.length;var E=0;while(E<A){var D=E+F;if(document.cookie.substring(E,D)==B){return vjGetCookieVal(D)}E=document.cookie.indexOf(" ",E)+1;if(E==0){break}}return null}function vjGetDomain(){var A=0;try{if(window.self.parent!=self){var D=/sina.com/i;var C=document.location.toString().toLowerCase();var B=parent.location.toString().toLowerCase();if(D.test(C)&&D.test(B)){A=1}}}catch(e){A=1}return A}vjTrack();
</script><img src="//sina.wrating.com/a.gif?a=153df8ff7ac&amp;t=&amp;i=2a8851c6b.153d06172d0.0.ad734318a19ce&amp;b=http%3A//finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml&amp;c=860010-0314010000&amp;s=800x600x24&amp;l=zh-cn&amp;z=8&amp;j=0&amp;f=21.0 r0&amp;n=1459707000&amp;ck=0" width="1" height="1" style="visibility:hidden;position:absolute;left:0px;top:0px;z-index:-1">
<!-- End Wrating-->

<!-- start dmp -->
<script type="text/javascript">
(function(d, s, id) {
var n = d.getElementsByTagName(s)[0];
if (d.getElementById(id)) return;
s = d.createElement(s);
s.id = id;
s.setAttribute('charset', 'utf-8');
s.src = '//d' + Math.floor(0 + Math.random() * (8 - 0 + 1)) + '.sina.com.cn/litong/zhitou/sinaads/src/spec/sinaads_ck.js';
n.parentNode.insertBefore(s, n);
})(document, 'script', 'sinaads-ck-script');
</script>
<!-- end dmp -->

<!-- body code end -->


<audio controls="controls" style="display: none;"></audio><div id="bsBox" class="bsBox"><div class="bsClose">X</div><div class="bsTop"><div class="bsReturn">选择其他平台 &gt;&gt;</div><span style="margin-left:15px;">分享到</span><span class="bsPlatName"></span></div><div class="bsFrameDiv"><iframe class="bShareFrame" name="bsFrame600" frameborder="0" scrolling="no" allowtransparency="true"></iframe></div><div id="bsMorePanel" style="display: none;"></div></div><iframe id="sinaads-ck-iframe" src="//d6.sina.com.cn/litong/zhitou/sinaads/src/spec/sinaads_ck.html" style="display: none;"></iframe><div class="sina-comment-tip" style="visibility: hidden; position: absolute; left: -9999px; opacity: 0;"></div><div id="ads"></div><div id="bsPanelHolder"><div id="bsPanel" style="display:none;"><div class="bsTitle"><a style="float:left;height:20px;line-height:20px;font-weight:bold;" class="bsSiteLink" target="_blank" href="http://www.bshare.cn/intro">分享到</a><a class="bsSiteLink" style="cursor:pointer;float:right;height:20px;line-height:20px;font-weight:bold;" onclick="document.getElementById('bsPanel').style.display='none';">X</a><div class="bsClear"></div></div><div class="bsClear"></div><div style="padding-left:8px;background:#fff;*height:244px;"><div style="height:47px;border-bottom:1px #ccc solid;padding:4px 0 4px 16px;margin-right:8px;_padding-left:12px;"><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'sinaminiblog');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/sinaminiblog.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">新浪微博</div></a></div><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'weixin');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/weixin.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">微信</div></a></div><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'qzone');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/qzone.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">QQ空间</div></a></div></div><div class="bsLogoLink"><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="有道笔记" onclick="javascript:bShare.share(event,'youdaonote');return false;" style="background:url(http://static.bshare.cn/frame/images//logos/s4/youdaonote.png) no-repeat;">有道笔记</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="QQ好友" onclick="javascript:bShare.share(event,'qqim');return false;" style="background:url(http://static.bshare.cn/frame/images//logos/s4/qqim.png) no-repeat;">QQ好友</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="开心网" onclick="javascript:bShare.share(event,'kaixin001');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1008px;">开心网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="网易微博" onclick="javascript:bShare.share(event,'neteasemb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1332px;">网易微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="百度空间" onclick="javascript:bShare.share(event,'baiduhi');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -144px;">百度空间</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="人民微博" onclick="javascript:bShare.share(event,'peoplemb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1368px;">人民微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="南方微博" onclick="javascript:bShare.share(event,'southmb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1818px;">南方微博</a></div></div><div class="bsLogoLink"><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="腾讯微博" onclick="javascript:bShare.share(event,'qqmb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1512px;">腾讯微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="人人网" onclick="javascript:bShare.share(event,'renren');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1674px;">人人网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="LinkedIn" onclick="javascript:bShare.share(event,'linkedin');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1080px;">LinkedIn</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="豆瓣网" onclick="javascript:bShare.share(event,'douban');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -540px;">豆瓣网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="朋友网" onclick="javascript:bShare.share(event,'qqxiaoyou');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1548px;">朋友网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="天涯" onclick="javascript:bShare.share(event,'tianya');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1890px;">天涯</a></div></div><div class="bsClear"></div></div><div style="height:20px;line-height:20px;padding:0 8px;border-top:1px solid #e8e8e8;color:#666;background:#f2f2f2;"><div class="buzzButton" style="float:left;">更多平台... <font style="font-weight:normal;">(133)</font></div><div id="bsPower" style="float:right;text-align:right;overflow:hidden;height:100%;"><a class="bsSiteLink" style="font-size:10px;vertical-align:text-bottom;line-height:24px;cursor:pointer;" href="http://www.bshare.cn" target="_blank"><span style="font-size:10px;vertical-align:text-bottom;"><span style="color:#f60;">b</span>Share</span></a></div></div></div></div></body></html>'''


def getHtml2():
    return '''<html><head>
<style id="znBdcsStyle" type="text/css">.bdcs-container .bdcs-main,.bdcs-container .bdcs-main *{box-sizing:content-box;margin:0;padding:0;float:none;clear:none;overflow:hidden;white-space:nowrap;word-wrap:normal;border:0;background:0 0;width:auto;height:auto;max-width:none;min-width:none;max-height:none;min-height:none;border-radius:0;box-shadow:none;transition:none;text-align:left}.bdcs-container .bdcs-clearfix:after{content:'';display:block;clear:both;height:0}.bdcs-container .bdcs-clearfix{zoom:1}.bdcs-container .bdcs-main{overflow:visible}.bdcs-container .bdcs-search{display:block;overflow:visible;position:relative;border-style:solid}.bdcs-container .bdcs-search-form-input-wrap{display:inline-block}.bdcs-container .bdcs-search-form-input{border-width:1px;border-style:solid;display:inline-block;vertical-align:top;text-indent:5px;background-color:#fff;float:left}.bdcs-container .bdcs-search-form-input:focus{border-width:1px;border-style:solid;outline:0}.bdcs-container .bdcs-search-form-submit-wrap{display:inline-block}.bdcs-container .bdcs-search-form-submit{display:inline-block;cursor:pointer;border-width:1px;border-style:solid;vertical-align:top;text-align:center;width:50px;//_overflow:hidden}.bdcs-container .bdcs-search-form-submit-magnifier{width:45px;padding:0;text-indent:-999em;overflow:hidden;background:url(http://znsv.baidu.com/static/customer-search/component/search/magnifier-icon.png) no-repeat center center;_background:url(http://znsv.baidu.com/static/customer-search/component/search/magnifier-icon_ie6.png) no-repeat center center}div#default-searchbox .default-channel-meun{position:relative;width:75px;display:inline-block;vertical-align:middle;cursor:pointer;background:#fff;float:left;overflow:visible}div#default-searchbox .default-channel-current{border:1px solid;position:relative;width:100%;border-right:0}div#default-searchbox .default-channel-current span{margin-left:8px}div#default-searchbox .default-channel-current i{overflow:hidden;width:0;height:0;border-width:6px 6px 0;border-color:#9E9E9E #fff;border-style:solid;display:block;position:absolute;right:10px;top:11px}div.cse-default-channel-container{display:block;position:absolute;z-index:30061000000}div.cse-default-channel-container .default-channel-list{display:none;width:99%;list-style:none;background:#fff;border:1px solid #DDD;border-top:0;margin:0;padding:0}div.cse-default-channel-container .default-channel-list li{background:0 0;line-height:24px;list-style:none;display:block;padding-left:7px;cursor:pointer}div.cse-default-channel-container .default-channel-list li:hover{background:#DDD}.bdcs-container .bdcs-search-form-input-wrap{}.bdcs-container .bdcs-search-form-input-notspan{margin-left:0px;font-family:Arial,SimSun,sans-serif;color:#000000;font-size:14px;}.bdcs-container .bdcs-search-form-input .icon-nofocus{left:;right:;top:;height:;width:;}.bdcs-container .bdcs-search{width:299px;height:28px;overflow:visible;border-color:#ffffff;border-radius:0px;border-width:0px;box-shadow:none;background-color:none;}.bdcs-container .bdcs-search-form-input{border-color:#e5e5e5;margin-right:5px;width:240px;height:26px;line-height:26px;font-family:Arial,SimSun,sans-serif;color:#000000;font-size:14px;border-radius:0px;background-color:#FFFFFF;}.bdcs-container .bdcs-search-form-input:focus{border-color:#f79646;}.bdcs-container .bdcs-search-form-submit-wrap{}.bdcs-container .bdcs-search-form-submit{border-color:#e5e5e5;height:26px;width:50px;background-color:#FFFFFF;color:#333333;font-family:Arial,SimSun,sans-serif;font-size:12px;border-radius:0px;}div#default-searchbox  .default-channel-meun{width:75px;}.bdcs-container .bdcs-search-form-input{width:165px;}.bdcs-container .bdcs-search-form-submit{*height:28px;*margin-top:1px;}.bdcs-container .bdcs-search-form-submit{line-height:26px;}#bdcs-search-inline{overflow:visible;}div#default-searchbox .default-channel-current{border-radius:0px;}div#default-searchbox .default-channel-current i{top:10px;}div#default-searchbox .default-channel-current{height:26px;line-height:26px;border-color:#e5e5e5}div#default-searchbox  .default-channel-meun{border-radius:0px;width:75px}#bdcs-rec{display:none;}</style><meta charset="utf-8">
<title>北京提倡生态葬 6.5亩骨灰生态林力争年内开建_河北新闻网</title>
<meta name="viewport" content="width=device-width, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no,initial-scale=1, ">
<meta name="applicable-device" content="pc,mobile ">
<meta http-equiv="Cache-Control" content="no-transform ">
<meta http-equiv="Cache-Control" content="no-siteapp">
<meta name="renderer" content="webkit">
<meta http-equiv="X-UA-Compatible" content="edge">
<link rel="shortcut icon" type="image/ico" href="http://www.hebnews.cn/index.ico">
<link href="../../31970.files/images/2016base.css?20160108" rel="stylesheet" type="text/css">
<script type="text/javascript" async="" src="http://znsv.baidu.com/customer_search/api/rs?sid=11379371077363865247&amp;plate_url=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;t=405555&amp;type=3"></script><script type="text/javascript" async="" src="http://znsv.baidu.com/customer_search/api/js?sid=11379371077363865247&amp;plate_url=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;t=405555"></script><script type="text/javascript" src="../../66613.files/js/jquery1.42.min.js"></script>
<script type="text/javascript" src="http://cbjs.baidu.com/js/m.js"></script>
<script src="http://bdimg.share.baidu.com/static/api/js/share.js?cdnversion=405553"></script><script src="http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion=405553"></script><style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style><link rel="stylesheet" href="http://bdimg.share.baidu.com/static/api/css/share_style0_16.css?v=6aba13f0.css"></head>
<body id="header"><div id="BAIDU_DUP_fp_wrapper" style="position: absolute; left: -1px; bottom: -1px; z-index: 0; width: 0px; height: 0px; overflow: hidden; visibility: hidden; display: none;"><iframe id="BAIDU_DUP_fp_iframe" src="http://pos.baidu.com/wh/o.htm?ltr=" style="width: 0px; height: 0px; visibility: hidden; display: none;"></iframe></div>
<div class="page_nav">
	<div class="m_center page_nav_box">

        <ul>
        	<li><a href="http://www.hebnews.cn">河北新闻网首页</a></li>
        	<li><a href="http://hebei.hebnews.cn">河北</a></li>
        	<li><a href="http://gov.hebnews.cn">政务</a></li>
        	<li><a href="http://comment.hebnews.cn">时评</a></li>
        	<li><a href="../../">国内国际</a></li>
        	<li><a href="http://hebei.hebnews.cn/node_116.htm">原创</a></li>
        	<li><a href="http://bbs.hebnews.cn">论坛</a></li>
        	<li><a href="http://v.hebnews.cn">视频</a></li>
        	<li><a href="http://ent.hebnews.cn">娱乐</a></li>
        	<li><a href="http://finance.hebnews.cn">财经</a></li>
        	<li><a href="http://zhuanti.hebnews.cn">专题</a></li>
        	<li><a href="http://bbs.hebnews.cn/smbk/">博客</a></li>
        	<li><a href="http://photo.hebnews.cn">图库</a></li>
        	<li><a href="http://house.hebnews.cn">房产</a></li>
        	<li><a href="http://auto.hebnews.cn">汽车</a></li>
        	<li><a href="http://edu.hebnews.cn">教育</a></li>
        	<li><a href="http://tousu.hebnews.cn">投诉</a></li>
        </ul>
    </div>
    <div class=" ad-top">
	<script type="text/javascript">BAIDU_CLB_fillSlot("382815");</script><div id="BAIDU_SSP__wrapper_382815_0"><iframe id="iframe382815_0" onload="BAIDU_SSP_renderFrame('382815_0', this);" src="about:blank" width="1000" height="85" align="center,center" vspace="0" hspace="0" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" style="border:0; vertical-align:bottom;margin:0;" allowtransparency="true"></iframe></div><script charset="utf-8" src="http://pos.baidu.com/ncom?di=382815&amp;dri=0&amp;dis=0&amp;dai=1&amp;ps=54x0&amp;dcb=BAIDU_SSP_define&amp;dtm=BAIDU_DUP_SETJSONADSLOT&amp;dvi=0.0&amp;dci=-1&amp;dpt=none&amp;tsr=0&amp;tpr=1459997636489&amp;ti=%E5%8C%97%E4%BA%AC%E6%8F%90%E5%80%A1%E7%94%9F%E6%80%81%E8%91%AC%206.5%E4%BA%A9%E9%AA%A8%E7%81%B0%E7%94%9F%E6%80%81%E6%9E%97%E5%8A%9B%E4%BA%89%E5%B9%B4%E5%86%85%E5%BC%80%E5%BB%BA_%E6%B2%B3%E5%8C%97%E6%96%B0%E9%97%BB%E7%BD%91&amp;ari=1&amp;dbv=2&amp;drs=1&amp;pcs=996x592&amp;pss=996x220&amp;cfv=0&amp;cpl=5&amp;chi=8&amp;cce=true&amp;cec=UTF-8&amp;tlm=1459997636&amp;ltu=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;ecd=1&amp;psr=1280x800&amp;par=1280x731&amp;pis=-1x-1&amp;ccd=24&amp;cja=false&amp;cmi=7&amp;col=zh-CN&amp;cdo=-1&amp;tcn=1459997636"></script>
    </div>
    <div class="m_center" style="margin-top:20px">
    	<div class="content_main">
        	<div class="path"><div class="channel"></div><div class="crumb"><a href="../../index.htm" target="_blank" class="">国内国际</a><font class="">&gt;&gt;</font><a href="../../node_152.htm" target="_blank" class="">社会</a></div></div>
        </div>
        <div class="content_side">
        	<div class="side_search">
        	 <div class="hebnews_search_box">
        	<!--<form onSubmit="per_submit();" method="post" name="form1" action="http://search.hebnews.cn:8070/servlet/SearchServlet.do">
            <input name="op" value="single" type="hidden"/>
            <input name="sort" value="date" type="hidden"/>
            <input name="siteID" type="hidden"/>
            <input class="page_search_text" name="contentKey" id="contentKey"  value="新闻搜索" onFocus="if(this.value=='新闻搜索')this.value='';" onBlur="if(this.value=='')this.value='新闻搜索';"/>
            <input class="page_search_buttom" name="submit" value=" " type="submit"/>
            </form>-->
            <script type="text/javascript">(function(){document.write(unescape('%3Cdiv id="bdcs"%3E%3C/div%3E'));var bdcs = document.createElement('script');bdcs.type = 'text/javascript';bdcs.async = true;bdcs.src = 'http://znsv.baidu.com/customer_search/api/js?sid=11379371077363865247' + '&plate_url=' + encodeURIComponent(window.location.href) + '&t=' + Math.ceil(new Date()/3600000);var s = document.getElementsByTagName('script')[0];s.parentNode.insertBefore(bdcs, s);})();
			</script><div id="bdcs"><div class="bdcs-container"><meta http-equiv="x-ua-compatible" content="IE=9">   <!-- 嵌入式 -->  <div class="bdcs-main bdcs-clearfix" id="default-searchbox">      <div class="bdcs-search bdcs-clearfix" id="bdcs-search-inline">          <form action="http://s.hebnews.cn/cse/search" method="get" target="_blank" class="bdcs-search-form" autocomplete="off" id="bdcs-search-form">              <input type="hidden" name="s" value="11379371077363865247">              <input type="hidden" name="entry" value="1">                                                                                      <div class="default-channel-meun" id="default-channel-meun">                  <div class="default-channel-current"><span id="default-channel-curr">综合</span><i></i></div>                    <input type="hidden" name="nsid" value="1" id="default-channel-nsid">              </div><input type="text" name="q" class="bdcs-search-form-input" id="bdcs-search-form-input" placeholder="请输入关键词" style="height: 26px; line-height: 26px;">              <input type="submit" class="bdcs-search-form-submit bdcs-search-form-submit-magnifier" id="bdcs-search-form-submit" value="搜索">                       </form>      </div>                  </div>                           </div></div>

        </div>

<script>
	with(document)0[(getElementsByTagName('head')[0]||body).appendChild(createElement('script')).src='http://bdimg.share.baidu.com/static/api/js/share.js?cdnversion='+~(-new Date()/36e5)];
</script>
        </div>
        </div>
    </div>
</div>



<div class="m_center">
	<div class="content_main">

      <h1 class="title">北京提倡生态葬 6.5亩骨灰生态林力争年内开建</h1>
      <div class="source">2016-03-30 15:46:09　	来源：北京晚报　责任编辑：王艳荣

    </div>
<div class="min-zy">根据近日印发的北京市“十三五”殡葬事业发展规划，到2020年，本市有墓地的行政区都将建设一处绿色生态墓地示范园，骨灰安葬生态化比例将达到50%。</div>      <div class="text">
<!--enpproperty <articleid>5424614</articleid><date>2016-03-30 15:46:09.0</date><author></author><title>北京提倡生态葬 6.5亩骨灰生态林力争年内开建</title><keyword></keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>152</nodeid><nodename>社会</nodename><nodesearchname></nodesearchname><picurl>http://world.hebnews.cn/attachement/jpg/site2/20160330/4437e63707e91865c8f351.jpg</picurl>/enpproperty--><!--enpcontent--><!--enpcontent--><p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;<strong>让生命栖息绿树花土</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify"><strong>&nbsp;&nbsp;&nbsp;&nbsp;6.5亩骨灰生态林力争年内开建</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;如果说入土为安是对传统文化的坚守，那么把生命终结的最后颗粒撒向花土、沉入绿地，或许正是让逝者回归自然的重生，而非仅仅是土地寸土寸金下的退让。根据近日印发的北京市“十三五”殡葬事业发展规划，到2020年，本市有墓地的行政区都将建设一处绿色生态墓地示范园，骨灰安葬生态化比例将达到50%。</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;<strong>花葬</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify"><strong>&nbsp;&nbsp;&nbsp;&nbsp;即使没人祭扫 照样生机勃勃</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify"><strong>&nbsp;&nbsp;&nbsp;&nbsp;地点：福田公墓</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: center" align="center"><a href="content_5424614_2.htm" target="_self"><img id="6682448" title="" border="0" align="默认" src="../../attachement/jpg/site2/20160330/4437e63707e91865c8f351.jpg" sourcedescription="编辑提供的本地文件" sourcename="本地文件"></a></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: center" align="center">花葬</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;没有成束的鲜花，不用漆笔描碑，只是默立鞠躬后，轻轻地放上一枝菊花。上周日早晨8点，田君女士一家三口来到紧邻西南五环的福田公墓祭奠逝去的母亲。不过，与多数人在传统墓碑前摆放鲜花、寒食等各种祭品不同，她的手中只有一枝简单的菊花。一年前，她将母亲的骨灰安放在了福田公墓“福缘阁”中繁花似锦的花坛，之后的祭扫，也一直以这样简单安静的方式进行。</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;“妈妈在生前就嘱咐我们，她百年之后不用传统椅子坟，而要用树葬或者花葬。”田君说，由于母亲文化水平不太高，当时有这样的想法很出人意料，但她的理由很有说服力。“妈妈只有我一个女儿，后来我们家也是独生子女，而在她病重的时候，我女儿正好在国外留学，她觉得传统的椅子坟必须得每年有人去扫墓，如果没人管会很难看，但是花葬、树葬不一样，即使没人祭扫，也生机勃勃，为了不给后代添麻烦，她选择了这种方式。”</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;作为北京市惟一被评为2014年民政部首批“全国生态文明示范墓园”的福田公墓，138亩的面积上近千棵白皮松、华山松、云杉、桧柏等树木四季常青，每到春季，百亩桃园盛开绽放，再搭配玉兰、榆叶梅、黄杨、月季等近万株花木，整个墓地更像是一个大公园，而福缘阁就是福田公墓特有的一个花坛葬区。</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;记者看到，每组葬区以一个花坛为主，中间是高大的常青绿树，花坛内种满了鸢尾、雏菊等花卉。在花坛外侧，以印度红花岗岩为原料的石壁被平均分成多个小区域，每块石材高60厘米，宽40厘米，中部预留有两个直径14厘米的孔穴，用于安放骨灰，顶部则配有莲花装饰，骨灰安放其中后，可以在外侧花岗岩上留下姓名和生卒年月，这种可安放两份骨灰的花坛葬价格为9800元。</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;“公墓里的树葬、花葬、立体骨灰墙等生态安葬方式这两年增长很快，总量已经超过了全部业务量的50%。”工作人员告诉记者，今年1月到3月，家属选择办理节地生态业务的有66份，而选择传统墓碑的是61份，生态葬超过了传统葬。</p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;<strong>&nbsp;服务</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify"><strong>&nbsp;&nbsp;&nbsp;&nbsp;景观撒散区</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify"><strong>&nbsp;&nbsp;&nbsp;&nbsp;可免费存放骨灰</strong></p>
<p style="TEXT-JUSTIFY: distribute; TEXT-ALIGN: justify" align="justify">&nbsp;&nbsp;&nbsp;&nbsp;“今年，福田还被北京市民政局确定为开展骨灰景观撒散试点单位之一，建成后家属可以免费安放逝者骨灰。”工作人员告诉记者，规划中的景观撒散区位于福缘阁最南侧，共两块长方形区域，面积为200平方米。“争取在今年内能够建成，到时候从远处看这两个区域就是盆景造型，栽种有龙爪槐、松树、柏树等树木，地下是一层鲜花，撒放区内逝者骨灰直接撒散到土壤里，外侧不立碑留名，地下不保留任何骨灰设施，几年后，逝者将与绿树花土融为一体。”</p>
<!--/enpcontent--><div width="100%" id="displaypagenum"><p></p><center> <span>1</span> <a href="content_5424614_2.htm" class="page-Article">2</a> <a href="content_5424614_3.htm" class="page-Article">3</a> <a href="content_5424614_2.htm" class="nextpage">下一页</a> <a href="content_5424614_3.htm" class="nextpage">尾页</a></center><p></p></div><!--/enpcontent-->
      </div>

        <div class="feed">
        	<h3 class="mod_title">相关新闻</h3>

<div class="feed-item">        <h2>           <a href="http://hebei.hebnews.cn/2016-03/27/content_5417235.htm" target="_blank"> 省民政厅通知要求做好清明祭扫工作 推行生态安葬</a>        </h2>        <div class="feed-time">           2016-03-27 08:42:15        </div><div class="cl"></div>       <p class="feed-txt">清明节即将来临。日前，省民政厅就做好清明祭扫工作发出通知，要求倡导移风易俗，推行文明祭扫生态安葬。通知要求，要充分发挥殡葬服务机构和城乡社区的平台作用，积极开展“鲜花替代烧纸”“丝带寄托哀思”等活动，组织社区公祭、集体共祭等现代追思活动，组织祭先烈、敬先贤等各种缅怀仪式，大力推广鲜花祭扫、植树祭扫、网络祭扫等文明祭扫方式，培育绿色文明殡葬理念。</p>     </div><div class="feed-item">        <h2>           <a href="http://sjz.hebnews.cn/2015-04/07/content_4683591.htm" target="_blank"> 石家庄：树葬花坛葬集体公益生态安葬获逝者亲属肯定</a>        </h2>        <div class="feed-time">           2015-04-07 23:33:28        </div><div class="cl"></div>       <p class="feed-txt">为倡导生态绿色、文明节俭殡葬祭祀新风尚，清明节当天，市殡葬管理处、市殡葬协会、平山县古中山陵园等单位联合举办了2015年集体公益生态葬暨大型公祭活动，对12位逝者进行了公益生态安葬。古中山陵园的花坛葬以及在海葬纪念碑上镌刻逝者姓名都是常年免费开放，树葬则要收取1000余元的费用。</p>     </div><div class="feed-item">        <h2>           <a href="http://handan.hebnews.cn/2015-02/05/content_4531845.htm" target="_blank"> 邯郸发布改革殡葬习俗倡议书 依法火葬生态安葬</a>        </h2>        <div class="feed-time">           2015-02-05 11:28:01        </div><div class="cl"></div>       <p class="feed-txt">为深入贯彻落实中共邯郸市委办公厅、邯郸市人民政府办公厅《关于发挥党员干部带头作用全面深化殡葬改革的意见》，引领广大干部群众自觉遵守火化政策，实行生态安葬，履行文明低碳祭祀，减轻群众丧葬负担，推动我市殡葬改革深入发展，提出如下倡议：</p>     </div><div class="feed-item">        <h2>           <a href="../../2013-03/01/content_3118572.htm" target="_blank"> 民政部鼓励生态安葬骨灰 海葬树葬等或政府买单</a>        </h2>        <div class="feed-time">           2013-03-01 08:18:11        </div><div class="cl"></div>       <p class="feed-txt">民政部称，将探索把告别厅租用、骨灰生态葬法等纳入基本服务项目范畴，这也意味着骨灰生态葬法将有望由政府来买单。鼓励经营性公墓开辟生态公益墓区，提供免费或者低价骨灰安葬服务，引导群众摒弃硬质墓穴和墓志等。</p>     </div>

    </div>
<div class="hot-news">
	<div class="feed" id="xgss">
        	<h3 class="mod_title">热门推荐</h3>

    <div style="margin-top:10px; margin-left:-5px"><script type="text/javascript">(function(){document.write(unescape('%3Cdiv id="bdcsFrameTitleBox"%3E%3C/div%3E'));var bdcs = document.createElement("script");bdcs.type = "text/javascript";bdcs.async = true;bdcs.src = "http://znsv.baidu.com/customer_search/api/rs?sid=11379371077363865247" + "&plate_url=" + encodeURIComponent(window.location.href) + "&t=" + Math.ceil(new Date()/3600000) + "&type=3";var s = document.getElementsByTagName("script")[0];s.parentNode.insertBefore(bdcs, s);})();
	</script><div id="bdcsFrameTitleBox" style="width: 610px; height: auto;"><iframe name="bdcsTitleFrame" id="bdcsTitleFrame" src="http://s.hebnews.cn/cse/search?s=11379371077363865247&amp;loc=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;width=610&amp;rec=1&amp;ht=3&amp;trec=1&amp;pn=12&amp;qfrom=4&amp;q=%E5%8C%97%E4%BA%AC%E6%8F%90%E5%80%A1%E7%94%9F%E6%80%81%E8%91%AC%206.5%E4%BA%A9%E9%AA%A8%E7%81%B0%E7%94%9F%E6%80%81%E6%9E%97%E5%8A%9B%E4%BA%89%E5%B9%B4%E5%86%85%E5%BC%80%E5%BB%BA_%E6%B2%B3%E5%8C%97%E6%96%B0%E9%97%BB%E7%BD%91" frameborder="0" width="100%" height="138px" marginwidth="0" marginheight="0" hspace="0" vspace="0" allowtransparency="true" scrolling="no"></iframe></div>
    </div>
    </div>
</div>
<div class="photo">
        	<h3 class="mod_title" style="margin-bottom:10px">精彩图库</h3><div class="tv_box"><a href="http://photo.hebnews.cn/2016-03/30/content_5423751.htm" target="_blank"><img src="../../attachement/jpg/site2/20160330/b8ca3a7bf9831865854804.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://photo.hebnews.cn/2016-03/30/content_5423751.htm" target="_blank">朱孝天间接承认已婚</a></span></div><div class="tv_box"><a href="http://photo.hebnews.cn/2016-03/30/content_5423729.htm" target="_blank"><img src="../../attachement/jpg/site2/20160330/b8ca3a7bf983186584b300.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://photo.hebnews.cn/2016-03/30/content_5423729.htm" target="_blank">招空乘旗袍美女面试</a></span></div><div class="tv_box"><a href="http://photo.hebnews.cn/2016-03/30/content_5423724.htm" target="_blank"><img src="../../attachement/jpg/site2/20160330/b8ca3a7bf9831865844259.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://photo.hebnews.cn/2016-03/30/content_5423724.htm" target="_blank">全球水下摄影大赛</a></span></div><div class="tv_box"><a href="http://photo.hebnews.cn/2016-03/30/content_5423676.htm" target="_blank"><img src="../../attachement/jpg/site2/20160330/b8ca3a7bf9831865822933.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://photo.hebnews.cn/2016-03/30/content_5423676.htm" target="_blank">刘诗诗诠释活力girl</a></span></div>
</div>

     <script type="text/javascript">  document.writeln(" <div class=\"baoliao\">想爆料？请拨打新闻热线0311-67563366，登录河北新闻网新浪微博（<a href=\"http://weibo.com/hebnews2012\" rel=\"nofollow\" style=\"text-decoration:underline\" target=\"_blank\">@河北新闻网官方</a>）或通过投稿邮箱（hbrbwgk@sina.com）提供新闻线索；时评稿件请投kangkaige2010@126.com,或直接加慷慨歌Q群314081840。</div>");
       </script> <div class="baoliao">想爆料？请拨打新闻热线0311-67563366，登录河北新闻网新浪微博（<a href="http://weibo.com/hebnews2012" rel="nofollow" style="text-decoration:underline" target="_blank">@河北新闻网官方</a>）或通过投稿邮箱（hbrbwgk@sina.com）提供新闻线索；时评稿件请投kangkaige2010@126.com,或直接加慷慨歌Q群314081840。</div>

  </div>
	<div class="content_side undis">


<div class="ad-box"><script type="text/javascript">BAIDU_CLB_fillSlot("1030513");</script><div id="BAIDU_SSP__wrapper_1030513_0"></div><script charset="utf-8" src="http://pos.baidu.com/ncom?di=1030513&amp;dri=0&amp;dis=0&amp;dai=2&amp;ps=220x700&amp;dcb=BAIDU_SSP_define&amp;dtm=BAIDU_DUP_SETJSONADSLOT&amp;dvi=0.0&amp;dci=-1&amp;dpt=none&amp;tsr=0&amp;tpr=1459997636489&amp;ti=%E5%8C%97%E4%BA%AC%E6%8F%90%E5%80%A1%E7%94%9F%E6%80%81%E8%91%AC%206.5%E4%BA%A9%E9%AA%A8%E7%81%B0%E7%94%9F%E6%80%81%E6%9E%97%E5%8A%9B%E4%BA%89%E5%B9%B4%E5%86%85%E5%BC%80%E5%BB%BA_%E6%B2%B3%E5%8C%97%E6%96%B0%E9%97%BB%E7%BD%91&amp;ari=1&amp;dbv=2&amp;drs=1&amp;pcs=981x577&amp;pss=1000x3285&amp;cfv=0&amp;cpl=5&amp;chi=8&amp;cce=true&amp;cec=UTF-8&amp;tlm=1459997636&amp;ltu=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;ecd=1&amp;psr=1280x800&amp;par=1280x731&amp;pis=-1x-1&amp;ccd=24&amp;cja=false&amp;cmi=7&amp;col=zh-CN&amp;cdo=-1&amp;tcn=1459997637"></script><script type="text/javascript">BAIDU_CLB_SLOT_ID = "1029661";</script>
<script type="text/javascript" src="http://cbjs.baidu.com/js/o.js"></script><div id="BAIDU_SSP__wrapper_1029661_0"><iframe id="iframe1029661_0" onload="BAIDU_SSP_renderFrame('1029661_0', this);" src="about:blank" width="300" height="250" align="center,center" vspace="0" hspace="0" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" style="border:0; vertical-align:bottom;margin:0;" allowtransparency="true"></iframe></div><script charset="utf-8" src="http://pos.baidu.com/ncom?di=1029661&amp;dri=0&amp;dis=0&amp;dai=3&amp;ps=220x700&amp;dcb=BAIDU_SSP_define&amp;dtm=BAIDU_DUP_SETJSONADSLOT&amp;dvi=0.0&amp;dci=-1&amp;dpt=none&amp;tsr=0&amp;tpr=1459997636489&amp;ti=%E5%8C%97%E4%BA%AC%E6%8F%90%E5%80%A1%E7%94%9F%E6%80%81%E8%91%AC%206.5%E4%BA%A9%E9%AA%A8%E7%81%B0%E7%94%9F%E6%80%81%E6%9E%97%E5%8A%9B%E4%BA%89%E5%B9%B4%E5%86%85%E5%BC%80%E5%BB%BA_%E6%B2%B3%E5%8C%97%E6%96%B0%E9%97%BB%E7%BD%91&amp;ari=1&amp;dbv=2&amp;drs=1&amp;pcs=981x577&amp;pss=1000x3438&amp;cfv=0&amp;cpl=5&amp;chi=8&amp;cce=true&amp;cec=UTF-8&amp;tlm=1459997637&amp;ltu=http%3A%2F%2Fworld.hebnews.cn%2F2016-03%2F30%2Fcontent_5424614.htm&amp;ecd=1&amp;psr=1280x800&amp;par=1280x731&amp;pis=-1x-1&amp;ccd=24&amp;cja=false&amp;cmi=7&amp;col=zh-CN&amp;cdo=-1&amp;tcn=1459997637"></script></div>
        <div class="side-box undis">
        	<div class="nav_side">品牌栏目</div>
            <div class="jhtuijian"><a href="http://zhuanti.hebnews.cn/kanba/160329.htm" target="_blank"><img src="../../attachement/jpg/site2/20160329/003018a0f0e1186482f707.jpg" border="0"></a>            	<span><a href="http://zhuanti.hebnews.cn/kanba/160329.htm" target="_blank">话题：文明标语大家侃</a></span><p>文明社会拼创意，期待您提供有意思、接地气的文明标语。</p>            </div><div class="jhtuijian"><a href="http://comment.hebnews.cn/2016-03/28/content_5419234.htm" target="_blank"><img src="../../attachement/jpg/site2/20160328/e0915373bc0018635cd501.jpg" border="0"></a>            	<span><a href="http://comment.hebnews.cn/2016-03/28/content_5419234.htm" target="_blank">评论:壮士断腕 改革创新</a></span><p>面对供给侧结构性改革，河北责任重大。</p>            </div><div class="jhtuijian"><a href="http://hui.hebnews.cn/2016-03/29/content_5421579.htm" target="_blank"><img src="../../attachement/jpg/site2/20160329/6c626d0159371864748528.jpg" border="0"></a>            	<span><a href="http://hui.hebnews.cn/2016-03/29/content_5421579.htm" target="_blank">数读：驾考新规15大变化</a></span><p>新法规关系千万驾驶人切身利益，15大变化要特别留意。</p>            </div><div class="jhtuijian"><a href="http://tousu.hebnews.cn/2016-03/24/content_5413376.htm" target="_blank"><img src="../../attachement/jpg/site2/20160229/b8ca3a789aed183ddf0803.jpg" border="0"></a>            	<span><a href="http://tousu.hebnews.cn/2016-03/24/content_5413376.htm" target="_blank">理政：发展农村电商<br></a></span><p>2016年底，全省将实现县域农村电子商务体系全覆盖。</p>            </div>


        </div>

        <div class="side-box undis" style="margin-bottom:1px; padding-bottom:1px">
        	<div class="nav_side">娱乐热图</div>
                 <div class="hot_pic_box">
                   <div class="tv_box"><a href="http://ent.hebnews.cn/2016-03/29/content_5420284.htm" target="_blank"><img src="../../attachement/jpg/site2/20160329/6c626d005cfe1864751b1d.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://ent.hebnews.cn/2016-03/29/content_5420284.htm" target="_blank">郑爽胡彦斌分手</a></span></div><div class="tv_box"><a href="http://ent.hebnews.cn/2016-03/29/content_5420442.htm" target="_blank"><img src="../../attachement/jpg/site2/20160329/6c626d005cfe186474ba1c.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://ent.hebnews.cn/2016-03/29/content_5420442.htm" target="_blank">包贝尔夫妻接机</a></span></div><div class="tv_box"><a href="http://ent.hebnews.cn/2016-03/28/content_5419185.htm" target="_blank"><img src="../../attachement/jpg/site2/20160328/6c626d005cfe1863357404.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://ent.hebnews.cn/2016-03/28/content_5419185.htm" target="_blank">撒贝宁李白领证</a></span></div><div class="tv_box"><a href="http://ent.hebnews.cn/2016-03/28/content_5419720.htm" target="_blank"><img src="../../attachement/jpg/site2/20160328/6c626d005cfe1863352303.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://ent.hebnews.cn/2016-03/28/content_5419720.htm" target="_blank">国产八大花美男</a></span></div>
          </div>
        </div>

		<div class="side-box undis">
               	<div class="nav_side ">新闻排行</div>
                <iframe src="http://www.hebnews.cn/top10/top10-2.html" width="100%" height="345" frameborder="0" scrolling="no" style="background:#fff; margin-top:10px"></iframe>
        </div>
        <div class="side-box undis" style="margin-bottom:1px;">
        	<div class="nav_side">论坛热帖</div>
                 <div class="hot_pic_box">
                   <div class="tv_box"><a href="http://bbs.hebnews.cn/thread-6905205-1-1.html" target="_blank"><img src="../../attachement/jpg/site2/20160329/003018a0f0e11864882e11.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://bbs.hebnews.cn/thread-6905205-1-1.html" target="_blank">Baby是素颜女神？</a></span></div><div class="tv_box"><a href="http://bbs.hebnews.cn/thread-6905211-1-1.html" target="_blank"><img src="../../attachement/jpg/site2/20160329/003018a0f0e1186487dc10.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://bbs.hebnews.cn/thread-6905211-1-1.html" target="_blank">盘点张馨予前6任男友</a></span></div><div class="tv_box"><a href="http://bbs.hebnews.cn/thread-6905268-1-1.html" target="_blank"><img src="../../attachement/jpg/site2/20160329/003018a0f0e1186487a90f.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://bbs.hebnews.cn/thread-6905268-1-1.html" target="_blank">雪莉自拍画面太“污”</a></span></div><div class="tv_box"><a href="http://bbs.hebnews.cn/thread-6905199-1-1.html" target="_blank"><img src="../../attachement/jpg/site2/20160329/003018a0f0e11864876b0e.jpg" border="0"></a><cite class="bg"></cite><span class="txt"><a href="http://bbs.hebnews.cn/thread-6905199-1-1.html" target="_blank">蛇精男刘梓晨被包养</a></span></div>
          </div>
        </div>
		<div class="">


           <iframe src="http://www.hebnews.cn/rss/node_113002.htm" width="100%" height="240" frameborder="0" scrolling="no"></iframe>

        </div>
  </div>
</div><div class="cse-default-channel-container" style="width: 75px;"><ul class="default-channel-list" id="default-channel-list"><li data-id="1">综合</li><li data-id="2">河北</li></ul></div>

<div class="m_center footer_nav">
<a href="http://sjz.hebnews.cn/" target="_blank">石家庄新闻</a>
<a href="http://handan.hebnews.cn/" target="_blank">邯郸新闻</a>
<a href="http://bd.hebnews.cn/" target="_blank">保定新闻</a>
<a href="http://zjk.hebnews.cn/" target="_blank">张家口新闻</a>
<a href="http://cd.hebnews.cn/" target="_blank">承德新闻</a>
<a href="http://ts.hebnews.cn/" target="_blank">唐山新闻</a>
<a href="http://qhd.hebnews.cn/" target="_blank">秦皇岛新闻</a>
<a href="http://lf.hebnews.cn/" target="_blank">廊坊新闻</a>
<a href="http://hs.hebnews.cn/" target="_blank">衡水新闻</a>
<a href="http://hebei.hebnews.cn/node_135.htm" target="_blank">沧州新闻</a>
<a href="http://hebei.hebnews.cn/node_136.htm" target="_blank">邢台新闻</a>
<a href="http://hebei.hebnews.cn/node_94522.htm" target="_blank">辛集新闻</a>
<a href="http://hebei.hebnews.cn/node_94523.htm" target="_blank">定州新闻</a>
<a href="http://nongmin.hebnews.cn" target="_blank">河北农民报</a>

</div>






<div class="foottxt">
	<div class="m_center">
        <div class="footlist">
<ul>
<li><a href="http://help.hebnews.cn/index.html" rel="nofollow" target="_blank">关于我们</a>| </li>
<li><a href="http://help.hebnews.cn/bqsm.html" rel="nofollow" target="_blank">版权声明</a>| </li>
<li><a href="http://help.hebnews.cn/fwtk.html" rel="nofollow" target="_blank">服务条款</a>| </li>
<li><a href="http://dynamic.hebnews.cn/node_7660.htm" rel="nofollow" target="_blank">广告业务</a>| </li>
<li><a href="http://help.hebnews.cn/sxsq.html" rel="nofollow" target="_blank">实习申请</a>| </li>
<li><a href="http://help.hebnews.cn/wstg.html" rel="nofollow" target="_blank">网上投稿</a>| </li>
<li><a href="http://help.hebnews.cn/xwrx.html" rel="nofollow" target="_blank">新闻热线</a>| </li>
<li><a href="http://www.hebnews.cn/sitemap.htm" target="_blank">网站地图</a> </li></ul></div>
<div class="foottxt">
<li>河北新闻网版权所有 本站点信息未经允许不得复制或镜像  法律顾问：<a title="" href="http://zhuanti.hebnews.cn/2012/node_41101.htm" rel="nofollow" target="_blank">河北球衡律师事务所</a> <a title="" href="http://zhuanti.hebnews.cn/2012/node_41103.htm" rel="nofollow" target="_blank">杨建国</a> </li>
<li class="dis"><a href="http://www.hebnews.cn/" target="_blank">www.hebnews.cn</a> copyright © 2000 - 2016 </li>
<li>新闻热线:0311-67563366 广告热线:0311-67562966 新闻投诉:0311-67562994 </li>
<li>冀ICP备 09047539号-1 | 互联网新闻信息服务许可证编号:1312006002 </li>
<li>广播电视节目制作经营许可证（冀）字第101号|信息网络传播视听节目许可证0311618号 </li>
<li style="HEIGHT: 54px">
<a title="河北互联网违法和不良信息举报" href="http://hbjubao.hebei.com.cn/" rel="nofollow" target="_blank"><img src="http://www.hebnews.cn/attachement/jpg/site2/20141212/f8b156a3fa6615f4a1861d.jpg"></a>
<a title="经营性网站备案信息" href="http://www.miibeian.gov.cn/" rel="nofollow" target="_blank"><img src="http://www.hebnews.cn/attachement/gif/site2/20120823/001aa0c3d91f119fcd371f.gif"></a>
<a title="不良信息举报中心" href="http://www.12377.cn/" rel="nofollow" target="_blank"><img src="http://www.hebnews.cn/72950.files/images/12377_2.jpg"></a>
<a title="新闻记者证管核系统" href="http://press.gapp.gov.cn/" rel="nofollow" target="_blank"><img src="http://www.hebnews.cn/attachement/gif/site2/20120823/001aa0c3d91f119fcd3721.gif"></a>
</li></div>
    </div>
</div>

<div id="tbox" style="display:none">

	<div id="sidenav">
        <a id="zhengwu1" class="sidenav_zhengwu" target="_blank" href="http://www.hebnews.cn/"></a>
        <a id="caijing1" class="sidenav_caijing" target="_blank" href="http://zhuanti.hebnews.cn/2015/node_112882.htm"></a>
        <a id="jiankang1" class="sidenav_jiankang" target="_self"></a>
        <a id="jiaoyu1" class="sidenav_jiaoyu" target="_self" href="#xgss"></a>

    </div>
<a id="gotop" href="#header" style="display: inline;"></a></div>

    <script type="text/javascript">
function a(x,y){
	l = $('#page').offset().left;
	w = $('#page').width();
	$('#tbox').css('left',(l + w + x) + 'px');
	$('#tbox').css('bottom',y + 'px');
}
function b(){
	h = $(window).height();
	t = $(document).scrollTop();
	if(t > h){
		$('#gotop').fadeIn('slow');
	}else{
		$('#gotop').fadeOut('slow');
	}
}
$(document).ready(function(e) {
	a(10,10);//#tbox的div距浏览器底部和页面内容区域右侧的距离
	b();
	$('#gotop').click(function(){
		$(document).scrollTop(0);
	})
});
$(window).resize(function(){
	a(10,10);////#tbox的div距浏览器底部和页面内容区域右侧的距离
});

$(window).scroll(function(e){
	b();
})
</script>
<script type="text/javascript" src="../../66613.files/js/gpsBar.js"></script>



<script type="text/javascript">
var _bdhmProtocol = (("https:" == document.location.protocol) ? " https://" : " http://");
document.write(unescape("%3Cscript src='" + _bdhmProtocol + "hm.baidu.com/h.js%3Ffc19c432c6dd37e78d6593b2756fb674' type='text/javascript'%3E%3C/script%3E"));
</script><script src=" http://hm.baidu.com/h.js?fc19c432c6dd37e78d6593b2756fb674" type="text/javascript"></script>
<script>window._bd_share_config={"common":{"bdSnsKey":{},"bdText":"","bdMini":"2","bdMiniList":false,"bdPic":"","bdStyle":"0","bdSize":"16"},"share":{}};with(document)0[(getElementsByTagName('head')[0]||body).appendChild(createElement('script')).src='http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion='+~(-new Date()/36e5)];
</script>

<!-- stat.hebnews.cn/mysql -->
<script language="javascript">var __$nodeid=152;var __$contentid=5424614;var __$title='北京提倡生态葬 6.5亩骨灰生态林力争年内开建';var __$AuthorPh='';var __$Editor='王艳荣';var __$Liability='王艳荣';var __$pubtime='2016-03-30 15:46:09';</script>
<script language="JavaScript" charset="gb2312" src="http://tongji.hebnews.cn/mysql/count/abceffgh/abceffgh.js"></script><script src="http://stat.hebnews.cn/mysql/logcount.php?C_U_=http://stat.hebnews.cn/mysql&amp;P_U_=/2016-03/30/content_5424614.htm&amp;W_S_=abceffgh&amp;R_F_=&amp;F_S_=&amp;K_W_=&amp;W_C_=&amp;W_P_=&amp;R_W_=&amp;P_S_=http://world.hebnews.cn&amp;N_D_I_D_=152&amp;C_T_I_D_=5424614&amp;E_D_T_=%u738B%u8273%u8363&amp;P_T_=2016-03-30 15:46:09&amp;PIC_U_=undefined&amp;P_D_=/2016-03/30/&amp;L_G_=zh-CN&amp;C_L_=24&amp;C_K_=1&amp;S_S_=1280*800&amp;F_T_=2016-4-7-10-53-57&amp;L_T_=2016-4-7-10-53-57&amp;C_S_=UTF-8&amp;F_L_=1&amp;J_V_=0&amp;A_L_=0&amp;S_Y_=other&amp;B_R_=chrome&amp;T_Z_=-8&amp;A_U_=undefined&amp;U_N_=&amp;M_T_=&amp;U_C_=1459997637240&amp;R_C_=0&amp;D_B_=&amp;T_P_=1&amp;I_M_=&amp;T_X_=hidden&amp;T_T_=%u5317%u4EAC%u63D0%u5021%u751F%u6001%u846C%206.5%u4EA9%u9AA8%u7070%u751F%u6001%u6797%u529B%u4E89%u5E74%u5185%u5F00%u5EFA"></script><noscript>&lt;img src="http://stat.hebnews.cn/mysql/count/abceffgh/abceffgh.php" alt="" style="border:0" /&gt;</noscript>
<!-- /stat.hebnews.cn/mysql -->


<audio controls="controls" style="display: none;"></audio></body></html>'''


def getHtml3():
    return '''<html><head>
<style id="znBdcsStyle" type="text/css">div#sliding-searchbox.sliding-searchbox-one #sliding-icon-left{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-right.png) no-repeat center center;margin-right:15px;float:left}div#sliding-searchbox.sliding-searchbox-two #sliding-icon-left{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-two-left.png) no-repeat center center;margin-right:15px;float:left}div#sliding-searchbox.sliding-searchbox-three #sliding-icon-left{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-three-left.png) no-repeat center center;margin-right:15px;float:left}div#sliding-searchbox.sliding-searchbox-four #sliding-icon-left{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-four-left.png) no-repeat center center;margin-right:15px;float:left}#sliding-searchbox #sliding-back-right{float:left;height:60px;width:14px;background:url(http://znsv.baidu.com/static/customer-search/img/back-right-common.png) no-repeat center center}#sliding-searchbox.sliding-searchbox-four #sliding-back-right{float:left;height:60px;width:14px;border-top:1px solid #C8E2F9;border-left:1px solid #C8E2F9;border-bottom:1px solid #C8E2F9;background:#F0F8FF url(http://znsv.baidu.com/static/customer-search/img/back-right-common-four.png) no-repeat center center}#sliding-box-item{width:383px;border:solid 1px;float:left}#sliding-box-item input{border:solid 1px;margin-right:0;text-indent:.5em}.sliding-box-meun #sliding-search-form-submit{text-indent:0}#sliding-hot{float:none;width:100%;margin-top:10px;overflow:hidden}#sliding-box-item .bdcs-container .bdcs-hot{height:50px}#sliding-searchbox #sliding-search-form .sliding-submit-magnifier{background:url(http://znsv.baidu.com/static/customer-search/img/search-icon.png) no-repeat center center;text-indent:-999em}.sliding-searchbox-four #sliding-searchbox .sliding-submit-magnifier{background:url(http://znsv.baidu.com/static/customer-search/img/search-icon-four.png) no-repeat center center;text-indent:-999em}#sliding-searchbox #sliding-box-item #sliding-search-form-submit{width:40px;text-align:center;margin-left:0;position:relative}#sliding-box-item input:focus{border:1px solid}#sliding-back{height:60px;width:14px;background:url(http://znsv.baidu.com/static/customer-search/img/back-left-common.png) no-repeat center center;float:left}.sliding-searchbox-four #sliding-back{height:60px;width:14px;background:url(http://znsv.baidu.com/static/customer-search/img/back-left-common-four.png) no-repeat center center;float:left}#sliding-search-sug-list{position:relative;//margin-left:10px}#sliding-search-sug .sliding-search-sug-list-item-current{background-color:#F5F5F5}div#sliding-searchbox.sliding-searchbox-one #sliding-icon-right{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-left.png) no-repeat center center;float:left;margin-left:15px}div#sliding-searchbox.sliding-searchbox-two #sliding-icon-right{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-two-right.png) no-repeat center center;float:left;margin-left:15px}div#sliding-searchbox.sliding-searchbox-three #sliding-icon-right{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-three-right.png) no-repeat center center;float:left;margin-left:15px}div#sliding-searchbox.sliding-searchbox-four #sliding-icon-right{height:60px;width:50px;background:url(http://znsv.baidu.com/static/customer-search/img/slidingbox-icon-four-right.png) no-repeat center center;float:left;margin-left:15px}#sliding-box-detail a{text-decoration:none;padding:3px;display:inline-block}#sliding-hot{width:0}.sliding-search-sug-list-item{cursor:pointer}.sliding-search-sug-list-item-value{position:relative;left:5px}.sliding-search-sug-list-item-author-novel,.sliding-search-sug-list-item-author-music,.sliding-search-sug-list-item-type-movie{color:#BABABA}.sliding-search-sug-list-item-author-novel,.sliding-search-sug-list-item-author-music{position:relative;left:5px}.sliding-search-sug-list-item-music{overflow:hidden;*zoom:1}#sliding-search-sug .sliding-search-sug-list-item-value-movie{float:left}#sliding-search-sug .sliding-search-sug-list-item-type-movie{float:right}#sliding-search-form-input{border-radius:0;float:none;padding:0;vertical-align:middle}#sliding-search-form-submit{border-radius:0;float:none;vertical-align:middle}#sliding-searchbox{overflow:visible;z-index:99999}div#sliding-searchbox .sliding-box-meun{padding-left:20px;padding-top:20px;position:relative;text-align:left}div#sliding-searchbox .sliding-channel-meun{position:relative;width:75px;display:inline-block;vertical-align:middle;background:#fff;cursor:pointer}div#sliding-searchbox .sliding-channel-current{border:1px solid;position:relative;width:100%;border-right:0}div#sliding-searchbox .sliding-channel-current span{margin-left:8px}div#sliding-searchbox .sliding-channel-current i{overflow:hidden;width:0;height:0;border-width:6px 6px 0;border-color:#9E9E9E #fff;border-style:solid;display:block;position:absolute;right:10px;top:15px}div.cse-sliding-channel-container{display:block;position:absolute;z-index:30061000000}div.cse-sliding-channel-container .sliding-channel-list{display:none;width:99%;list-style:none;background:#fff;border:1px solid #DDD;border-top:0;margin:0;padding:0}div.cse-sliding-channel-container .sliding-channel-list li{background:0 0;line-height:24px;list-style:none;padding-left:7px;cursor:pointer;display:block}div.cse-sliding-channel-container .sliding-channel-list li:hover{background:#DDD}#sliding-box-item{width:320px;height:120px;background-color:#fff;border-color:#ececec;}div#sliding-searchbox #sliding-back-right, div#sliding-searchbox #sliding-back{background-color:#1a89ed;}#sliding-box-item input{width:220px;height:35px;border-color:#ececec;color:#666;font-size:12px;font-family:微软雅黑;}#sliding-box-item #sliding-search-form-submit{background-color:#1a89ed;border-color:#1a89ed;color:#fff;font-family:微软雅黑;font-size:14px;font-weight:normal;}#sliding-box-item input:focus{border-color:#87C6F9;}#sliding-box-item #sliding-search-form-submit{position:relative;left:0px}#sliding-search-form-input{line-height:35px;}#sliding-hot{width:300px}#sliding-box-item #sliding-search-form-submit{height:35px}#sliding-searchbox{position:fixed;left:-428px;top:150px;}#bdcs-rec{display:none;}</style><meta http-equiv="content-type" content="text/html;charset=GB2312">
<script type="text/javascript" async="" src="http://znsv.baidu.com/customer_search/api/js?sid=5102689337316652524&amp;plate_url=http%3A%2F%2Fcq.people.com.cn%2Fn2%2F2016%2F0401%2Fc365411-28065405.html&amp;t=405556"></script><script type="text/javascript">
var cururl=document.URL;
var cid=cururl.substring(cururl.indexOf('-')+1,cururl.lastIndexOf ('.'));
var sUserAgent = navigator.userAgent.toLowerCase();
var IsTC = sUserAgent.match(/transcoder/i) == "transcoder";
var bIsIpad = sUserAgent.match(/ipad/i) == "ipad";
var bIsIphoneOs = sUserAgent.match(/iphone os/i) == "iphone os";
var bIsAndroid = sUserAgent.match(/android/i) == "android";
var bIsMidp = sUserAgent.match(/midp/i) == "midp";
var bIsWP = sUserAgent.match(/windows phone/i) == "windows phone";
var bIsCE = sUserAgent.match(/windows ce/i) == "windows ce";
var bIsWM = sUserAgent.match(/windows mobile/i) == "windows mobile";
var bIsSYB = sUserAgent.match(/symbian/i) == "symbian";
var bIsSER = sUserAgent.match(/series/i) == "series";
//if(cid.length>1 && !isNaN(cid)){alert(cid);}
if(cid.length>1 && !isNaN(cid) && (IsTC || bIsIphoneOs || bIsAndroid || bIsWP || bIsCE || bIsWM || bIsSYB || bIsSER)){ window.location.href="http://cq.people.com.cn/GB/365644/367006/?Num=28065405";}
//if(bIsIpad){ window.location.href="http://cq.people.com.cn/m/phone/mnews.htm?Num=" + cid;}
</script>
<meta http-equiv="Content-Language" content="utf-8">
<meta name="mobile-agent" content="format=html5;url=http://cq.people.com.cn/GB/365644/367006/?Num=28065405">
<meta name="baidu-site-verification" content="0P8HvCoDek">
<meta content="all" name="robots">
<title>城口：2015年近8成贫困户获公益林生态效益补偿--重庆视窗--人民网 </title>
<meta name="keywords" content="城口">
<meta name="description" content="　　近日，笔者获悉，自精准扶贫工作开展以来，该县把公益林生态效益补偿作为一项重要的脱贫措施，大力实施公益林生态效益直补政策扶贫工程。2015年该县近8成贫困户获公益林生态效益补偿。">
<meta name="copyright" content="人民网版权所有">
<meta name="filetype" content="0">
<meta name="publishedtype" content="1">
<meta name="pagetype" content="1">
<meta name="catalogs" content="L_365411">
<meta name="contentid" content="L_28065405">
<meta name="publishdate" content="2016-04-01">
<meta name="author" content="L_104268">
<meta name="editor" content="L_104268">
<meta name="source" content="来源：人民网 原创稿">
<meta name="sourcetype" content="2">
<link rel="Shortcut Icon" href="/img/LOCAL/2014/06/112486/fav_icon.ico">
<link rel="stylesheet" type="text/css" href="/img/LOCAL/2014/06/112486/index_2013.css">
<link rel="stylesheet" type="text/css" href="/img/LOCAL/2014/06/112486/index_fy_2013.css">
<link rel="stylesheet" type="text/css" href="/img/LOCAL/2014/06/112486/wbtw.css">
<script src="http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion=405554"></script><script type="BAIDU_HH" runed="true">{"type":"flowbar","fixed_tpl":"2","di":"u2092251","rsi0":"auto","rsi1":"50","n":"1"}</script><script src="http://su.bdimg.com/static/dspui/js/ll/ls.js?dv=569"></script><style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style><link rel="stylesheet" href="http://bdimg.share.baidu.com/static/api/css/share_style1_32.css"></head>
<body>
<div class="w980 clear cj01"><!-- #BeginlibraryItem "/library/2014dfnavtop.lbi" --><!-- 调用样式表 -->
<script type="text/javascript" src="http://www.people.com.cn/img/2011people/jquery-1.4.3.min.js"></script>
<script type="text/javascript">
	/**处理已经登录的用户*/
	function sso_page_login_user(guzzLoginUser){
		var status = guzzLoginUser.displayName + "，欢迎您"  ;
		$("#loginStatus").html(status) ;
		$("#txz_dlq").hide();
		$("#txz_dlh").show();
	}
</script>
<script type="text/javascript" src="http://bbs1.people.com.cn/sns/newjs/common/jquery.rmw.global.js" charset="utf-8"></script>
<script type="text/javascript" src="http://bbs1.people.com.cn/sns/newjs/pages/www.news.js" charset="utf-8"></script>
  <style type="text/css">
.nav_top2{ height:32px; background:url(/img/2012wbn/images/top_bg.gif);}
.nav_top2 div{ line-height:32px;}
.nav_top2 div em{ float:left;}
.nav_top2 div.fr input,.nav_top2 div.fr select{ vertical-align:middle;}
.nav_top2 div.fr input.input01{ height:16px; line-height:16px; width:60px; margin-left:5px; margin-right:10px;}
.nav_top2 div.fr input.input02{ margin-left:10px; margin-right:10px; width:32px; height:20px;}
.nav_top{ text-align:center; width:970px;}
.nav_top em{ display:none;}
.nav_top a{ padding:0 3px;}
.nav_top i,.nav01 i a{ color:#c00;}
.logo_line em{ float:left; padding-top:12px;}
.logo_line i{ float:right;}
.path a{ padding:0 10px;}
.path em{ display:none;}
  </style>
  <!--[if !IE]><!-->
<style type="text/css">
.nav div span{margin-top:0px}
.nav ul{ margin:6px 10px;}
</style>
<!--<![endif]-->
  <!--人民网主导航-->
  <!--nav-->
<div class="nav_top2 clear">
   <div class="w960">
     <em><a href="http://www.people.com.cn" target="_blank">人民网首页</a></em>
     <div class="fr" id="txz_dlq"><form id="sso_login_form" action="http://passport.people.com.cn/_login.do">账号<input value="" name="userName" id="userName" type="text" class="input01">密码<input type="password" value="" name="password" id="password" class="input01"><span style="display:none;"><input type="checkbox" name="rememberMe" id="rememberMe" checked="checked" value="1"><label for="rememberMe">记住登录状态</label></span><select name="retUrl" id="sso_login_form_retUrl" class="retUrl">
  <option value="refer" selected="selected">选择去向</option>
  <option value="http://bbs1.people.com.cn">强国社区</option>
  <option value="http://bbs1.people.com.cn/boardList.do?action=postList&amp;boardId=1">强国论坛</option>
  <option value="http://qgblog.people.com.cn">强国博客</option>
  <option value="http://sns.people.com.cn">SNS</option>
  <option value="http://t.people.com.cn">人民微博</option>
  <option value="http://liaoba.people.com.cn">人民聊吧</option>
  <option value="http://vblog.people.com.cn">人民播客</option>
  <option value="http://ezheng.people.com.cn">E政广场</option>
  <option value="http://71.people.com.cn">七一社区</option>
  <option value="http://passport.people.com.cn/usr/loginSuccess.do">通行证首页</option>
</select><input type="submit" name="" value="登录" class="input02">|&nbsp;&nbsp;<a href="http://passport.people.com.cn/usrReg.do?regFrom=news" target="_blank">注册</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="http://www.people.com.cn/GB/138812/index.html" target="_blank">网站地图</a></form></div>
     <div class="fr" id="txz_dlh" style="display:none;"><span id="loginStatus"></span>&nbsp;
<select class="dlh_select" onchange="window.open(this.value)">
  <option value="http://www.people.com.cn" selected="selected">选择去向</option>
  <option value="http://bbs1.people.com.cn">强国社区</option>
  <option value="http://bbs1.people.com.cn/boardList.do?action=postList&amp;boardId=1">强国论坛</option>
  <option value="http://qgblog.people.com.cn">强国博客</option>
  <option value="http://sns.people.com.cn">SNS</option>
  <option value="http://t.people.com.cn">人民微博</option>
  <option value="http://liaoba.people.com.cn">人民聊吧</option>
  <option value="http://vblog.people.com.cn">人民播客</option>
  <option value="http://ezheng.people.com.cn">E政广场</option>
  <option value="http://71.people.com.cn">七一社区</option>
  <option value="http://passport.people.com.cn/usr/loginSuccess.do">通行证首页</option>
</select>
&nbsp;<a href="http://passport.people.com.cn/logout.do?retUrl=refer"><img src="/img/2011people/images/login_exit.jpg" width="40" height="19" alt="" data-bd-imgshare-binded="1"></a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="http://www.people.com.cn/GB/138812/index.html" target="_blank">网站地图</a></div>
   </div>
</div>
<script type="text/javascript">
$("#sso_login_form").bind('submit', function(event){
	if(!$("#userName").val()){
		alert("请输入用户名") ;
		event.preventDefault() ;
	}else if(!$("#password").val()){
		alert("请输入密码") ;
		event.preventDefault() ;
	}

}) ;

$("#sso_login_form_retUrl").bind('change', function(event){
	if($(this).val() == 'http://www.people.com.cn'){
		$("#sso_login_form").attr("target", "_top") ;
	}else{
		$("#sso_login_form").attr("target", "_blank") ;
	}
}) ;
</script>
<div class="nav_top m10"><em><img src="/img/2012wbn/images/logo03.gif" width="103" height="43" data-bd-imgshare-binded="1"></em><i><a href="http://cpc.people.com.cn/" target="_blank">共产党新闻</a></i><a href="http://news.people.com.cn/" target="_blank">要闻</a><a href="http://politics.people.com.cn/" target="_blank">时政</a><a href="http://legal.people.com.cn/" target="_blank">法治</a>|<a href="http://world.people.com.cn/" target="_blank">国际</a><a href="http://military.people.com.cn/" target="_blank">军事</a>|<a href="http://tw.people.com.cn/" target="_blank">台港澳</a><a href="http://edu.people.com.cn/" target="_blank">教育</a>|<a href="http://society.people.com.cn/" target="_blank">社会</a><a href="http://pic.people.com.cn/" target="_blank">图片</a><a href="http://opinion.people.com.cn/" target="_blank">观点</a><a href="http://unn.people.com.cn/GB/41796/index.html" target="_blank">地方</a>|<a href="http://finance.people.com.cn/" target="_blank">财经</a><a href="http://auto.people.com.cn/" target="_blank">汽车</a><a href="http://house.people.com.cn/" target="_blank">房产</a>|<a href="http://sports.people.com.cn/" target="_blank">体育</a><a href="http://ent.people.com.cn/" target="_blank">娱乐</a><a href="http://culture.people.com.cn/" target="_blank">文化</a><a href="http://media.people.com.cn/" target="_blank">传媒</a>|<a href="http://tv.people.com.cn/" target="_blank">电视</a><a href="http://bbs.people.com.cn/" target="_blank">社区</a><a href="http://zhengwutong.com" target="_blank">政务通</a><a href="http://blog.people.com.cn" target="_blank">博客</a><a href="http://fangtan.people.com.cn/" target="_blank">访谈</a>|<a href="http://game.people.com.cn/" target="_blank">游戏</a><a href="http://mms.people.com.cn/" target="_blank">彩信</a><a href="http://comic.people.com.cn/" target="_blank">动漫</a><a href="http://rss.people.com.cn/" target="_blank">RSS</a></div>
<script type="text/javascript">
var bForcepc = fGetQuery("dv") == "pc";
function fBrowserRedirect(){
    var sUserAgent = navigator.userAgent.toLowerCase();
    var bIsIpad = sUserAgent.match(/ipad/i) == "ipad";
    var bIsIphoneOs = sUserAgent.match(/iphone os/i) == "iphone os";
    var bIsMidp = sUserAgent.match(/midp/i) == "midp";
    var bIsUc7 = sUserAgent.match(/rv:1.2.3.4/i) == "rv:1.2.3.4";
    var bIsUc = sUserAgent.match(/ucweb/i) == "ucweb";
    var bIsAndroid = sUserAgent.match(/android/i) == "android";
    var bIsCE = sUserAgent.match(/windows ce/i) == "windows ce";
    var bIsWM = sUserAgent.match(/windows mobile/i) == "windows mobile";
    if(bIsIphoneOs || bIsAndroid||bIsMidp||bIsUc7||bIsUc||bIsCE||bIsWM){
        var sUrl = location.href;
        if(!bForcepc){
		var iframe=document.getElementsByTagName("iframe");
    for(var i=0;i<iframe.length;i++){
    iframe[i].src="";
	}
    }
    }
}
function fGetQuery(name){
    var sUrl = window.location.search.substr(1);
    var r = sUrl.match(new RegExp("(^|&)" + name + "=([^&]*)(&|$)"));
    return (r == null ? null : unescape(r[2]));
}
fBrowserRedirect();
</script>
  <!--结束 人民网主导航--><!-- #EndlibraryItem --></div>
<div class="div990">
<div class="Logo mt10"><a href="http://cq.people.com.cn" target="_top"><img src="http://mcq.people.com.cn/img201508/logo.gif" alt="人民网重庆视窗" data-bd-imgshare-binded="1"></a></div>
  <div class="main_nav01 mt10"><ul class="mt7">
			<li><a href="http://cq.people.com.cn/" target="_blank">&nbsp;首页&nbsp;</a></li>
            <li><a href="http://cq.people.com.cn/GB/365401/" target="_blank">&nbsp;原创&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365402/" target="_blank">&nbsp;重庆&nbsp;</a></li>
			<li><a href="http://mcq.people.com.cn/video-web/" target="_blank">&nbsp;电视&nbsp;</a></li>
			<li><a href="http://mcq.people.com.cn/pic-web/" target="_blank">&nbsp;高清&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365403/" target="_blank">&nbsp;国内&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365424/" target="_blank">&nbsp;舆情&nbsp;</a></li>
            <li><a href="http://cq.people.com.cn/GB/365405/" target="_blank">&nbsp;社会&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365408/" target="_blank">&nbsp;评论&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365417/" target="_blank">&nbsp;专题&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365425/" target="_blank">&nbsp;人民日报看重庆&nbsp;</a></li>
		</ul>
		<ul>
			<li><a href="http://cq.people.com.cn/GB/365411/" target="_blank">&nbsp;区县&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365415/" target="_blank">&nbsp;房产&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365412/" target="_blank">&nbsp;企业&nbsp;</a></li>
            <li><a href="http://cq.people.com.cn/GB/365413/" target="_blank">&nbsp;金融&nbsp;</a></li>
            <li><a href="http://cq.people.com.cn/GB/371335/" target="_blank">&nbsp;教育&nbsp;</a></li>
			<li><a href="http://mcq.people.com.cn/jkpd/" target="_blank">&nbsp;健康&nbsp;</a></li>
			<li><a href="http://mcq.people.com.cn/newscenter/cq/cqlb.cqr300" target="_blank">&nbsp;联播&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365416/" target="_blank">&nbsp;汽摩&nbsp;</a></li>
			<li><a href="http://cq.people.com.cn/GB/365409/" target="_blank">&nbsp;文娱&nbsp;</a></li>
            <li><a href="http://cq.people.com.cn/GB/365410/" target="_blank">&nbsp;体育&nbsp;</a></li>
            <li><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank">&nbsp;给地方领导留言&nbsp;</a></li>
		</ul></div>
  <div class="blank10 clear"></div>
  <div class="ad990"><a href="http://lianghui.people.com.cn/2016npc/" target="_blank" title="十二届全国人大四次会议专题--中国人大新闻"><img src="http://mcq.people.com.cn/gg2016/990x75_quanguolianghui.jpg" width="990" height="75" alt="十二届全国人大四次会议专题--中国人大新闻" data-bd-imgshare-binded="1"></a></div>
</div>
<script src="http://code.jquery.com/jquery-1.11.0.min.js"></script>
<script type="text/javascript" src="/img/LOCAL/2014/06/112486/js/easytabswb.js"></script>
<script src="/css/search.js"></script>
<!--------loginbar-------->
<div id="loginbar" class="clear clearfix">
  <div class="w980">

    <form action="http://search.people.com.cn/rmw/GB/rmwsearch/gj_search_pd.jsp" name="searchForm" method="post" onsubmit="if(getParameter_DJ('上海频道') == false) return false;" target="_blank">
<input type="hidden" name="XMLliST">
	<div class="search"><input type="text" name="names" id="names" size="27" maxlength="50"> <input name="submit1" type="image" src="/img/LOCAL/2014/06/112486/images/icon_ser1.gif"></div></form>
<div class="toplist">
  <div class="topicon">
    <ul><li><a><img src="/img/LOCAL/2014/06/112486/images/home.png" alt="主页" data-bd-imgshare-binded="1"></a></li>
      <li><a href="/cqqs_bbs/register.cq" target="_blank"><img src="/img/LOCAL/2014/06/112486/images/zhuce.png" alt="注册" data-bd-imgshare-binded="1"></a></li>
      <li><a href="mailto:rmrb_cq@163.net" target="_blank"><img src="/img/LOCAL/2014/06/112486/images/tougao.png" alt="投稿" data-bd-imgshare-binded="1"></a></li>
      <li style="border:0px;cursor:hand; a:hover:test-decoration: underline;" onclick="window.external.addFavorite('http://cq.people.com.cn','人民网·重庆视窗')"><img src="/img/LOCAL/2014/06/112486/images/shouchang.png" alt="收藏" data-bd-imgshare-binded="1"></li></ul>
    </div>
  </div>
  </div>
</div>
<!--------topnav-------->
<table width="980" id="main" border="0" cellspacing="0" cellpadding="0">
  <tbody><tr>
    <td align="left" valign="top" width="660"><div id="left">
    <div class="left_nav">
	 	<div class="left_nav_text"><a href="http://www.people.com.cn/">人民网</a> &gt;&gt; <a href="http://cq.people.com.cn/">重庆视窗</a> &gt;&gt; <a href="http://cq.people.com.cn/GB/365411/">区县</a></div>
	</div>
	<!-----标题----->
	<div class="j_title"><span></span></div>
	<div class="m_title"><span>城口：2015年近8成贫困户获公益林生态效益补偿</span></div>
	<div class="f_title"><span></span></div>
	<!-----来源----->
	<div class="m_zs">
	<p class="sjly">2016年04月01日15:51　 来源：<a href="http://www.people.com.cn/" target="_blank">人民网</a>　 (责编：王嫚、张祎)</p>
	<p class="sjwb"><a href="http://t.sina.com.cn/cqpeople" target="_blank">微博看重庆</a></p>
	</div>
	<!-----摘要----->
	<div class="m_zy"><table class="summary" cellpadding="0" cellspacing="0" border="0"><tbody><tr><td valign="top" align="left">　　近日，笔者获悉，自精准扶贫工作开展以来，该县把公益林生态效益补偿作为一项重要的脱贫措施，大力实施公益林生态效益直补政策扶贫工程。2015年该县近8成贫困户获公益林生态效益补偿。</td></tr></tbody></table></div>
	<div class="m_text">

	<p></p><p>
	　　人民网重庆4月1日电 近日，笔者获悉，自精准扶贫工作开展以来，该县把公益林生态效益补偿作为一项重要的脱贫措施，大力实施公益林生态效益直补政策扶贫工程。2015年该县近8成贫困户获公益林生态效益补偿。</p>
<p>
	　　2015年，该县共兑现林农公益林生态效益补偿资金1604万元，惠及林农49000余户。其中，建卡贫困户8493户，占全县建卡贫困户总数的77.2%，兑现补偿资金2823762.12元，人均获得补偿75元。</p>
<p>
	　　“自2014年起，保证政策落实到户到人，资金的兑现采用银行“一卡通”发放。”县林业局有关负责人说，有效减少了资金发放环节，杜绝了资金被截留、挪用等现象，这一到户脱贫政策的落实，增加了贫困户政策性收入，在一定程度上帮助了贫困户缓解了生产生活筹资难。</p>
<p>
	　　目前，该县正在积极向上级部门争取利用生态补偿和生态保护工程资金，将本地有劳动能力的部分贫困人口转为护林员等生态保护人员，以解决贫困群众就业问题，帮助贫困人口稳定增收，实现脱贫不返贫。（王嫚 李小玲 黄座登 王文）</p>
<p></p>
</div>
	<!-----分享----->
	<div class="m_zr"><div class="bdsharebuttonbox bdshare-button-style1-32" data-bd-bind="1459998436047"><a class="bds_more" href="#" data-cmd="more"></a><a title="分享到QQ好友" class="bds_sqq" href="#" data-cmd="sqq"></a><a title="分享到微信" class="bds_weixin" href="#" data-cmd="weixin"></a><a title="分享到新浪微博" class="bds_tsina" href="#" data-cmd="tsina"></a><a title="分享到腾讯微博" class="bds_tqq" href="#" data-cmd="tqq"></a><a title="分享到QQ空间" class="bds_qzone" href="#" data-cmd="qzone"></a><a title="分享到人人网" class="bds_renren" href="#" data-cmd="renren"></a></div>
<script>window._bd_share_config={"common":{"bdSnsKey":{},"bdText":"","bdMini":"2","bdMiniList":false,"bdPic":"","bdStyle":"1","bdSize":"32"},"share":{},"image":{"viewList":["sqq","weixin","tsina","tqq","qzone","renren"],"viewText":"分享到：","viewSize":"16"},"selectShare":{"bdContainerClass":null,"bdSelectMiniList":["sqq","weixin","tsina","tqq","qzone","renren"]}};with(document)0[(getElementsByTagName('head')[0]||body).appendChild(createElement('script')).src='http://bdimg.share.baidu.com/static/api/js/share.js?v=89860593.js?cdnversion='+~(-new Date()/36e5)];</script></div>



	<!-----评论----->
	<div class="pl">
	  <span id="news_id" style="display:none;">28065405</span>
       <a name="liuyan"></a>
       <!-- 页面1开始 -->
	 <div class="message">
		<script type="text/javascript">
			var isLogin = false;
			/**处理已经登录的用户*/
			function sso_page_login_user(guzzLoginUser){
				var status = guzzLoginUser.displayName + ", 欢迎你&nbsp;&nbsp;&nbsp;<a href='http://passport.people.com.cn/logout.do?retUrl=refer'><font color=red>【退出】</font></a>" ;
				$("#idForLoginPanel").html(status) ;
				$("#operPanel").css("display", "none") ;
				portraitImg = rmw.global.getPortraitUrl(guzzLoginUser.userNick, 50) ;
				$(".portrait").attr("src",portraitImg);
				$("#userLink").attr("href","http://sns.people.com.cn/home.do?uid="+guzzLoginUser.userId);
				$("#userLink").attr("target","_blank");
				var o=new Image();
		        o.src=portraitImg;
		        o.onerror=function(){
		         $(".portrait").attr("src","/img/2012wbn/images/message/b2.jpg");
		         $("#userLink").attr("href","#");

		        };
				$("#errorMsg").html("");

				var status1 = guzzLoginUser.displayName + "，欢迎您" ;
				$("#loginStatus").html(status1) ;
				$("#txz_dlq").hide();
				$("#txz_dlh").show();
				isLogin = true;
			}

			/**处理访客*/
			function sso_page_login_guest(){
			    var href = window.location.href;
			    var errorMsg = _rmw_util_.getQueryString(href, "errorMsg") ;
			    if(errorMsg == 1){
				$("#errorMsg").html("<font color='red'>登录失败!请检查用户名和密码</font>");
				}
			}

			$(document).ready(function(){
				$("#login_btn").click(function(){
					 var userName = $("#loginForm_userName").attr("value") ;
					 var password = $("#loginForm_password").attr("value");
					  if(userName==''||userName==null){
			                 $("#login_error_tip").html("<font color='red'>请输入通行证帐号</font>").hide().fadeIn(1500) ;
			                 $("#login_error_tip").fadeOut(1500);
					 		 return false ;
					  }else if(password==''||password==null){
			                 $("#login_error_tip").html("<font color='red'>请输入通行证密码</font>").hide().fadeIn(1500) ;
			                 $("#login_error_tip").fadeOut(1500);
					 		 return false ;
					  }
					  $("#loginForm").attr("action","http://passport.people.com.cn/_login.do"); //test
					  $("#loginForm").submit();

				})
				 //登录动作
				 $(".dlk_a").click(function(){
					 $("#postReply").hide();
					 $("#dlkLogin").show();
			     })


				 $(".close").click(function(){
					$("#dlkLogin").hide();
					 $("#postReply").show();
				 })
				var quesType = "";

				$("#messageContent").blur(function(){
					 if($(this).val()==""){
						 $(this).addClass("messageContentRed");
						 $(this).val("请输入留言内容") ;
			        };
				});
				$("#messageContent").focus(function(){
					  if($(this).val()=="请输入留言内容"){
						  $(this).removeClass("messageContentRed");
						  $(this).val("");
			          }
				});
				var count = 30;
				$("#replyForm_nid").val($("#news_id").html());
				$("#loginForm_nid").val($("#news_id").html());
				$('#replyForm').submit(function(){
					if($("#messageContent").val().length==0||$("#messageContent").val()=="请输入留言内容"){
						$("#messageContent").blur();
					}else{
					  jQuery.ajax({
							url : "http://bbs1.people.com.cn/postRecieveFromNewsLocal.do" ,
							type: "GET",
							dataType: "jsonp",
							data : $(this).serialize(),
							success: function(text){
								 var obj = eval('(' + text + ')');
								 $("#postReply").hide();
								 $("#messageContent").val("");
								 $(".post0").attr("href",obj.postLink0);
								 $(".post0").html(obj.postTitle0);
								 $(".post1").attr("href",obj.postLink1);
								 $(".post1").html(obj.postTitle1);
								 if(obj.msg=='success'&& obj.quickPost==1){
									 $("#randomUserName").html(obj.userName);
									 $("#randomUserPassword").html(obj.password);
									 $("#quickPostSuccess").show();
									 setTimeout(BtnCount, 1000);
								 }else if(obj.msg=='success'){
									 $("#success").show();
									 setTimeout("$('#success').hide();", 5000);
									 setTimeout("$('#postReply').show();", 5000);
								 }else{
									 $("#postErrorMsg").html(obj.msg);
									 $("#fail").show();
									 setTimeout("$('#fail').hide();", 5000);
									 setTimeout("$('#postReply').show();", 5000);
								 }
							}
						});
					}
				   return false;
			   });

				BtnCount = function(){
					 if (count == 0) {
						 location.reload();
					 }else{
						 $("#returnTime").html(count--);
						 setTimeout(BtnCount, 1000);
					 }
				}
			});

		</script>
	<!-- 页面1结束 --><!-- 页面2开始 -->
<div id="postReply">
		<!--留言-->
		<div class="w600">
			<form id="replyForm" name="replyForm" method="post">
				<input type="hidden" name="nid" id="replyForm_nid" value="28065405">
				<input type="hidden" name="isAjax" value="true">
				<div class="tit">
					<h2>我要留言</h2>
					<span>
						<a href="http://bbs1.people.com.cn" target="_blank">进入讨论区</a>
						<a href="http://bbs1.people.com.cn" target="_blank">论坛</a>
						<a href="http://blog.people.com.cn" target="_blank">博客</a>
						<a href="http://t.people.com.cn" target="_blank">微博</a>
						<a href="http://sns.people.com.cn" target="_blank">SNS</a>
						<a href="http://bbs1.people.com.cn/board/131.html" target="_blank">育儿宝</a>
						<a href="http://bbs1.people.com.cn/board/3/29.html" target="_blank">图片</a>
					</span>
				</div>
				<dl class="message_c">
					<dt>
						<a href="#" id="userLink"><img class="portrait" src="/img/2012wbn/images/message/b2.jpg" width="48" height="48" alt=" " data-bd-imgshare-binded="1"> </a> <br>
						<span id="operPanel"> <a href="http://passport.people.com.cn/usrReg.do?regFrom=qglt" target="_blank">注册</a>/<a class="dlk_a" style="cursor: pointer;">登录</a> </span>
					</dt>
					<dd>
						<b><a href="http://bbs1.people.com.cn/gltl.do" target="_blank">发言请遵守新闻跟帖服务协议</a> </b>&nbsp;&nbsp;<b id="errorMsg"></b><br>
						<textarea name="messageContent" cols="" rows="" id="messageContent" onfocus="if(value=='善意回帖，理性发言!'){value=''}">善意回帖，理性发言!</textarea>
						<p>
							<span id="idForLoginPanel">使用其他账号登录:
								<a href="http://open.denglu.cc/transfer/sina?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/sina.gif" width="16" height="17" alt="新浪微博帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/qzone?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/qq.gif" width="16" height="17" alt="QQ帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/renren?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/renren.gif" width="16" height="17" alt="人人帐号登录" data-bd-imgshare-binded="1"> </a> <a href="http://open.denglu.cc/transfer/baidu?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/baidu.gif" width="16" height="17" alt="百度帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/douban?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/douban.gif" width="16" height="17" alt="豆瓣帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/tianya?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/tianya.gif" width="16" height="17" alt="天涯帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/taobao?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/taobao.gif" width="16" height="17" alt="淘宝帐号登录" data-bd-imgshare-binded="1"> </a>
								<a href="http://open.denglu.cc/transfer/windowslive?appid=11646denmMU7U45KpQ1WYz2J9lfOnA&amp;param1=1" target="_blank">
								<img src="/img/2012wbn/images/message/dl3.gif" width="16" height="17" alt="MSN帐号登录" data-bd-imgshare-binded="1"> </a> </span>
								<strong>同步：<input type="checkbox" checked=""><a href="#"><img src="/img/2012wbn/images/message/people.gif" width="16" height="16" alt="分享到人民微博" data-bd-imgshare-binded="1"> </a>&nbsp;
								<input type="submit" class="sub_input" value=""></strong>
						</p>
					</dd>
				</dl>
			</form>
		</div>
	</div>

	<!-- 弹出层页面 -->
	<style type="text/css">
	   body{padding:0;margin:0;font:normal 12px/180% "SimSun"; color:#333;background:#fff;text-align:left;}
	    h1,h2,h3,h4,h5,h6,hr,p,blockquote,dl,dt,dd,ul,ol,li,pre,form,button,input,textarea,th,td{margin:0;padding:0;}
	    div{ margin:0 auto;text-align:left;font:normal 12px/180% "SimSun";}
	    a:link,a:visited{color:#000;text-decoration:none}
	    a:hover{color:#c00;text-decoration:underline}
	    img{ border:none}
	    ol,ul,li{list-style:none;}
	    i{font-style:normal;}
	      /*clear*/
	      .clear{clear:both}
	      .clearfix:after,.search_left p:after,.search_list_c p:after{display:block;clear:both;content:".";visibility:hidden; height:0;}
	      /*color style*/
	      .green{color:#498b08;}
	      /*other*/
	      .w980{width:980px;}
	      .fl{float:left;}
	      .fr{float:right;}
	      .tc{text-align:center;}
	      .tl{text-align:left;}
	      .tr{text-align:right;}
	      /*留言提示*/
	      .message_tip{width: 570px;height: 196px;border: 5px solid #e9f6fc;margin: 0;}
	      .message_tip p{text-align: center;padding: 5px 0;color: #8a8a8a;}
	      .message_tip p img{vertical-align: middle;}
	      .message_tip p.t1{color: #4c86d0;padding: 15px 0;font-size: 14px;}
	      .message_tip p.t2{background: #e6f5fc;color: #878988;}
	      .message_tip p.t2 a:link,.message_tip p.t2 a:visited,.message_tip p.t2 a:hover,.message_tip p.t1 a:link,.message_tip p.t1 a:visited,.message_tip p.t1 a:hover{color: #c30101;}
	      .message_tip p a:link,.message_tip p a:visited,.message_tip p a:hover{color: #878988;}
	      .messageContentRed{ color:red;}
     </style>
	<!-- 登录 -->
	<div class="clearfix" id="dlkLogin">
	<div class="dlk">
			<div class="dlk_t">
				<b>社区登录</b><b id="login_error_tip" align="center"></b><a href="javascript:void(0);" class="close"><img src="/img/2012wbn/images/message/dl_06.gif" alt="" data-bd-imgshare-binded="1"> </a>
			</div>
			<form id="loginForm" method="post">
				<input type="hidden" name="rememberMe" value="1">
				<input type="hidden" name="retUrl" value="refer">
				<input type="hidden" name="nid" id="loginForm_nid" value="28065405">
				<table border="0" align="center" cellpadding="0" cellspacing="15">
					<tbody><tr>
						<td>用户名： <input type="text" class="input_userName" name="userName" id="loginForm_userName"> <i>
							<a href="http://passport.people.com.cn/usrReg.do?regFrom=qglt" target="_blank">立即注册</a> </i>
						</td>
					</tr>
					<tr>
						<td>密&nbsp;&nbsp;码： <input type="password" class="input_userName" id="loginForm_password" name="password"> <i>
							<a href="http://passport.people.com.cn/findPsw_selectType.do" target="_blank">找回密码</a> </i>
						</td>
					</tr>
					<tr>
						<td align="center">
							<a id="login_btn"><img src="/img/2012wbn/images/message/dl_11.gif" data-bd-imgshare-binded="1"> </a>&nbsp;&nbsp;
							<a class="close"><img src="/img/2012wbn/images/message/dl_13.gif" data-bd-imgshare-binded="1"> </a>
						</td>
					</tr>
				</tbody></table>
			</form>
	</div>
	<div class="dlk_bg"></div>
	</div>
	<!-- quickPost eq '1' && msg eq 'success' -->
	<div class="message_tip" id="quickPostSuccess" style="display: none;">
	    <p class="t1"><img src="/img/2012wb/images/dui.gif" alt="" border="0" data-bd-imgshare-binded="1">恭喜你，发表成功!</p>
	    <p class="t2">请牢记你的用户名:<span id="randomUserName"></span>，密码:<span id="randomUserPassword"></span>,立即进入<a href="http://sns.people.com.cn" target="_blank">个人中心</a>修改密码。</p>
	    <p><span id="returnTime">30</span>s后自动返回</p>
	    <p><a href="javascript:location.reload();"><img src="/img/2012wb/images/fanhui.gif" alt="" border="0" data-bd-imgshare-binded="1"></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="http://bbs1.people.com.cn/" target="_blank"><img src="/img/2012wb/images/jinru.gif" alt="" border="0" data-bd-imgshare-binded="1"></a></p>
	    <p><a class="post0" href="" target="_blank">推荐帖子推荐帖子推荐帖子</a>&nbsp;&nbsp;&nbsp;&nbsp;<a class="post1" href="" target="_blank">推荐帖子推荐帖子推荐帖子</a></p>
	</div>

	<!-- msg != 'success' -->
	<div class="message_tip" id="fail" style="display: none;">
	    <p class="t1"><img src="/img/2012wb/images/close.jpg" alt="" border="0" data-bd-imgshare-binded="1"><span id="postErrorMsg"></span>!</p>
	    <p></p>
	    <p>5s后自动返回</p>
	    <p><a href="javascript:location.reload();"><img src="/img/2012wb/images/fanhui.gif" alt="" border="0" data-bd-imgshare-binded="1"></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="http://bbs1.people.com.cn/" target="_blank"><img src="/img/2012wb/images/jinru.gif" alt="" border="0" data-bd-imgshare-binded="1"></a></p>
	    <p><a href="" class="post0" target="_blank">推荐帖子推荐帖子推荐帖子</a>&nbsp;&nbsp;&nbsp;&nbsp;<a class="post1" href="" target="_blank">推荐帖子推荐帖子推荐帖子</a></p>
	</div>

	<!-- msg == 'success' -->
	<div class="message_tip" id="success" style="display: none;">
	    <p class="t1"><img src="/img/2012wb/images/dui.gif" alt="" border="0" data-bd-imgshare-binded="1">恭喜你，发表成功!</p>
	    <p>5s后自动返回</p>
	    <p><a href="javascript:location.reload();"><img src="/img/2012wb/images/fanhui.gif" alt="" border="0" data-bd-imgshare-binded="1"></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="http://bbs1.people.com.cn/" target="_blank"><img src="/img/2012wb/images/jinru.gif" alt="" border="0" data-bd-imgshare-binded="1"></a></p>
	    <p><a class="post0" href="" target="_blank">推荐帖子推荐帖子推荐帖子</a>&nbsp;&nbsp;&nbsp;&nbsp;<a class="post1" href="" target="_blank">推荐帖子推荐帖子推荐帖子</a></p>
	</div>
	</div>
       <!--message end-->
       <!--留言板块--><div class="note_list clearfix" style="display: none;"><div class="note_t clearfix"><ul><li id="news_pinglun" class="focus">最新评论</li><li id="hot_pinglun">热门评论</li></ul><span id="hot_key">热词:<a href="http://bbs1.people.com.cn/quickSearch.do?field=title&amp;threadtype=1&amp;content=%E5%8D%81%E4%B8%89%E4%BA%94" target="_blank">十三五</a><a href="http://bbs1.people.com.cn/quickSearch.do?field=title&amp;threadtype=1&amp;content=%E5%85%BB%E8%80%81" target="_blank">养老</a><a href="http://bbs1.people.com.cn/quickSearch.do?field=title&amp;threadtype=1&amp;content=%E6%89%B6%E8%B4%AB" target="_blank">扶贫</a><a href="http://bbs1.people.com.cn/quickSearch.do?field=title&amp;threadtype=1&amp;content=%E5%9B%BD%E4%BC%81%E6%94%B9%E9%9D%A9" target="_blank">国企改革</a><a href="http://bbs1.people.com.cn/quickSearch.do?field=title&amp;threadtype=1&amp;content=%E8%82%A1%E5%B8%82" target="_blank">股市</a></span><a href="" id="all_link" target="_blank">鏌ョ湅鍏ㄩ儴undefined鏉＄暀瑷€</a></div><div class="note_list_c clearfix" id="note_list_c"><ul></ul></div></div><script type="text/javascript" src="/img/2012wb/jquery.note.local.js"></script><script type="text/javascript">$(document).ready(function() {$.show_note_list('28065405','28065405');});</script><!--结束留言板块-->
	</div>
	<div class="blank30"></div>
	<!-----底部新闻----->
	<div class="zhxw">
		<div class="menu">
			  <ul><li><a href="http://cq.people.com.cn/GB/365409/" target="_blank" onmouseover="easytabs('1', '1');" onfocus="easytabs('1', '1');" title="娱乐" id="tablink1">娱乐</a></li>
				<li><a href="http://cq.people.com.cn/GB/365418/" target="_blank" onmouseover="easytabs('1', '2');" onfocus="easytabs('1', '2');" title="旅游" id="tablink2">旅游</a></li>
				<li><a href="http://cq.people.com.cn/GB/365411/" target="_blank" onmouseover="easytabs('1', '3');" onfocus="easytabs('1', '3');" title="区县" id="tablink3">区县</a></li>
				<li><a href="http://mcq.people.com.cn/jrcq/" target="_blank" onmouseover="easytabs('1', '4');" onfocus="easytabs('1', '4');" title="金融" id="tablink4">金融</a> </li>
				<li><a href="http://mcq.people.com.cn/qiyemingpian/" target="_blank" onmouseover="easytabs('1', '5');" onfocus="easytabs('1', '5');" title="企业" id="tablink5">企业</a> </li>
				<li><a href="http://mcq.people.com.cn/house/" target="_blank" onmouseover="easytabs('1', '6');" onfocus="easytabs('1', '6');" title="房产" id="tablink6">房产</a> </li>
				<li><a href="http://mcq.people.com.cn/jkpd/" target="_blank" onmouseover="easytabs('1', '7');" onfocus="easytabs('1', '7');" title="健康" id="tablink7">健康</a> </li>
<script type="text/javascript">var cpro_id = 'u2092251';</script><script src=" http://su.bdimg.com/static/dspui/js/uf.js" type="text/javascript"></script></ul>
			</div>
			<div id="tabcontent1">

		      <div class="tab_m">


		      </div>
			</div>
			<!--Start Tabcontent 2-->
			<div id="tabcontent2">
              <div class="tab_pic"><ul class="tw195">
				  <li class="pic"><a href="/n/2015/1104/c365418-27015263.html" target="_blank"><img src="/NMediaFile/2015/1104/LOCAL201511041455000378016161602.jpg" width="300" height="225" border="0" alt="尚色美术教育户外写生活动回顾" data-bd-imgshare-binded="1"></a></li>
				  <li class="text"><a href="/n/2015/1104/c365418-27015263.html" target="_blank">尚色美术教育户外写生活动回顾</a></li>
				  <li class="trans_layer"></li>
		        </ul>
<ul class="tw195">
				  <li class="pic"><a href="/n/2015/1104/c365418-27015243.html" target="_blank"><img src="/NMediaFile/2015/1104/LOCAL201511041453000567643554704.jpg" width="300" height="225" border="0" alt="巴蜀书院塘河古镇民俗文化探索之旅" data-bd-imgshare-binded="1"></a></li>
				  <li class="text"><a href="/n/2015/1104/c365418-27015243.html" target="_blank">巴蜀书院塘河古镇民俗文化探索...</a></li>
				  <li class="trans_layer"></li>
		        </ul>

</div>
		      <div class="tab_m">


		      </div>
			</div>
			<!--Start Tabcontent 3-->
			<div id="tabcontent3">
              <div class="tab_pic"><ul class="tw195">
				  <li class="pic"><a href="/n2/2016/0331/c367652-28057224.html" target="_blank"><img src="/NMediaFile/2016/0331/LOCAL201603311537000356050341149.jpg" width="300" height="225" border="0" alt="铜梁改革让共青团活力四射 " data-bd-imgshare-binded="1"></a></li>
				  <li class="text"><a href="/n2/2016/0331/c367652-28057224.html" target="_blank">铜梁改革让共青团活力四射&nbsp;</a></li>
				  <li class="trans_layer"></li>
		        </ul>
<ul class="tw195">
				  <li class="pic"><a href="/n2/2016/0329/c367652-28033404.html" target="_blank"><img src="/NMediaFile/2016/0329/LOCAL201603290826000431634595705.jpg" width="300" height="225" border="0" alt="库区航运生机勃勃" data-bd-imgshare-binded="1"></a></li>
				  <li class="text"><a href="/n2/2016/0329/c367652-28033404.html" target="_blank">库区航运生机勃勃</a></li>
				  <li class="trans_layer"></li>
		        </ul>

</div>
		      <div class="tab_m">
			    <div class="smalltt"><h2><a href="/n2/2016/0401/c367651-28065292.html" target="_blank">重庆市第25期区县部门主要领导干部进修班到重庆市廉政教育基地接受警示教育 </a></h2>
         <p>&nbsp;&nbsp;&nbsp;&nbsp;　　3月29日，重庆市第25期区县部门主要领导干部进修班全体学员前往铁山坪，参观重庆市廉政教育基地，接受廉政警示教育，进一步强化党员干部的党性、法纪、廉洁意识。</p>

</div>
                <ul class="list360"><li><a href="/n2/2016/0331/c367650-28057192.html" target="_blank">江北区“云创空间”入选国家级众创空间</a></li>
<li><a href="/n2/2016/0331/c367650-28056740.html" target="_blank">綦江区着力打造重庆交通用铝产业基地</a></li>
<li><a href="/n2/2016/0331/c365411-28056697.html" target="_blank">奉节电商网络脐橙节4月1日启幕 网购送“大礼”</a></li>
<li><a href="/n2/2016/0329/c367650-28033623.html" target="_blank">“重庆武隆”品牌价值逾90亿元</a></li>
<li><a href="/n2/2016/0329/c367650-28033456.html" target="_blank">江北成立群团公益基金会</a></li>
<li><a href="/n2/2016/0328/c367650-28031536.html" target="_blank">当“钢琴”遇见“油画” </a></li>

</ul>
		      </div>
			</div>
			<!--Start Tabcontent 4-->
			<div id="tabcontent4">

		      <div class="tab_m">

                <ul class="list360"><li><a href="/n/2015/1203/c367643-27241206.html" target="_blank">双十一生鲜销售成黑马，农村电商如何进军生鲜市场？</a></li>

</ul>
		      </div>
			</div>
			<!--Start Tabcontent 5-->
			<div id="tabcontent5">

		      <div class="tab_m">


		      </div>
			</div>
			<!--Start Tabcontent 6-->
			<div id="tabcontent6">

		      <div class="tab_m">


		      </div>
			</div>
			<!--Start Tabcontent 7-->
			<div id="tabcontent7">

		      <div class="tab_m">


		      </div>
			</div>
	</div>
	<div class="blank30"></div>

	</div>
	</td>
    <td align="left" valign="top" width="320"><div id="right">

		<div class="blank10"></div>
  	<div class="r_tt2"><h2><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank">给地方领导留言</a></h2></div>
  <div class="r_box"><div class="con_ld">
	    <div class="pic65"><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank"><img src="/NMediaFile/2014/1028/LOCAL201410281754302564767097808.jpg" width="75" height="80" border="0" data-bd-imgshare-binded="1"></a></div>
		<div class="ldr_ly"><div class="ldr_ly">
		  <h4>孙政才</h4>
		  <h5>重庆市委书记</h5>
		  <h3><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank" title="给重庆市委书记孙政才留言"><img src="http://cq.people.com.cn/images_2013/wyly.jpg" alt="给重庆市委书记孙政才留言" data-bd-imgshare-binded="1"></a></h3>
		</div></div>
   </div>
    <div class="blank10"></div>
<div class="con_ld">
	    <div class="pic65"><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank"><img src="/NMediaFile/2014/1028/LOCAL201410281754309465823593584.jpg" width="75" height="80" border="0" data-bd-imgshare-binded="1"></a></div>
		<div class="ldr_ly"><div class="ldr_ly">
		  <h4>黄奇帆</h4>
		  <h5>重庆市市长</h5>
		  <h3><a href="http://liuyan.people.com.cn/index.php?gid=33" target="_blank" title="给重庆市市长黄奇帆留言"><img src="http://cq.people.com.cn/images_2013/wyly.jpg" alt="给重庆市市长黄奇帆留言" data-bd-imgshare-binded="1"></a> </h3>
		</div></div>
   </div>
    <div class="blank10"></div>
</div>
  		<div class="blank10"></div>
  <div class="r_tt"><h2><a href="http://cq.people.com.cn/GB/365402/" target="_blank" title="重庆新闻">重庆新闻</a></h2></div>
      <div class="r_box2">

        <ul class="r_l12 pb10"><li><a href="/n2/2016/0401/c365402-28059423.html" target="_blank">联合签证申请中心在渝设立 可受理八个申根国签证</a></li>
<li><a href="/n2/2016/0401/c365402-28059415.html" target="_blank">重庆:清明节400万人出行祭扫 请你避开主城堵点 </a></li>
<li><a href="/n2/2016/0401/c365402-28059380.html" target="_blank">陈坤携《火锅英雄》回到家乡 想让全世界知道重庆</a></li>
<li><a href="/n2/2016/0401/c365402-28059345.html" target="_blank">补换领驾照不用再跑回核发地办 四大亮点值得关注</a></li>

</ul>
      </div>
  		<div class="blank10"></div>
  <div class="r_tt"><h2><a href="http://cq.people.com.cn/video-web/" target="_blank" title="人民网直播重庆">人民网直播重庆</a></h2></div>
  <div class="r_box2">
    <div class="blank10"></div>
    <div class="r_piclist">
      <ul><li><a href="/n2/2016/0126/c362578-27633639.html" target="_blank"><img src="/NMediaFile/videotemp/201601/26/LOCALVIDEO20160126211752F6972012688.jpg" width="134" height="95" border="0" alt="委员声音：为城市过街天桥加顶棚 彰显人文关怀" data-bd-imgshare-binded="1"></a><h4><a href="/n2/2016/0126/c362578-27633639.html" target="_blank">委员声音：为城市...</a></h4></li>
<li><a href="/n2/2016/0126/c362578-27633638.html" target="_blank"><img src="/NMediaFile/videotemp/201601/26/LOCALVIDEO20160126211752F6114482155.jpg" width="134" height="95" border="0" alt="委员声音：重视和保护青少年视力健康刻不容缓" data-bd-imgshare-binded="1"></a><h4><a href="/n2/2016/0126/c362578-27633638.html" target="_blank">委员声音：重视和...</a></h4></li>
<li><a href="/n2/2016/0126/c362578-27633471.html" target="_blank"><img src="/NMediaFile/videotemp/201601/26/LOCALVIDEO20160126200052F4424423169.jpg" width="134" height="95" border="0" alt="重庆三部门负责人谈“十三五”规划" data-bd-imgshare-binded="1"></a><h4><a href="/n2/2016/0126/c362578-27633471.html" target="_blank">重庆三部门负责人...</a></h4></li>
<li><a href="/n2/2016/0126/c362578-27625285.html" target="_blank"><img src="/NMediaFile/videotemp/201601/26/LOCALVIDEO20160126010020F1967835358.jpg" width="134" height="95" border="0" alt="李建春：巴南今后五年要打好“殷实小康”这一仗" data-bd-imgshare-binded="1"></a><h4><a href="/n2/2016/0126/c362578-27625285.html" target="_blank">李建春：巴南今后...</a></h4></li>

</ul>
    </div>
  </div>
  <div class="blank10"></div>
  		<div class="r_tt"><h2><a href="http://cq.people.com.cn/GB/367698/" target="_blank" title="图片频道">图片新闻</a></h2></div>
  <div class="r_box2">
    <div class="blank10"></div>
	<div class="con134"><ul class="tw134">
		<li class="pic"><a href="/n2/2016/0401/c367698-28059517.html" target="_blank"><img src="/NMediaFile/2016/0401/LOCAL201604010734000325947479853.jpg" width="134" height="95" border="0" alt="习近平会见丹麦首相拉斯穆森" data-bd-imgshare-binded="1"></a></li>
		<li class="text"><a href="/n2/2016/0401/c367698-28059517.html" target="_blank">习近平会见丹麦首...</a></li>
		<li class="trans_layer"></li>
	  </ul>
<ul class="tw134">
		<li class="pic"><a href="/n2/2016/0401/c367698-28059488.html" target="_blank"><img src="/NMediaFile/2016/0401/LOCAL201604010733000057021887219.jpg" width="134" height="95" border="0" alt="清明节将至 南京雨花台布置花坛“缅怀”先烈" data-bd-imgshare-binded="1"></a></li>
		<li class="text"><a href="/n2/2016/0401/c367698-28059488.html" target="_blank">清明节将至&nbsp;南京...</a></li>
		<li class="trans_layer"></li>
	  </ul>
<ul class="tw134">
		<li class="pic"><a href="/n2/2016/0401/c367698-28059142.html" target="_blank"><img src="/NMediaFile/2016/0401/LOCAL201604010708000487326967964.jpg" width="134" height="95" border="0" alt="重庆自主开发新型单轨道岔设备安装在碧津站" data-bd-imgshare-binded="1"></a></li>
		<li class="text"><a href="/n2/2016/0401/c367698-28059142.html" target="_blank">重庆自主开发新型...</a></li>
		<li class="trans_layer"></li>
	  </ul>
<ul class="tw134">
		<li class="pic"><a href="/n2/2016/0401/c367698-28059105.html" target="_blank"><img src="/NMediaFile/2016/0401/LOCAL201604010702000519512775409.jpg" width="134" height="95" border="0" alt="江津几江长江大桥合龙 预计6月28日通车" data-bd-imgshare-binded="1"></a></li>
		<li class="text"><a href="/n2/2016/0401/c367698-28059105.html" target="_blank">江津几江长江大桥...</a></li>
		<li class="trans_layer"></li>
	  </ul>

</div>
  </div>
  <div class="blank10"></div>


  		<div class="blank10"></div>
   <div class="r_tt"><h2>微博关注</h2></div>
   <div class="r_wb"><iframe width="100%" height="100" class="share_self" frameborder="0" scrolling="no" src="http://widget.weibo.com/weiboshow/index.php?language=&amp;width=0&amp;height=100&amp;fansRow=0&amp;ptype=1&amp;speed=0&amp;skin=1&amp;isTitle=0&amp;noborder=0&amp;isWeibo=1&amp;isFans=0&amp;uid=1887449931&amp;verifier=a4b838a0&amp;dpc=1"></iframe></div>
</div>
<script language="javascript">
<!--
function cqpeople_changesfunction_right2013_pics_22(id1,id2)
{
id1status=document.getElementById(id1).style.display;
id2status=document.getElementById(id2).style.display;
if (id1status=='block'){
	document.getElementById(id1).style.display = 'none';
	$("#" + id2).fadeIn(1000);
	document.getElementById(id2).style.display = 'block';}
if (id2status=='block'){
	document.getElementById(id2).style.display = 'none';
	$("#" + id1).fadeIn(1000);
	document.getElementById(id1).style.display = 'block';}
}

$(function () {setInterval(function (){cqpeople_changesfunction_right2013_pics_22("sjjy-b","sjjy-c");},4000);});
-->
</script>
</td>
  </tr>
</tbody></table>
<!--------footer-------->
<div class="blank30"></div>
<div id="footer">
  <div class="footernav"><h3><a href="/" target="_blank">首页</a> - <a href="http://cq.people.com.cn/GB/365401/" target="_blank">原创</a> - <a href="http://cq.people.com.cn/GB/365402/" target="_blank">重庆</a> - <a href="http://cq.people.com.cn/GB/365407/" target="_blank">旗帜</a> - <a href="http://cq.people.com.cn/GB/365403/" target="_blank">国内</a> - <a href="http://cq.people.com.cn/GB/365404/" target="_blank">国际</a> - <a href="http://cq.people.com.cn/GB/365405/" target="_blank">社会</a> - <a href="http://cq.people.com.cn/GB/365408/" target="_blank">评论</a> - <a href="http://cq.people.com.cn/GB/365409/" target="_blank">娱乐</a> - <a href="http://cq.people.com.cn/GB/365410/" target="_blank">体育</a> - <a href="http://cq.people.com.cn/GB/365415/" target="_blank">
房产</a> - <a href="http://cq.people.com.cn/GB/365413/" target="_blank">金融</a> - <a href="http://cq.people.com.cn/GB/365412/" target="_blank">企业</a> - <a href="http://cq.people.com.cn/GB/371335/" target="_blank">教育</a> - <a href="http://cq.people.com.cn/GB/365406/" target="_blank">科教</a> - <a href="http://cq.people.com.cn/GB/365418/" target="_blank">旅游</a> - <a href="http://cq.people.com.cn/GB/365416/" target="_blank">汽摩</a> - <a href="http://mcq.people.com.cn/pic-web/" target="_blank">图片</a> - <a href="http://mcq.people.com.cn/video-web/" target="_blank">人民网直播重庆</a> - <a href="http://cq.people.com.cn/GB/365425/" target="_blank">人民日报看重庆</a></h3>
  </div>
  <div class="blank15"></div>
  <div class="footerbox">
    <div class="footerbox_l">
	  <div class="footertext"><h5><a href="http://www.people.com.cn/GB/50142/104580/index.html" target="_blank">人民日报社概况</a> | <a href="http://www.people.com.cn/GB/50142/353480/353481/index.html" target="_blank">关于人民网</a> | <a href="http://www.people.com.cn/GB/1018/22259/6138836.html" target="_blank">网站声明</a> | <a href="http://www.people.com.cn/GB/50142/50459/57871/4064597.html" target="_blank">网站律师</a> | <a href="http://kf.people.com.cn/" target="_blank">呼叫中心</a></h5>
<h5><a href="http://www.people.com.cn/img/2011zzzs/2011icp.htm" target="_blank">京ICP证000006号</a> | 京公网安备110000000008号 | <a href="http://www.people.com.cn/img/2011zzzs/2011xxwlcb.htm" target="_blank">网上传播视听节目许可证（0104065）</a> | <a href="http://tv.people.com.cn/GB/6983227.html" target="_blank">中国互联网视听节目服务自律公约</a></h5>
<h5>地址：重庆市北部新区星光大道62号海王星大厦B区5楼 | 电话：023-67885665 023-67885660 | 传真：023-67885600 </h5>
<h5></h5>
<h6>人 民 网 版 权 所 有 ，未 经 书 面 授 权 禁 止 使 用</h6>
<h6>Copyright © 1997-2016 by www.people.com.cn. all rights reserved</h6></div>
    </div>
    <div class="footerbox_r">
  		<div class="footerlinks"><select size="1" name="D1" class="linkstext" onchange="window.open(this.options[this.selectedIndex].value,'_blank')"><option selected="">-- 人民网地方频道 --</option><option value="http://bj.people.com.cn/">北京</option><option value="http://tj.people.com.cn/">天津</option><option value="http://he.people.com.cn/">河北</option><option value="http://sx.people.com.cn/">山西</option><option value="http://nm.people.com.cn/">内蒙古</option><option value="http://ln.people.com.cn/">辽宁</option><option value="http://jl.people.com.cn/">吉林</option><option value="http://hl.people.com.cn/">黑龙江</option><option value="http://sh.people.com.cn/">上海</option><option value="http://sd.people.com.cn/">山东</option><option value="http://ah.people.com.cn/">安徽</option><option value="http://zj.people.com.cn/">浙江</option><option value="http://fj.people.com.cn/">福建</option><option value="http://js.people.com.cn/">江苏</option><option value="http://jx.people.com.cn/">江西</option><option value="http://gd.people.com.cn/">广东</option><option value="http://gx.people.com.cn/">广西</option><option value="http://hi.people.com.cn/">海南</option><option value="http://hb.people.com.cn/">湖北</option><option value="http://hn.people.com.cn/">湖南</option><option value="http://ha.people.com.cn/">河南</option><option value="http://cq.people.com.cn/">重庆</option><option value="http://sc.people.com.cn/">四川</option><option value="http://yn.people.com.cn/">云南</option><option value="http://gz.people.com.cn/">贵州</option><option value="http://www.chinatibetnews.com/">西藏</option><option value="http://sn.people.com.cn/">陕西</option><option value="http://gs.people.com.cn/">甘肃</option><option value="http://xj.people.com.cn/">新疆</option><option value="http://qh.people.com.cn/">青海</option><option value="http://nx.people.com.cn/">宁夏</option><option>港澳</option><option value="http://tw.people.com.cn/">台湾</option></select></div>

	  <div class="footerlinks"><select size="1" name="D2" class="linkstext" onchange="window.open(this.options[this.selectedIndex].value,'_blank')"><option selected="">-- 人民日报报系 --</option><option value="http://paper.people.com.cn/rmrb/index.html">人民日报</option>
<option value="http://paper.people.com.cn/rmrbhwb/paperindex.htm">海外版</option>
<option value="http://paper.people.com.cn/xwzx/paperindex.htm">新闻战线</option>
<option value="http://paper.people.com.cn/xaq/paperindex.htm">新安全</option>
<option value="http://paper.people.com.cn/smsb/paperindex.htm">生命时报</option>
<option value="http://www.people.com.cn/paper/tx_hqrw/tx_hqrw.html">环球人物</option>
<option value="http://paper.people.com.cn/rmlt/paperindex.htm">人民论坛</option>
<option value="http://paper.people.com.cn/jksb/paperindex.htm">健康时报</option>
<option value="http://epaper.stcn.com/">证券时报</option>
<option value="http://paper.people.com.cn/zgnyb/paperindex.htm">中国能源报</option>
<option value="http://paper.people.com.cn/mszk/paperindex.htm">民生周刊</option>
<option value="http://paper.people.com.cn/gjjrb/paperindex.htm">国际金融报</option>
<option value="http://paper.people.com.cn/rmwz/paperindex.htm">人民文摘</option>
<option value="http://paper.people.com.cn/fcyym/paperindex.htm">讽刺与幽默</option>
<option value="http://history.people.com.cn/GB/198819/index.html">国家人文历史</option>
<option value="http://paper.people.com.cn/zgjjzk/paperindex.htm">中国经济周刊</option>
<option value="http://www.cnautonews.com/">汽车网</option>
<option value="http://www.marketdaily.com.cn/">市场网</option>
</select></div>

	  <div class="footerlinks"><select size="1" name="D4" class="linkstext" onchange="window.open(this.options[this.selectedIndex].value,'_blank')"><option selected="">-- 重庆主要媒体 --</option><option value="http://www2.cqnews.net/showpdf/index.cqx?name=重庆日报">重庆日报</option><option value="http://www.cqwb.com.cn">重庆晚报</option><option value="http://www.cqcb.com">重庆晨报</option><option value="http://www.chinacqsb.com">重庆商报</option><option value="http://www.chongqingtimes.com.cn/">重庆时报</option><option value="http://www.cqqn.com/">重庆青年报</option><option value="http://www.newoo.com/">新女报</option><option value="http://www.cqdsrb.com/">都市热报</option><option value="http://www.cqtoday.cq.cn/">今日重庆</option><option value="http://www.shangjie.biz/">商界在线</option><option value="http://www.ccqtv.com/">重庆电视台</option><option value="http://www.cqnews.net">华龙网</option></select></div>

	  <div class="footerlinks"><select size="1" name="D3" class="linkstext" onchange="window.open(this.options[this.selectedIndex].value,'_blank')"><option selected="">-- 重庆机构 --</option><option value="http://www.cq.gov.cn/">市政府公众信息</option><option value="http://www.rd.cq.gov.cn/">市人大</option><option value="http://www.cqzx.gov.cn/">市政协</option><option value="http://www.cqjcy.gov.cn/">市人民检察院</option><option value="http://www.cqcourt.gov.cn/">市人民法院</option><option value="http://www.cqdpc.gov.cn/">市发改委</option><option value="http://www.cqec.gov.cn/">市经委</option><option value="http://www.cqedu.gov.cn/">市教委</option><option value="http://www.ctin.ac.cn/">市科委</option><option value="http://www.cqga.gov.cn/">市公安局</option><option value="http://jsf.cq.gov.cn/">市司法局</option><option value="http://jcz.cq.gov.cn/">市财政局</option><option value="http://www.cqpa.gov.cn/">市人事局</option><option value="http://www.cqldbz.gov.cn/">市劳动保障局</option><option value="http://www.cqgtfw.gov.cn/">市国土房管局</option><option value="http://www.ccc.gov.cn/">市建委</option><option value="http://www.cqupb.gov.cn/">市规划局</option><option value="http://wsz.cq.gov.cn/">市政管理委</option><option value="http://www.cqjt.gov.cn/">市交委</option><option value="http://www.cqit.gov.cn/">市信产局</option><option value="http://www.cqwater.gov.cn/">市水利局</option><option value="http://www.cqagri.gov.cn/">市农业局</option><option value="http://wsy.cq.gov.cn/">市商委</option><option value="http://www.ft.cq.cn/">市外经贸委</option><option value="http://www.cqcrtv.gov.cn/">市文广局</option><option value="http://www.cqwsj.gov.cn/">市卫生局</option><option value="http://www.cqrk.gov.cn/">市人口计生委</option><option value="http://jsj.cq.gov.cn/">市审计局</option><option value="http://bws.cq.gov.cn/">市政府外事办</option><option value="http://www.sasaccq.gov.cn/">市国资委</option><option value="http://www.cq-l-tax.gov.cn/">市地税局</option><option value="http://www.cepb.gov.cn/">市环保局</option><option value="http://www.cqtj.gov.cn/">市统计局</option><option value="http://www.cqgs12315.cn/">市工商局</option><option value="http://www.cqppb.gov.cn/">市新闻出版局</option><option value="http://jliny.cq.gov.cn/">市林业局</option><option value="http://www.cqzj.gov.cn/">市质监局</option><option value="http://www.cqda.gov.cn/">市药监局</option><option value="http://www.cqta.gov.cn/">市旅游局</option><option value="http://jls.cq.gov.cn/">市粮食局</option></select></div>

	  <div class="footerlinks"><select size="1" name="D5" class="linkstext" onchange="window.open(this.options[this.selectedIndex].value,'_blank')"><option selected="">-- 合作站点 --</option><option value="http://www.ccpc.cq.cn/">重庆人大</option><option value="http://www.cq.gov.cn/">重庆市政府公众信息网</option><option value="http://cqzx.gov.cn/">重庆政协</option><option value="http://cqfy.chinacourt.org/">重庆法院网</option><option value="http://www.cqyzfy.gov.cn/">重庆一中法院</option><option value="http://www.cqsy.org/">重庆社会主义学院</option><option value="http://www.hongyan.info/">红岩联线</option><option value="http://cq.xinhuanet.com/">新华网重庆频道</option><option value="http://www.cqnews.net/">华龙网</option><option value="http://www.cq.chinanews.com.cn/">重庆新闻网</option><option value="http://www.cqcb.com/">重庆晨报网</option><option value="http://www.cqwb.com.cn/">重庆晚报网</option><option value="http://online.cq.cn/">重庆热线</option><option value="http://www.cqca.gov.cn/">重庆市通信管理局</option><option value="http://www.cepb.gov.cn/">重庆环境保护</option><option value="http://www.cqrcb.com/">重庆农村商业银行</option><option value="http://www.caistv.com/">商界财视网</option><option value="http://123.sogou.com/">搜狗网址</option><option value="http://www.cqsalt.com/">重庆盐业信息网</option><option value="http://www.koy.com">KOY.COM</option><option value="http://mzh.china5000.cn/">民族魂</option><option value="http://www.cn6154.com/">赛乐网</option><option value="http://www.dmguo.com/">动漫国</option><option value="http://www.cqfz.org.cn/">重庆发展网</option><option value="http://www.csts.net.cn/">重庆市大型科学仪器资源共享平台</option><option value="http://www.cqdxc.gov.cn/">重庆大学城</option><option value="http://news.swu.edu.cn/">西南大学资讯网</option><option value="http://www.cqyzfy.gov.cn/">重庆市一中院</option><option value="http://www.pacq.gov.cn/">平安重庆网</option><option value="http://www.cqst.org.cn/">重庆少年儿童图书馆</option><option value="http://www.tg630.com/">重庆630团购网</option><option value="http://www.cq7.cn/">7度重庆社区</option><option value="http://www.cq-ce.cn/">重庆经济网</option><option value="http://cq.kankan.com/">看看重庆</option></select></div>
	</div>
</div>
  <div class="blank15"></div>
  <div class="footerbox2">
    <div class="fo_kfd"><div class="footerkfd">
<ul>
<li style="margin-left:0;"><p><span class="upsver">V1.0.5</span></p>
<a style="cursor:hand" onclick="javascript:document.getElementById('app1_1').style.display='none';document.getElementById
('app1_2').style.display='block';"><img id="app1_1" style="display:block;" src="/img/LOCAL/2014/06/112486/images/ydimg1.jpg" alt="iphone客户端" data-bd-imgshare-binded="1"></a>
<a style="cursor:hand" onclick="javascript:document.getElementById('app1_2').style.display='none';document.getElementById
('app1_1').style.display='block';"><img id="app1_2" style="display:none;" src="http://mcq.people.com.cn/m/2codepng/ios.png" width="79" height="79" data-bd-imgshare-binded="1"></a>
</li>
<li><p><span class="upsver">V1.0.5</span></p>
<a style="cursor:hand" onclick="javascript:document.getElementById('app2_1').style.display='none';document.getElementById
('app2_2').style.display='block';"><img id="app2_1" style="display:block;" src="/img/LOCAL/2014/06/112486/images/ydimg2.jpg" alt="ipad客户端" data-bd-imgshare-binded="1"></a>
<a style="cursor:hand" onclick="javascript:document.getElementById('app2_2').style.display='none';document.getElementById
('app2_1').style.display='block';"><img id="app2_2" style="display:none;" src="http://mcq.people.com.cn/m/2codepng/ios.png" width="79" height="79" data-bd-imgshare-binded="1"></a>
</li>
<li><p><span class="upsver">V1.0.5</span></p>
<a style="cursor:hand" onclick="javascript:document.getElementById('app6_1').style.display='none';document.getElementById
('app6_2').style.display='block';"><img id="app6_1" style="display:block;" src="/img/LOCAL/2014/06/112486/images/ydimg6.jpg" alt="wp8手机客户端" data-bd-imgshare-binded="1"></a>
<a style="cursor:hand" onclick="javascript:document.getElementById('app6_2').style.display='none';document.getElementById
('app6_1').style.display='block';"><img id="app6_2" style="display:none;" src="http://mcq.people.com.cn/m/2codepng/wp8.png" width="79" height="79" data-bd-imgshare-binded="1"></a>
</li>
<li><p><span class="upsver">V1.0.5</span></p>
<a href="http://apps.microsoft.com/windows/app/6b5d21f9-a8b3-41fe-8ce8-349928bb9639" target="_blank"><img src="/img/LOCAL/2014/06/112486/images/ydimg5.jpg" alt="win8客户端" data-bd-imgshare-binded="1"></a>
</li>
<li><p><span class="upsver">V2.2.0</span></p>
<a style="cursor:hand" onclick="javascript:document.getElementById('app4_1').style.display='none';document.getElementById
('app4_2').style.display='block';"><img id="app4_1" style="display:block;" src="/img/LOCAL/2014/06/112486/images/ydimg4.jpg" alt="andriod手机客户端" data-bd-imgshare-binded="1"></a>
<a style="cursor:hand" onclick="javascript:document.getElementById('app4_2').style.display='none';document.getElementById
('app4_1').style.display='block';"><img id="app4_2" style="display:none;" src="http://mcq.people.com.cn/m/2codepng/android_1.png" width="79" height="79" data-bd-imgshare-binded="1"></a>
</li>
<li><p><span class="upsver">V1.8.5</span></p>
<a style="cursor:hand" onclick="javascript:document.getElementById('app3_1').style.display='none';document.getElementById
('app3_2').style.display='block';"><img id="app3_1" style="display:block;" src="/img/LOCAL/2014/06/112486/images/ydimg3.jpg" alt="andriod平板客户端" data-bd-imgshare-binded="1"></a>
<a style="cursor:hand" onclick="javascript:document.getElementById('app3_2').style.display='none';document.getElementById
('app3_1').style.display='block';"><img id="app3_2" style="display:none;" src="http://mcq.people.com.cn/m/2codepng/android_2.png" width="79" height="79" data-bd-imgshare-binded="1"></a>
</li>
</ul>
  </div>
      <div class="info_khd">·如何安装：苹果|微软在其官方应用商店、安卓手机在91助手中搜索“人民网重庆”；
或点击图标获得二维码<br>·我们也欢迎通过手机|平板的浏览器直接访问域名cq.people.com.cn，自动依照您的设备呈现最佳的
浏览体验</div>
<script type="text/javascript">(function(){document.write(unescape('%3Cdiv id="bdcs"%3E%3C/div%3E'));var bdcs = document.createElement('script');bdcs.type = 'text/javascript';bdcs.async = true;bdcs.src = 'http://znsv.baidu.com/customer_search/api/js?sid=5102689337316652524' + '&plate_url=' + encodeURIComponent(window.location.href) + '&t=' + Math.ceil(new Date()/3600000);var s = document.getElementsByTagName('script')[0];s.parentNode.insertBefore(bdcs, s);})();</script><div id="bdcs"><div class="bdcs-container"><meta http-equiv="x-ua-compatible" content="IE=9">                                     <!-- 侧滑式 -->          <div id="sliding-searchbox" class="8 sliding-searchbox-one" style="position: fixed; top: 150px;">              <form action="http://zhannei.baidu.com/cse/search" method="get" target="_blank" class="bdcs-search-form" id="sliding-search-form">                  <div id="sliding-box-detail">                      <div id="sliding-icon-left"></div>                      <div id="sliding-back-right"></div>                      <div class="sliding-box-item" id="sliding-box-item">                          <div class="sliding-box-meun bdcs-clearfix" id="sliding-box-meun">                  <input type="text" name="q" class="bdcs-search-form-input" id="sliding-search-form-input" placeholder="请输入关键词"><input type="submit" class="bdcs-search-form-submit  " id="sliding-search-form-submit" value="搜索">                           <input type="hidden" name="s" value="5102689337316652524">                                                                                <input type="hidden" name="ie" value="gbk">                                                                                    </div>              </div>              <div id="sliding-back"></div>              <div id="sliding-icon-right" style="display: block;"> </div>          </div>      </form>  </div>            </div></div></div>
    <div class="fo_tgjs"><h4><a href="mailto:cq_people@qq.com"><img src="http://mcq.people.com.cn/images_2013/tgts2.jpg" alt="投稿/投诉" data-bd-imgshare-binded="1"></a></h4>
	  <h4><a href="mailto:cqpeople@126.com"><img src="http://mcq.people.com.cn/images_2013/jshz2.jpg" alt="技术合作" data-bd-imgshare-binded="1"></a></h4></div>
  </div>
</div>
<div class="AdLayer"><a href="#top"><img src="/img/LOCAL/2014/06/112486/images/goto_top.gif" data-bd-imgshare-binded="1"></a></div>
<img src="http://58.68.146.44:8000/f.gif?id=28065405" width="0" height="0" data-bd-imgshare-binded="1">
<script language="javascript" src="/img/LOCAL/2014/06/112486/js/index_changes.js"></script>
<script src="/css/2010tianrun/webdig_test.js" language="javascript" type="text/javascript"></script><div id="BAIDU_DSPUI_FLOWBAR" fixed="true" style="height: 70px; position: fixed; width: 100%; z-index: 2147483647; zoom: 1; overflow: visible; bottom: 0px; margin-top: 0px; left: 0px; right: auto;"><iframe src="http://entry.baidu.com/rp/home?ifr=infr:1_cross:0_drs:1_pcs:1280x592_pss:1265x2331_cfv:0_cpl:5_chi:1_cce:1_cec:GBK_tlm:1459497192_ecd:1_adw:1265x50&amp;type=flowbar&amp;fixed_tpl=2&amp;di=u2092251&amp;rsi0=auto&amp;rsi1=50&amp;n=1&amp;title=%E5%9F%8E%E5%8F%A3%EF%BC%9A2015%E5%B9%B4%E8%BF%918%E6%88%90%E8%B4%AB%E5%9B%B0%E6%88%B7%E8%8E%B7%E5%85%AC%E7%9B%8A%E6%9E%97%E7%94%9F%E6%80%81%E6%95%88%E7%9B%8A%E8%A1%A5%E5%81%BF--%E9%87%8D%E5%BA%86%E8%A7%86%E7%AA%97--%E4%BA%BA%E6%B0%91%E7%BD%91&amp;ltu=http%3A%2F%2Fcq.people.com.cn%2Fn2%2F2016%2F0401%2Fc365411-28065405.html&amp;ref=&amp;pageWidth=1265&amp;pageHeight=592&amp;t=1459998435586&amp;rsi0=1265&amp;rsi1=50" style="height: 70px; background-color: transparent;" width="100%" height="100%" align="center,center" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" allowtransparency="true"></iframe><div style="position: absolute; opacity: 0.4; width: 40px; height: 20px; z-index: 111; top: -20px; right: 0px; background: rgb(0, 0, 0);"></div><div style="position: absolute; width: 40px; height: 20px; line-height: 20px; cursor: pointer; text-align: center; color: rgb(255, 255, 255); font-size: 12px; z-index: 112; top: -20px; right: 0px;">关闭</div></div><script id="tr_statobj" src="http://cl2.webterren.com/webdig.js?z=15" type="text/javascript"></script><script type="text/javascript"> wd_paramtracker('_wdxid=000000000000000000000000000000000000000000');</script>
<div style="position:absolute; width:20px; height:20px; visibility: hidden"><script src="http://s47.cnzz.com/stat.php?id=2038604&amp;web_id=2038604" language="JavaScript"></script><script src="http://c.cnzz.com/core.php?web_id=2038604&amp;t=z" charset="utf-8" type="text/javascript"></script><a href="http://www.cnzz.com/stat/website.php?web_id=2038604" target="_blank" title="站长统计">站长统计</a></div>

<audio controls="controls" style="display: none;"></audio><iframe frameborder="0" id="bdSharePopup_selectshare1459998436058bg" class="bdselect_share_bg" style="display:none;"></iframe><div id="bdSharePopup_selectshare1459998436058box" style="display:none;" share-type="selectshare" class="bdselect_share_box" data-bd-bind="1459998436057"><div class="selectshare-mod-triangle"><div class="triangle-border"></div><div class="triangle-inset"></div></div><div class="bdselect_share_head"><span>分享到</span><a href="http://www.baidu.com/s?wd=&amp;tn=SE_hldp08010_vurs2xrp" class="bdselect_share_dialog_search" target="_blank"><i class="bdselect_share_dialog_search_i"></i><span class="bdselect_share_dialog_search_span">百度一下</span></a><a class="bdselect_share_dialog_close"></a></div><div class="bdselect_share_content"><ul class="bdselect_share_list bdshare-button-style1-32"><div class="bdselect_share_partners"></div><a href="#" class="bds_more" data-cmd="more"></a></ul></div></div><div id="bdimgshare_1459998436084" class="sr-bdimgshare sr-bdimgshare-list sr-bdimgshare-16 sr-bdimgshare-black" style="height:36px;line-height:26px;font-size:12px;width:autopx;display:none;" data-bd-bind="1459998436083"><div class="bdimgshare-bg"></div><div class="bdimgshare-content bdsharebuttonbox bdshare-button-style0-16"><label class="bdimgshare-lbl">分享到：</label><a href="#" onclick="return false;" class="bds_sqq" data-cmd="sqq" hidefocus=""></a><a href="#" onclick="return false;" class="bds_weixin" data-cmd="weixin" hidefocus=""></a><a href="#" onclick="return false;" class="bds_tsina" data-cmd="tsina" hidefocus=""></a><a href="#" onclick="return false;" class="bds_tqq" data-cmd="tqq" hidefocus=""></a><a href="#" onclick="return false;" class="bds_qzone" data-cmd="qzone" hidefocus=""></a><a href="#" onclick="return false;" class="bds_renren" data-cmd="renren" hidefocus=""></a><a href="#" onclick="return false;" class="bds_more" data-cmd="more" hidefocus=""></a></div></div></body></html>'''


def getHtml4():
    return '''<html xmlns="http://www.w3.org/1999/xhtml"><head>
<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7">
<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7">
<meta http-equiv="Content-Type" content="text/html; charset=gb2312">
<title>千人采茶 齐游名山万亩生态茶园_云贵旅游地理网-中南偏西 精彩云贵</title>
<link media="all" href="/templets/default/style/article.css" type="text/css" rel="stylesheet"><link media="all" href="/templets/default/style/header_footer.css" type="text/css" rel="stylesheet">
<link media="all" href="/templets/default/style/css.css" type="text/css" rel="stylesheet">
<link href="/templets/default/style/dedecms.css" rel="stylesheet" media="screen" type="text/css">
<link href="/templets/default/style/top_hhw.css" type="text/css" rel="stylesheet">
<meta content="千人,采茶,齐游,名山,万亩,生态,茶园" name="keywords">
<meta content="春意盎然，仙茶飘香，4月2日清明小长假第一天，第十二届蒙顶山茶文化旅游节系列活动之一的蒙茶仙子春采茶活动在名山区中峰乡牛碾坪万亩生态观光茶园隆重举行，" 1000余人参与了体验活动。="" 本次活动由雅安市委农工委、雅安市名山区人民政府主办，四川蒙顶山茶业有限公司、四川省贸易学校协办。="" 踏春摄影="" 寻醉美茶仙子="" 清晨，牛碾坪万亩生态观光茶园笼罩在氤氲雾气中，满眼的油绿，被春雨滋润后的春茶，萌发出嫩绿的茶芽，散发出淡="" name="description">
<meta content="MSHTML 6.00.2900.3676" name="GENERATOR">
<script language="javascript" type="text/javascript" src="/include/dedeajax2.js"></script>
<script language="javascript" type="text/javascript">
<!--
function CheckLogin(){
	  var taget_obj = document.getElementById('_ajax_feedback');
	  myajax = new DedeAjax(taget_obj,false,false,'','','');
	  myajax.SendGet2("/member/ajax_feedback.php");
	  DedeXHTTP = null;
}
function postBadGood(ftype,fid)
{
	var taget_obj = document.getElementById(ftype+fid);
	var saveid = GetCookie('badgoodid');
	if(saveid != null)
	{
		var saveids = saveid.split(',');
		var hasid = false;
		saveid = '';
		j = 1;
		for(i=saveids.length-1;i>=0;i--)
		{
			if(saveids[i]==fid && hasid) continue;
			else {
				if(saveids[i]==fid && !hasid) hasid = true;
				saveid += (saveid=='' ? saveids[i] : ','+saveids[i]);
				j++;
				if(j==10 && hasid) break;
				if(j==9 && !hasid) break;
			}
		}
		if(hasid) { alert('您刚才已表决过了喔！'); return false;}
		else saveid += ','+fid;
		SetCookie('badgoodid',saveid,1);
	}
	else
	{
		SetCookie('badgoodid',fid,1);
	}
	myajax = new DedeAjax(taget_obj,false,false,'','','');
	myajax.SendGet2("/plus/feedback.php?aid="+fid+"&action="+ftype+"&fid="+fid);
}
function postDigg(ftype,aid)
{
	var taget_obj = document.getElementById('newdigg');
	var saveid = GetCookie('diggid');
	if(saveid != null)
	{
		var saveids = saveid.split(',');
		var hasid = false;
		saveid = '';
		j = 1;
		for(i=saveids.length-1;i>=0;i--)
		{
			if(saveids[i]==aid && hasid) continue;
			else {
				if(saveids[i]==aid && !hasid) hasid = true;
				saveid += (saveid=='' ? saveids[i] : ','+saveids[i]);
				j++;
				if(j==20 && hasid) break;
				if(j==19 && !hasid) break;
			}
		}
		if(hasid) { alert("您已经顶过该帖，请不要重复顶帖 ！"); return; }
		else saveid += ','+aid;
		SetCookie('diggid',saveid,1);
	}
	else
	{
		SetCookie('diggid',aid,1);
	}
	myajax = new DedeAjax(taget_obj,false,false,'','','');
	var url = "/plus/digg_ajax.php?action="+ftype+"&id="+aid;
	myajax.SendGet2(url);
}
function getDigg(aid)
{
	var taget_obj = document.getElementById('newdigg');
	myajax = new DedeAjax(taget_obj,false,false,'','','');
	myajax.SendGet2("/plus/digg_ajax.php?id="+aid);
	DedeXHTTP = null;
}
function check(){
		if(document.formsearch.searchtype.value=="")
		document.formsearch.action="http://www.google.cn/custom"
		else
		document.formsearch.action="/plus/search.php"
	}
-->
</script>
<style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style><script src="http://bdimg.share.baidu.com/static/js/logger.js?cdnversion=405604"></script><link href="http://bdimg.share.baidu.com/static/css/bdsstyle.css?cdnversion=20131219" rel="stylesheet" type="text/css"></head>
<body><iframe frameborder="0" style="display: none;"></iframe><div id="bdshare_s" style="display: block;"><iframe id="bdsIfr" style="position:absolute;display:none;z-index:9999;" frameborder="0"></iframe><div id="bdshare_l" style="display: none;"><div id="bdshare_l_c"><h6>分享到</h6><ul><li><a href="#" class="bds_mshare mshare">一键分享</a></li><li><a href="#" class="bds_qzone qqkj">QQ空间</a></li><li><a href="#" class="bds_tsina xlwb">新浪微博</a></li><li><a href="#" class="bds_bdysc bdysc">百度云收藏</a></li><li><a href="#" class="bds_renren rrw">人人网</a></li><li><a href="#" class="bds_tqq txwb">腾讯微博</a></li><li><a href="#" class="bds_bdxc bdxc">百度相册</a></li><li><a href="#" class="bds_kaixin001 kxw">开心网</a></li><li><a href="#" class="bds_tqf txpy">腾讯朋友</a></li><li><a href="#" class="bds_tieba bdtb">百度贴吧</a></li><li><a href="#" class="bds_douban db">豆瓣网</a></li><li><a href="#" class="bds_tsohu shwb">搜狐微博</a></li><li><a href="#" class="bds_bdhome bdhome">百度新首页</a></li><li><a href="#" class="bds_sqq sqq">QQ好友</a></li><li><a href="#" class="bds_thx thx">和讯微博</a></li><li><a href="#" class="bds_more">更多...</a></li></ul><p><a href="#" class="goWebsite">百度分享</a></p></div></div></div>
<div id="header">
<div class="bar">
<div class="sethome"><a href="">云贵旅游地理网</a>
</div>
<div class="login">
 请按这里把云贵旅游地理网-中南偏西 精彩云贵加入收藏：<a href="javascript:window.open('http://shuqian.qq.com/post?from=3&amp;title='+encodeURIComponent(document.title)+'&amp;uri='+encodeURIComponent(document.location.href)+'&amp;jumpback=2&amp;noui=1','favit','width=930,height=470,left=50,top=50,toolbar=no,menubar=no,location=no,scrollbars=yes,status=yes,resizable=yes');void(0)"><img src="/templets/default/images/qq.gif" alt="加入QQ收藏！" border="0" align="absmiddle"></a>
<a href="javascript:location.href='http://www.google.com/bookmarks/mark?op=add&amp;bkmk='+encodeURIComponent(location.href)+'&amp;title='+encodeURIComponent(document.title)"><img src="/templets/default/images/google.gif" alt="加入Google收藏！" border="0" align="absmiddle"></a>
<a href="javascript:window.open('http://cang.baidu.com/do/add?it='+encodeURIComponent(document.title.substring(0,76))+'&amp;iu='+encodeURIComponent(location.href)+'&amp;fr=ien#nw=1','_blank','scrollbars=no,width=600,height=450,left=75,top=20,status=no,resizable=yes'); void 0"><img src="/templets/default/images/baidu.gif" alt="加入Baidu收藏！" border="0" align="absmiddle"></a>
<a href="javascript:window.open('http://www.xianguo.com/service/submitfav/?link='+encodeURIComponent(location.href)+'&amp;title='+encodeURIComponent(document.title),'_blank');void 0;"><img src="/templets/default/images/xianguo.gif" alt="添加到鲜果" border="0" align="absmiddle"></a>
<a href="#" onclick="javascript:window.external.AddFavorite(document.URL,document.title);return false"><img src="/templets/default/images/ie.gif" alt="添加到我的收藏夹！" border="0" align="absmiddle"></a>
<a href="/data/sitemap.html">网站地图</a>
</div></div></div>
<div class="toparea">
<div class="logo">
<h1><a title="云贵旅游地理网-中南偏西" 精彩云贵="" href="/">云贵旅游地理网-中南偏西 精彩云贵</a></h1></div>
<div class="leftad">
<script src="/plus/ad_js.php?aid=8" language="javascript"></script><a href="http://fam.cntgol.com"><img src="http://www.csunews.com/uploads/allimg/130106/1_1517389951.jpg" width="592" height="80" border="0"></a>

</div>
<div class="rightad">
<script src="/plus/ad_js.php?aid=6" language="javascript"></script><a href="http://www.news.cn/politics/gygg/"><img src="http://www.csunews.com/uploads/allimg/130106/1_1519242561.jpg" width="150" height="80" border="0"></a>
</div>
<div class="rightad">

</div></div>
<div class="headmenu">
<ul>
  <li class="menu1">
  <p><a href="/news/" target="_blank">新闻</a><a href="/news/yc" target="_blank">原创</a><a href="/news/jiaodian" target="_blank">焦点</a><a href="/news/shiye" target="_blank">视野</a>
<br><a href="/news/dt" target="_blank">动态</a><a href="/news/qw" target="_blank">奇闻</a><a href="/news/gk" target="_blank">公告</a><a href="/news/hw" target="_blank">海外</a></p></li>
  <li class="menu2">
  <p><a href="/xing/" target="_blank">行走</a><a href="/xing/lushu" target="_blank">路书</a><a href="/xing/renwu" target="_blank">人物</a><a href="/xing/zijia" target="_blank">自驾</a><br><a href="/xing/tanxian" target="_blank">探险</a><a href="/xing/tubu" target="_blank">徒步</a><a href="/xing/meishi" target="_blank">美食</a><a href="/xing/baodian" target="_blank">宝典</a></p></li>
  <li class="menu3">
  <p><a href="/faxian" target="_blank">发现</a><a href="/faxian/wh/" target="_blank">文化</a><a href="/faxian/fq" target="_blank">风情</a>
<a href="/faxian/juzhu" target="_blank">居住</a>
<br>
<a href="/faxian/st" target="_blank">生态</a><a href="/faxian/qx" target="_blank">气象</a><a href="/faxian/yiji" target="_blank">遗迹</a>
<a href="/faxian/sc" target="_blank">山川</a>
</p>
</li>
  <li class="menu4">
  <p><a href="/fam" target="_blank">秘境</a><a href="/fam/kg" target="_blank">考古</a><a href="/fam/qy" target="_blank">奇异</a>
<a href="/pic" target="_blank">图片</a><br><a href="/fam/jm" target="_blank">解密</a>
<a href="/fam/js" target="_blank">旧事</a><a href="/fam/sclh" target="_blank">沙场</a>
<a href="/video" target="_blank">视频</a></p></li></ul><br class="clear"></div>
<div class="a980">
<script src="/plus/ad_js.php?aid=3" language="javascript"></script><a href="http://www.csunews.com/zhuanti/zhenggao"><img src="http://www.csunews.com/uploads/allimg/130321/13_1327032861.jpg" width="980" height="96" border="0"></a>

</div>
<div id="secmenu"><span>贵州省</span>
 <em><a href="/guizhousheng/gy">贵阳</a></em>
<em><a href="/guizhousheng/zy">遵义</a></em>
<em><a href="/guizhousheng/lps">六盘水</a></em>
<em><a href="/guizhousheng/as">安顺</a></em>
<em><a href="/guizhousheng/bj">毕节</a></em>
<em><a href="/guizhousheng/tr">铜仁</a></em>
<em><a href="/guizhousheng/qdn">黔东南</a></em>
<em><a href="/guizhousheng/qn">黔南</a></em>
<em><a href="/guizhousheng/qxn">黔西南</a></em>
 </div>
<div id="secmenu"><span>云南省</span>
 <em><a href="/yunnan/km">昆明</a></em>
<em><a href="/yunnan/zt">昭通</a></em>
<em><a href="/yunnan/qj">曲靖</a></em>
<em><a href="/yunnan/yx">玉溪</a></em>
<em><a href="/yunnan/bs">保山</a></em>
<em><a href="/yunnan/cx/">楚雄</a></em>
<em><a href="/yunnan/hh">红河</a></em>
<em><a href="/yunnan/ws/">文山</a></em>
<em><a href="/yunnan/puer">普洱</a></em>
<em><a href="/yunnan/xsbn">西双版纳</a></em>
<em><a href="/yunnan/dali">大理</a></em>
<em><a href="/yunnan/dh">德宏</a></em>
<em><a href="/yunnan/lijinag/">丽江</a></em>
<em><a href="/yunnan/nj">怒江</a></em>
<em><a href="/yunnan/dq">迪庆</a></em>
<em><a href="/yunnan/lc">临沧</a></em> </div>

<div class="a980">
<script src="/plus/ad_js.php?aid=11" language="javascript"></script>
</div>
<div id="zdlist"><!--列表页左边 开始 -->
<div id="zdlistbig">
<div class="topad">
<script language="javascript" src="/templets/default/js/q.js"></script>
</div>
<div class="zdlist">
<h4><a href="http://www.csunews.com/">云贵旅游地理网</a> &gt; <a href="/news/">新闻</a> &gt; <a href="/news/dt/">动态</a> &gt; </h4></div>
<div class="arctitle">
<h1>千人采茶 齐游名山万亩生态茶园</h1></div>
<div class="arcinfo"><span>时间:2016-04-03 15:41:36 | 来源:网络整理 |
编辑: | 作者:云贵旅游地理据网络整理 | </span> </div>

<div class="arccontent">
<p>
</p><table style="border-right: #cccccc 1px dotted; table-layout: fixed; border-top: #cccccc 1px dotted; border-left: #cccccc 1px dotted; border-bottom: #cccccc 1px dotted" cellspacing="0" cellpadding="6" width="95%" align="center" border="0">
    <tbody>
        <tr>
              <td style="WORD-WRAP: break-word" bgcolor="#fdfddf">[导读]：春意盎然，仙茶飘香，4月2日清明小长假第一天，第十二届蒙顶山茶文化旅游节系列活动之一的蒙茶仙子春采茶活动在名山区中峰乡牛碾坪万亩生态观光茶园隆重举行， 1000余人参与了体验活动。 本次活动由雅安市委农工委、雅安市名山区人民政府主办，四川蒙顶山茶业有限公司、四川省贸易学校协办。 踏春摄影 寻醉美茶仙子 清晨，牛碾坪万亩生态观光茶园笼罩在氤氲雾气中，满眼的油绿，被春雨滋润后的春茶，萌发出嫩绿的茶芽，散发出淡
</td>
        </tr>
    </tbody>
</table>
<p></p>
<p>　　</p><img alt="千人采茶 齐游名山万亩生态茶园" border="0" width="600" src="/uploads/allimg/c160403/1459B929B020-12246.jpg"><p></p><p>　　春意盎然，仙茶飘香，4月2日清明小长假第一天，第十二届蒙顶山茶文化<a href="http://www.cntgol.com">旅游</a>节系列活动之一的蒙茶仙子“春·<a href="/news/jiaodian/26001.html">采茶</a>”活动在<a href="/news/yc/3030.html">名山</a>区中峰乡牛碾坪万亩<a href="/news/dt/22718.html">生态</a>观光茶园隆重举行， 1000余人参与了体验活动。</p>

<p>　　本次活动由雅安市委农工委、雅安市名山区人民政府主办，四川蒙顶山茶业有限公司、四川省贸易学校协办。</p>

<p>　　踏春摄影　寻“醉美”茶仙子</p>

<p>　　清晨，牛碾坪万亩生态观光茶园笼罩在氤氲雾气中，满眼的油绿，被春雨滋润后的春茶，萌发出嫩绿的茶芽，散发出淡淡的茶香，置身其中，让人不禁沉醉。</p>

<p>　　微凉的天气却挡不住人们的热情。一辆辆自驾游旅行车行驶到牛碾坪的水泥路上，受邀的嘉宾和周边的游客早早地来到牛碾坪万亩生态观光茶园。</p>

<p>　　上午10时左右，记者在牛碾坪万亩观光茶园内起伏的茶垅间看到，最引人注目的来自四川省贸易学校蒙茶仙子们，她们一个个身着红色、蓝色或是白色碎花衣，头戴碎花巾，腰挎茶篼，挥动着灵巧的双手，在茶树上不停地上下翻飞采摘嫩芽，美丽的蒙茶仙子在如诗如画的茶山中人、茶、山三者合一，绘出一幅美丽画卷……</p>

<p>　　“雅雨飘飘蒙顶山，蒙顶山茶发新芽……”同一时间，在四周的茶山坡上，由四川贸易学校学生组成的蒙茶仙子们，唱起了悦耳动听的蒙顶山茶歌。云雾缭绕的茶山、漂亮的蒙茶仙子、动听的茶歌，让人心驰神往。</p>

<p>　　顿时，牛碾坪万亩生态观光茶园沸腾了，这里成了摄影爱好者的摄影天堂。各路媒体记者、摄影师，不停地按动相机快门，，留下蒙茶仙子们采茶的靓影。</p>

<p>　　“蒙茶仙子春·采茶活动美女云集，纤纤妙手蜻蜓点水般在茶树嫩叶上采摘。”来自成都的一位摄影爱好者王先生走进茶园内，不停用手机拍照，将蒙茶仙子们的靓照发到微信圈上，引来众多朋友点赞。</p>

<p>　　前来茶园游玩的游客们，也一个个按捺不住，开始在茶园里一试身手。</p>

<p>　　徜徉于茶乡，其实最惬意的方式当属骑自行车游茶道。还有部分游客骑着自行车，慢行在牛碾坪的骑游道上，视线所及都是似碧绿锦带般的垄垄茶林，微湿的空气中飘来淡淡的茶香，格外舒适、心旷神怡。</p>

<p>　　据介绍，今年，雅安市名山区将围绕“春·采茶”、“ 夏·纳凉”、“ 秋·骑游”、“ 冬·喝汤”，大力开展“生态名山，精彩四季”系列<a href="http://www.csunews.com" target="_blank"><u>旅游</u></a>宣传促销活动，进一步促进名山生态和文化资源转化为旅游产业发展优势。</p>

<p>　　游园品茗　赏“醉美”茶技艺</p>

<p>　　当天，蒙茶仙子“春·采茶”活动现场还设置了现场炒制茶叶展示，同时还举行了茶艺、茶技等的相关表演。</p>

<p>　　精湛的蒙顶山茶技——龙行十八式，也在音乐中，吸引了人们的眼神。</p>

<p>　　在茶艺表演场地，茶艺师们轻灵飘逸的一招一式，将中式、藏式、韩式不同的茶艺韵味展示的淋漓尽致，观众们看得也是如醉如痴。</p>

<p>　　真可谓是，美人，美景，茶艺，茶技，美不胜收。</p>

<p>　　素有“天然氧吧”美誉的牛碾坪，空气清新的茶园为成都以及周边的市民提供了踏青好去处，本届采茶节吸引了周边大批市民前往生态茶园，观美景，赏茶艺，嗅春风，品春茶，十分惬意。据悉，雅攀共建蒙顶山茶产业园—中峰乡牛碾坪是国家级茶树良种繁育场、<a href="http://www.csunews.com" target="_blank"><u>西南</u></a>最大的茶树基因库、全国农业旅游示范点，是名山灾后重建蒙顶山茶产业发展的代表和缩影，集基地、科创、生产和旅游为一体的茶叶旅游经济综合体。</p>

<p>　　在灾后恢复重建中，名山区立足景区茶区一体化，启动了以中峰乡牛碾坪为核心的国家茶叶公园建设。依托中峰乡牛碾坪良好的茶产业基础和深厚的茶文化底蕴，加快推进以“茶”为核心的茶旅综合体打造，推广“茶+桂”立体种植，形成“茶中有花、梯次开放、色彩纷呈、四季辉映”的花海茶香景观;建成了茶园骑游道、游步道以及儿童游乐设施，完成了观光亭廊、超市、茶楼、茶庄等配套服务设施。</p>

<p>　　通过旅游功能的完善，有效增强了牛碾坪旅游吸附能力，推动了以“茶”为核心的休闲农业与乡村旅游融合发展，实现了“茶园变公园、茶区变景区”。2015年，牛碾坪万亩观光茶园被评为“全国生态茶园示范基地”。</p>
<p></p><p><a href="http://www.csunews.com" style="float:right;margin-right:20px;margin-bottom:20px;"><img alt="" src="http://www.csunews.com/favicon.ico" style="width: 20px; height: 20px"></a></p>
<p></p>
<p><!-- Baidu Button BEGIN -->
</p><div id="bdshare" class="bdshare_t bds_tools get-codes-bdshare">
<a class="bds_tsina" title="分享到新浪微博" href="#"></a>
<a class="bds_tqq" title="分享到腾讯微博" href="#"></a>
<a class="bds_t163" title="分享到网易微博" href="#"></a>
<a class="bds_tsohu" title="分享到搜狐微博" href="#"></a>
<a class="bds_thx" title="分享到和讯微博" href="#"></a>
<a class="bds_tqf" title="分享到腾讯朋友" href="#"></a>
<a class="bds_renren" title="分享到人人网" href="#"></a>
<a class="bds_qzone" title="分享到QQ空间" href="#"></a>
<a class="bds_hi" title="分享到百度空间" href="#"></a>
<a class="bds_mshare" title="分享到一键分享" href="#"></a>
<span class="bds_more">更多</span>
</div>
<script type="text/javascript" id="bdshare_js" data="type=tools&amp;uid=0" src="http://bdimg.share.baidu.com/static/js/bds_s_v2.js?cdnversion=405604"></script>

<script type="text/javascript">
document.getElementById("bdshell_js").src = "http://bdimg.share.baidu.com/static/js/shell_v2.js?cdnversion=" + Math.ceil(new Date()/3600000)
</script>
<!-- Baidu Button END --><p></p>
<div class="pleft">
<div class="viewbox">
<div class="dede_pages">
<ul class="pagelist">
  <li></li></ul></div></div></div></div>
<div id="likeart">
<div class="hot mt1">
     <dl class="tbox">

           <dt><strong>相关文章</strong></dt>
               <dd>
                  <ul class="c1 ico2">
                       <table width="100%" border="0" cellspacing="0" cellpadding="0">
<tbody><tr>
    <td width="50%">
<li><a href="/news/dt/30737.html">第六届成都采茶节在蒲江开幕</a></li>
    </td>
    <td width="50%">
<li><a href="/news/dt/30566.html">进一步提升茶产业和乡村旅游融合发展 实现农业增效农民</a></li>
    </td>
    </tr>
<tr>
    <td width="50%">
<li><a href="/news/dt/23148.html">蜀道举办年猪节 千人共享庖汤宴</a></li>
    </td>
    <td width="50%">
<li><a href="/news/dt/22955.html">黎平上演非遗“侗族大歌”赛和千人“长桌宴”，场面精彩</a></li>
    </td>
    </tr>
<tr>
    <td width="50%">
    </td>
    <td width="50%">
    </td>
    </tr>
<tr>
    <td width="50%">
    </td>
    <td width="50%">
    </td>
    </tr>
<tr>
    <td width="50%">
    </td>
    <td width="50%">
    </td>
    </tr>
<tr>
    <td width="50%">
    </td>
    <td width="50%">
    </td>
    </tr>
<tr>
    <td width="50%">
    </td>
    <td width="50%">
    </td>
    </tr>
    </tbody></table>

                  </ul>
               </dd>
     </dl>
</div></div>

<div id="meirong_zq_div">
<div class="mr_newtop">
<h3>热点关注</h3>
<h2>
<a href="/member/article_add.php" target="_blank">原创投稿</a> </h2></div>
<div id="mr_cont_div">
<div id="mr_cont_left">
<ul>
<li><a href="/news/dt/32290.html" target="_blank"><img height="161" alt="吴文学：把握大众旅游" src="/uploads/allimg/c160409/146014455404Q0-1M09_lit.jpg" width="132" border="0"></a><br><a href="/news/dt/32290.html" target="_blank">吴文学：把握大众旅游</a> </li>
<li><a href="/news/shiye/32281.html" target="_blank"><img height="161" alt="第七届四川国际自驾游" src="/uploads/allimg/c160409/146013K01V510-1K52_lit.jpg" width="132" border="0"></a><br><a href="/news/shiye/32281.html" target="_blank">第七届四川国际自驾游</a> </li>

</ul></div>
<div id="mr_cont_right">
<h3><a href="/news/yc/23333.html" target="_blank">[关注世界遗产]冬日云南哈尼梯田美如画(图)</a></h3>

<ul>
<li><a href="/news/shiye/32279.html" target="_blank"><img height="80" alt="建政务云用大数据" 提="" src="/uploads/allimg/c160409/146013I533L20-13Q8_lit.jpg" width="100" border="0"></a><br><a href="/news/shiye/32279.html" target="_blank">建政务云用大数据 提</a> </li>
<li><a href="/news/jiaodian/32278.html" target="_blank"><img height="80" alt="冈仁波齐" |="" 一座藏地="" src="/uploads/allimg/c160409/1460135191L050-11431_lit.jpg" width="100" border="0"></a><br><a href="/news/jiaodian/32278.html" target="_blank">冈仁波齐 | 一座藏地</a> </li>
<li><a href="/news/jiaodian/32277.html" target="_blank"><img height="80" alt="【童言无忌走湘西】雪" src="/uploads/allimg/c160409/1460135161G3Z-195M_lit.jpg" width="100" border="0"></a><br><a href="/news/jiaodian/32277.html" target="_blank">【童言无忌走湘西】雪</a> </li>
<li><a href="/news/jiaodian/32276.html" target="_blank"><img height="80" alt="清明时节，当麓湖美成" src="/uploads/allimg/c160409/14601351033K60-12G2_lit.jpg" width="100" border="0"></a><br><a href="/news/jiaodian/32276.html" target="_blank">清明时节，当麓湖美成</a> </li>
<li><a href="/news/jiaodian/32275.html" target="_blank"><img height="80" alt="【意大利】" 从垂死之="" src="/uploads/allimg/c160409/14601350125bZ-1K05_lit.jpg" width="100" border="0"></a><br><a href="/news/jiaodian/32275.html" target="_blank">【意大利】 从垂死之</a> </li>
<li><a href="/news/jiaodian/32274.html" target="_blank"><img height="80" alt="岩溶之国" 探秘中国的="" src="/uploads/allimg/c160409/1460134953Q450-11295_lit.jpg" width="100" border="0"></a><br><a href="/news/jiaodian/32274.html" target="_blank">岩溶之国 探秘中国的</a> </li>

</ul>
<div id="mr_list_waik">
<dl>
<dd>·<a href="/news/dt/32290.html" target="_blank">吴文学：把握大众旅游时代特征 全力发展新</a> </dd>
<dd>·<a href="/news/shiye/32281.html" target="_blank">第七届四川国际自驾游交易博览会十月相约巴</a> </dd>
<dd>·<a href="/news/shiye/32280.html" target="_blank">王宁常务副省长在印度推介四川旅游</a> </dd>
<dd>·<a href="/news/shiye/32279.html" target="_blank">建政务云用大数据 提升现代社会治理能力</a> </dd>

</dl>
<dl>
<dd>·<a href="/fam/kg/30002.html" target="_blank">全国文物修复人员仅400人左右</a> </dd>
<dd>·<a href="/fam/kg/29772.html" target="_blank">古西域女子爱红妆 首饰妆品很时髦</a> </dd>
<dd>·<a href="/fam/kg/29614.html" target="_blank">海昏侯墓出土金器纯度达99% 金饼金板属于酎</a> </dd>
<dd>·<a href="/fam/kg/29407.html" target="_blank">海昏侯墓考古记：站在最前沿 汉代火锅出炉</a> </dd>

</dl>
<dl>
<dd>·<a href="/faxian/sw/31435.html" target="_blank">相机拍摄贵州从江加勉乡雨后春笋采挖成美食</a> </dd>
<dd>·<a href="/faxian/xs/31432.html" target="_blank">贵州雷山苗族举办千人“讨花带”公开求爱活</a> </dd>
<dd>·<a href="/faxian/yiji/31431.html" target="_blank">贵州黎平革命教育基地已接待游客600万人次</a> </dd>
<dd>·<a href="/faxian/wh/31402.html" target="_blank">[地理风物][黔东南]新寨：藤条做的“寨门”</a> </dd>

</dl>
<dl>
<dd>·<a href="/xing/lushu/20101119/1827.html" target="_blank">教你如何打造家居客厅好风水</a> </dd>
<dd>·<a href="/xing/lushu/20101119/1828.html" target="_blank">客厅布局 家居风水第一步</a> </dd>
<dd>·<a href="/xing/lushu/20101119/1829.html" target="_blank">教您巧妙布置甜美爱情风水</a> </dd>
<dd>·<a href="/xing/lushu/20101119/1830.html" target="_blank">高考家居风水解密 文昌加贵的家居布置</a> </dd>

</dl>
</div></div></div></div>
<div id="Show_bottom">
<ol>
  <li>
  <div class="Show_b_list">
  <h2><a href="/news/yc/" target="_blank">原创</a><span></span></h2>
<p><a href="/news/yc/23333.html" target="_blank"><img height="79" alt="[关注世界遗产]冬日云南哈尼梯田美如画(图)" src="/uploads/allimg/160113/2245215331-0-lp.jpg" width="173" border="0"></a></p>

  <ul>
<li>· <a href="/news/yc/31881.html" target="_blank">重庆巫山牡丹花清明节盛放引游客</a> </li>
<li>· <a href="/news/yc/31658.html" target="_blank">安利钙镁片的作用与功能：辅以维</a> </li>
<li>· <a href="/news/yc/31416.html" target="_blank">湖北楚罐楚蒸餐饮店长培训内容简</a> </li>
</ul><br clear="all"></div></li>
  <li>
  <div class="Show_b_list">
  <h2><a href="/pic" target="_blank">图片</a><span></span></h2>
<p><a href="/pic/jishi/30548.html" target="_blank"><img height="79" alt="贵州雷山：苗族同胞迎来13年一次“招龙节”（图）" src="/uploads/160319/13-160319145A95P.jpg" width="173" border="0"></a></p>

  <ul>
<li>· <a href="/pic/dili/31605.html" target="_blank">走近春日黔东南从江侗族古寨增冲</a> </li>
<li>· <a href="/pic/lvyou/30687.html" target="_blank">贵州岑巩桃花节，上万名游客赏花</a> </li>
<li>· <a href="/pic/jishi/30548.html" target="_blank">贵州雷山：苗族同胞迎来13年一次</a> </li>

</ul><br clear="all"></div></li>
  <li class="clear_R">
  <div class="Show_b_list">
  <h2><a href="/video" target="_blank">视频</a><span></span></h2>
<p><a href="/video/faxian/2304.html" target="_blank"><img height="79" alt="韩国超性感美女歌手Ora新单-Naughty" face="" src="/uploads/allimg/100618/1-10061Q525030-L.jpg" width="173" border="0"></a></p>

  <ul>
<li>· <a href="/video/faxian/2308.html" target="_blank">张靓颖ft张学友ft K'naan-MV(MTV</a> </li>
<li>· <a href="/video/faxian/2309.html" target="_blank">土耳其性感美媚歌手Sila 新单曲-</a> </li>
<li>· <a href="/video/faxian/2310.html" target="_blank">漂亮美媚抽疯的甩葱歌</a> </li>

</ul><br clear="all"></div></li></ol></div>



</div><!--列表页右边 开始 -->
<div id="zdlist_R">
<div class="zd_top">
<div class="zd_top_title">
<ul>
<a href="/fam/qy/22134.html" target="_blank">省假日办检查云南国庆节前旅游筹备工作</a>
</ul></div>
<div class="zd_top_L">
<ul>
<li><a href="/fam/kg/23816.html" target="_blank"><img height="88" alt="新疆沙湾县第一次" src="/uploads/allimg/c160114/1452K1120bI0-14428_lit.jpg" width="113" border="0"></a><br><a href="/fam/kg/23816.html" target="_blank"><font color="#ff0000">新疆沙湾县第一次</font></a> </li>
</ul></div>
<div class="zd_top_R">
<ul>
<li><a href="/fam/kg/30002.html" target="_blank">全国文物修复人员仅400人左右</a> </li>
<li><a href="/fam/kg/29772.html" target="_blank">古西域女子爱红妆 首饰妆品很时髦</a> </li>
<li><a href="/fam/kg/29614.html" target="_blank">海昏侯墓出土金器纯度达99% 金饼金板属于酎</a> </li>
<li><a href="/fam/kg/29407.html" target="_blank">海昏侯墓考古记：站在最前沿 汉代火锅出炉</a> </li>
<li><a href="/fam/kg/29406.html" target="_blank">故宫文物修复师：工作时聊个天都不行</a> </li>

</ul></div></div>
<div class="zd_R">
<div class="small_listt">
<h4>热门文章HOT</h4></div>
<ul>
<li><span>热</span><a href="/news/dt/880.html" target="_blank">15岁女孩因被班主任劝退反省 自家窗前留遗</a> </li>
<li><span>热</span><a href="/news/dt/882.html" target="_blank">城管也有情：夫妻卖油条14年连供3个大学生 </a> </li>
<li><span>热</span><a href="/news/dt/879.html" target="_blank">农民工自制土炮轰退强制拆迁队 声称自己并</a> </li>
<li><span>热</span><a href="/news/dt/881.html" target="_blank">4000平米村委会办公楼 只有10人孤零零办公</a> </li>
<li><span>热</span><a href="/news/dt/884.html" target="_blank">菲律宾应试现新种巨型蜥 长达2米体重十公斤</a> </li>
<li><span>热</span><a href="/news/hw/701.html" target="_blank">首都军区工兵团救出32岁藏族女青年</a> </li>

</ul></div>
<div class="zd_tuijian">
<div class="zd_tuijian_title">
<ul>
<a href="/news/dt/20996.html" target="_blank">河南安阳大学生暑期到广西融水苗乡支教（图</a>
</ul></div>
<div class="zd_tuijian_L">
<ul>
<li><a href="/faxian/sw/19145.html" target="_blank"><img height="80" alt="肯尼亚桑布鲁国" src="/uploads/allimg/130504/13-1305041302580-L.jpg" width="100" border="0"></a><br><a href="/faxian/sw/19145.html" target="_blank"><font color="#ff0000">肯尼亚桑布鲁国</font></a> </li>
<li><a href="/faxian/hl/7659.html" target="_blank"><img height="80" alt="西藏2处风景区" src="/uploads/allimg/130129/0023513J5_lit.jpg" width="100" border="0"></a><br><a href="/faxian/hl/7659.html" target="_blank"><font color="#ff0000">西藏2处风景区</font></a> </li>

</ul></div>
<div class="zd_tuijian_R">
<ul>
<li><a href="/faxian/sw/31435.html" target="_blank">相机拍摄贵州从江加勉乡雨后春</a> </li>
<li><a href="/faxian/xs/31432.html" target="_blank">贵州雷山苗族举办千人“讨花带</a> </li>
<li><a href="/faxian/yiji/31431.html" target="_blank">贵州黎平革命教育基地已接待游</a> </li>
<li><a href="/faxian/wh/31402.html" target="_blank">[地理风物][黔东南]新寨：藤条</a> </li>
<li><a href="/faxian/wh/31403.html" target="_blank">[地理风物][黔东南]贵州施秉:</a> </li>
<li><a href="/faxian/juzhu/27689.html" target="_blank">杨丽萍大理豪宅曝光依山傍水 </a> </li>
<li><a href="/faxian/qx/22129.html" target="_blank">端午旅游人气排行榜 日本超韩</a> </li>
<li><a href="/faxian/qx/22114.html" target="_blank">第十五届中缅胞波狂欢节将于10</a> </li>
<li><a href="/faxian/qx/22113.html" target="_blank">泰领馆：落地签需提供往返机票</a> </li>

</ul></div></div>
<div class="zd_R">
<div class="small_listt">
<h4>最新文章NEW</h4></div>
<ul>
<li><span>新</span><a href="/news/dt/32290.html" target="_blank">吴文学：把握大众旅游时代特征 全力发</a> </li>
<li><span>新</span><a href="/news/shiye/32281.html" target="_blank">第七届四川国际自驾游交易博览会十月相</a> </li>
<li><span>新</span><a href="/news/shiye/32280.html" target="_blank">王宁常务副省长在印度推介四川旅游</a> </li>
<li><span>新</span><a href="/news/shiye/32279.html" target="_blank">建政务云用大数据 提升现代社会治理能</a> </li>
<li><span>新</span><a href="/news/jiaodian/32278.html" target="_blank">冈仁波齐 | 一座藏地神山</a> </li>
<li><span>新</span><a href="/news/jiaodian/32277.html" target="_blank">【童言无忌走湘西】雪花曼舞凤凰城</a> </li>

</ul></div>
<div class="zd_R">
<div class="small_listt">
<h4>最新评论</h4></div>
<ul>
<li><span>评</span><a href="/news/dt/32290.html" target="_blank">吴文学：把握大众旅游时代特征 全力发</a> </li>
<li><span>评</span><a href="/news/shiye/32281.html" target="_blank">第七届四川国际自驾游交易博览会十月相</a> </li>
<li><span>评</span><a href="/news/shiye/32280.html" target="_blank">王宁常务副省长在印度推介四川旅游</a> </li>
<li><span>评</span><a href="/news/shiye/32279.html" target="_blank">建政务云用大数据 提升现代社会治理能</a> </li>
<li><span>评</span><a href="/news/jiaodian/32278.html" target="_blank">冈仁波齐 | 一座藏地神山</a> </li>
<li><span>评</span><a href="/news/jiaodian/32277.html" target="_blank">【童言无忌走湘西】雪花曼舞凤凰城</a> </li>

</ul></div>
<div class="zd_tuijian">
<div class="zd_tuijian_title">
<ul>
<a href="/xing/gonglue/20130106/3096.html" target="_blank">北京驴友遇难震动无锡驴友圈 读攻略玩户外</a>
</ul></div>
<div class="zd_tuijian_L">
<ul>
<li><a href="/xing/gonglue/20160407/32135.html" target="_blank"><img height="80" alt="漫步勐腊热带雨" src="/uploads/allimg/c160407/146000aH64T0-41T1.jpg" width="100" border="0"></a><br><a href="/xing/gonglue/20160407/32135.html" target="_blank"><font color="#ff0000">漫步勐腊热带雨</font></a> </li>
<li><a href="/xing/gonglue/20160402/31752.html" target="_blank"><img height="80" alt="怒江雾里村 中" src="/uploads/allimg/c160402/14595W2522P30-434I.jpg" width="100" border="0"></a><br><a href="/xing/gonglue/20160402/31752.html" target="_blank"><font color="#ff0000">怒江雾里村 中</font></a> </li>

</ul></div>
<div class="zd_tuijian_R">
<ul>
<li><a href="/xing/renwu/20160408/32222.html" target="_blank">尚启元:《跟着电影去旅行》系</a> </li>
<li><a href="/xing/renwu/20160407/32206.html" target="_blank">唱响苗侗大地 记乐为宣传美丽</a> </li>
<li><a href="/xing/gonglue/20160407/32136.html" target="_blank">西双版纳曼掌村 传统文化演绎</a> </li>
<li><a href="/xing/gonglue/20160407/32135.html" target="_blank">漫步勐腊热带雨林 在童话世界</a> </li>
<li><a href="/xing/gonglue/20160407/32134.html" target="_blank">西双版纳告庄旅游攻略</a> </li>
<li><a href="/xing/gonglue/20160407/32133.html" target="_blank">大理春季旅游线路推荐 像梦一</a> </li>
<li><a href="/xing/gonglue/20160407/32132.html" target="_blank">云南德宏泼水节攻略 盘点瑞丽</a> </li>
<li><a href="/xing/tuijian/20160406/32002.html" target="_blank">亚美尼亚：神话与奇迹的国家</a> </li>
<li><a href="/xing/tuijian/20160406/32001.html" target="_blank">那仰望的人 化身为夜空中最亮</a> </li>

</ul></div></div>
<div class="zd_R">
<div class="small_listt">
<h4>新闻排行</h4></div>
<ul>
<li><span>热</span><a href="/news/dt/880.html" target="_blank">15岁女孩因被班主任劝退反省 自家窗前</a> </li>
<li><span>热</span><a href="/news/dt/882.html" target="_blank">城管也有情：夫妻卖油条14年连供3个大</a> </li>
<li><span>热</span><a href="/news/dt/879.html" target="_blank">农民工自制土炮轰退强制拆迁队 声称自</a> </li>
<li><span>热</span><a href="/news/dt/881.html" target="_blank">4000平米村委会办公楼 只有10人孤零零</a> </li>
<li><span>热</span><a href="/news/dt/884.html" target="_blank">菲律宾应试现新种巨型蜥 长达2米体重十</a> </li>
<li><span>热</span><a href="/news/hw/701.html" target="_blank">首都军区工兵团救出32岁藏族女青年</a> </li>

</ul></div>
<div class="zd_R">
<div class="small_listt">
<h4>图片排行</h4></div>
<ul>
<li><span>热</span><a href="/pic/jishi/19712.html" target="_blank">贵州松桃:实拍三阳佳肴“神仙豆腐”制</a> </li>
<li><span>热</span><a href="/pic/jishi/1971.html" target="_blank">抓拍大牌明星们＂掉链子＂出糗时的瞬间</a> </li>
<li><span>热</span><a href="/pic/jishi/10954.html" target="_blank">云南德宏：古老神秘的德昂族婚俗[高清]</a> </li>
<li><span>热</span><a href="/pic/jishi/9532.html" target="_blank">巴布新几内亚土著部落仍然保持树叶遮体</a> </li>
<li><span>热</span><a href="/pic/ys/9850.html" target="_blank"><font color="#330099">高清图集：第56届世界新闻摄影比赛（荷</font></a> </li>
<li><span>热</span><a href="/pic/jishi/18804.html" target="_blank">云南玉溪一周视觉回眸（4月15日—4月19</a> </li>

</ul></div>
<div class="zd_R">
<div class="small_listt">
<h4>视频排行</h4></div>
<ul>
<li><span>热</span><a href="/video/xing/2193.html" target="_blank">世界杯今日之最：巴西技高一筹 朝鲜意</a> </li>
<li><span>热</span><a href="/video/faxian/2310.html" target="_blank">漂亮美媚抽疯的甩葱歌</a> </li>
<li><span>热</span><a href="/video/xing/2440.html" target="_blank">世界杯回顾： 丹麦2:1喀麦隆全场回顾</a> </li>
<li><span>热</span><a href="/video/xing/2441.html" target="_blank">世界杯视频：澳大利亚1:1险平加纳 科威</a> </li>
<li><span>热</span><a href="/video/xing/2442.html" target="_blank">法国队球员阿内尔卡辱骂多梅内克被法国</a> </li>
<li><span>热</span><a href="/video/xing/2443.html" target="_blank">闪电罗梅达尔世界杯里超越猎豹 全场赛</a> </li>

</ul></div>
</div><br clear="all"></div>
<div id="footer">
<h3><a href="/news/">新闻</a> | <a href="/faxing">发现</a> | <a href="/fam">秘镜</a> | <a href="/pic">图片</a> | <a href="http://www.cntgol.com/bbs">论坛</a> | <a href="http://www.cntgol.com/home">家园</a> | <a href="/plus/flink_add.php">申请链接</a>
| <a href="http://www.csunews.com/member/article_add.php">在线投稿</a></h3>
  云贵旅游地理网-中南偏西 精彩云贵版权所有 网站内容来源为原创以及互联网 转载请声明出处
<br>
如果发现本站触犯了您的版权和利益，请联系邮�䣺csunews@163.com(投稿)，我们将在三个工作日内作删除等处理．
  <br>
  Copyright @2008-2013  Corporation, All Rights Reserved 浙ICP备13001813-3  <script type="text/javascript">
var _bdhmProtocol = (("https:" == document.location.protocol) ? " https://" : " http://");
document.write(unescape("%3Cscript src='" + _bdhmProtocol + "hm.baidu.com/h.js%3F8588335ff630561d73199fb4cc386ea5' type='text/javascript'%3E%3C/script%3E"));
</script><script src=" http://hm.baidu.com/h.js?8588335ff630561d73199fb4cc386ea5" type="text/javascript"></script><a href="http://tongji.baidu.com/hm-web/welcome/ico?s=8588335ff630561d73199fb4cc386ea5" target="_blank"><img border="0" src="http://eiv.baidu.com/hmt/icon/21.gif" width="20" height="20"></a>

</div>


<audio controls="controls" style="display: none;"></audio></body></html>'''


def getHtml5():
    return '''<html><head><script type="text/javascript" async="" src="https://d31qbv1cthcecs.cloudfront.net/atrk.js"></script><script async="" src="//www.google-analytics.com/analytics.js"></script><script type="text/javascript" charset="utf-8" src="http://assets.changyan.sohu.com/upload/changyan.js?conf=prod_97075b09bc8da2c6efe5649a72a8c43f&amp;appid=cyr45LmB4"></script>  <script type="text/javascript" async="" src="http://motions.gmw.cn/show/19695837"></script><script id="allmobilize" charset="utf-8" src="http://a.yunshipei.com/220ab67da786fc1e7db0820652045017/allmobilize.min.js"></script><style type="text/css"></style><meta http-equiv="Cache-Control" content="no-siteapp"><link rel="alternate" media="handheld" href="#">

<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<meta name="keywords" content="候鸟">
<meta name="description" content="　　眼下，我国北方地区天气回暖，又进入到候鸟迁徙的季节，在年复一年的南来北往中，它们既要承受来自自然界的生存考验，又要面临人类活动带来的侵扰——湿地退化，人鸟争粮，以观赏之名的打搅，甚至是无情捕杀…… <BR>　　野生鸟类尤其是候鸟对栖息环境质量的要求极高，因此成为国际公认的最能直观反映地区生态文明发展程度的标志。为了给候鸟营造一个安全的栖息环境，最大限度地排除人类活动的干扰，各地采取了很多强有力的保护措施。">
<meta name="filetype" content="0">
<meta name="publishedtype" content="1">
<meta name="pagetype" content="1">
<meta name="webterren_speical" content="gmrbanalytics">
<meta name="catalogs" content="4108">
<meta name="contentid" content="19695837">
<meta name="publishdate" content="2016-04-14">
<meta name="author" content="徐皓">
<title>生态补偿探索候鸟保护新机制 让候鸟平安返乡(1)_光明日报
_光明网</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="stylesheet" type="text/css" href="http://img.gmw.cn/css/content_global.css">
<link rel="stylesheet" type="text/css" href="http://img.gmw.cn/css/public_gmw.css">
<script src="http://static.bshare.cn/b/components/bsStatic.js?v=20160206" type="text/javascript" charset="utf-8"></script><style></style><script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/r.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.sohu.com/upload/version-v3.js?14622636646190.2929450429120251"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.sohu.com/debug/cookie?callback=changyan86114571"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/v3/v20160429150/src/adapter.min.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.sohu.com/api/2/config/get/cyr45LmB4?callback=changyan303197533"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/v3/v20160429150/src/start.min.js"></script><style type="text/css">#SOHUCS{clear:both}#SOHUCS #SOHU_MAIN *{box-sizing:content-box;-moz-box-sizing:content-box;-webkit-box-sizing:content-box}#SOHUCS,#SOHUCS #SOHU_MAIN{margin:0;margin-left:auto;margin-right:auto;padding:0;border:0;font-weight:400;text-align:left;width:100%;height:auto;overflow:visible;font-size:12px;color:#333;background-color:transparent;line-height:1}#SOHUCS #SOHU_MAIN a,#SOHUCS #SOHU_MAIN abbr,#SOHUCS #SOHU_MAIN acronym,#SOHUCS #SOHU_MAIN address,#SOHUCS #SOHU_MAIN applet,#SOHUCS #SOHU_MAIN article,#SOHUCS #SOHU_MAIN aside,#SOHUCS #SOHU_MAIN audio,#SOHUCS #SOHU_MAIN b,#SOHUCS #SOHU_MAIN big,#SOHUCS #SOHU_MAIN blockquote,#SOHUCS #SOHU_MAIN canvas,#SOHUCS #SOHU_MAIN caption,#SOHUCS #SOHU_MAIN center,#SOHUCS #SOHU_MAIN cite,#SOHUCS #SOHU_MAIN code,#SOHUCS #SOHU_MAIN dd,#SOHUCS #SOHU_MAIN del,#SOHUCS #SOHU_MAIN details,#SOHUCS #SOHU_MAIN dfn,#SOHUCS #SOHU_MAIN dialog,#SOHUCS #SOHU_MAIN div,#SOHUCS #SOHU_MAIN dl,#SOHUCS #SOHU_MAIN dt,#SOHUCS #SOHU_MAIN em,#SOHUCS #SOHU_MAIN embed,#SOHUCS #SOHU_MAIN fieldset,#SOHUCS #SOHU_MAIN figcaption,#SOHUCS #SOHU_MAIN figure,#SOHUCS #SOHU_MAIN font,#SOHUCS #SOHU_MAIN footer,#SOHUCS #SOHU_MAIN form,#SOHUCS #SOHU_MAIN h1,#SOHUCS #SOHU_MAIN h2,#SOHUCS #SOHU_MAIN h3,#SOHUCS #SOHU_MAIN h4,#SOHUCS #SOHU_MAIN h5,#SOHUCS #SOHU_MAIN h6,#SOHUCS #SOHU_MAIN header,#SOHUCS #SOHU_MAIN hgroup,#SOHUCS #SOHU_MAIN hr,#SOHUCS #SOHU_MAIN i,#SOHUCS #SOHU_MAIN iframe,#SOHUCS #SOHU_MAIN img,#SOHUCS #SOHU_MAIN ins,#SOHUCS #SOHU_MAIN kbd,#SOHUCS #SOHU_MAIN label,#SOHUCS #SOHU_MAIN legend,#SOHUCS #SOHU_MAIN li,#SOHUCS #SOHU_MAIN mark,#SOHUCS #SOHU_MAIN menu,#SOHUCS #SOHU_MAIN meter,#SOHUCS #SOHU_MAIN nav,#SOHUCS #SOHU_MAIN object,#SOHUCS #SOHU_MAIN ol,#SOHUCS #SOHU_MAIN output,#SOHUCS #SOHU_MAIN p,#SOHUCS #SOHU_MAIN pre,#SOHUCS #SOHU_MAIN progress,#SOHUCS #SOHU_MAIN q,#SOHUCS #SOHU_MAIN rp,#SOHUCS #SOHU_MAIN rt,#SOHUCS #SOHU_MAIN ruby,#SOHUCS #SOHU_MAIN s,#SOHUCS #SOHU_MAIN samp,#SOHUCS #SOHU_MAIN section,#SOHUCS #SOHU_MAIN small,#SOHUCS #SOHU_MAIN span,#SOHUCS #SOHU_MAIN strike,#SOHUCS #SOHU_MAIN strong,#SOHUCS #SOHU_MAIN sub,#SOHUCS #SOHU_MAIN summary,#SOHUCS #SOHU_MAIN sup,#SOHUCS #SOHU_MAIN table,#SOHUCS #SOHU_MAIN tbody,#SOHUCS #SOHU_MAIN td,#SOHUCS #SOHU_MAIN tfoot,#SOHUCS #SOHU_MAIN th,#SOHUCS #SOHU_MAIN thead,#SOHUCS #SOHU_MAIN time,#SOHUCS #SOHU_MAIN tr,#SOHUCS #SOHU_MAIN tt,#SOHUCS #SOHU_MAIN u,#SOHUCS #SOHU_MAIN ul,#SOHUCS #SOHU_MAIN var,#SOHUCS #SOHU_MAIN video,#SOHUCS #SOHU_MAIN xmp{border:0;margin:0;padding:0;font-size:100%;text-align:left;vertical-align:baseline;background-image:none;background-position:0 0;width:auto;float:none;overflow:visible;text-indent:0}#SOHUCS #SOHU_MAIN article,#SOHUCS #SOHU_MAIN aside,#SOHUCS #SOHU_MAIN details,#SOHUCS #SOHU_MAIN figcaption,#SOHUCS #SOHU_MAIN figure,#SOHUCS #SOHU_MAIN footer,#SOHUCS #SOHU_MAIN header,#SOHUCS #SOHU_MAIN hgroup,#SOHUCS #SOHU_MAIN menu,#SOHUCS #SOHU_MAIN nav,#SOHUCS #SOHU_MAIN section{display:block}#SOHUCS #SOHU_MAIN b,#SOHUCS #SOHU_MAIN h1,#SOHUCS #SOHU_MAIN h2,#SOHUCS #SOHU_MAIN h3,#SOHUCS #SOHU_MAIN h4,#SOHUCS #SOHU_MAIN h5,#SOHUCS #SOHU_MAIN h6,#SOHUCS #SOHU_MAIN strong{font-weight:400}#SOHUCS #SOHU_MAIN img{color:transparent;font-size:0;vertical-align:middle;-ms-interpolation-mode:bicubic}#SOHUCS #SOHU_MAIN li,#SOHUCS #SOHU_MAIN ol,#SOHUCS #SOHU_MAIN ul{list-style:none}#SOHUCS #SOHU_MAIN li{display:list-item}#SOHUCS #SOHU_MAIN table{border-collapse:collapse;border-spacing:0}#SOHUCS #SOHU_MAIN caption,#SOHUCS #SOHU_MAIN td,#SOHUCS #SOHU_MAIN th{font-weight:400;vertical-align:top;text-align:left}#SOHUCS #SOHU_MAIN q{quotes:none}#SOHUCS #SOHU_MAIN q:after,#SOHUCS #SOHU_MAIN q:before{content:'';content:none}#SOHUCS #SOHU_MAIN small,#SOHUCS #SOHU_MAIN sub,#SOHUCS #SOHU_MAIN sup{font-size:75%}#SOHUCS #SOHU_MAIN sub,#SOHUCS #SOHU_MAIN sup{line-height:0;position:relative;vertical-align:baseline}#SOHUCS #SOHU_MAIN sub{bottom:-.25em}#SOHUCS #SOHU_MAIN sup{top:-.5em}#SOHUCS #SOHU_MAIN svg{overflow:hidden}#SOHUCS #SOHU_MAIN del,#SOHUCS #SOHU_MAIN ins,#SOHUCS #SOHU_MAIN s,#SOHUCS #SOHU_MAIN u{text-decoration:none}#SOHUCS #SOHU_MAIN p{word-wrap:break-word;break-word:break-all}#SOHUCS #SOHU_MAIN em,#SOHUCS #SOHU_MAIN i{font-style:normal}#SOHUCS #SOHU_MAIN a,#SOHUCS #SOHU_MAIN b,#SOHUCS #SOHU_MAIN em,#SOHUCS #SOHU_MAIN i,#SOHUCS #SOHU_MAIN img,#SOHUCS #SOHU_MAIN input,#SOHUCS #SOHU_MAIN label,#SOHUCS #SOHU_MAIN s,#SOHUCS #SOHU_MAIN span,#SOHUCS #SOHU_MAIN strong,#SOHUCS #SOHU_MAIN sub,#SOHUCS #SOHU_MAIN sup,#SOHUCS #SOHU_MAIN textarea,#SOHUCS #SOHU_MAIN u{display:inline}#SOHUCS #SOHU_MAIN input,#SOHUCS #SOHU_MAIN select,#SOHUCS #SOHU_MAIN select option,#SOHUCS #SOHU_MAIN textarea{margin:0;padding:0;border:0;outline:0}#SOHUCS #SOHU_MAIN a:focus,#SOHUCS #SOHU_MAIN input:focus,#SOHUCS #SOHU_MAIN textarea:focus{outline:0}#SOHUCS #SOHU_MAIN button,#SOHUCS #SOHU_MAIN input,#SOHUCS #SOHU_MAIN select,#SOHUCS #SOHU_MAIN textarea{background-attachment:scroll}#SOHUCS #SOHU_MAIN li{clear:none}#SOHUCS #SOHU_MAIN a{color:#44708e;text-decoration:none}#SOHUCS #SOHU_MAIN a:hover{color:#ee542a;text-decoration:underline}#SOHUCS #SOHU_MAIN .clear-g{zoom:1}#SOHUCS #SOHU_MAIN .clear-g:after{content:".";display:block;visibility:hidden;height:0;clear:both}#SOHUCS #SOHU_MAIN .global-clear-spacing{letter-spacing:-6px}#SOHUCS #SOHU_MAIN .global-clear-spacing *{letter-spacing:normal}</style><style type="text/css">.module-cy-user-page *{box-sizing:content-box;-moz-box-sizing:content-box;-webkit-box-sizing:content-box}.module-cy-user-page{margin:0;margin-left:auto;margin-right:auto;padding:0;border:0;font-weight:400;text-align:left;width:100%;height:auto;overflow:visible;font-size:12px;color:#333;background-color:transparent;line-height:1}.module-cy-user-page a,.module-cy-user-page abbr,.module-cy-user-page acronym,.module-cy-user-page address,.module-cy-user-page applet,.module-cy-user-page article,.module-cy-user-page aside,.module-cy-user-page audio,.module-cy-user-page b,.module-cy-user-page big,.module-cy-user-page blockquote,.module-cy-user-page canvas,.module-cy-user-page caption,.module-cy-user-page center,.module-cy-user-page cite,.module-cy-user-page code,.module-cy-user-page dd,.module-cy-user-page del,.module-cy-user-page details,.module-cy-user-page dfn,.module-cy-user-page dialog,.module-cy-user-page div,.module-cy-user-page dl,.module-cy-user-page dt,.module-cy-user-page em,.module-cy-user-page embed,.module-cy-user-page fieldset,.module-cy-user-page figcaption,.module-cy-user-page figure,.module-cy-user-page font,.module-cy-user-page footer,.module-cy-user-page form,.module-cy-user-page h1,.module-cy-user-page h2,.module-cy-user-page h3,.module-cy-user-page h4,.module-cy-user-page h5,.module-cy-user-page h6,.module-cy-user-page header,.module-cy-user-page hgroup,.module-cy-user-page hr,.module-cy-user-page i,.module-cy-user-page iframe,.module-cy-user-page img,.module-cy-user-page ins,.module-cy-user-page kbd,.module-cy-user-page label,.module-cy-user-page legend,.module-cy-user-page li,.module-cy-user-page mark,.module-cy-user-page menu,.module-cy-user-page meter,.module-cy-user-page nav,.module-cy-user-page object,.module-cy-user-page ol,.module-cy-user-page output,.module-cy-user-page p,.module-cy-user-page pre,.module-cy-user-page progress,.module-cy-user-page q,.module-cy-user-page rp,.module-cy-user-page rt,.module-cy-user-page ruby,.module-cy-user-page s,.module-cy-user-page samp,.module-cy-user-page section,.module-cy-user-page small,.module-cy-user-page span,.module-cy-user-page strike,.module-cy-user-page strong,.module-cy-user-page sub,.module-cy-user-page summary,.module-cy-user-page sup,.module-cy-user-page table,.module-cy-user-page tbody,.module-cy-user-page td,.module-cy-user-page tfoot,.module-cy-user-page th,.module-cy-user-page thead,.module-cy-user-page time,.module-cy-user-page tr,.module-cy-user-page tt,.module-cy-user-page u,.module-cy-user-page ul,.module-cy-user-page var,.module-cy-user-page video,.module-cy-user-page xmp{border:0;margin:0;padding:0;font-size:100%;text-align:left;vertical-align:baseline;background-image:none;background-position:0 0;width:auto;float:none;overflow:visible;text-indent:0}.module-cy-user-page article,.module-cy-user-page aside,.module-cy-user-page details,.module-cy-user-page figcaption,.module-cy-user-page figure,.module-cy-user-page footer,.module-cy-user-page header,.module-cy-user-page hgroup,.module-cy-user-page menu,.module-cy-user-page nav,.module-cy-user-page section{display:block}.module-cy-user-page b,.module-cy-user-page h1,.module-cy-user-page h2,.module-cy-user-page h3,.module-cy-user-page h4,.module-cy-user-page h5,.module-cy-user-page h6,.module-cy-user-page strong{font-weight:400}.module-cy-user-page img{color:transparent;font-size:0;vertical-align:middle;-ms-interpolation-mode:bicubic}.module-cy-user-page li,.module-cy-user-page ol,.module-cy-user-page ul{list-style:none}.module-cy-user-page li{display:list-item}.module-cy-user-page table{border-collapse:collapse;border-spacing:0}.module-cy-user-page caption,.module-cy-user-page td,.module-cy-user-page th{font-weight:400;vertical-align:top;text-align:left}.module-cy-user-page q{quotes:none}.module-cy-user-page q:after,.module-cy-user-page q:before{content:'';content:none}.module-cy-user-page small,.module-cy-user-page sub,.module-cy-user-page sup{font-size:75%}.module-cy-user-page sub,.module-cy-user-page sup{line-height:0;position:relative;vertical-align:baseline}.module-cy-user-page sub{bottom:-.25em}.module-cy-user-page sup{top:-.5em}.module-cy-user-page svg{overflow:hidden}.module-cy-user-page del,.module-cy-user-page ins,.module-cy-user-page s,.module-cy-user-page u{text-decoration:none}.module-cy-user-page p{word-wrap:break-word;break-word:break-all}.module-cy-user-page em,.module-cy-user-page i{font-style:normal}.module-cy-user-page a,.module-cy-user-page b,.module-cy-user-page em,.module-cy-user-page i,.module-cy-user-page img,.module-cy-user-page input,.module-cy-user-page label,.module-cy-user-page s,.module-cy-user-page span,.module-cy-user-page strong,.module-cy-user-page sub,.module-cy-user-page sup,.module-cy-user-page textarea,.module-cy-user-page u{display:inline}.module-cy-user-page input,.module-cy-user-page select,.module-cy-user-page select option,.module-cy-user-page textarea{margin:0;padding:0;border:0;outline:0}.module-cy-user-page a:focus,.module-cy-user-page input:focus,.module-cy-user-page textarea:focus{outline:0}.module-cy-user-page button,.module-cy-user-page input,.module-cy-user-page select,.module-cy-user-page textarea{background-attachment:scroll}.module-cy-user-page li{clear:none}.module-cy-user-page a{color:#44708e;text-decoration:none}.module-cy-user-page a:hover{color:#ee542a;text-decoration:underline}.module-cy-user-page .clear-g{zoom:1}.module-cy-user-page .clear-g:after{content:".";display:block;visibility:hidden;height:0;clear:both}.module-cy-user-page .global-clear-spacing{letter-spacing:-6px}.module-cy-user-page .global-clear-spacing *{letter-spacing:normal}</style><style type="text/css">.changyan-overlay-lock{overflow:hidden!important;width:auto}.changyan-overlay-lock .changyan-overlay{overflow:auto;overflow-y:scroll}.changyan-overlay{position:absolute;top:0;left:0;overflow:hidden;z-index:8010;background:#000;filter:alpha(opacity=50);opacity:.5;width:auto;height:auto;display:block}.changyan-overlay-fixed{position:fixed;bottom:0;right:0}.changyan-overlay-outer{position:fixed;z-index:8030;top:0;left:0;filter:alpha(opacity=1);opacity:.01}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/icp-tips/005/icp-tips.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-skin/001/cy-skin.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-header/026/cmt-header.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-header .section-title-w{padding:15px 0 13px;height:24px}#SOHUCS #SOHU_MAIN .module-cmt-header .title-join-w{float:left}#SOHUCS #SOHU_MAIN .module-cmt-header .title-join-w .join-wrap-w{line-height:24px;height:24px;overflow:hidden;font-family:"Microsoft YaHei"}#SOHUCS #SOHU_MAIN .module-cmt-header .title-join-w .join-wrap-w a{color:#333}#SOHUCS #SOHU_MAIN .module-cmt-header .title-join-w .join-wrap-w a:hover{text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-header .join-wrap-w .wrap-name-w{font-size:17px;color:#333}#SOHUCS #SOHU_MAIN .module-cmt-header .join-wrap-w .wrap-join-w{font-size:16px;color:#333}#SOHUCS #SOHU_MAIN .module-cmt-header .join-wrap-w .join-strong-gw{font-family:Georgia;font-size:18px;color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w{float:right}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-w{float:right;padding:4px 8px;margin:0 0 0 19px;border:0;display:none}#SOHUCS #SOHU_MAIN .module-cmt-header .user-wrap-w .wrap-icon-w,#SOHUCS #SOHU_MAIN .module-cmt-header .user-wrap-w .wrap-name-w{display:inline-block;line-height:18px;height:18px;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-header .user-wrap-w .wrap-name-w{margin:0 4px 0 0;vertical-align:-5px;color:#44708E}#SOHUCS #SOHU_MAIN .module-cmt-header .user-wrap-w .wrap-icon-w{*position:relative;*top:2px;width:12px;height:7px;overflow:hidden;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/b01.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .wrap-menu-w{width:100%;display:none}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e{padding:2px 6px;cursor:pointer;position:relative;zoom:1;min-width:52px;border:2px solid #ccd4d9;border-bottom:0;z-index:10}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e .wrap-icon-w{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/b02.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e .wrap-menu-w{position:absolute;left:-2px;top:22px;display:block;background-color:#fff;border:2px solid #ccd4d9;border-top:0}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e .menu-box-w{border:1px solid #fff;border-bottom:0;border-top:0}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e .menu-box-w a{display:block;width:100%;line-height:16px;height:16px;padding:6px 0;text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-w .menu-box-w a:hover{background-color:#f2f2f2;color:#44708E}#SOHUCS #SOHU_MAIN .module-cmt-header .title-user-w .user-wrap-e .menu-box-w a .gap-w{padding:0 0 0 6px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w{padding:1px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .block-head-w{float:left;width:42px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .head-img-w,#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .head-img-w img{width:42px;height:42px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .block-post-w{padding:0 0 0 62px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-default-w{height:38px;border:2px solid #ccd4d9;border-right:0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-default-w .default-wrap-w{padding:8px 90px 8px 8px;height:22px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-default-w .default-wrap-w .wrap-text-f{width:100%;height:22px;line-height:22px;font-size:14px;border:0;padding:0;float:left;color:#b8b8b8;background:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-default-w .default-wrap-w .btn-fw{float:right;margin:-10px -90px 0 0;width:90px;height:42px;overflow:hidden;line-height:500px;border:0;padding:0;cursor:pointer;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/bg01.gif);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w{padding:5px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul{float:left;margin:0 -10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li{float:left;padding:10px 12px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-w{width:117px;height:40px;border:1px solid #ccd4d9;background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-visitor-b{border:1px dashed #ccd4d9}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-w a{width:107px;height:30px;padding:5px;display:block;text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-w a:hover{background-color:#f8f8f8}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-w .wrap-icon-w{display:inline-block;width:30px;height:30px;cursor:pointer;vertical-align:-10px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .login-wrap-w .wrap-name-w{width:72px;text-align:center;line-height:16px;display:inline-block;font-size:14px;margin:0 0 0 5px;cursor:pointer;color:#333;*position:relative;*top:2px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .login-wrap-w a:hover .wrap-name-w{color:#333}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .icon30-sohu-w{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/icon30-01.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .icon30-sina-w{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/icon30-02.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .icon30-qq-w{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/icon30-03.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .icon30-phone-w{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/icon30-04.jpg);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-other-w a{width:115px;height:38px;padding:1px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-other-w .wrap-icon-w{display:inline-block;width:70px;height:38px;cursor:pointer;vertical-align:-14px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .post-login-w ul li .login-wrap-other-w .wrap-name-w{width:44px;text-align:center;line-height:16px;display:inline-block;font-size:14px;margin:0 0 0 1px;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .prompt-empty-w{margin:10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .cbox-prompt-w a.prompt-reply-w{display:block;text-align:center;line-height:16px;padding:9px 0 8px;background-color:#ecf8ff;color:#4799d0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .cbox-prompt-w a.prompt-reply-w:hover{background-color:#d9f1ff;color:#4799d0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .prompt-close-w{float:right;width:12px;height:12px;cursor:pointer;padding:11px 12px 10px;margin:-9px 0 0 -36px}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .prompt-close-w .close-img-w{display:block;width:100%;height:100%;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/b03.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .icp-notice{width:100%;text-align:center;font-size:14px;line-height:20px;background:#fef2e2;color:#f16840;font-family:"Microsoft YaHei";margin:10px 0;padding:10px 0}#SOHUCS #SOHU_MAIN .module-cmt-header .icp-notice a{color:#44708E}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .list-comment-empty-w .empty-prompt-w{padding:10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .list-comment-empty-w .empty-prompt-w .prompt-null-w{display:block;text-align:center;line-height:16px;padding:9px 0 8px;background-color:#ecf8ff;color:#0090eb}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .list-close-comment-w .close-comment-prompt-w{padding:10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-header .section-cbox-w .list-close-comment-w .close-comment-prompt-w .close-comment-prompt{border-top:1px solid #dee4e9;background-color:#f5f5f5;color:#333;display:block;text-align:center;line-height:18px;font-size:14px;padding:12px 0 9px;zoom:1;margin:-1px 0 0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .changyan-change-password-header{border-radius:3px 3px 0 0;height:30px;line-height:18px;padding:14px 0 0;background-color:#fafafa;border-bottom:1px solid #ccd4d9}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .changyan-change-password-header .changyan-change-password-close{float:right;width:18px;height:18px;overflow:hidden;margin:0 12px 0 0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .changyan-change-password-header .changyan-change-password-closeIcon{background:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/b17.png);width:100%;height:100%;display:block}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .changyan-change-password-header .changyan-change-password-closeIcon:hover{background:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/b18.png)}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .changyan-change-password-header .changyan-change-password-title{font-size:14px;font-weight:700;display:inline-block;padding:0 0 0 20px;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw{width:400px;border:1px solid #ccd4d9;background-color:#fff}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-title-dw{height:30px;line-height:18px;padding:14px 0 0;background-color:#fafafa;border-bottom:1px solid #ccd4d9}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-title-dw .title-name-dw{font-size:14px;font-weight:700;display:inline-block;padding:0 0 0 20px;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-title-dw .title-close-dw{float:right;width:18px;height:18px;overflow:hidden;margin:0 12px 0 0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-title-dw .title-close-dw a{width:100%;height:100%;display:block;background-position:-100px -50px}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-title-dw .title-close-dw a:hover{background-position:-100px -75px}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-form-dw{padding:25px 0 0;height:33px;overflow:hidden}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-form-dw .form-name-dw{float:left;line-height:16px;padding:9px 12px 0 0;width:93px;text-align:right;font-size:14px;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-form-dw .form-action-dw .action-text-dfw{width:249px;height:31px;line-height:31px;padding:0 0 0 8px;font-size:14px;float:left;vertical-align:-4px;border:1px solid #ccd4d9;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-prompt-dw{height:16px;line-height:16px;overflow:hidden;padding:0 0 0 105px!important;margin:2px 0 4px;color:#ee542a;visibility:hidden}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-password-dw{height:33px;overflow:hidden}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-password-dw .password-name-dw{float:left;font-size:14px;line-height:16px;padding:6px 12px 0 0;text-align:right;width:93px;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-password-dw .password-action-dw .action-text-dfw{float:left;font-size:14px;height:31px;line-height:31px;padding:0 0 0 8px;width:249px;border:1px solid #ccd4d9;color:#333}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-password-dw .password-action-dw .password-btn-dw{float:left;width:117px;border:1px solid #ccd4d9;height:31px;overflow:hidden;line-height:32px;margin-left:10px;text-align:center;font-size:14px;cursor:pointer}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-password-dw .password-action-dw .password-time-dw{display:none;float:left;width:134px;height:31px;overflow:hidden;line-height:32px;margin-left:10px;padding:0 5px;border:1px solid #d1d2d4;color:#9a9a9a;background-color:#f5f6f8}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw{height:33px;overflow:hidden;padding:8px 36px 25px 106px}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw .btn-dfw{width:66px;height:33px;padding:0;cursor:pointer;border:0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw .btn-bdf{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/bg11.gif);background-repeat:no-repeat;background-position:-4px 0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw a:hover .btn-bdf{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/bg12.gif)}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw a button.btn-cancel,#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .cont-btn-dw a:hover button.btn-cancel{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-header/026/images/btn-cancel-small.jpg);background-position:0 0}#SOHUCS #SOHU_MAIN .change-password-wrapper-dw .forget-password{color:#5788aa;text-decoration:underline;float:right;margin-top:17px}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-box/017/cmt-box.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w{border-radius:3px;border:2px solid #ccd4d9;background-color:#fff;display:block;zoom:1}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .area-textarea-w{position:relative;z-index:9;zoom:1;padding:4px 0 3px 7px;overflow:hidden;background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .area-textarea-e .textarea-fw{color:#333;background-color:transparent}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .textarea-fw{width:100%;height:66px;line-height:22px;font-size:14px;resize:none;overflow-x:hidden;overflow-y:auto;background-image:none;color:#b8b8b8}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w{height:39px;background-color:#fafafa;border-top:1px solid #e6eaed}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w{position:relative;float:left;z-index:12}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li{float:left}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w,#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w,#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w{float:right}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li{width:40px;height:39px;border-right:1px solid #e6eaed;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li .effect-w{height:19px;padding:12px 10px 8px;display:block}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li .effect-w i{width:100%;height:100%;display:inline-block;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e{margin-top:-1px;margin-left:-1px;border-left:1px solid #ccd4d9;border-right:1px solid #ccd4d9;border-top:1px solid #ccd4d9}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w{padding-bottom:11px!important;cursor:default;background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face-active.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image-active.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w{width:19px;padding:11px 11px 9px 10px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w:hover .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face-active.png)}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw{top:40px;left:-2px;display:none;width:331px;position:absolute;z-index:2}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw{width:327px;padding:0;overflow:hidden;background-color:#fff;border:2px solid #ccd4d9;border-left:2px solid #ccd4d9;border-top:0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw a:hover{background-color:#f2f2f2}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul{margin:0 -1px -1px 0;border-bottom:1px dotted #ccd4d9}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul li{float:left;display:inline;width:40px;height:36px;overflow:hidden;border-right:1px dotted #ccd4d9}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul li a{display:inline-block;width:22px;height:20px;padding:8px 9px;margin:1px 0 0;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .effect-w{width:20px;padding:10px 10px 8px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .effect-w .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w:hover .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image-active.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .uploading-file-w{width:40px;height:39px;overflow:hidden;margin:-39px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-wrapper-dw{top:40px;position:absolute;left:39px;display:none}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw{padding:53px 0 50px;background-color:#fff;border:2px solid #ccd4d9;border-top:0;width:190px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-word-dw{height:22px;text-align:center;color:#999}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-word-dw .word-icon-dw{display:inline-block;width:22px;height:22px;margin:0 5px 0 0;vertical-align:-6px;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/loading.gif);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw{padding:20px 0 0;height:25px;text-align:center}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw a{display:inline-block;width:65px;line-height:16px;padding:5px 0 4px;text-align:center;font-size:12px;background-color:#699ec3;color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw a:hover{text-decoration:none;background-color:#5788aa}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw{display:none}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw{display:block;width:165px;padding:7px 7px 15px 18px;background-color:#fff;border:2px solid #ccd4d9;border-top:0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw{height:18px;width:100%}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw a{float:right;width:18px;height:18px;overflow:hidden;background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/b17.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw a:hover{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/b18.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-pic-dw{padding:10px 13px 0 2px;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-pic-dw img{display:block;margin:0 auto;min-height:60px;max-height:150px;min-width:60px;max-width:150px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w,#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w a{height:39px;text-decoration:none!important;display:inline-block;color:#44708e;*width:88px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w .btn-fw{float:right;width:90px;height:42px;overflow:hidden;line-height:500px;border:0;border-radius:0 0 3px;padding:0;margin:-1px -2px 0 0;cursor:pointer;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/issue01.gif);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w:hover .btn-fw{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/issue02.gif)}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w{padding:0 10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w ul li{float:right;display:inline;padding:11px 0 0;margin:0 10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-w{display:inline-block;width:17px;height:17px}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-name-w{line-height:16px;padding:12px 0 0;margin:0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-name-w .name-b{color:#999}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-cancel-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu-cancel.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu-click.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-b:hover{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina-click.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina-cancel.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-cancel-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq-cancel.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq-click.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq.png) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-box .cbox-prompt-w .prompt-empty-w{display:none;text-align:center;line-height:16px;padding:9px 0 8px;background-color:#fef2e1;color:#ee542a;margin:10px 0}#SOHUCS #SOHU_MAIN .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li object{display:block!important}</style><style type="text/css">.module-cy-user-page .module-cmt-box .post-wrap-w{border-radius:3px;border:2px solid #ccd4d9;background-color:#fff;display:block;zoom:1}.module-cy-user-page .module-cmt-box .post-wrap-w .area-textarea-w{position:relative;z-index:9;zoom:1;padding:4px 0 3px 7px;overflow:hidden;background-color:#fff}.module-cy-user-page .module-cmt-box .post-wrap-w .area-textarea-e .textarea-fw{color:#333;background-color:transparent}.module-cy-user-page .module-cmt-box .post-wrap-w .textarea-fw{width:100%;height:66px;font-family:"Microsoft YaHei";line-height:22px;font-size:14px;resize:none;overflow-x:hidden;overflow-y:auto;background-image:none;color:#b8b8b8}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w{height:39px;background-color:#fafafa;border-top:1px solid #e6eaed}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w{position:relative;float:left;z-index:12}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li{float:left}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w,.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w,.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w{float:right}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li{width:40px;height:39px;border-right:1px solid #e6eaed;cursor:pointer}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li .effect-w{height:19px;padding:12px 10px 8px;display:block}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li .effect-w i{width:100%;height:100%;display:inline-block;cursor:pointer}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e{margin-top:-1px;margin-left:-1px;border-left:1px solid #ccd4d9;border-right:1px solid #ccd4d9;border-top:1px solid #ccd4d9}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w{padding-bottom:11px!important;cursor:default;background-color:#fff}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face-active.png);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w ul li.function-e .effect-w .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image-active.png);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w{width:19px;padding:11px 11px 9px 10px}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face.png);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-face-w .effect-w:hover .face-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/face-active.png)}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw{top:40px;left:-2px;display:none;width:331px;position:absolute;z-index:2}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw{width:327px;padding:0;overflow:hidden;background-color:#fff;border:2px solid #ccd4d9;border-left:2px solid #ccd4d9;border-top:0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw a:hover{background-color:#f2f2f2}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul{margin:0 -1px -1px 0;border-bottom:1px dotted #ccd4d9}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul li{float:left;display:inline;width:40px;height:36px;overflow:hidden;border-right:1px dotted #ccd4d9}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .face-wrapper-dw .wrapper-cont-dw ul li a{display:inline-block;width:22px;height:20px;padding:8px 9px;margin:1px 0 0;overflow:hidden}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .effect-w{width:20px;padding:10px 10px 8px}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .effect-w .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image.png);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w:hover .uploading-b{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/image-active.png);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .function-uploading-w .uploading-file-w{width:40px;height:39px;overflow:hidden;margin:-39px 0 0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-wrapper-dw{top:40px;position:absolute;left:39px;display:none}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw{padding:53px 0 50px;background-color:#fff;border:2px solid #ccd4d9;border-top:0;width:190px}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-word-dw{height:22px;text-align:center;color:#999}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-word-dw .word-icon-dw{display:inline-block;width:22px;height:22px;margin:0 5px 0 0;vertical-align:-6px;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/loading.gif);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw{padding:20px 0 0;height:25px;text-align:center}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw a{display:inline-block;width:65px;line-height:16px;padding:5px 0 4px;text-align:center;font-size:12px;background-color:#699ec3;color:#fff}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw .loading-btn-dw a:hover{text-decoration:none;background-color:#5788aa}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-loading-dw{display:none}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw{display:block;width:165px;padding:7px 7px 15px 18px;background-color:#fff;border:2px solid #ccd4d9;border-top:0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw{height:18px;width:100%}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw a{float:right;width:18px;height:18px;overflow:hidden;background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/b17.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-close-dw a:hover{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/b18.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-pic-dw{padding:10px 13px 0 2px;overflow:hidden}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-function-w .uploading-efw .wrapper-image-dw .image-pic-dw img{display:block;margin:0 auto;max-height:150px;min-height:60px;max-width:150px;min-width:60px}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w,.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w a{height:39px;text-decoration:none!important;display:inline-block;color:#44708e}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w .btn-fw{float:right;width:90px;height:42px;overflow:hidden;line-height:500px;border:0;border-radius:0 0 3px;padding:0;margin:-1px -2px 0 0;cursor:pointer;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/issue01.gif);background-repeat:no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-btn-w:hover .btn-fw{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/issue02.gif)}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w{padding:0 10px 0 0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w ul li{float:right;display:inline;padding:11px 0 0;margin:0 10px 0 0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-w{display:inline-block;width:17px;height:17px}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-name-w{line-height:16px;padding:12px 0 0;margin:0}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-name-w .name-b{color:#999}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-cancel-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu-cancel.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu-click.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sohu-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sohu.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-b:hover{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina-click.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-sina-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/sina-cancel.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-cancel-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq-cancel.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-click-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq-click.png) no-repeat}.module-cy-user-page .module-cmt-box .post-wrap-w .wrap-action-w .action-issue-w .issue-icon-w .icon-qq-b{background:url(//changyan.sohu.com/mdevp/extensions/cmt-box/017/images/qq.png) no-repeat}.module-cy-user-page .module-cmt-box .cbox-prompt-w .prompt-empty-w{display:none;text-align:center;line-height:16px;padding:9px 0 8px;background-color:#fef2e1;color:#ee542a;margin:10px 0}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-list/017/cmt-list.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-list .block-title-gw{padding:12px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .list-hot-w{padding:17px 0 13px}#SOHUCS #SOHU_MAIN .module-cmt-list .block-title-gw ul{border-bottom:2px solid #88abc3;background-color:transparent}#SOHUCS #SOHU_MAIN .module-cmt-list .block-title-gw ul li{float:left;line-height:16px;padding:0 0 10px}#SOHUCS #SOHU_MAIN .module-cmt-list .block-title-gw ul li .title-name-gw{font-size:16px;font-family:'Microsoft YaHei';color:#333}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw{padding:13px 0 11px;border-bottom:1px dotted #d9d9d9}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw .cont-head-gw{float:left;width:42px}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw .cont-head-gw .head-img-gw{padding:7px 0 0;width:42px;height:42px;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw .cont-head-gw .head-img-gw img{width:42px;height:42px}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw .msg-wrap-gw{padding:0 0 0 62px}#SOHUCS #SOHU_MAIN .module-cmt-list .block-cont-gw .wrap-user-gw{height:24px;line-height:16px;padding:1px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-address-gw,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-name-gw{display:inline-block;padding:5px 7px 0 0;cursor:default}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-address-gw{color:#b8b8b8}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-spread-gw,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-top-gw{float:right;padding:4px 0 0 9px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-spread-gw i,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-top-gw i{display:block;width:31px;height:18px;overflow:hidden;line-height:500px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-top-gw i{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b01.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-spread-gw i{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b02.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-time-gw{float:right;padding:5px 0 0;font-family:Arial;color:#b8b8b8}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-issue-gw{padding:12px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-issue-gw .issue-wrap-gw{line-height:22px;font-size:14px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-issue-gw .issue-wrap-gw .wrap-word-gw img{margin:1px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw{line-height:16px;margin:11px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-from-gw{float:left;line-height:16px}#SOHUCS #SOHU_MAIN .module-cmt-list .action-from-gw,#SOHUCS #SOHU_MAIN .module-cmt-list .action-from-gw a{color:#b8b8b8}#SOHUCS #SOHU_MAIN .module-cmt-list .action-from-gw a:hover{color:#EE542A;text-decoration:underline}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw{text-align:right}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw span a{color:#999;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw span a .icon-name-bg,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw span a:hover,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw span a:hover .icon-name-bg{color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .icon-gw{display:inline-block;width:13px;height:14px;overflow:hidden;vertical-align:-3px;*vertical-align:0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .icon-name-bg{padding:0 0 0 4px;font-family:Arial;*position:relative;*top:3px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .click-cai-gw a,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .click-ding-gw a{text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw a .icon-ding-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b03.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw a:hover .icon-ding-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b05.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw a .icon-cai-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b04.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw a:hover .icon-cai-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b06.png);background-position:0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a .icon-ding-bg,#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a:hover .icon-ding-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b07.png);background-position:0 0;cursor:default}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a .icon-cai-bg,#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a:hover .icon-cai-bg{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/b08.png);background-position:0 0;cursor:default}#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a:hover,#SOHUCS #SOHU_MAIN .module-cmt-list .action-click-gw .click-disable-eg a:hover em.icon-name-bg{text-decoration:none;cursor:default}#SOHUCS #SOHU_MAIN .module-cmt-list .module-cmt-box{margin:10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .module-cmt-box .textarea-fw{height:44px!important}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .gap-gw{width:1px;height:11px;display:inline-block;overflow:hidden;margin:0 9px -1px 9px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-action-gw .action-click-gw .gap-line-gw{background-color:#e5e5e5}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw{margin:9px 0 6px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .build-floor-gw{padding:4px 4px 6px;border:1px solid #dee4e9;background-color:#fbfbfb}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .build-first-floor-gw{padding:0 5px 7px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .build-msg-gw{padding:8px 10px 0}#SOHUCS #SOHU_MAIN .module-cmt-list .build-msg-gw .user-floor-gw{font-size:14px;font-family:Arial}#SOHUCS #SOHU_MAIN .module-cmt-list .build-msg-gw .wrap-action-gw{margin:8px 0 0;visibility:hidden}#SOHUCS #SOHU_MAIN .module-cmt-list .build-msg-gw .wrap-action-gw-hover{visibility:visible}#SOHUCS #SOHU_MAIN .module-cmt-list .build-middle-floor-dw .wrap-action-gw{margin:3px 0 0;visibility:hidden}#SOHUCS #SOHU_MAIN .module-cmt-list .build-middle-floor-dw .wrap-action-gw-hover{visibility:visible}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .build-middle-floor-dw{padding:8px 10px 10px;border:1px solid #dee4e9;border-top:0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .bulid-middle-hide-floor-dw{padding:5px 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .bulid-middle-hide-floor-dw a{display:block;text-align:center;line-height:16px;font-size:12px;padding:5px 0 4px;background-color:#eee;color:#666}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .block-cont-hover-e{background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-admin-gw{display:inline-block;height:21px;padding:0 0 0 24px;overflow:hidden;margin:0 5px 0 -1px;vertical-align:-6px;cursor:pointer;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/p-lvAdmin.png);background-position:left 0;background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-user-gw .user-admin-gw i{display:inline-block;height:21px;line-height:23px;padding:0 5px 0 0;font-size:12px;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/p-lvAdminbg.png);background-position:right 0;background-repeat:no-repeat;color:#fff}</style><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw{margin:13px 0 0;padding:18px 20px 30px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw{line-height:16px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li{float:left}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li .gap-gw{width:1px;height:11px;margin:0 7px;vertical-align:-1px;display:inline-block;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-area-gw .area-icon-gw{display:inline-block;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-hide-gw .area-icon-gw{width:9px;height:10px;margin:0 6px 0 0;vertical-align:-1px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-look-gw .area-icon-gw{width:7px;height:7px;margin:0 7px 0 0;vertical-align:0}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-left-gw .area-icon-gw,#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-right-gw .area-icon-gw{width:7px;height:8px;margin:0 7px 0 0;vertical-align:0}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-area-gw .area-image-gw{text-align:center;margin:9px auto 0}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-area-gw .area-image-gw img{display:block;margin:0 auto;max-width:400px;max-height:400px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .picture-box-gw{padding:0;margin:0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .picture-box-gw .box-area-gw .area-image-gw{margin:9px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .picture-box-gw .box-area-gw .area-image-gw img{margin:0;max-width:150px;max-height:150px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .picture-box-gw .box-action-gw{display:none}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .wrap-picture-hide-e .picture-box-gw{margin:10px 0 0}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .wrap-picture-hide-e .picture-box-gw .box-area-gw .area-image-gw{padding:0;text-align:left;zoom:1}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .wrap-picture-show-gw{padding:0 0 4px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .picture-box-gw{margin:13px 0 0;padding:0 0 10px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw{border:1px solid #dee4e9;background-color:#fbfbfb}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw a{color:#999}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw a:hover{color:#EE542A}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li .gap-bg{background-color:#d6d6d6}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-hide-gw .area-icon-gw{background-position:-175px 0}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-look-gw i.area-icon-gw{background-position:-175px -25px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-left-gw i.area-icon-gw{background-position:-175px -50px}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-right-gw i.area-icon-gw{background-position:-175px -75px}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .area-image-gw img{cursor:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/big.cur),auto!important}#SOHUCS #SOHU_MAIN .module-cmt-list .area-image-e img{cursor:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/small.cur),auto!important}#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-build-gw .picture-box-gw,#SOHUCS #SOHU_MAIN .module-cmt-list .wrap-picture-hide-e .picture-box-gw{border:0;background-color:transparent}#SOHUCS #SOHU_MAIN .module-cmt-list .picture-box-gw .box-action-gw ul li.action-area-gw .area-icon-gw{background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-list/017/images/p-merage-20140113.png);background-repeat:no-repeat}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/hot-topic/011/hot-topic.js"></script><script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/r.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-footer/018/cmt-footer.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-footer{padding:17px 0}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-more-comment-w{margin:20px 0 0;display:none}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-more-comment-w .more-wrap-w{margin:-1px 0 0;background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-more-comment-w .more-wrap-w a{display:block;text-align:center;line-height:18px;font-size:12px;padding:7px 0 5px;zoom:1;color:#44708e;background-color:#f5f5f5}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-more-comment-w .more-wrap-w a:hover{color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-more-comment-w .more-wrap-w a em.wrap-strong-w{font-family:Georgia;font-size:18px;color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-comment-close-w{display:none}#SOHUCS #SOHU_MAIN .module-cmt-footer .list-comment-close-w .close-wrap-w{display:block;text-align:center;line-height:18px;font-size:14px;padding:12px 0 9px;zoom:1;margin:-1px 0 0;border-top:1px solid #dee4e9;background-color:#f5f5f5;color:#333}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w{text-align:center;font-size:0}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-gw,#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w{font-size:12px;display:inline-block}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-gw a,#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w a{display:inline-block;line-height:18px;height:18px;overflow:hidden;padding:5px 10px 2px;margin:0 4px;text-decoration:none;font-size:14px;border:1px solid #e6e6e6;color:#333}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-gw a:hover,#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w a:hover{border:1px solid #5788aa}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-gw a{margin:0}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w a{font-family:Arial;padding:4px 10px 3px}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w .wrap-ellipsis-w{display:inline-block;width:25px;margin:0 4px;overflow:hidden;vertical-align:top;padding:6px 0 7px;font-size:12px;border:1px solid #e6e6e6}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w a.wrap-current-e{color:#fff;font-weight:700;background-color:#5788aa;border:1px solid #5788aa;cursor:default}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-page-w .page-wrap-w .wrap-ellipsis-w i{width:100%;height:12px;display:block;overflow:hidden;background-image:none;text-align:center;font-family:verdana;color:#333}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w .service-wrap-w{line-height:16px}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w,#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w .service-wrap-w,#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w .service-wrap-w a{display:block!important;text-align:right!important}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w .service-wrap-w a{display:inline-block!important;color:#44708e}#SOHUCS #SOHU_MAIN .module-cmt-footer .section-service-w .service-wrap-w a:hover{color:#ee542a}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/face/007/face.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-av/003/cy-av.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.sohu.com/activity/advert_static/main.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-float-bar/012/cmt-float-bar.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.sohu.com/activity/advert_static/render-pc.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-float-bar,#SOHUCS #SOHU_MAIN .module-cmt-float-bar *{margin:0;padding:0;border:0;overflow:visible}#SOHUCS #SOHU_MAIN .module-cmt-float-bar,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .close-w a,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .btn-load-bf,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .button-w{background:transparent url(//changyan.sohu.com/mdevp/extensions/cmt-float-bar/012/images/g-merage-20140213.gif) repeat-x scroll 0 0}#SOHUCS #SOHU_MAIN .module-cmt-float-bar ul li a{background:transparent url(//changyan.sohu.com/mdevp/extensions/cmt-float-bar/012/images/botbar/p-merage-20141106.png) repeat-x scroll 0 0}#SOHUCS #SOHU_MAIN .module-cmt-float-bar{z-index:1000000;position:fixed;background-position:0 -450px;bottom:0;left:0;float:none;width:100%;height:38px;line-height:normal;text-align:right;font-weight:400;font-size:100%;font-family:SimSun;_position:absolute;_top:expression(eval(document.documentElement.scrollTop+document.documentElement.clientHeight-this.offsetHeight-(parseInt(this.currentStyle.marginTop, 10)||0)-(parseInt(this.currentStyle.marginBottom, 10)||0)))}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-sohu-w{background-position:0 -160px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar03.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-sina-w{background-position:-35px -160px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar01.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-qq-w{background-position:-70px -160px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar02.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-renren-w{background-position:-105px -160px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar04.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-sohu-w:hover{background-position:0 -125px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar07.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-sina-w:hover{background-position:-35px -125px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar05.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-qq-w:hover{background-position:-70px -125px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar06.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-renren-w:hover{background-position:-105px -125px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/botbar08.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-qzone-w{background-position:0 -195px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/p_ico_03.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-qzone-w:hover{background-position:-35px -195px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/p_ico_04.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-weixin-w{background-position:-70px -195px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/p_ico_05.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .icon-weixin-w:hover{background-position:-105px -195px;filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="./images/botbar/p_ico_06.png", sizingMethod="crop")}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .clear{zoom:1;overflow:visible;width:auto;height:auto;clear:none;line-height:normal;font-size:12px;visibility:visible}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .clear:after{content:".";display:block;visibility:hidden;height:0;clear:both}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .close-w{width:40px;height:38px;overflow:hidden;position:absolute;right:0;bottom:0;z-index:1}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .close-w a{display:block;width:100%;height:100%;text-indent:-20em;background-position:0 -690px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .close-w a:hover{background-position:-50px -690px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w{width:960px;height:38px;margin:0 auto}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w{padding:0 353px 0 0;height:38px;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w{float:left;zoom:1;height:38px;line-height:38px;font-family:"Microsoft YaHei",SimSun}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w a.comment-link-w,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w span.comment-text-w{padding:8px 20px 0 0;font-size:16px;line-height:22px;color:#5788aa}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w a.comment-link-w{text-align:center;text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w a.comment-link-w:hover{color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-comment-w a.comment-link-w i{font-family:Georgia;font-size:18px;padding:0 4px;color:#ee542a}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-minwidth-w .cont-form-w{text-align:left;overflow:hidden;position:relative;zoom:1}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w{height:38px;padding:0 100px 0 10px;border-radius:3px 0 0 3px;background-position:0 -490px;border-left:2px solid #5788a9}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .btn-load-bf,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .button-w{float:right;width:100px;height:38px;margin:0 -100px 0 0;line-height:500px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .btn-load-bf{background-position:0 -650px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .button-w{background-position:0 -570px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w .button-w:hover{background-position:0 -610px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-w input.text-w{float:right;width:100%;height:34px;overflow:hidden;margin:2px 0 0;line-height:34px;font-size:14px;font-family:"Microsoft YaHei",SimSun;outline:0;background-color:transparent;color:#999}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-form-w .form-text-e{background-position:0 -530px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w{_margin:-38px 0 0!important;margin:-38px 0 0;float:right;width:353px;height:38px}@media all and (max-width:900px){#SOHUCS #SOHU_MAIN .module-cmt-float-bar .cont-login-w{display:none}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .cont-minwidth-w{padding:0 40px 0 0!important}#SOHUCS #SOHU_MAIN .module-cmt-float-bar.ipad-input-focus{bottom:308px!important}}@media all and (min-width:900px) and (max-width:1300px){#SOHUCS #SOHU_MAIN .module-cmt-float-bar.ipad-input-focus{bottom:398px!important}}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w{display:inline-block;padding:4px 10px 4px 20px;height:30px;vertical-align:middle;overflow:visible;*zoom:1;_zoom:1;*display:inline;_display:inline}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w ul.post-login-w{overflow:visible}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w ul.post-login-w li{list-style:none;cursor:pointer;padding:0 10px 0 0;width:30px;height:30px;float:left}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w ul.post-login-w li a{display:inline-block;width:100%;height:100%}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w ul.post-login-w li.first-w{line-height:22px;float:left;width:auto;height:auto}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-logout-wrap-w ul.post-login-w li.first-w span{padding:4px 0 0;display:inline-block;font-size:16px;color:#666;font-family:"Microsoft YaHei",SimSun}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-login-wrap-w{display:inline-block;vertical-align:middle;height:38px;padding-left:21px;margin-right:17px;*zoom:1;_zoom:1;*display:inline;_display:inline}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-login-wrap-w .user-info{font-size:16px;line-height:38px;font-family:'Microsoft YaHei';color:#666;position:relative}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-login-wrap-w .user-info img{width:30px;height:30px;border-radius:30px;vertical-align:-9px;margin-right:5px;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-login-wrap-w .user-info span{cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .fb-login-wrap-w .user-info .floatbar-quit{font-family:'Microsoft YaHei';color:#5788aa;text-decoration:none;margin-left:4px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .wrap-cont-w .cont-login-w .new-share{vertical-align:middle;top:1px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share{font-size:14px;font-family:'Microsoft YaHei';color:#5788aa;background:0 0;text-decoration:none;line-height:22px;cursor:pointer;position:relative;padding:4px}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share:hover{border-radius:3px;background-color:#d7d7d7}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .share-select{position:absolute;left:4px;bottom:42px;width:30px;padding:2px 10px 10px;z-index:1000001;display:none;background-color:#ededed;border:1px solid #dbdbdb}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .share-select ul{width:30px;position:relative}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .share-select ul li{float:left;width:30px;height:30px;margin:8px 0 0;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .share-select ul li a{display:block;width:100%;height:100%;text-indent:0;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .share-select .arrow{width:9px;height:6px;position:absolute;left:21px;bottom:-6px;_bottom:-12px;background:url(//changyan.sohu.com/mdevp/extensions/cmt-float-bar/012/images/botbar/g_ico_01.gif) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .ico{display:inline-block;width:18px;height:16px;margin-right:5px;*margin-right:0;*padding-right:5px;vertical-align:-2px;*vertical-align:0;background-image:url(//changyan.sohu.com/mdevp/extensions/cmt-float-bar/012/images/share-ico.png);background-repeat:no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode{position:absolute;bottom:42px;left:-144px;z-index:1000009;width:128px;height:164px;display:none;border:1px solid #c9c9c9;background-color:#f2f2f2}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap{width:90px;height:90px;padding:6px 19px 5px;position:relative;background-color:#fff}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-img{position:relative;display:inline-block;width:100%;height:100%}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-img canvas,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-img img,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-img table{position:absolute;top:0;left:0}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-close{position:absolute;top:6px;right:6px;width:10px;height:10px;overflow:hidden}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-close a,#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-wrap .qrcode-close a:hover{display:block;width:100%;height:100%;background:url(//changyan.sohu.com/mdevp/extensions/cmt-float-bar/012/images/botbar/g_ico_02.gif) no-repeat}#SOHUCS #SOHU_MAIN .module-cmt-float-bar .new-share .qrcode-text{line-height:18px;font-size:12px;padding:4px 8px 0 15px;zoom:1;color:#404040}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-page/011/cy-user-page.js"></script><style type="text/css">.module-cy-user-page{width:710px;position:fixed;z-index:2147483647;top:0;zoom:1;font-family:"Microsoft YaHei"}.module-cy-user-page:after{content:".";display:block;visibility:hidden;height:0;clear:both}.cy-mask{width:100%;background:#000;opacity:.6;filter:alpha(opacity=60);position:fixed;z-index:2147483647;top:0;left:0}.module-cy-user-page .cy-user-page-close-btn{cursor:pointer;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-page/011/image/close-btn.png);width:20px;height:20px;float:left;margin-top:15px}.module-cy-user-page .cy-user-page-tab{width:43px;background:#111;height:100%;float:right;position:relative}.module-cy-user-page .cy-tab-list{margin-top:7px;overflow:hidden}.module-cy-user-page .cy-tab-list li{width:100%;cursor:pointer;margin-top:23px}.module-cy-user-page .cy-tab-list li .cy-tab-icon{width:22px;height:22px;margin:0 auto;display:block}.module-cy-user-page .cy-tab-list li .cy-my-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-page/011/image/tab-list-icon1.png)}.module-cy-user-page .cy-tab-list li i{width:100%;display:block;margin-top:2px;font-size:12px;color:#666;text-align:center;font-style:normal}.module-cy-user-page .cy-tab-list li.active .cy-my-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-page/011/image/tab-list-icon-active1.png)}.module-cy-user-page .cy-tab-list li.active i{color:#38a3fd}.module-cy-user-page .cy-tab-list li.info-li:hover .cy-my-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-page/011/image/tab-list-icon-active1.png)}.module-cy-user-page .cy-tab-list li.info-li:hover i{color:#38a3fd}.module-cy-user-page .cy-user-page-tab .power-by-cy{width:26px;height:12px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-page/011/image/logo.png);position:absolute;bottom:12px;left:8px}.module-cy-user-page .cy-user-page-main{float:right;background:#FFF;width:630px;height:100%;position:relative}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-info/011/cy-user-info.js"></script><style type="text/css">.module-cy-user-page .module-cy-user-info .cy-user-info-header{padding:20px;height:84px}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-photo-container{position:relative;width:84px;height:84px;float:left}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-photo{width:84px;height:84px;display:block;float:left;border-radius:3px}.module-cy-user-page .module-cy-user-info .cy-user-info-header .avatar-mask{width:84px;height:84px;background:#000;opacity:.6;filter:alpha(opacity=60);position:absolute;border-radius:3px;top:0;left:0;display:none;line-height:84px;font-size:16px;text-align:center;color:#FFF;font-family:'Microsoft YaHei';cursor:pointer}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-photo-container:hover .avatar-mask{display:block}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-info{float:left;width:505px;height:84px}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-info .cy-user-info-txt{margin-left:21px;margin-top:14px}.module-cy-user-page .module-cy-user-info .cy-user-info-header .cy-user-info .cy-user-info-txt .cy-user-name{color:#111;font-size:20px;font-family:'Microsoft YaHei';font-style:normal;letter-spacing:1px}.module-cy-user-page .module-cy-user-info .cy-user-my{position:relative}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-tab-active-bar{position:absolute;background:#38a3fd;width:84px;height:2px;margin-left:63px;margin-top:-2px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label{border-bottom:1px solid #c3cad4}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label li{width:210px;float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label li .cy-my-label-item{width:84px;margin:0 auto;height:28px;font-family:'Microsoft YaHei';font-size:14px;color:#333;text-align:center;cursor:pointer;line-height:15px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label li.active .cy-my-label-item{color:#38a3fd}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label li .cy-my-label-item .cy-num{font-family:'Microsoft YaHei';font-size:14px;color:#333;font-style:normal}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-label li.active .cy-my-label-item .cy-num{color:#38a3fd}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-container{position:relative}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page{position:absolute;top:0;left:0;width:630px;overflow:hidden;overflow-y:auto;display:none}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-container .active{display:block}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list{width:575px;margin:20px 0 0 20px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i{margin-top:20px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i:first-child{margin-top:0}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-photo{width:40px;float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-photo img{width:40px;height:40px;display:block;border-radius:3px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .module-cmt-box{margin:12px 0 0}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .module-cmt-box .textarea-fw{height:44px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container{float:left;width:518px;margin-left:15px;padding-bottom:17px;border-bottom:1px solid #e9f0f5}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-user-name{font-size:14px;font-family:'Microsoft YaHei';color:#38a3fd;line-height:14px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment{font-family:'Microsoft YaHei';font-size:16px;color:#111;margin-top:15px;line-height:21px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment img{vertical-align:-2px;*vertical-align:0}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-other{background:#fdefef}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-auditing-status{font-size:14px;color:#f05858;margin-left:10px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-warning-ico{display:inline-block;width:13px;height:13px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/warning-ico.png);vertical-align:-1px;*vertical-align:3px;margin-right:4px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-source{font-family:'Microsoft YaHei';font-size:14px;color:#465e72;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin-top:14px;display:inline-block;max-width:100%}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-site-from{font-family:'Microsoft YaHei';float:left;font-size:12px;color:#999;margin-top:6px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-time{float:right;font-family:'Microsoft YaHei';margin-top:3px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-time em{display:inline-block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/time-ico.png);width:12px;height:12px;vertical-align:-2px;*vertical-align:2px;margin-top:4px;*margin-left:4px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-comment-time i{font-style:normal;font-size:12px;color:#999;font-family:'Microsoft YaHei'}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-my-comment-list .comment-list-i .cy-my-comment-container .cy-my-user-name{line-height:15px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-reply-ico{width:13px;height:9px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/reply-ico.png);display:inline-block;margin:0 4px 0 2px;*vertical-align:3px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-my-user-name em{font-style:normal;color:#333;margin-left:4px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-my-user-name em img{vertical-align:-2px;*vertical-align:0}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle{margin-top:18px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group{float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-nonsupport-ico,.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-support-ico{display:inline-block;width:13px;height:14px;margin-right:4px;vertical-align:-2px;*vertical-align:2px;cursor:pointer;float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-support-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/support-ico.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-support-ico:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/support-ico-hover.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-support-ico-disabled,.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-support-ico-disabled:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/support-ico-disabled.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-nonsupport-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/nonsupport-ico.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-nonsupport-ico:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/nonsupport-ico-hover.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-nonsupport-ico-disabled,.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group .cy-nonsupport-ico-disabled:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/nonsupport-ico-disabled.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group em{color:#f05858;font-size:12px;font-style:normal;font-family:Arial;float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-support-group i{margin:0 9px 0 7px;float:left;display:block;height:12px;width:1px;border-left:1px solid #cdcdcd}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-reply .cy-comment-handle .cy-reply-btn{color:#999;font-size:12px;margin-left:22px;font-style:normal;cursor:pointer;float:left}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list{background:#f2f2f2;padding:12px 7px;margin-top:16px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list .cy-arrow-ico{display:block;width:20px;height:10px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/arrow-ico.png);margin:-22px 0 0 33px;*position:absolute;*margin:-22px 0 0 23px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list p{margin-top:12px;*margin-top:0;font-family:'Microsoft YaHei';font-size:14px;padding:0 5px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list p em{color:#51acf9;font-size:14px;font-style:normal;margin:0 6px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list ul{margin-top:3px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list ul .cy-user-item{float:left;margin:6px 5px 0}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page-support .cy-support-list ul .cy-user-item img{width:40px;height:40px;display:block;border-radius:3px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place{display:block;text-align:center;line-height:16px;font-size:16px;font-family:'Microsoft YaHei';width:345px;margin:0 auto;padding-bottom:50px}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .pet-pic{margin-top:100px;width:345px;height:293px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/notice-empty.png);background-repeat:no-repeat}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .empty-txt{width:345px;height:22px;margin-top:70px;background-repeat:no-repeat}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .comment-empty-txt{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/title-nocomment.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .replay-empty-txt{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/title-noreply.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .support-empty-txt{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/title-nosupport.png)}.module-cy-user-page .module-cy-user-info .cy-user-my .cy-my-page .cy-my-comment-list .empty-hold-place .power-by-cy-txt{width:345px;height:16px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-info/011/image/power-by.png);background-repeat:no-repeat;margin-top:30px}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-avatar/008/cy-user-avatar.js"></script><script src="http://static.bshare.cn/js/libs/fingerprint2.min.js" type="text/javascript" charset="utf-8"></script><script src="http://static.bshare.cn/b/engines/bs-engine.js?v=20160206" type="text/javascript" charset="utf-8"></script><style type="text/css">.module-cy-user-page .module-cy-user-avatar{position:absolute;top:0;z-index:1000}.module-cy-user-page .module-cy-user-avatar .avatar-mask{height:124px}.module-cy-user-page .module-cy-user-avatar .avatar-mask .fake-avatar{width:84px;height:84px;display:none;margin:20px;float:left}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw{padding:17px 20px 0;border-top:1px solid #c3cad4;overflow:hidden;overflow-y:auto;background:#FFF;position:relative}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group-title{font-size:14px;font-family:'Microsoft YaHei'}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group{margin:0 auto;padding:0 0 27px 9px}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group li{width:72px;height:72px;border-radius:3px;float:left;margin:20px 11px 0;cursor:pointer;position:relative}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group li:hover{border:1px solid #ccc;width:70px;height:70px}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group li img{width:72px;height:72px;display:block;border-radius:3px}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group li:hover img{width:70px;height:70px}.module-cy-user-page .module-cy-user-avatar .avatar-page-wrapper-dw .avatar-group li span{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-avatar/008/image/checked.png);background-repeat:no-repeat;width:26px;height:26px;display:block;bottom:0;right:0;position:absolute}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group{border-top:1px solid #c3cad4;height:49px;background:#FFF}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group .avatar-btn{display:block;height:32px;width:84px;text-align:center;line-height:32px;font-size:16px;margin:10px 0 0 20px;cursor:pointer;float:left;font-family:'Microsoft YaHei'}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group .avatar-submit-btn{color:#51acf9;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-avatar/008/image/btn.png)}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group .avatar-cancel-btn{color:#bcc3cc;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-avatar/008/image/btn2.png)}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group .avatar-submit-btn:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-avatar/008/image/btn-hover.png);color:#FFF;text-decoration:none}.module-cy-user-page .module-cy-user-avatar .avatar-btn-group .avatar-cancel-btn:hover{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-avatar/008/image/btn-hover2.png);color:#FFF;text-decoration:none}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-view/008/cy-user-view.js"></script><style type="text/css">a.bshareDiv,#bsPanel,#bsMorePanel,#bshareF{border:none;background:none;padding:0;margin:0;font:12px Helvetica,Calibri,Tahoma,Arial,宋体,sans-serif;line-height:14px;}#bsPanel div,#bsMorePanel div,#bshareF div{display:block;}.bsRlogo .bsPopupAwd,.bsRlogoSel .bsPopupAwd,.bsLogo .bsPopupAwd,.bsLogoSel .bsPopupAwd{line-height:16px !important;}a.bshareDiv div,#bsFloatTab div{*display:inline;zoom:1;display:inline-block;}a.bshareDiv img,a.bshareDiv div,a.bshareDiv span,a.bshareDiv a,#bshareF table,#bshareF tr,#bshareF td{text-decoration:none;background:none;margin:0;padding:0;border:none;line-height:1.2}a.bshareDiv span{display:inline;float:none;}div.buzzButton{cursor:pointer;font-weight:bold;}.buzzButton .shareCount a{color:#333}.bsStyle1 .shareCount a{color:#fff}span.bshareText{white-space:nowrap;}span.bshareText:hover{text-decoration:underline;}a.bshareDiv .bsPromo,div.bshare-custom .bsPromo{display:none;position:absolute;z-index:100;}a.bshareDiv .bsPromo.bsPromo1,div.bshare-custom .bsPromo.bsPromo1{width:51px;height:18px;top:-18px;left:0;line-height:16px;font-size:12px !important;font-weight:normal !important;color:#fff;text-align:center;background:url(http://static.bshare.cn/frame/images/bshare_box_sprite2.gif) no-repeat 0 -606px;}div.bshare-custom .bsPromo.bsPromo2{background:url(http://static.bshare.cn/frame/images/bshare_promo_sprite.gif) no-repeat;cursor:pointer;}</style><style type="text/css">.bsBox{display:none;z-index:100000001;font-size:12px;background:url(http://static.bshare.cn/frame/images//background-opaque-dark.gif) !important;padding:6px !important;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}.bsClose{_overflow:hidden;cursor:pointer;position:absolute;z-index:10000000;color:#666;font-weight:bold;font-family:Helvetica,Arial;font-size:14px;line-height:20px;}.bsTop{color:#666;background:#f2f2f2;height:24px;line-height:24px;border-bottom:1px solid #e8e8e8;}.bsTop span{float:left;}.bsFrameDiv,#bsMorePanel{border:none;background:#fff;}.bsReturn{float:right;*margin-right:20px;margin-right:36px;text-align:right;cursor:pointer;line-height:24px;color:#666;opacity:0.5;}#bsReturn:hover{text-decoration:underline;opacity:1;}</style><script src="http://static.bshare.cn/b/components/bsMore.js?v=20160206" type="text/javascript" charset="utf-8"></script><style type="text/css">.module-cy-user-view .cy-user-view-header{padding:20px;height:84px}.module-cy-user-view .cy-user-view-header .cy-user-photo-container{position:relative;width:84px;height:84px;float:left}.module-cy-user-view .cy-user-view-header .cy-user-photo{width:84px;height:84px;display:block;float:left;border-radius:3px}.module-cy-user-view .cy-user-view-header .cy-user-view{float:left;width:505px;height:84px}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-user-view-txt{margin-left:21px;margin-top:12px}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-user-view-txt .cy-user-name{color:#111;font-size:20px;font-family:'Microsoft YaHei';font-style:normal;letter-spacing:1px}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info{margin-left:21px;margin-top:17px}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li{width:89px;height:22px;float:left}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li .other-info-ico{width:20px;height:22px;display:block;float:left}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li .comment-info-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-view/008/image/comments.png)}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li .reply-info-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-view/008/image/reply.png)}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li .support-info-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-view/008/image/support.png)}.module-cy-user-view .cy-user-view-header .cy-user-view .cy-other-info li .other-info-txt{float:left;font-size:14px;font-family:'Microsoft YaHei';margin-left:6px;margin-top:5px}.module-cy-user-view .cy-user-other{position:relative}.module-cy-user-view .cy-user-other .cy-tab-active-bar{position:absolute;background:#38a3fd;width:84px;height:2px;margin-left:63px;margin-top:-2px}.module-cy-user-view .cy-user-other .cy-other-label{border-bottom:1px solid #c3cad4}.module-cy-user-view .cy-user-other .cy-other-label li{width:210px;float:left}.module-cy-user-view .cy-user-other .cy-other-label li .cy-other-label-item{width:84px;margin:0 auto;height:28px;font-family:'Microsoft YaHei';font-size:14px;color:#333;text-align:center;cursor:pointer;line-height:15px}.module-cy-user-view .cy-user-other .cy-other-label li.active .cy-other-label-item{color:#38a3fd}.module-cy-user-view .cy-user-other .cy-other-label li .cy-other-label-item .cy-num{font-family:'Microsoft YaHei';font-size:14px;color:#333;font-style:normal}.module-cy-user-view .cy-user-other .cy-other-label li.active .cy-other-label-item .cy-num{color:#38a3fd}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page{width:630px;overflow:hidden;overflow-y:auto;display:none}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page-container .active{display:block}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list{width:575px;margin:20px 0 0 20px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li{margin-top:20px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li:first-child{margin-top:0}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-photo{width:40px;float:left}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-photo img{width:40px;height:40px;display:block;border-radius:3px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container{float:left;width:518px;margin-left:15px;padding-bottom:17px;border-bottom:1px solid #e9f0f5}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-user-name{font-size:14px;font-family:'Microsoft YaHei';color:#38a3fd;line-height:14px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment{font-family:'Microsoft YaHei';font-size:16px;color:#111;margin-top:15px;line-height:21px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment img{vertical-align:-2px;*vertical-align:0}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-other{background:#fdefef}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-auditing-status{font-size:14px;color:#f05858;padding:4px 0 4px 10px;background:#fdefef;display:block}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-warning-ico{display:inline-block;width:13px;height:13px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-view/008/image/warning-ico.png);vertical-align:-1px;*vertical-align:3px;margin-right:4px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-source{font-family:'Microsoft YaHei';font-size:14px;color:#465e72;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin-top:14px;display:block}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-site-from{font-family:'Microsoft YaHei';float:left;font-size:12px;color:#999;margin-top:4px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-time{float:right;font-family:'Microsoft YaHei'}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-time em{display:inline-block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-view/008/image/time-ico.png);width:12px;height:12px;vertical-align:-2px;*vertical-align:3px;margin-top:4px;*margin-left:4px}.module-cy-user-page .module-cy-user-view .cy-user-other .cy-other-page .cy-other-comment-list li .cy-other-comment-container .cy-other-comment-time i{font-style:normal;font-size:12px;color:#999;font-family:'Microsoft YaHei'}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-report/007/cy-report.js"></script><style type="text/css">div.bsClear{clear:both;height:0;line-height:0;overflow:hidden;font-size:0;}.bsSearchDiv{padding:5px 15px;background-color:#fafafa;}.bFind-wrapper-top{background:#fff;border-color:#ccc #aaa #aaa #ccc;border-style:solid;border-width:1px;height:16px;padding:4px;margin:0;}.bFind-wrapper-top input{padding:0 !important;border:none !important;box-shadow:none !important;line-height:16px !important;}.bFind-placeholder{background:url("http://static.bshare.cn/css/images/search-icon.gif") no-repeat;display:block;float:left;height:16px;width:16px;}.bFind{background:none;border:none;float:left;font-size:11px !important;height:16px !important;margin-left:3px;outline:none;padding:0;width:400px;}.bsPlatDiv{height:322px;background:#fff;overflow:auto;padding:0 15px;}#bsLogoList{display:block;list-style:none;overflow:hidden;margin:0;padding:0;}#bsLogoList li{float:left;display:inline-block;width:71px;text-align:center;font-size:12px;height:80px;margin:0 !important;}#bsLogoList .bsPlatIcon{cursor:pointer;display:block !important;text-align:center;}#bsLogoList .bsPlatImg{width:32px;height:32px;border:none !important;display:inline-block;}#bsLogoList .bsPlatImg:hover{-moz-border-radius:7px;-webkit-border-radius:7px;border-radius:7px;box-shadow:0 0 15px #a7a8ac;}#bsLogoList .bsPlatName{white-space:nowrap;text-overflow:ellipsis;overflow:hidden;text-align:center;color:#333 !important;margin-top:2px;line-height:140%;*width:70px;}#bsLogoList .bsPromoM{text-align:center;}.bsFooterDiv{height:24px;line-height:24px;padding:0 15px;border-top:1px solid #e8e8e8;background:#f2f2f2;text-align:right;}a.bsLogoLink{color:#666;}.bsLogoLink:hover{text-decoration:underline;}.bsPromoM{background:url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;}.bsNew,.bsHot,.bsRec,.bsAwd{background-position:0 -552px;width:19px;margin:5px auto 1px;line-height:16px;height:18px;font-size:12px;color:#fff;overflow:hidden;}.bsNew{background-position:0 -570px;}.bsRec{width:30px;background-position:0 -588px;}.bsAwd{background:url(http://static.bshare.cn/frame/images//promot/promote.gif) no-repeat;}</style><style type="text/css">.bshare-custom{font-size:13px;line-height:16px !important;}.bshare-custom a{text-decoration:none;display:none;zoom:1;height:16px;_height:18px;vertical-align:middle;cursor:pointer;color:#2e3192;padding-left:19px;margin-right:3px;filter:alpha(opacity=100);-moz-opacity:1;-khtml-opacity:1;opacity:1;}*+html .bshare-custom a{height:16px}.bshare-custom a:hover{text-decoration:underline;filter:alpha(opacity=75);-moz-opacity:0.75;-khtml-opacity:0.75;opacity:0.75;}.bshare-custom .bshare-more{padding-left:0;color:#000;*display:inline;display:inline-block;}.bshare-custom #bshare-shareto{text-decoration:none;font-weight:bold;margin-right:8px;*display:inline;display:inline-block;}.bshare-custom .bshare-115{background:url("http://static.bshare.cn/frame/images/logos/s4/115.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-139mail{background:url("http://static.bshare.cn/frame/images/logos/s4/139mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-9dian{background:url("http://static.bshare.cn/frame/images/logos/s4/9dian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiducang{background:url("http://static.bshare.cn/frame/images/logos/s4/baiducang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-baiduhi{background:url("http://static.bshare.cn/frame/images/logos/s4/baiduhi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bgoogle{background:url("http://static.bshare.cn/frame/images/logos/s4/bgoogle.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-bsharesync{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -18px;*display:inline;display:inline-block;}.bshare-custom .bshare-caimi{background:url("http://static.bshare.cn/frame/images/logos/s4/caimi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cfol{background:url("http://static.bshare.cn/frame/images/logos/s4/cfol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chouti{background:url("http://static.bshare.cn/frame/images/logos/s4/chouti.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-clipboard{background:url("http://static.bshare.cn/frame/images/logos/s4/clipboard.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyolbbs{background:url("http://static.bshare.cn/frame/images/logos/s4/cyolbbs.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-cyzone{background:url("http://static.bshare.cn/frame/images/logos/s4/cyzone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-delicious{background:url("http://static.bshare.cn/frame/images/logos/s4/delicious.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-dig24{background:url("http://static.bshare.cn/frame/images/logos/s4/dig24.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-digg{background:url("http://static.bshare.cn/frame/images/logos/s4/digg.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diglog{background:url("http://static.bshare.cn/frame/images/logos/s4/diglog.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diigo{background:url("http://static.bshare.cn/frame/images/logos/s4/diigo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-douban{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -36px;*display:inline;display:inline-block;}.bshare-custom .bshare-dream{background:url("http://static.bshare.cn/frame/images/logos/s4/dream.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duitang{background:url("http://static.bshare.cn/frame/images/logos/s4/duitang.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-eastdaymb{background:url("http://static.bshare.cn/frame/images/logos/s4/eastdaymb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-email{background:url("http://static.bshare.cn/frame/images/logos/s4/email.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-evernote{background:url("http://static.bshare.cn/frame/images/logos/s4/evernote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-facebook{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -54px;*display:inline;display:inline-block;}.bshare-custom .bshare-fanfou{background:url("http://static.bshare.cn/frame/images/logos/s4/fanfou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-favorite{background:url("http://static.bshare.cn/frame/images/logos/s4/favorite.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-feixin{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -72px;*display:inline;display:inline-block;}.bshare-custom .bshare-friendfeed{background:url("http://static.bshare.cn/frame/images/logos/s4/friendfeed.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-fwisp{background:url("http://static.bshare.cn/frame/images/logos/s4/fwisp.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ganniu{background:url("http://static.bshare.cn/frame/images/logos/s4/ganniu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmail{background:url("http://static.bshare.cn/frame/images/logos/s4/gmail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmw{background:url("http://static.bshare.cn/frame/images/logos/s4/gmw.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gtranslate{background:url("http://static.bshare.cn/frame/images/logos/s4/gtranslate.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hemidemi{background:url("http://static.bshare.cn/frame/images/logos/s4/hemidemi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hexunmb{background:url("http://static.bshare.cn/frame/images/logos/s4/hexunmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-huaban{background:url("http://static.bshare.cn/frame/images/logos/s4/huaban.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengkb{background:url("http://static.bshare.cn/frame/images/logos/s4/ifengkb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-ifengmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -90px;*display:inline;display:inline-block;}.bshare-custom .bshare-ifensi{background:url("http://static.bshare.cn/frame/images/logos/s4/ifensi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-instapaper{background:url("http://static.bshare.cn/frame/images/logos/s4/instapaper.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-itieba{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -108px;*display:inline;display:inline-block;}.bshare-custom .bshare-joinwish{background:url("http://static.bshare.cn/frame/images/logos/s4/joinwish.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kaixin001{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -126px;*display:inline;display:inline-block;}.bshare-custom .bshare-laodao{background:url("http://static.bshare.cn/frame/images/logos/s4/laodao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leihou{background:url("http://static.bshare.cn/frame/images/logos/s4/leihou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-leshou{background:url("http://static.bshare.cn/frame/images/logos/s4/leshou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-linkedin{background:url("http://static.bshare.cn/frame/images/logos/s4/linkedin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-livespace{background:url("http://static.bshare.cn/frame/images/logos/s4/livespace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mala{background:url("http://static.bshare.cn/frame/images/logos/s4/mala.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-masar{background:url("http://static.bshare.cn/frame/images/logos/s4/masar.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-meilishuo{background:url("http://static.bshare.cn/frame/images/logos/s4/meilishuo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-miliao{background:url("http://static.bshare.cn/frame/images/logos/s4/miliao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mister_wong{background:url("http://static.bshare.cn/frame/images/logos/s4/mister_wong.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mogujie{background:url("http://static.bshare.cn/frame/images/logos/s4/mogujie.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-moptk{background:url("http://static.bshare.cn/frame/images/logos/s4/moptk.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-msn{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -144px;*display:inline;display:inline-block;}.bshare-custom .bshare-myshare{background:url("http://static.bshare.cn/frame/images/logos/s4/myshare.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-myspace{background:url("http://static.bshare.cn/frame/images/logos/s4/myspace.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-neteasemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -162px;*display:inline;display:inline-block;}.bshare-custom .bshare-netvibes{background:url("http://static.bshare.cn/frame/images/logos/s4/netvibes.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-peoplemb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -180px;*display:inline;display:inline-block;}.bshare-custom .bshare-pinterest{background:url("http://static.bshare.cn/frame/images/logos/s4/pinterest.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-poco{background:url("http://static.bshare.cn/frame/images/logos/s4/poco.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printer{background:url("http://static.bshare.cn/frame/images/logos/s4/printer.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-printf{background:url("http://static.bshare.cn/frame/images/logos/s4/printf.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqmb{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -198px;*display:inline;display:inline-block;}.bshare-custom .bshare-qqshuqian{background:url("http://static.bshare.cn/frame/images/logos/s4/qqshuqian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqxiaoyou{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -216px;*display:inline;display:inline-block;}.bshare-custom .bshare-qzone{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -234px;*display:inline;display:inline-block;}.bshare-custom .bshare-readitlater{background:url("http://static.bshare.cn/frame/images/logos/s4/readitlater.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-reddit{background:url("http://static.bshare.cn/frame/images/logos/s4/reddit.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-redmb{background:url("http://static.bshare.cn/frame/images/logos/s4/redmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renjian{background:url("http://static.bshare.cn/frame/images/logos/s4/renjian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renmaiku{background:url("http://static.bshare.cn/frame/images/logos/s4/renmaiku.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-renren{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -252px;*display:inline;display:inline-block;}.bshare-custom .bshare-shouji{background:url("http://static.bshare.cn/frame/images/logos/s4/shouji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -270px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinaqing{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -288px;*display:inline;display:inline-block;}.bshare-custom .bshare-sinavivi{background:url("http://static.bshare.cn/frame/images/logos/s4/sinavivi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohubai{background:url("http://static.bshare.cn/frame/images/logos/s4/sohubai.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohuminiblog{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -306px;*display:inline;display:inline-block;}.bshare-custom .bshare-southmb{background:url("http://static.bshare.cn/frame/images/logos/s4/southmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-stumbleupon{background:url("http://static.bshare.cn/frame/images/logos/s4/stumbleupon.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szone{background:url("http://static.bshare.cn/frame/images/logos/s4/szone.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-taojianghu{background:url("http://static.bshare.cn/frame/images/logos/s4/taojianghu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianya{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -324px;*display:inline;display:inline-block;}.bshare-custom .bshare-tongxue{background:url("http://static.bshare.cn/frame/images/logos/s4/tongxue.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tuita{background:url("http://static.bshare.cn/frame/images/logos/s4/tuita.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tumblr{background:url("http://static.bshare.cn/frame/images/logos/s4/tumblr.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-twitter{background:url("http://static.bshare.cn/frame/images/logos/s4/sprite/top_logos_sprite.png") no-repeat 0 -342px;*display:inline;display:inline-block;}.bshare-custom .bshare-ushi{background:url("http://static.bshare.cn/frame/images/logos/s4/ushi.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-waakee{background:url("http://static.bshare.cn/frame/images/logos/s4/waakee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wealink{background:url("http://static.bshare.cn/frame/images/logos/s4/wealink.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-woshao{background:url("http://static.bshare.cn/frame/images/logos/s4/woshao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xianguo{background:url("http://static.bshare.cn/frame/images/logos/s4/xianguo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xiaomeisns{background:url("http://static.bshare.cn/frame/images/logos/s4/xiaomeisns.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinminmb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinminmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xyweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/xyweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yaolanmb{background:url("http://static.bshare.cn/frame/images/logos/s4/yaolanmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yijee{background:url("http://static.bshare.cn/frame/images/logos/s4/yijee.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdao{background:url("http://static.bshare.cn/frame/images/logos/s4/youdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-zjol{background:url("http://static.bshare.cn/frame/images/logos/s4/zjol.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xinhuamb{background:url("http://static.bshare.cn/frame/images/logos/s4/xinhuamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-szmb{background:url("http://static.bshare.cn/frame/images/logos/s4/szmb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-changshamb{background:url("http://static.bshare.cn/frame/images/logos/s4/changshamb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-hefeimb{background:url("http://static.bshare.cn/frame/images/logos/s4/hefeimb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wansha{background:url("http://static.bshare.cn/frame/images/logos/s4/wansha.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189share{background:url("http://static.bshare.cn/frame/images/logos/s4/189share.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-diandian{background:url("http://static.bshare.cn/frame/images/logos/s4/diandian.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-tianji{background:url("http://static.bshare.cn/frame/images/logos/s4/tianji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jipin{background:url("http://static.bshare.cn/frame/images/logos/s4/jipin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-chezhumb{background:url("http://static.bshare.cn/frame/images/logos/s4/chezhumb.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gplus{background:url("http://static.bshare.cn/frame/images/logos/s4/gplus.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-yidongweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/yidongweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-youdaonote{background:url("http://static.bshare.cn/frame/images/logos/s4/youdaonote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jschina{background:url("http://static.bshare.cn/frame/images/logos/s4/jschina.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-mingdao{background:url("http://static.bshare.cn/frame/images/logos/s4/mingdao.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jxcn{background:url("http://static.bshare.cn/frame/images/logos/s4/jxcn.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qileke{background:url("http://static.bshare.cn/frame/images/logos/s4/qileke.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-sohukan{background:url("http://static.bshare.cn/frame/images/logos/s4/sohukan.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-maikunote{background:url("http://static.bshare.cn/frame/images/logos/s4/maikunote.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-lezhimark{background:url("http://static.bshare.cn/frame/images/logos/s4/lezhimark.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-189mail{background:url("http://static.bshare.cn/frame/images/logos/s4/189mail.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-wo{background:url("http://static.bshare.cn/frame/images/logos/s4/wo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-gmweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/gmweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-jianweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/jianweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qingbiji{background:url("http://static.bshare.cn/frame/images/logos/s4/qingbiji.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-duankou{background:url("http://static.bshare.cn/frame/images/logos/s4/duankou.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-qqim{background:url("http://static.bshare.cn/frame/images/logos/s4/qqim.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-kdweibo{background:url("http://static.bshare.cn/frame/images/logos/s4/kdweibo.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-xueqiu{background:url("http://static.bshare.cn/frame/images/logos/s4/xueqiu.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom .bshare-weixin{background:url("http://static.bshare.cn/frame/images/logos/s4/weixin.png") no-repeat;*display:inline;display:inline-block;}.bshare-custom #bshare-more-icon,.bshare-custom .bshare-more-icon{background:url("http://static.bshare.cn/frame/images/logos/s4/more.png") no-repeat;padding-left:19px;}.bshare-custom .bshare-share-count{width:41px;background:transparent url(http://static.bshare.cn/frame/images/counter_box_18.gif) no-repeat;height:18px;line-height:18px !important;color:#333;text-align:center;font:bold 11px Arial,宋体,sans-serif;*display:inline;display:inline-block;zoom:1;_padding-top:2px;}.bshare-custom .bshareDiv{*display:inline;display:inline-block;}</style><script src="http://static.bshare.cn/b/styles/bshareS887.js?v=20160206" type="text/javascript" charset="utf-8"></script><style type="text/css">.cy-report{position:relative;*overflow:hidden}.cy-report .rpt-title{text-align:left;padding-left:20px;background-color:#fafafa;border-bottom:1px solid #cfd6dc}.cy-report .rpt-title span{height:44px;line-height:44px;font-weight:700;font-size:14px}.cy-report .rpt-close{position:absolute;top:16px;right:16px;background-image:url(//changyan.sohu.com/mdevp/extensions/cy-report/007/images/close.png);background-repeat:no-repeat;width:12px;height:12px}.cy-report .rpt-close:hover{cursor:pointer}.cy-report .rpt-reason-item{list-style:none;display:inline-block;*display:inline;*zoom:1;margin-right:80px;width:80px;text-align:left;margin-top:14px}.cy-report .rpt-hint{display:none;padding-top:48px}.cy-report .rpt-hint-image{display:inline-block;width:40px;height:40px;background:url(//changyan.sohu.com/mdevp/extensions/cy-report/007/images/ok.png) no-repeat;margin-bottom:24px}.cy-report .rpt-hint-text{font-size:15px;font-weight:600}.cy-report ul{font-size:0;margin-left:80px;line-height:1}.cy-report .rpt-reason-item .rpt-list-style{display:inline-block;width:10px;height:10px;border:1px solid #a9aeb1;border-radius:50%;margin-right:10px}.cy-report .rpt-reason-item .rpt-text{font-size:14px}.cy-report .rpt-submit{display:inline-block;text-align:center}.cy-report .rpt-submit a{display:inline-block;height:28px;width:100px;border:2px solid #50acf9;line-height:28px;border-radius:14px;margin-top:18px;font-size:16px}.cy-report .rpt-submit:hover{cursor:default}.cy-report .rpt-submit a:hover{color:#000;text-decoration:none}.cy-report .rpt-item-selected .rpt-list-style{background-color:#51adfa}</style><style type="text/css">.dialog-wrapper{z-index:2147483647!important;position:fixed;top:0;left:0;width:100%;height:100%;padding:0;margin:0;border:0;text-align:center;background:none9;*background:0 0;_background:0 0;background-image:url(data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)9;*background-image:url(data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7);_background-image:url(data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7);background-color:#000 transparent;background-color:rgba(0,0,0,.4);zoom:1;filter:progid:DXImageTransform.Microsoft.gradient(startcolorstr=#7F000000, endcolorstr=#7F000000);-ms-filter:"progid:DXImageTransform.Microsoft.gradient(startcolorstr=#7F000000,endcolorstr=#7F000000)";overflow:hidden}.dialog-wrapper-noOverlay{background-color:rgba(0,0,0,0);filter:progid:DXImageTransform.Microsoft.gradient(startcolorstr=#00000000, endcolorstr=#00000000);-ms-filter:"progid:DXImageTransform.Microsoft.gradient(startcolorstr=#00000000,endcolorstr=#00000000)"}.dialog-wrapper *{padding:0;margin:0;border:0}.dialog-docker{position:absolute;visibility:hidden;zoom:1;overflow:visible}.dialog-docker-p0{top:0;left:0;width:100%;height:100%}.dialog-wrapper .dialog{margin:0 auto;color:#000;background-color:#fff;border:1px solid #eee;border-radius:2px;visibility:visible;zoom:1;padding:0}.dialog-docker-p1{top:0;left:0}.dialog-docker-p2{top:0;left:50%}.dialog-docker-p3{top:0;right:0}.dialog-docker-p4{top:50%;left:0}.dialog-docker-p5{top:50%;left:50%}.dialog-docker-p6{top:50%;right:0}.dialog-docker-p7{bottom:0;left:0}.dialog-docker-p8{bottom:0;left:50%}.dialog-docker-p9{bottom:0;right:0}.dialog-docker-p0 .dialog{margin:0;border:0}.dialog-docker-p1 .dialog{position:absolute;top:0;left:0}.dialog-docker-p2 .dialog{position:absolute;top:0;left:-50%}.dialog-docker-p3 .dialog{position:absolute;top:0;right:0}.dialog-docker-p4 .dialog{position:absolute;top:-50%;left:0}.dialog-docker-p5 .dialog{position:absolute;top:-50%;left:-50%}.dialog-docker-p6 .dialog{position:absolute;top:-50%;right:0}.dialog-docker-p7 .dialog{position:absolute;bottom:0;left:0}.dialog-docker-p8 .dialog{position:absolute;bottom:0;left:-50%}.dialog-docker-p9 .dialog{position:absolute;bottom:0;right:0}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-notice/016/cy-user-notice.js"></script><style type="text/css">.module-cy-user-notice{display:none;position:relative}.module-cy-user-notice .notice-title{padding-left:24px;height:60px;border-bottom:1px solid #c3cad4;line-height:60px;font-size:20px;font-family:'Microsoft YaHei';position:relative;top:0;left:0}.module-cy-user-notice .notice-info{overflow-x:hidden;overflow-y:auto;position:relative;top:0;left:0}.module-cy-user-notice .notice-info ul{margin-bottom:20px}.module-cy-user-notice .notice-info .notice-empty{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/notice-empty.png);width:339px;height:431px;margin:145px auto 50px}.module-cy-user-notice .notice-info ul.noticeinfo-list{position:relative;top:0;left:0}.module-cy-user-notice .notice-info .noticeinfo-list li{border-bottom:solid 1px #e9f0f5;padding:16px 20px 19px;position:relative}.module-cy-user-notice .notice-info .noticeinfo-list li:hover{background-color:#f3faff}.module-cy-user-notice .notice-info .noticeinfo-list li .info-header{margin-bottom:9px;height:18px;line-height:18px}.module-cy-user-notice .notice-info .noticeinfo-list li .info-header .info-type{float:left;font-size:12px;color:#999;font-family:'Microsoft YaHei'}.module-cy-user-notice .notice-info .noticeinfo-list li .info-header .notice-time{float:right}.module-cy-user-notice .notice-info .noticeinfo-list li .info-header .notice-time em{display:inline-block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/time-ico.png);width:12px;height:12px;vertical-align:-1px;*vertical-align:3px}.module-cy-user-notice .notice-info .noticeinfo-list li .info-header .notice-time i{margin-left:4px;font-style:normal;font-size:12px;color:#999;font-family:'Microsoft YaHei'}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:'Microsoft YaHei';padding-right:10px}.module-cy-user-notice .notice-info .noticeinfo-list li .indicator-unread{display:inline-block;width:6px;height:6px;border-radius:50%;background-color:red;position:absolute;bottom:25px;right:20px}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content span{font-size:16px;color:#111;line-height:21px;font-family:'Microsoft YaHei'}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content a.link-mall,.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content a.link-paper{font-size:14px;text-decoration:underline;cursor:pointer;font-family:'Microsoft YaHei'}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content a.link-mall{color:#38a3fd}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content a.link-paper{color:#465e72}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content a.notice-user{font-size:16px;color:#38a3fd;font-family:'Microsoft YaHei';text-decoration:none}.module-cy-user-page .cy-tab-list li .cy-notice-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/tab-list-notice.png)}.module-cy-user-page .cy-tab-list li.active .cy-notice-ico,.module-cy-user-page .cy-tab-list li.notice-li:hover .cy-notice-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/tab-list-icon-active-notice.png)}.module-cy-user-page .cy-tab-list li.notice-li:hover i{color:#38a3fd}.module-cy-user-notice .noticeinfo-detail{position:absolute;width:100%;height:100%;overflow-y:auto;overflow-x:hidden;background-color:#fff;top:0;left:0;padding:0 0 10px;font-family:'Microsoft YaHei'}.module-cy-user-notice .noticeinfo-detail .notice-detail-title{padding-left:24px;height:60px;border-bottom:1px solid #c3cad4;line-height:60px;font-size:20px;font-family:'Microsoft YaHei';width:100%;background-color:#fff;position:relative;top:0;left:0}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap{position:relative;left:0;top:0;min-height:300px}.module-cy-user-notice .noticeinfo-detail a.notice-back{display:inline-block;width:40px;height:100%;background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/back.png);background-repeat:no-repeat;background-position:0 16px;cursor:pointer}.module-cy-user-notice .noticeinfo-detail .comment-desc{font-size:16px;padding:18px 18px 8px}.module-cy-user-notice .noticeinfo-detail .comment-desc span{font-weight:700}.module-cy-user-notice .noticeinfo-detail .comment-detail-wrap{padding:8px 18px;position:relative;left:0;top:0}.module-cy-user-notice .noticeinfo-detail .comment-detail{position:relative;left:0;top:0;margin:8px 0;font-size:16px;background-color:#FAFAFA;border:1px solid #F2F2F2;padding:10px 0 10px 75px}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-user-figure{position:absolute;top:18px;left:18px;width:40px;height:40px;border-radius:3px;overflow:hidden}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-user-figure img{width:100%;height:100%}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-user-name{padding:8px 0;margin:0;position:relative}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-user-name a{color:#38a3fd;text-decoration:none}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-content{padding:8px 0;margin-right:20px;line-height:20px}.module-cy-user-notice .noticeinfo-detail .comment-detail a.comment-subhead{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;margin-right:20px;padding:8px 0;text-decoration:none}.module-cy-user-notice .noticeinfo-detail .comment-detail .comment-attrs{padding-right:20px;height:16px}.module-cy-user-notice .noticeinfo-detail .comment-attrs .comment-site{font-size:12px;text-decoration:none;color:#aaa;float:left;line-height:16px;display:inline-block;height:16px;vertical-align:bottom;*zoom:1;_zoom:1;*display:inline;_display:inline}.module-cy-user-notice .noticeinfo-detail .comment-attrs .comment-time{float:right;display:inline-block;line-height:16px;height:16px;vertical-align:bottom;*zoom:1;_zoom:1;*display:inline;_display:inline}.module-cy-user-notice .noticeinfo-detail .comment-attrs .comment-time em{display:inline-block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/time-ico.png);width:12px;height:12px;vertical-align:-1px;*vertical-align:3px}.module-cy-user-notice .noticeinfo-detail .comment-attrs .comment-time i{margin-left:4px;font-style:normal;font-size:12px;color:#aaa;font-family:'Microsoft YaHei'}.module-cy-user-notice .noticeinfo-detail .comment-attrs .clear-f{float:none;display:none}.module-cy-user-notice .noticeinfo-detail .comment-remark-header-wrap{height:24px;background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/remark-bg.gif);background-position:0 6px;background-repeat-x:none;background-repeat-y:no-repeat;margin:0 40px;text-align:center}.module-cy-user-notice .noticeinfo-detail .comment-remark-header{border-right:12px solid #fff;display:inline-block;background-color:#fff;font-size:16px;color:#ffb026;border-left:12px solid #fff;line-height:24px;*zoom:1;_zoom:1;*display:inline;_display:inline}.module-cy-user-notice .noticeinfo-detail .comment-remark-content{text-align:center;padding:15px 20px;font-size:20px;line-height:24px}.module-cy-user-notice .noticeinfo-detail ul.comment-props{padding-top:32px;position:relative;left:0;top:0}.module-cy-user-notice .noticeinfo-detail ul.comment-props li.comment-prop{height:60px;padding:0 40px;position:relative;left:0;top:0;margin-bottom:40px}.module-cy-user-notice .noticeinfo-detail .prop-bar{border:28px 0;border-top:28px solid #fff;border-bottom:28px solid #fff;height:4px;display:inline-block;position:absolute;width:0}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg{border-top:28px solid #fff;border-bottom:28px solid #fff;height:4px;width:auto;margin:auto}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg-1{background-color:#fee2e2}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg-2{background-color:#d7edff}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg-3{background-color:#f9e9d1}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg-4{background-color:#d9e5fc}.module-cy-user-notice .noticeinfo-detail .prop-bar-bg-5{background-color:#ffdcdc}.module-cy-user-notice .noticeinfo-detail .prop-label{position:absolute;top:3px;left:0;width:54px;height:54px;text-align:center;color:#fff;background-repeat:no-repeat;background-size:100% 100%}.module-cy-user-notice .noticeinfo-detail .prop-label-1{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/prop-bar-1.png)}.module-cy-user-notice .noticeinfo-detail .prop-label-2{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/prop-bar-2.png)}.module-cy-user-notice .noticeinfo-detail .prop-label-3{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/prop-bar-3.png)}.module-cy-user-notice .noticeinfo-detail .prop-label-4{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/prop-bar-4.png)}.module-cy-user-notice .noticeinfo-detail .prop-label-5{background-image:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/prop-bar-5.png)}.module-cy-user-notice .noticeinfo-detail .prop-label .prop-label-text{position:absolute;top:-32px;left:-27px;height:32px;width:108px;line-height:32px;text-align:center;font-size:16px;border-radius:3px}.module-cy-user-notice .noticeinfo-detail .prop-label .prop-label-text i{padding:0 4px;font-size:12px}.module-cy-user-notice .noticeinfo-detail .prop-label .prop-label-arrow{position:absolute;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;top:0;left:21px}.module-cy-user-notice .noticeinfo-detail .prop-bar-1,.module-cy-user-notice .noticeinfo-detail .prop-label-1 .prop-label-text{background-color:#eb6d6d}.module-cy-user-notice .noticeinfo-detail .prop-bar-2,.module-cy-user-notice .noticeinfo-detail .prop-label-2 .prop-label-text{background-color:#6db1eb}.module-cy-user-notice .noticeinfo-detail .prop-bar-3,.module-cy-user-notice .noticeinfo-detail .prop-label-3 .prop-label-text{background-color:#ff9c00}.module-cy-user-notice .noticeinfo-detail .prop-bar-4,.module-cy-user-notice .noticeinfo-detail .prop-label-4 .prop-label-text{background-color:#3e82ff}.module-cy-user-notice .noticeinfo-detail .prop-bar-5,.module-cy-user-notice .noticeinfo-detail .prop-label-5 .prop-label-text{background-color:#fd3838}.module-cy-user-notice .noticeinfo-detail .prop-label-1 .prop-label-arrow{border-top:4px solid #eb6d6d}.module-cy-user-notice .noticeinfo-detail .prop-label-2 .prop-label-arrow{border-top:4px solid #6db1eb}.module-cy-user-notice .noticeinfo-detail .prop-label-3 .prop-label-arrow{border-top:4px solid #ff9c00}.module-cy-user-notice .noticeinfo-detail .prop-label-4 .prop-label-arrow{border-top:4px solid #3e82ff}.module-cy-user-notice .noticeinfo-detail .prop-label-5 .prop-label-arrow{border-top:4px solid #fd3838}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content .feedback-content-wrap{display:inline-block;font-size:100%;line-height:1}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content .feedback-content-wrap span{font-size:100%}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content .feedback-content{display:inline-block;max-width:168px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;line-height:1}.module-cy-user-notice .notice-info .noticeinfo-list li .notice-content .feedback-note{color:#38a3fd}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .official-reply-wrap{margin:18px 18px 2px;font-size:16px}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .official-reply-wrap .feedback-title{display:block}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .official-reply-wrap .official-reply{display:block;margin-top:20px;line-height:20px}.module-cy-user-notice .noticeinfo-detail .feedback-content-warp .comment-detail{padding:0}.module-cy-user-notice .noticeinfo-detail .feedback-content-warp .comment-detail .reply-content{padding:10px 25px 10px 10px;line-height:20px;color:#a6a6a6;margin-bottom:25px}.module-cy-user-notice .noticeinfo-detail .feedback-content-warp .comment-detail .feedback-time{position:absolute;right:25px;bottom:10px}.module-cy-user-notice .noticeinfo-detail .feedback-content-warp .comment-detail .feedback-time em{display:inline-block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/time-ico.png);width:12px;height:12px;vertical-align:-1px;*vertical-align:3px}.module-cy-user-notice .noticeinfo-detail .feedback-content-warp .comment-detail .feedback-time i{margin-left:4px;font-style:normal;font-size:12px;color:#999;font-family:'Microsoft YaHei'}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .feedback-extra{font-size:16px;margin:0 18px 0 30px}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .feedback-qrcode-wrap{margin-top:24px;text-align:center}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .feedback-qrcode-wrap .feedback-qrcode{display:block;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-notice/016/image/qrcode.jpg);width:258px;height:258px;margin:0 auto}.module-cy-user-notice .noticeinfo-detail .notice-content-wrap .feedback-qrcode-wrap .feedback-qrnote{display:inline-block;font-size:16px;margin:10px 0}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-user-feedback/023/cy-user-feedback.js"></script><style type="text/css">.module-cy-user-page .cy-tab-list li .cy-feedback-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/tab-list-icon5.png) no-repeat}.module-cy-user-page .cy-tab-list .feedback-li:hover .cy-feedback-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/tab-list-icon-active5.png) no-repeat}.module-cy-user-page .cy-tab-list .feedback-li:hover .feedback-text{color:#38a3fd}.module-cy-user-page .cy-tab-list li.active .cy-feedback-ico{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/tab-list-icon-active5.png) no-repeat}.module-cy-user-page .cy-tab-list li.active .feedback-text{color:#38a3fd}.module-cy-user-page .module-cy-user-feedback{height:100%;overflow-x:hidden;overflow-y:auto;display:none;position:relative}.module-cy-user-page .module-cy-user-feedback .main{width:100%;height:100%;font-family:"microsoft yahei";position:relative;min-height:680px;overflow-y:auto;overflow-x:hidden}.module-cy-user-page .module-cy-user-feedback .title{width:100%;height:60px;line-height:60px;padding:0 0 0 25px;font-size:20px;font-family:"microsoft yahei";margin-bottom:-60px}.module-cy-user-page .module-cy-user-feedback .form{width:100%;margin:60px 0 0;border:solid #ccc 1px;border-width:1px 0 0;padding:40px 0 0 25px}.module-cy-user-page .module-cy-user-feedback .form .faq{font-size:16px;font-family:"microsoft yahei"}.module-cy-user-page .module-cy-user-feedback .form .faq-questions{margin:10px 0 0;font-size:16px;font-family:"microsoft yahei";overflow:hidden}.module-cy-user-page .module-cy-user-feedback .form .faq-questions .faq-question{float:left;width:278px;margin:10px 0 0;font-family:"microsoft yahei";font-size:14px;color:#666;cursor:pointer}.module-cy-user-page .module-cy-user-feedback .form .faq-questions .faq-question:hover{color:#5eb0fd}.module-cy-user-page .module-cy-user-feedback .form .faq-questions .faq-question .point{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/point.png) no-repeat;width:4px;height:4px;display:inline-block;*display:inline;*zoom:1;vertical-align:middle;margin:0 6px 0 0}.module-cy-user-page .module-cy-user-feedback .form .faq-questions .faq-question:hover .point{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/point-hover.png) no-repeat}.module-cy-user-page .module-cy-user-feedback .form .question{font-size:16px;font-family:"microsoft yahei";margin:40px 0 0}.module-cy-user-page .module-cy-user-feedback .form .questionCon{margin-top:20px;padding:10px 0 10px 10px;width:560px;height:160px;border-radius:3px;resize:none;font-family:"microsoft yahei";border:solid #ccc 1px;overflow:auto;font-size:14px}.module-cy-user-page .module-cy-user-feedback .link{width:560px;margin:40px 0 0;font-family:"microsoft yahei";line-height:1;background-color:#fff}.module-cy-user-page .module-cy-user-feedback .link .phone{font-size:16px}.module-cy-user-page .module-cy-user-feedback .link .select{float:right;color:#ccc}.module-cy-user-page .module-cy-user-feedback .link .text{width:100%;height:38px;line-height:38px;margin:20px 0 0;padding-left:10px;border:solid #ccc 1px;border-radius:3px;font-size:14px;font-family:microsoft yahei}.module-cy-user-page .module-cy-user-feedback .tip{height:36px;line-height:36px;background-color:#e9eef1;font-size:14px;position:absolute;bottom:70px;display:none}.module-cy-user-page .module-cy-user-feedback .tip .ok{width:14px;height:14px;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/ok.png) no-repeat;vertical-align:middle;display:inline-block;*display:inline;*zoom:1;margin:0 0 0 10px}.module-cy-user-page .module-cy-user-feedback .tip .error{background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/error.png) no-repeat}.module-cy-user-page .module-cy-user-feedback .tip .tipText{margin:0 10px 0 0}.module-cy-user-page .module-cy-user-feedback .button{width:100%;height:50px;line-height:50px;position:absolute;bottom:0;border:solid #ccc 1px;border-width:1px 0 0;padding:0 0 0 25px}.module-cy-user-page .module-cy-user-feedback .button .confirm{width:84px;height:32px;line-height:32px;color:#51acf9;border:solid #38a3fd 2px;border-radius:24px;vertical-align:top;display:inline-block;*display:inline;*zoom:1;font-size:16px;font-weight:500;text-align:center;cursor:pointer;margin:9px 0 0}.module-cy-user-page .module-cy-user-feedback .button .confirm:hover{background-color:#38a3fd;color:#fff}.module-cy-user-page .module-cy-user-feedback .feedback-second{width:100%}.module-cy-user-page .module-cy-user-feedback .feedback-second .feedback-detail-title{width:100%;height:59px;line-height:54px;border:1px solid #c3cad4;border-width:0 0 1px}.module-cy-user-page .module-cy-user-feedback .feedback-second .feedback-detail-title .feedback-back{display:inline-block;*display:inline;*zoom:1;background:url(//changyan.sohu.com/mdevp/extensions/cy-user-feedback/023/image/back.png) no-repeat;width:35px;height:28px;margin:0 0 0 24px;vertical-align:middle;cursor:pointer}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists{margin:0 0 0 30px}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists .faq{margin:16px 0 0;width:550px;padding-bottom:21px;border-bottom:1px solid #e9f0f5}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists .faq .faq-title{font-size:16px;height:20px;line-height:20px}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists .faq .faq-title .title-bar{width:3px;height:20px;background-color:#38a3fd;border-radius:2px;display:inline-block;*display:inline;*zoom:1;vertical-align:middle}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists .faq .faq-title .title-text{margin:0 0 0 7px;font-family:microsoft yahei}.module-cy-user-page .module-cy-user-feedback .feedback-second .faq-lists .faq .faq-detail{margin:19px 0 0;font-size:14px;color:#959595;line-height:21px}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cmt-notice-no-task-msg/001/cmt-notice-no-task-msg.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-cmt-notice-dot,.module-cmt-notice-dot{z-index:1000;display:block;width:4px;height:4px;background-color:#F74F4F;border-radius:2px;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-notice-bubble,.module-cmt-notice-bubble{z-index:1000;display:block;min-width:12px;height:16px;line-height:16px;padding:0 2px;text-align:center;font-size:12px;font-style:normal;font-family:arial;color:#FFF;background-color:#F74F4F;border-radius:8px;cursor:pointer}#SOHUCS #SOHU_MAIN .module-cmt-notice{position:fixed;right:0;bottom:0;padding:38px 0;font-family:'Microsoft YaHei';z-index:999999}#SOHUCS #SOHU_MAIN .module-cmt-notice ul.nt-list{max-width:300px;text-align:right;overflow:visible;position:relative}#SOHUCS #SOHU_MAIN .module-cmt-notice ul.nt-list li.nt-item{position:relative;display:inline-block;overflow:auto;max-width:200px;min-width:170px;line-height:24px;background-color:#f8f9f9;color:#000!important;margin:5px 10px;padding:10px 35px 10px 30px;border:1px solid #e9f0f5;border-top-color:#e9f0f5;border-right-color:#d6dde1;border-bottom-color:#d6dde1;border-left-color:#e9f0f5;text-decoration:none;cursor:pointer;font-size:15px}#SOHUCS #SOHU_MAIN .module-cmt-notice ul.nt-list li.nt-item .nt-text{color:#000!important;text-decoration:none}#SOHUCS #SOHU_MAIN .module-cmt-notice ul.nt-list li.nt-item .nt-text i{color:#f74f4f!important;padding:0 4px}#SOHUCS #SOHU_MAIN .module-cmt-notice .nt-close{display:inline-block;position:absolute;right:12px;top:12px;width:10px;height:10px;background:transparent url(//changyan.sohu.com/mdevp/extensions/cmt-notice-no-task-msg/001/images/close.gif) repeat-x scroll 0 0}#SOHUCS #SOHU_MAIN .module-cmt-notice .nt-close:hover{background-position:-10px 0}.module-cy-user-page .module-cmt-notice-dot{position:absolute;top:0;right:6px;width:6px;height:6px;background-color:#F74F4F;border-radius:6px}.module-cy-user-page .module-cmt-notice-bubble{display:inline-block;position:absolute;min-width:12px;height:16px;line-height:16px;padding:0 2px;text-align:center;font-size:12px;font-style:normal;font-family:arial;color:#FFF;background-color:#F74F4F;border-radius:16px;margin-left:4px}.module-cmt-float-bar .module-cmt-notice-bubble{position:absolute;top:-8px;*top:-4px;left:20px;min-width:12px;height:16px;line-height:16px;padding:0 2px;text-align:center;font-size:12px;font-style:normal;font-family:arial;color:#FFF;background-color:#F74F4F;border-radius:8px}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-grade/004/cy-grade.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cy-score/002/cy-score.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/jump-url/003/jump-url.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .more-comment{padding:0 0 17px}#SOHUCS #SOHU_MAIN .more-comment a{color:#44708e;background-color:#f5f5f5;padding:7px 0 5px;line-height:18px;display:block;text-align:center}#SOHUCS #SOHU_MAIN .more-comment a em{font-family:Georgia;font-size:18px;color:#ee542a}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/disable-user-photo/005/disable-user-photo.js"></script><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/sohu-treaty/001/sohu-treaty.js"></script><style type="text/css">#SOHUCS #SOHU_MAIN .module-sohu-treaty .title-link-w{padding:12px 0 0;font-size:12px;color:#ccd3d9;text-align:right}#SOHUCS #SOHU_MAIN .module-sohu-treaty .title-link-w a{display:inline-block;line-height:16px;color:#ccd3d9}#SOHUCS #SOHU_MAIN .module-sohu-treaty .title-link-w a:hover{text-decoration:underline}</style><script type="text/javascript" charset="UTF-8" src="http://changyan.itc.cn/mdevp/extensions/cui/002/swfupload.v2.2.0/swfupload.js"></script><script src="http://bshare.optimix.asia/bshare_view?Callback=bShare.viewcb&amp;url=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;h=&amp;uuid=fbe7b28e-050d-4ab3-9af4-0740ed16ea11&amp;sc=1&amp;l=17&amp;lite=1&amp;ref=http%3A%2F%2Fnews.baidu.com%2Fns%3Fword%3D%25E7%2594%259F%25E6%2580%2581%25E8%25A1%25A5%25E5%2581%25BF%26pn%3D80%26cl%3D2%26ct%3D1%26tn%3Dnews%26rn%3D20%26ie%3Dutf-8%26bt%3D0%26et%3D0&amp;q=%E7%94%9F%E6%80%81%E8%A1%A5%E5%81%BF&amp;cs=UTF-8&amp;ot=生态补偿探索候鸟保护新机制 让候鸟平安返乡(1)_光明日报 _光明网&amp;kws=候鸟&amp;fp=e85bd2c0f55c775fa47a30da16457da7&amp;b=bs184e18" type="text/javascript" charset="utf-8"></script><style type="text/css">a.bsSiteLink{text-decoration:none;color:#666;}a.bsSiteLink:hover{text-decoration:underline;}a.bshareDiv{overflow:hidden;height:16px;line-height:18px;font-size:14px;color:#333;padding-left:0;}a.bshareDiv:hover{text-decoration:none;}div.bsTitle{padding:0 8px;border-bottom:1px solid #e8e8e8;color:#666;background:#f2f2f2;text-align:left;}div.buzzButton{cursor:pointer;}div.bsRlogo,div.bsRlogoSel{width:68px;float:left;margin:0;padding:2px 0;}div.bsRlogo a,div.bsRlogoSel a{float:left;}div.bsLogo,div.bsLogoSel{float:left;width:111px;text-align:left;height:auto;padding:2px 4px;margin:2px 0;white-space:nowrap;overflow:hidden;}div.bsLogoSel,div.bsRlogoSel{border:1px solid #ddd;background:#f1f1f1;}div.bsLogo,div.bsRlogo{border:1px solid #fff;background:#fff;}div.bsLogo a,div.bsLogoSel a{display:block;height:16px;line-height:16px;padding:0 0 0 24px;text-decoration:none;float:left;overflow:hidden;}div.bsLogoSel a,div.bsRlogoSel a{color:#000;border:none;}div.bsLogo a,div.bsRlogo a{color:#666;border:none;}div.bsLogoLink{width:121px;overflow:hidden;background:#FFF;float:left;margin:3px 0;}#bsPanel{position:absolute;z-index:100000000;font-size:12px;width:258px;background:url(http://static.bshare.cn/frame/images/background-opaque-dark.png);padding:6px;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}div.bsClear{clear:both;height:0;line-height:0;font-size:0;overflow:hidden;}div.bsPopupAwd{background: url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;background-position:0 -624px;width:18px;padding-left:3px;text-align:center;float:left;margin-left:2px;height:15px;font-size:12px;color:#fff;overflow:hidden;}div.bsRlogo .bsPopupAwd,div.bsRlogoSel .bsPopupAwd{float:left;margin:5px 0 0 -14px;}</style><style type="text/css">a.bsSiteLink{text-decoration:none;color:#666;}a.bsSiteLink:hover{text-decoration:underline;}a.bshareDiv{overflow:hidden;height:16px;line-height:18px;font-size:14px;color:#333;padding-left:0;}a.bshareDiv:hover{text-decoration:none;}div.bsTitle{padding:0 8px;border-bottom:1px solid #e8e8e8;color:#666;background:#f2f2f2;text-align:left;}div.buzzButton{cursor:pointer;}div.bsRlogo,div.bsRlogoSel{width:68px;float:left;margin:0;padding:2px 0;}div.bsRlogo a,div.bsRlogoSel a{float:left;}div.bsLogo,div.bsLogoSel{float:left;width:111px;text-align:left;height:auto;padding:2px 4px;margin:2px 0;white-space:nowrap;overflow:hidden;}div.bsLogoSel,div.bsRlogoSel{border:1px solid #ddd;background:#f1f1f1;}div.bsLogo,div.bsRlogo{border:1px solid #fff;background:#fff;}div.bsLogo a,div.bsLogoSel a{display:block;height:16px;line-height:16px;padding:0 0 0 24px;text-decoration:none;float:left;overflow:hidden;}div.bsLogoSel a,div.bsRlogoSel a{color:#000;border:none;}div.bsLogo a,div.bsRlogo a{color:#666;border:none;}div.bsLogoLink{width:121px;overflow:hidden;background:#FFF;float:left;margin:3px 0;}#bsPanel{position:absolute;z-index:100000000;font-size:12px;width:258px;background:url(http://static.bshare.cn/frame/images/background-opaque-dark.png);padding:6px;-moz-border-radius:5px;-webkit-border-radius:5px;border-radius:5px;}div.bsClear{clear:both;height:0;line-height:0;font-size:0;overflow:hidden;}div.bsPopupAwd{background: url(http://static.bshare.cn/frame/images//bshare_box_sprite2.gif) no-repeat top left;background-position:0 -624px;width:18px;padding-left:3px;text-align:center;float:left;margin-left:2px;height:15px;font-size:12px;color:#fff;overflow:hidden;}div.bsRlogo .bsPopupAwd,div.bsRlogoSel .bsPopupAwd{float:left;margin:5px 0 0 -14px;}</style></head>
<body><img src="http://afptrack.alimama.com/opt?bid=0ab74121000057285f712efb019fdfe6&amp;pid=mm_113716014_12970037_52772462&amp;cid=1505&amp;mid=2919&amp;oid=275&amp;productType=1&amp;cb=215087889" style="display: none;"><img src="http://afptrack.alimama.com/imp?bid=0ab74121000057285f712efb019fdfe6&amp;pid=mm_113716014_12970037_52772462&amp;cid=1505&amp;mid=2919&amp;oid=275&amp;productType=1&amp;e=h5ph3Ar8rtmsjluw4xAyS1QowhUDb8kEOg7jWnKuP5d2VeXfOmxTHeF9G8O%2BDM4U&amp;k=65&amp;cb=416453951" style="display: none;"><img src="http://afptrack.csbew.com/opt?bid=0a67349c000057285f70105704ee5b33&amp;pid=mm_113716014_12970037_52772602&amp;cid=2482&amp;mid=3264&amp;oid=376&amp;productType=1&amp;cb=926787354" style="display: none;"><img src="http://afptrack.csbew.com/imp?bid=0a67349c000057285f70105704ee5b33&amp;pid=mm_113716014_12970037_52772602&amp;cid=2482&amp;mid=3264&amp;oid=376&amp;productType=1&amp;e=ME1rhOOdKyqMpq0A4M5XOy9Fsvytu%2FqkwV4ppYXa9JHv4VC5ZdHFOy%2BeulKuEBd4&amp;k=65&amp;cb=823307585" style="display: none;"><img src="http://afptrack.csbew.com/opt?bid=0ab74121000057285f702ef101a0c816&amp;pid=mm_113716014_12970037_52772603&amp;cid=2406&amp;mid=3257&amp;oid=187&amp;productType=1&amp;cb=49188037" style="display: none;"><img src="http://afptrack.csbew.com/imp?bid=0ab74121000057285f702ef101a0c816&amp;pid=mm_113716014_12970037_52772603&amp;cid=2406&amp;mid=3257&amp;oid=187&amp;productType=1&amp;e=1H10OvbDTHusjluw4xAyS1QowhUDb8kErO63jeMzNGrutKtr18jOjk2%2F8aVxs1Nd&amp;k=65&amp;cb=669381446" style="display: none;"><img src="http://afptrack.csbew.com/opt?bid=0a67349c000057285f70104f04ef0807&amp;pid=mm_113716014_12970037_52772596&amp;cid=2485&amp;mid=3274&amp;oid=376&amp;productType=1&amp;cb=385275225" style="display: none;"><img src="http://afptrack.csbew.com/imp?bid=0a67349c000057285f70104f04ef0807&amp;pid=mm_113716014_12970037_52772596&amp;cid=2485&amp;mid=3274&amp;oid=376&amp;productType=1&amp;e=iGn5b7L1772Mpq0A4M5XOy9Fsvytu%2FqkwV4ppYXa9JHlCwi2dBruXh5ratQhwKRD&amp;k=65&amp;cb=359020082" style="display: none;"><iframe src="http://s.csbew.com/acookie.html" style="width: 0px; height: 0px; display: none;"></iframe>
<div class="noMobile">
	<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
	<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE7">

	<meta name="msapplication-navbutton-color" content="#d40004">
	<meta content="name=光明日报;action-uri=http://epaper.gmw.cn/gmrb/;icon-uri=http://img.gmw.cn/ico/paper.ico" name="msapplication-task">
	<meta content="name=时评;action-uri=http://guancha.gmw.cn/;icon-uri=http://img.gmw.cn/ico/guancha.ico" name="msapplication-task">
	<meta content="name=科技探索;action-uri=http://tech.gmw.cn/;icon-uri=http://img.gmw.cn/ico/tech.ico" name="msapplication-task">
	<meta content="name=文化娱乐;action-uri=http://culture.gmw.cn/;icon-uri=http://img.gmw.cn/ico/e.ico" name="msapplication-task">

	<link rel="stylesheet" type="text/css" href="http://img.gmw.cn/css/jquery.mbox.css" media="all">
	<link rel="stylesheet" type="text/css" href="http://img.gmw.cn/css/public_gmw.css?fan" media="all">
	<script type="text/javascript" src="http://img.gmw.cn/js/jquery.js"></script>
	<script type="text/javascript" src="http://img.gmw.cn/js/jquery.contentTab.js"></script>
	<script src="http://img.gmw.cn/js/jquery.mbox.js"></script>
	<script src="http://img.gmw.cn/js/eggshell.js"></script>

	<!--[if IE 6]>
	<script type="text/javascript" src="http://img.gmw.cn/js/ie6png.js" ></script>
	<script type="text/javascript">DD_belatedPNG.fix('#GMWlogo,#Larrow,#Rarrow');   </script>
	<![endif]-->
	<style type="text/css">
	*{font-family:"微软雅黑"}
	#channelHead{ width:100%; background:#f1f1f1; border-bottom:1px #999 solid;}
	.headtopNav{ width:1000px; margin:0 auto; padding:4px 0; height:24px; line-height:24px; _padding-bottom:0;}
	.headtopNav span{ margin:0 5px;color:#bb2737;}
	.channeLogin{float:left; height:24px; line-height:24px;text-align: right;width: 550px;}
	.headLogin{ width:80px; height:18px; border:1px #ccc solid;}
	.headSubLog{ width:50px; height:24px; margin-right:4px;}
	.whereGo li{ width:100px; height:24px; background:#fff; border:1px #999 solid; float:right; text-align:center; list-style:none; cursor:pointer;}
	.whereGo{ margin-right:9px;}
	.whereGo li a{ font-size:12px; color:#000; line-height:24px;}
	.whereGo li ul{ display:none;}
	.whereGo li ul li{ border-top:none; position:relative; z-index:2; left:1px; top:1px; background:#f2f2f2;}
	.whereGo li ul a:hover li{ background:#bb2737; color:#fff;}
	.whereGo li:hover ul{ display:block;}
	.navBg{ width:100%; background:#fff;}
	.channelNav{ width:1000px; text-align:center; margin:0 auto; clear:both; height:24px; line-height:24px; position:relative; z-index:1; padding-top:6px; background:#fff;}
	.channelNav li{ padding:0 9px; list-style:none; float:left; border-right:1px #ccc solid; font-size:12px; color:#000; line-height:14px;}
	.channelNav li a{ color:#000;}
	.channelNav li a:hover{ color:#bb2737;}
	.lightgrey12{ font-size:12px; color:#ccc;}
	#back_top{ display:none;}
	.footLine{ width:1000px; margin:0 auto; height:0; font-size:0; border-bottom:1px #999 solid;}
	</style>
	<div id="back_top">
	<a><span>回到顶部</span></a>
	</div>
	<div class="banner1000" id="banner_top"></div>
	<div class="banner1000" id="banner_top2"></div>
	<div id="channelHead">
		<div class="grey12_3 headtopNav">
			<div style="width:320px; float:left;">
               <a title="光明网" href="http://www.gmw.cn/"><img id="GMWlogo" src="http://img.gmw.cn/pic/Logo.png" style="float:left; padding-top:2px;" alt="光明网"></a>
                <span></span>
                <span><a href="http://www.gmw.cn/" style="color:#bb2737;">简体版</a></span>
                <span>|</span>
                <span><a href="http://chinese.gmw.cn/" style="color:#bb2737;">海外版</a></span>
                <span>|</span>
                <span><a href="http://en.gmw.cn/" style="color:#bb2737;">English</a></span>
                <span>|</span>
                <span><a href="http://guancha.gmw.cn/2012-04/27/content_4048222.htm" style="color:#bb2737;">投稿</a></span>
            </div>
			<div class="channeLogin" id="loginbar_new"><input class="headSubLog" type="submit" value="登录" onclick="gotoLogin('http://news.gmw.cn/2016-04/14/content_19695837.htm')"><input class="headSubLog" name="login" type="button" value="注册" onclick="document.location.href='http://home.gmw.cn/register.php?callback=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm'"></div>
			<ul class="whereGo">
				<li><a href="http://home.gmw.cn/">您想去哪里？</a>
					<ul class="wgse">
						<a href="http://pic.gmw.cn/"><li>光明图片</li></a>
						<a href="http://guancha.gmw.cn/2012-04/27/content_4048222.htm"><li>我要投稿</li></a>
						<a href="http://training.gmw.cn/"><li>光明培训</li></a>
					</ul>
				</li>
			</ul>
		</div>
		<div class="clear"></div>
	</div>
	<div class="navBg">
		<div class="channelNav">
			<li><a href="http://politics.gmw.cn/">时政</a></li><li><a href="http://world.gmw.cn/">国际</a></li><li><a href="http://guancha.gmw.cn/">时评</a></li><li><a href="http://theory.gmw.cn/">理论</a></li><li><a href="http://culture.gmw.cn/">文化</a></li><li><a href="http://tech.gmw.cn/">科技</a></li><li><a href="http://edu.gmw.cn/">教育</a></li><li><a href="http://economy.gmw.cn/">经济</a></li><li><a href="http://life.gmw.cn/">生活</a></li><li><a href="http://legal.gmw.cn/">法治</a></li><li><a href="http://mil.gmw.cn/">军事</a></li><li><a href="http://health.gmw.cn/">卫生</a></li><li><a href="http://yangsheng.gmw.cn/">养生</a></li><li><a href="http://lady.gmw.cn/">女人</a></li><li><a href="http://e.gmw.cn/">娱乐</a></li><li><a href="http://v.gmw.cn/">电视</a></li><li><a href="http://photo.gmw.cn">图片</a></li><li><a href="http://blog.gmw.cn/">博客</a></li><li><a href="http://bbs.gmw.cn/">论坛</a></li><li><a href="http://qp.gmw.cn/?from=publicdh">棋牌</a></li><li><a href="http://epaper.gmw.cn/">光明报系</a></li><li style="border:none;"><a href="http://www.gmw.cn/map.htm">更多&gt;&gt;</a></li>
		</div>
	</div>
</div>
<div class="noMobile">
	<link rel="stylesheet" type="text/css" href="http://img.gmw.cn/css/public_gmw.css">
	<div class="banner1000" id="banner_top_index"></div>
	<div class="banner1000" id="banner_top02"></div>
	<div class="banner1000" id="banner"></div>
	<div class="banner1000" id="bannertop1000"></div>
	<div class="clear"></div>
</div>

<div class="contentWrapper">
  <div class="contentLeft">
    <div id="contentBreadcrumbs2" class="black12">
      <a href="../../node_4108.htm"><img src="http://img.gmw.cn/pic/contentlogo/4108.gif" id="ArticleChannelID"></a><a href="http://www.gmw.cn/" target="_blank">首页</a><font class="">&gt; </font><a href="../../node_4108.htm" target="_blank" class="">光明日报</a>
    </div>
    <div id="articlePreTitle">

    </div>
    <h1 id="articleTitle">
      生态补偿探索候鸟保护新机制 让候鸟平安返乡
    </h1>
    <div id="articleSubtitle">

    </div>
    <div id="contentMsg">
      <span id="pubTime">2016-04-14 05:49</span>　<span id="source">来源：<a href="http://epaper.gmw.cn/gmrb/html/2016-04/14/nw.D110000gmrb_20160414_1-04.htm" target="_blank">光明网-《光明日报》</a></span>　<span id="author"></span><span><a href="#commentAnchor" style="color:#f33">我有话说</a></span></div>
	<div class="noMobile"><meta content="text/html; charset=utf-8" http-equiv="Content-Type"></div>
    <div id="contentMain">
      <!--enpproperty <articleid>19695837</articleid><date>2016-04-14 05:49:42.0</date><author></author><title>生态补偿探索候鸟保护新机制 让候鸟平安返乡(1)_光明日报
_光明网</title><keyword>候鸟</keyword><subtitle></subtitle><introtitle></introtitle><siteid>2</siteid><nodeid>4108</nodeid><nodename>光明日报</nodename><nodesearchname>光明日报</nodesearchname>/enpproperty--><!--enpcontent--><!--enpcontent--><p>　　<strong><font color="#993300">【多彩神州·春天的故事】</font></strong></p>
<p>　　眼下，我国北方地区天气回暖，又进入到候鸟迁徙的季节，在年复一年的南来北往中，它们既要承受来自自然界的生存考验，又要面临人类活动带来的侵扰——湿地退化，人鸟争粮，以观赏之名的打搅，甚至是无情捕杀……</p>
<p>　　野生鸟类尤其是候鸟对栖息环境质量的要求极高，因此成为国际公认的最能直观反映地区生态文明发展程度的标志。为了给候鸟营造一个安全的栖息环境，最大限度地排除人类活动的干扰，各地采取了很多强有力的保护措施。</p>
<p align="center"><img id="33351074" align="center" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160414/eca86bd9d822187903e728.jpg" title="生态补偿探索候鸟保护新机制 让候鸟平安返乡" alt="生态补偿探索候鸟保护新机制 让候鸟平安返乡"></p>
<p style="TEXT-ALIGN: center" align="center"><font color="blue">4月9日，众多候鸟在内蒙古克什克腾旗达里诺尔湖流域的湖畔栖息、飞翔。新华社发（孙国树摄）</font></p>
<p><strong>　<font color="#993300">　保护湿地，守护候鸟家园</font></strong></p>
<p>　　保护好原生态的湖泊、湿地，是给候鸟最好的“礼物”。近年来，不少地方通过立法保护湿地、退耕还林还湿、改善湿地水质等措施，优化候鸟的生存环境，为人类与这些“长着翅膀的朋友”和谐相处创造更好的条件。</p>
<p>　　辽宁法库县是著名的“白鹤之乡”，每年70%以上的白鹤东部种群都会在这里的獾子洞湿地停歇。湿地恢复工程成为法库县保护湿地的重头戏，目前法库县已完成宽10米、深1米的环湖沟7000余延长米的治理任务，预计到今年5月可完成11800米，包括河滩治理、植被恢复、疏浚清淤等全部工程将于8月完成。</p>
<p>　　湿地的恢复为候鸟提供了良好的休憩地。“上个月的一天早上，我们监测到的迁徙回来的白鹤已经有200多只了！”法库县旅游局局长杨秀玲兴奋地说。</p>
<p>　　云南昭通大山包自然保护区内分布着5958公顷高山沼泽化草甸湿地，是黑颈鹤等越冬水禽的重要栖息地。近年来，当地实施了移民搬迁、退耕还林、退耕还湿等多个保护恢复项目。目前，大山包国际重要湿地已被列入国家2014年湿地生态效益补偿试点，中央财政资金将对周边村民提供生态效益补偿，并进行村庄生态环境整治。</p>
<p>　　每年秋冬季，中科院昆明动物研究所研究员杨晓君的团队都会去大山包做观测。据他介绍，这几年到大山包越冬的黑颈鹤数量稳中有升，从1990年的200余只增加到2004年1月14日的1186只，“2014年11月28日更是曾经记录到1269只”。</p>
<!--/enpcontent--><div id="contentLiability">[责任编辑:徐皓]</div><div width="100%" id="displaypagenum"><p></p><center> <span class="pagefontcon">1</span> <a href="content_19695837_2.htm" class="pagefontcon">2</a> <a href="content_19695837_2.htm" class="ptfontcon">下一页</a> <a href="content_19695837_2.htm" class="ptfontcon">尾页</a> <span class="pagefontcon" style="background:#fff; color:#000;">共2页</span></center><p></p></div><div id="mpagecount" style="display:none">2</div><div id="mcurrentpage" style="display:none">1</div><!--/enpcontent-->
    </div>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<div class="noMobile">
	<div id="sc0001"></div>
	<!-- AFP两段式代码-公用代码 -->
	<script type="text/javascript" src="http://s.csbew.com/k.js"></script>
	<!-- 92477：全部频道通投-文章页底部（新） 类型：固定广告位 尺寸：650x200-->
	<ins id="ac_js86_92477" style="display: none;"></ins><script type="text/javascript">
		_acK({aid:92477,format:0,mode:1,gid:1,destid:"sc0001",serverbaseurl:"afp.csbew.com/"});
	</script><script type="text/javascript">
ac_as_id = 92477;
window.afp_cur_query="?pv=1&sp=92477,1,0,0,0,1,1,21&ec=UTF-8&re=1280,800&jsv=7&cb=2921973207&seq=1&fs=2";ac_format = 0;
ac_mode = 1;
window.__trans__92477 = true;
ac_group_id = 1;
ac_server_base_url = "afpeng.csbew.com/";
</script>
<script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/k.js"></script><script type="text/javascript" src="http://afpeng.csbew.com/ex?a=92477&amp;sp=1&amp;cb=_acM.r&amp;u=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;ds=1280x800&amp;_=1462263663389&amp;fs=3&amp;pvid=bf69933c8f25e482eaaa0fdda3feada2&amp;cg=ffac751766d63d5a572cd9b6e30a2bf5&amp;from_csbew=1" id="ac_js86_$8030840675"></script>

	<div class="contentColumnLeft" style="margin:20px 0;">
		<table width="100%" border="0" cellspacing="0" cellpadding="0">
			<tbody><tr>
				<td width="210" align="left">
					<!-- 关注新浪微博
					<iframe src="http://widget.weibo.com/relationship/followbutton.php?btn=red&style=3&uid=1752825395&width=100%&height=22&language=zh_cn" width="100%" height="22" frameborder="0" scrolling="no" marginheight="0"></iframe>-->
				</td>
				<td width="120" align="left"><!-- 关注QQ空间
					<iframe src="http://open.qzone.qq.com/like?url=http%3A%2F%2Fuser.qzone.qq.com%2F2232833389&type=button_num&width=120&height=22&style=2" allowtransparency="true" scrolling="no" border="0" frameborder="0" style="width:120px;height:22px;border:none;overflow:hidden; text-align:right;vertical-align:middle;"></iframe>-->
				</td>
				<td align="right">
					<div class="bshare-custom"><div class="bsPromo bsPromo2"></div>
						<a title="分享到QQ空间" class="bshare-qzone" href="javascript:;"></a>
						<a title="分享到新浪微博" class="bshare-sinaminiblog" href="javascript:;"></a>
						<a title="分享到微信" class="bshare-weixin" href="javascript:;"></a>
						<span class="BSHARE_COUNT bshare-share-count" style="float: none;">2</span>
						<a title="更多平台" class="bshare-more bshare-more-icon" href="javascript:;"></a>
					</div>
					<script language="javascript" type="text/javascript" src="http://static.bshare.cn/b/buttonLite.js#style=-1&amp;uuid=fbe7b28e-050d-4ab3-9af4-0740ed16ea11&amp;pophcol=2&amp;lang=zh"></script>
					<script language="javascript" type="text/javascript" src="http://static.bshare.cn/b/bshareC1.js"></script>
				</td>
			</tr>
		</tbody></table>
	</div>
</div>
	<div class="contentColumnLeft contentRelatedArea">
      <!-- 相关报道 -->

	  <!-- baidu  ����ϲ��-->
<div class="contentColumnLeft contentRelatedArea noMobile">
    <script>document.write(unescape('%3Cdiv id="hm_t_90610"%3E%3C/div%3E%3Cscript charset="utf-8" src="http://crs.baidu.com/t.js?siteId=0b2007edc647fec486f98a9528a1e9cd&planId=90610&async=0&referer=') + encodeURIComponent(document.referrer) + '&title=' + encodeURIComponent(document.title) + '&rnd=' + (+new Date) + unescape('"%3E%3C/script%3E'));</script><div id="hm_t_90610"><div style="display: block; margin: 0px; padding: 0px; float: none; clear: none; overflow: hidden; position: relative; border: 0px; max-width: none; max-height: none; border-radius: 0px; box-shadow: none; transition: none; text-align: left; box-sizing: content-box; width: 648px; height: 206px; background: none;"><div style="display: block; margin: 0px; padding: 0px; float: none; clear: none; overflow: hidden; position: relative; border: 0px; max-width: none; max-height: none; border-radius: 0px; box-shadow: none; transition: none; text-align: left; box-sizing: content-box; width: 100%; height: 100%; background: none;"></div></div></div><script charset="utf-8" src="http://crs.baidu.com/t.js?siteId=0b2007edc647fec486f98a9528a1e9cd&amp;planId=90610&amp;async=0&amp;referer=http%3A%2F%2Fnews.baidu.com%2Fns%3Fword%3D%25E7%2594%259F%25E6%2580%2581%25E8%25A1%25A5%25E5%2581%25BF%26pn%3D80%26cl%3D2%26ct%3D1%26tn%3Dnews%26rn%3D20%26ie%3Dutf-8%26bt%3D0%26et%3D0&amp;title=%E7%94%9F%E6%80%81%E8%A1%A5%E5%81%BF%E6%8E%A2%E7%B4%A2%E5%80%99%E9%B8%9F%E4%BF%9D%E6%8A%A4%E6%96%B0%E6%9C%BA%E5%88%B6%20%E8%AE%A9%E5%80%99%E9%B8%9F%E5%B9%B3%E5%AE%89%E8%BF%94%E4%B9%A1(1)_%E5%85%89%E6%98%8E%E6%97%A5%E6%8A%A5%20_%E5%85%89%E6%98%8E%E7%BD%91&amp;rnd=1462263663498"></script>
<div class="clear"></div>
</div>
    </div><!--<div id="PrevNextContent">上一篇下一篇</div>-->

    <a name="commentAnchor"></a>
<!--新闻表情 begin-->
<div id="motionsDiv"><a name="Mtns"></a><style>#mood *{margin:0;padding:0;text-align: center;font-size:12px;}#mood ul li a{color:#000; text-decoration:none;cursor:pointer;}#mood ul li a img{border:0;}#mood ul li,#mood ul li div.pillar{display:inline-block;display:-moz-inline-stack;zoom:1;*display:inline;}#mood ul li{vertical-align: bottom;display:inline-block;display:inline9;}#mood ul li{width:70px; padding-bottom:10px}#mood ul li div.pillar{width:70px; display:inline-block !important; height:0px; max-height:40px; line-height:0px; background:url(http://imghealth.gmw.cn/motions/mood.gif) repeat-y center; margin-bottom:5px;}#mood_title{background-color:#f0f0f0;height:26px;line-height:26px;}#mood_title div{margin:0 2em;font-size:14px;font-weight:bold;}#mood_tl{float:left;}#mood_tr{float:right;}.list_more{border-top:1px solid #fff;clear:both;overflow-:hidden;padding-bottom:8px; margin:0 auto; width:94%;}.list_more a{-webkit-border-radius:10px;-moz-border-radius:10px;border-radius:10px;display:block;text-align:center;border:1px solid #eae9e9;height:30px;line-height:30px;font-size:15px;background-color:#e6e6e6;background-image:-webkit-gradient(linear,left top,left bottom,from(#f3f3f3),to(#e6e6e6));background-image:-webkit-linear-gradient(top,#f3f3f3,#e6e6e6);background-image:-moz-linear-gradient(top,#f3f3f3,#e6e6e6);background-image:-ms-linear-gradient(top,#f3f3f3,#e6e6e6);background-image:-o-linear-gradient(top,#f3f3f3,#e6e6e6);background-image:linear-gradient(top,#f3f3f3,#e6e6e6);filter:progid:DXImageTransform.Microsoft.gradient(startColorStr="#f3f3f3",EndColorStr="#e6e6e6"); color:#9b9b9b; text-shadow:1px 1px 1px #fff; font-weight:bold; -moz-box-shadow:1px 1px 1px #999; -webkit-box-shadow:1px 1px 1px #999; box-shadow:1px 1px 1px #999;}.list_more a:hover{ color:#0095EF; text-decoration:none;}</style><div id="mood"><div id="mood_title"><div id="mood_tl">您此时的心情</div><div id="mood_tr">新闻表情排行 <a href="http://www.gmw.cn/motionsdaytop.htm" target="_blank">日</a>/<a href="http://www.gmw.cn/motionsweektop.htm" target="_blank">周</a></div></div><div style="clear:both;"></div><ul><li><p id="hits_1">0</p><div id="zhu_1" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(1);"><img src="http://imgp.gmw.cn/motionsimg/0/m1.gif"><p>开心</p></a></li><li><p id="hits_2">0</p><div id="zhu_2" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(2);"><img src="http://imgp.gmw.cn/motionsimg/0/m2.gif"><p>板砖</p></a></li><li><p id="hits_3">0</p><div id="zhu_3" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(3);"><img src="http://imgp.gmw.cn/motionsimg/0/m3.gif"><p>感动</p></a></li><li><p id="hits_4">3</p><div id="zhu_4" style="height:40px; line-height:40px;" class="pillar">&nbsp;</div><a onclick="getMotions(4);"><img src="http://imgp.gmw.cn/motionsimg/0/m4.gif"><p>撒花</p></a></li><li><p id="hits_5">0</p><div id="zhu_5" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(5);"><img src="http://imgp.gmw.cn/motionsimg/0/m5.gif"><p>怀疑</p></a></li><li><p id="hits_6">1</p><div id="zhu_6" style="height:14px; line-height:14px;" class="pillar">&nbsp;</div><a onclick="getMotions(6);"><img src="http://imgp.gmw.cn/motionsimg/0/m6.gif"><p>难过</p></a></li><li><p id="hits_7">0</p><div id="zhu_7" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(7);"><img src="http://imgp.gmw.cn/motionsimg/0/m7.gif"><p>无聊</p></a></li><li><p id="hits_8">0</p><div id="zhu_8" style="height:0px; line-height:0px;" class="pillar">&nbsp;</div><a onclick="getMotions(8);"><img src="http://imgp.gmw.cn/motionsimg/0/m8.gif"><p>震惊</p></a></li></ul></div></div>
<script>
    var M_contentId = $("META[name=contentid]").attr("content");
    (function() {
        var mojs1 = document.createElement('script');
        mojs1.type = 'text/javascript';
        mojs1.async = true;
        mojs1.src = 'http://motions.gmw.cn/show/'+M_contentId;
        var smo1 = document.getElementsByTagName('script')[0];
        smo1.parentNode.insertBefore(mojs1, smo1);
    })();
</script>
<!--新闻表情 end-->
<!-- 20151113 豆子游戏 begin -->
<div class="noMobile" style="margin:10px 0;">
<!-- 112417：通发-内-底部表情下-豆子 类型：固定广告位 尺寸：650x90-->
<span style="overflow: visible; position: relative; display: block; width: 650px; height: 90px; border: 0px; text-align: left; background: none;"><span style="overflow: hidden; position: absolute; display: block; width: 650px; height: 90px; border: 0px; text-align: left; background: none;"><span style="overflow: hidden; position: absolute; display: block; width: 650px; height: 90px; border: 0px; text-align: left; background: none;"><a href="http://afptrack.csbew.com/clk?bid=0a67349c000057285f70104f04ef0807&amp;pid=mm_113716014_12970037_52772596&amp;cid=2485&amp;mid=3274&amp;oid=376&amp;productType=1&amp;target=http%3A%2F%2Fqp.gmw.cn%2Fgmw%2Findex_contentcenter.do" target="_blank" style="position: absolute; display: block; top: 0px; left: 0px; margin: 0px; padding: 0px; width: 650px; height: 90px; text-decoration: none; opacity: 0; z-index: 1; cursor: pointer; background: rgb(255, 255, 255);"></a><img id="ac_cs_112417_1" border="0" src="http://afp.alicdn.com/afp-creative/creative/u113716014/eff5dfa1162572534f37bf33ae5ac665.jpg" style="width: 650px; height: 90px;"></span></span></span><ins id="ac_js86_112417" style="display: none;"></ins><script type="text/javascript">
_acK({aid:112417,format:0,mode:1,gid:1,serverbaseurl:"afp.csbew.com/"});
</script><script type="text/javascript">
ac_as_id = 112417;
window.afp_cur_query="?pv=1&sp=112417,1,0,0,0,1,1,21&ec=UTF-8&re=1280,800&jsv=7&cb=1848368335&seq=2&fs=3";ac_format = 0;
ac_mode = 1;
window.__trans__112417 = true;
ac_group_id = 1;
ac_server_base_url = "afpeng.csbew.com/";
</script>
<script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/k.js"></script><script></script><script type="text/javascript" src="http://afpeng.csbew.com/ex?a=112417&amp;sp=1&amp;cb=_acM.r&amp;u=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;ds=1280x800&amp;_=1462263664413&amp;fs=3&amp;pvid=a73d52f73c2a5360f3ffd5d091c82d1a&amp;cg=ae6e010c57a535ccaaa9d56cd0d76a4f&amp;from_csbew=1" id="ac_js86_$617211619"></script>

</div>
<!-- 20151113 豆子游戏 end -->
<!--畅言高速版 begin-->
<div class="contentColumnLeft"><div id="SOHUCS" sid="19695837"><div id="SOHU_MAIN"><div class="module-cmt-header">
    <div class="clear-g section-title-w">
        <div class="title-join-w">
            <div node-type="join-wrap" class="join-wrap-w">
                <a href="javascript:;">
                    <strong class="wrap-name-w">评论</strong><span class="wrap-join-w">(<span node-type="participation-wrapper"><em node-type="participation-number" class="join-strong-gw">0</em>人参与<i class="gap-b">，</i></span><em node-type="comment-number" class="join-strong-gw">0</em>条评论)</span>
                </a>
            </div>
        </div>
        <div class="title-user-w">
            <div node-type="user" class="clear-g user-wrap-w">
                <span node-type="user-name" class="wrap-name-w"></span><span class="wrap-icon-w"></span>
                <div class="wrap-menu-w">
                    <div class="menu-box-w">
                        <a href="javascript:void(0);" node-type="my-changyan"><i class="gap-w">我的畅言</i></a>
                        <a node-type="logout" href="javascript:;">
                            <i class="gap-w">退出</i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="section-cbox-w">
        <div class="cbox-block-w clear-g">
            <div class="block-head-w" node-type="avatar">
                <div class="head-img-w">
                    <a href="javascript:void(0);">
                        <img node-type="user-head" src="http://changyan.sohu.com/upload/asset/scs/images/pic/pic42_null.gif" width="42" height="42" alt="">
                    </a>
                </div>
            </div>
            <div node-type="login-select" class="block-post-w">
                <!-- 放置cbox初始状态 -->
                <div class="module-cmt-box">
    <!-- 展开状态 -->
    <div class="post-wrap-w">
        <div class="wrap-area-w">
            <div class="area-textarea-w">
                <textarea node-type="textarea" name="" class="textarea-fw textarea-bf">有事没事说两句...</textarea>
            </div>
        </div>
        <div class="clear-g wrap-action-w">
            <div class="action-function-w">
                <ul class="clear-g">
                    <li node-type="function-face" class="function-face-w">
                        <a class="effect-w" href="javascript:void(0)">
                            <i class="face-b"></i>
                        </a>
                    </li>
                    <li node-type="function-uploading" class="function-uploading-w" style="display: none; position: relative;">
                <span style="position: absolute; top: 0; left: 0; height: 39px; width: 40px; overflow: hidden; opacity: 0.1; filter:alpha(opacity=10);">
                    <object id="SWFUpload_0" type="application/x-shockwave-flash" data="http://changyan.itc.cn/mdevp/extensions/cui/002/swfupload.v2.2.0/swfupload.swf" width="40" height="39" class="swfupload"><param name="wmode" value="transparent"><param name="movie" value="http://changyan.itc.cn/mdevp/extensions/cui/002/swfupload.v2.2.0/swfupload.swf"><param name="quality" value="high"><param name="menu" value="false"><param name="allowScriptAccess" value="always"><param name="flashvars" value="movieName=SWFUpload_0&amp;uploadURL=http%3A%2F%2Fchangyan.sohu.com%2Fapi%2F2%2Fcomment%2Fattachment&amp;useQueryString=false&amp;requeueOnError=false&amp;httpSuccess=&amp;assumeSuccessTimeout=0&amp;params=&amp;filePostName=file&amp;fileTypes=*.jpg%3B*.png%3B*.gif%3B*.jpeg&amp;fileTypesDescription=All%20Files&amp;fileSizeLimit=2%20MB&amp;fileUploadLimit=0&amp;fileQueueLimit=0&amp;debugEnabled=false&amp;buttonImageURL=http%3A%2F%2Fchangyan.itc.cn%2Fmdevp%2Fextensions%2Fcui%2F002%2Fswfupload.v2.2.0%2Fswfupload.js%3Fbutton_image_url&amp;buttonWidth=40&amp;buttonHeight=39&amp;buttonText=&amp;buttonTextTopPadding=0&amp;buttonTextLeftPadding=0&amp;buttonTextStyle=color%3A%20%23000000%3B%20font-size%3A%2016pt%3B&amp;buttonAction=-110&amp;buttonDisabled=false&amp;buttonCursor=-2"></object>
                </span>

                        <a class="effect-w" href="javascript:void(0)" title="上传图片">
                            <i class="uploading-b"></i>
                        </a>
                        <div class="uploading-file-w">
                            <a href="javascript:void(0);" name="" class="file-fw"></a>
                        </div>
                    </li>
                </ul>
                <!-- 表情 -->
                <div node-type="face-box" class="face-wrapper-dw">
                    <div node-type="face-cont" class="wrapper-cont-dw">
                        <ul class="clear-g">
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/流汗"><img title="流汗" alt="流汗" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_01.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/钱"><img title="钱" alt="钱" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_02.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/发怒"><img title="发怒" alt="发怒" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_03.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/浮云"><img title="浮云" alt="浮云" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_04.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/给力"><img title="给力" alt="给力" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_05.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/大哭"><img title="大哭" alt="大哭" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_06.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/憨笑"><img title="憨笑" alt="憨笑" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_07.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/色"><img title="色" alt="色" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_08.gif"></a>
                            </li>
                        </ul>
                        <ul class="clear-g">
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/奋斗"><img title="奋斗" alt="奋斗" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_09.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/鼓掌"><img title="鼓掌" alt="鼓掌" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_10.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/鄙视"><img title="鄙视" alt="鄙视" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_11.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/可爱"><img title="可爱" alt="可爱" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_12.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/闭嘴"><img title="闭嘴" alt="闭嘴" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_13.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/疑问"><img title="疑问" alt="疑问" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_14.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/抓狂"><img title="抓狂" alt="抓狂" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_15.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/惊讶"><img title="惊讶" alt="惊讶" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_16.gif"></a>
                            </li>
                        </ul>
                        <ul class="clear-g">
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/可怜"><img title="可怜" alt="可怜" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_17.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/弱"><img title="弱" alt="弱" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_18.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/强"><img title="强" alt="强" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_19.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/握手"><img title="握手" alt="握手" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_20.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/拳头"><img title="拳头" alt="拳头" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_21.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/酒"><img title="酒" alt="酒" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_22.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/玫瑰"><img title="玫瑰" alt="玫瑰" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_23.gif"></a>
                            </li>
                            <li>
                                <a href="javascript:void(0);" data_path="base" data-ubb="/打酱油"><img title="打酱油" alt="打酱油" src="http://changyan.itc.cn/mdevp/extensions/new-face/001/new_face_24.gif"></a>
                            </li>
                        </ul>
                    </div>
                </div>
                <!--  上传图片 --><!--  uploading-efw -->
                <div node-type="uploading-wrapper" class="uploading-wrapper-dw uploading-efw ">
                    <div node-type="image-uploading" class="wrapper-loading-dw">
                        <div class="loading-word-dw"><span class="word-icon-dw"></span>图片正在上传，请稍后...</div>
                        <div class="loading-btn-dw">
                            <a href="javascript:void(0)">取消上传</a>
                        </div>
                    </div>
                    <div node-type="image-uploaded" class="wrapper-image-dw">
                        <div class="image-close-dw">
                            <a href="javascript:void(0)"></a>
                        </div>
                        <div class="image-pic-dw">
                            <img node-type="image-pic" alt="" src="">
                        </div>
                    </div>
                </div>
            </div>
            <div class="clear-g action-issue-w">
                <div class="issue-btn-w">
                    <a href="javascript:void(0)">
                        <button node-type="issue" class="btn-fw">发布</button>
                    </a>
                </div>
                <div class="issue-icon-w" node-type="share-icons">
                </div>
            </div>
        </div>
    </div>
    <div class="cbox-prompt-w" node-type="error-tips">
        <span node-type="prompt-empty" class="prompt-empty-w">未输入评论内容</span>
    </div>
</div>
                <!-- 放置cbox发布状态 -->
                <!-- 用户登录 -->

                <div node-type="login-btn" class="post-login-w clear-g">
                    <ul class="clear-g">

                            <li>
                                <div label="" class="login-wrap-w login-wrap-other-w">
                                    <a class="global-clear-spacing" href="javascript:;">
                                        <span class="wrap-icon-w icon30-other-w" style="background: url(http://0d077ef9e74d8.cdn.sohucs.com/97075b09bc8da2c6efe5649a72a8c43f_logo_1461659035475_jpg)"></span>
                                        <span class="wrap-name-w">登录</span>
                                    </a>
                                </div>
                            </li>





                                <li>
                                    <div label="weibo" class="login-wrap-w">
                                        <a class="global-clear-spacing" href="javascript:;">
                                            <span class="wrap-icon-w icon30-sina-w"></span>
                                            <span class="wrap-name-w">微博登录</span>
                                        </a>
                                    </div>
                                </li>







                                <li>
                                    <div label="qq" class="login-wrap-w">
                                        <a class="global-clear-spacing" href="javascript:;">
                                            <span class="wrap-icon-w icon30-qq-w"></span>
                                            <span class="wrap-name-w">QQ登录</span>
                                        </a>
                                    </div>
                                </li>



                                <li>
                                    <div label="phone" class="login-wrap-w">
                                        <a class="global-clear-spacing" href="javascript:;">
                                            <span class="wrap-icon-w icon30-phone-w"></span>
                                            <span class="wrap-name-w">手机登录</span>
                                        </a>
                                    </div>
                                </li>





                    </ul>
                </div>
                                <!-- 提示条 -->
                <!-- 零评论提示条 -->
                <div class="list-comment-empty-w">
                    <div node-type="empty-prompt" class="empty-prompt-w">
                        <span class="prompt-null-w">还没有评论，快来抢沙发吧！</span>
                    </div>
                </div>
                <!--关闭评论-->
                <div class="list-close-comment-w">

                </div>
            </div>
        </div>
    </div>
</div><!-- 评论列表  S -->
<div class="module-cmt-list section-list-w">
        <!-- 最新评论 -->
    <div class="list-block-gw list-newest-w">
        <div node-type="cmt-list-title" class="block-title-gw" style="display: none;">
            <ul class="clear-g">
                <li><strong class="title-name-gw title-name-bg">最新评论</strong></li>
            </ul>
        </div>
        <div node-type="cmt-list"></div>
    </div>
</div>
<!-- 评论列表  E --><div class="module-cmt-footer">
    <!-- 评论关闭 -->
    <div class="list-comment-close-w">
        <div class="close-wrap-w close-wrap-b">该评论已关闭!</div>
    </div>
    <!-- 翻页 -->
    <div class="section-page-w" style="display: none;">
        <span node-type="page-wrapper" class="page-wrap-gw page-wrap-w">

</span>
    </div><div class="more-comment">

    <a href="http://changyan.sohu.com/admin/jump?topic_id=1167097790&amp;client_id=cyr45LmB4&amp;default_url=http://bbs.gmw.cn/&amp;bbs_url=http://bbs.gmw.cn/thread-{tid}-1-1.html" target="_blank">
        已有<em class="wrap-strong-w wrap-strong-b">0</em>人参与，点击查看更多精彩评论&gt;&gt;
    </a>
    </div>
    <!-- 某站正在使用畅言 -->
    <div class="section-service-w">
        <div class="service-wrap-w">
            <a href="http://changyan.kuaizhan.com/" target="_blank">

            光明网正在使用畅言
                                                            </a>
        </div>
    </div>
</div><div class="module-cmt-float-bar">
    <div class="module-cmt-float-bar-body" style="bottom: 0;">
        <div class="close-w"><a node-type="close" href="javascript:void(0)">关闭</a></div>
        <div class="wrap-cont-w">
            <!-- 评论 Begin -->
            <div class="cont-minwidth-w">
                <div class="cont-comment-w">
                    <span class="comment-text-w" style="display:  block ">立刻说两句吧！</span>
                    <a class="comment-link-w" href="javascript:void(0)" style="display:  none ">查看<i>0</i>条评论</a>
                </div>
                <div class="cont-form-w">
                    <div node-type="post-form" class="form-text-w">
                        <span class="btn-load-bf"></span>
                        <a class="button-w" href="javascript:void(0)">按钮</a>
                        <input type="text" value="来说两句吧..." class="text-w" data-default="来说两句吧...">
                    </div>
                </div>
            </div>
            <!-- 评论 End -->
            <!-- 登录 Begin -->
            <div class="cont-login-w">
                <div class="fb-login-wrap-w" style=" display: none ">
                    <span node-type="fb-user-name" class="user-info" style="position: relative;">
                        <img src="">
                        <span>nickname</span>
                        <a class="floatbar-quit" href="javascript:void(0)">[退出]</a>
                    <div class="module-cmt-notice-bubble" style="display: none;">0</div></span>
                </div>
                <div class="fb-logout-wrap-w" style=" ">
                    <ul node-type="login-list" class="post-login-w">
                        <li class="first-w"><span>登录：</span></li>

                        <li>
                            <a node-type="login-way" data-key="sina" data-platform="2" class="icon-sina-w" href="javascript:void(0)"></a>
                        </li>

                        <li>
                            <a node-type="login-way" data-key="qq" data-platform="3" class="icon-qq-w" href="javascript:void(0)"></a>
                        </li>
                                            </ul>
                </div>
                <span node-type="share-btn" class="new-share">
    <!-- 分享浮窗 Begin -->
    <div node-type="share-list" class="func-select share-select" style="display: none;">
        <ul class="clear">
            <li><a data-key="renren" class="icon-renren-w" href="javascript:;" title="人人网"></a></li>
            <li><a data-key="qzone" class="icon-qzone-w" href="javascript:;" title="QQ空间"></a></li>
            <li><a data-key="weixin" class="icon-weixin-w" href="javascript:;" title="腾讯微信"></a></li>
            <li><a data-key="sina" class="icon-sina-w" href="javascript:;" title="新浪"></a></li>
        </ul>
        <div class="arrow"></div>
    </div>
    <!-- 分享浮窗 End   -->
    <!-- 分享浮窗-二维码 Begin -->
    <div node-type="weixin-code" class="qrcode" style="display: none;">
        <div class="qrcode-wrap">
            <!--<img src="about:blank" width="90" height="90" alt=""/>-->
            <div class="qrcode-img"></div>
            <div class="qrcode-close"><a href="javascript:;"></a></div>
        </div>
        <p class="qrcode-text">用微信扫描二维码即可分享此网页至好友和朋友圈</p>
    </div>
    <!-- 分享浮窗-二维码 End   -->
    <i class="ico"></i>分享
</span>
            </div>
            <!-- 登录 End -->
        </div>
    </div>
</div><div class="module-cmt-notice">
    <ul class="nt-list">

        <li node-type="notice-message" data-alias="message" data-type="message" data-static="static" class="nt-item" style=" display: none ">
            <a node-type="notice-content" class="nt-text" href="javascript:void(0);">你收到<i>0</i>条新通知</a>
            <a class="nt-close" href="javascript:void(0);"></a>
        </li>

        <li node-type="notice-support" data-alias="support" data-type="support" data-static="static" class="nt-item" style=" display: none ">
            <a node-type="notice-content" class="nt-text" href="javascript:void(0);">你有<i>0</i>条评论收到赞同</a>
            <a class="nt-close" href="javascript:void(0);"></a>
        </li>

        <li node-type="notice-reply" data-alias="reply" data-type="reply" data-static="static" class="nt-item" style=" display: none ">
            <a node-type="notice-content" class="nt-text" href="javascript:void(0);">你有<i>0</i>条新回复</a>
            <a class="nt-close" href="javascript:void(0);"></a>
        </li>

        <li node-type="notice-task" data-alias="task" data-type="task" data-static="static" class="nt-item" style=" display: none ">
            <a node-type="notice-content" class="nt-text" href="javascript:void(0);">你有<i>0</i>个任务已完成</a>
            <a class="nt-close" href="javascript:void(0);"></a>
        </li>
            </ul>
</div></div></div></div>
<style>#SOHUCS #SOHU_MAIN #SOHU-comment-main .section-cbox-w .post-login-w ul li .login-wrap-other-w a,.user-login-wrapper-dw .cont-login-dw ul li .login-wrap-other-w a{padding:0;width:117px;height:40px;background-image:url("http://img.gmw.cn/pic/img_117x40.jpg");background-repeat:no-repeat;background-position:0 0}#SOHUCS #SOHU_MAIN #SOHU-comment-main .section-cbox-w .post-login-w ul li .login-wrap-other-w a:hover,.user-login-wrapper-dw .cont-login-dw ul li .login-wrap-other-w a:hover{background-image:url("http://img.gmw.cn/pic/img_117x40_hover.jpg");background-repeat:no-repeat;background-position:0 0}#SOHUCS #SOHU_MAIN #SOHU-comment-main .section-cbox-w .post-login-w ul li .login-wrap-other-w span.wrap-icon-w,.user-login-wrapper-dw .cont-login-dw ul li .login-wrap-other-w span.wrap-icon-w{display:none}#SOHUCS #SOHU_MAIN #SOHU-comment-main .section-cbox-w .post-login-w ul li .login-wrap-other-w span.wrap-name-w,.user-login-wrapper-dw .cont-login-dw ul li .login-wrap-other-w span.wrap-name-w{display:none}#changyan_floatbar_wrapper #bottombar-wrap-w .wrap-cont-w .cont-login-w .logout-wrap-w ul li.login-wrap-w,#changyan_floatbar_wrapper #bottombar-wrap-w .wrap-cont-w .cont-login-w .logout-wrap-w ul li img{width:30px!important}</style>
<script>
    var content_source_id = M_contentId || $("META[name='contentid']").attr("content");
    $("#SOHUCS").attr("sid", content_source_id);
    (function(){
        document.domain = 'gmw.cn';
        var appid = 'cyr45LmB4',
        conf = 'prod_97075b09bc8da2c6efe5649a72a8c43f';
        var doc = document,
        s = doc.createElement('script'),
        h = doc.getElementsByTagName('head')[0] || doc.head || doc.documentElement;
        s.type = 'text/javascript';
        s.charset = 'utf-8';
        s.src =  'http://assets.changyan.sohu.com/upload/changyan.js?conf='+ conf +'&appid=' + appid;
        h.insertBefore(s,h.firstChild);
        window.SCS_NO_IFRAME = true;
    })();
    // 畅言登录
    function cy_login(){
        var cookie_name_cy=decodeURIComponent(getCookie('Example_auth_username'));
        if(cookie_name_cy.length>0 && cookie_name_cy != null){
            if(document.getElementById('loginbar_new')!=null){
                var if_loginbar_new = 1;
            }
            if(if_loginbar_new == 1){
                document.getElementById('loginbar_new').innerHTML="<div id='login'>"+cookie_name_cy+"&nbsp;&nbsp;您好!&nbsp;&nbsp;<a href='http://home.gmw.cn' style='color:#c00;' target='_blank'>用户统一登录平台</a>&nbsp;&nbsp;<a href='#' onclick=\"login_in();\" target='_self'>安全退出</a></div>";
            }
        }
    }
</script>
<!--畅言高速版 end-->
    <div class="noMobile"><meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<style type="text/css">
.contentPicTxt_left01{ padding:5px 0;}
.contentPicTxt_left01 img{ margin:5px 5px 0 0;}
/* 左侧排行*/
.rankLeft .contentTxtArea{ padding-top:20px;}
.rankLeft p{ display:block;margin:0; padding:0;clear:both;}
.rankLeft p span{ padding:3px;height:28px; line-height:28px;}
.rankLeft p span.r1,.rankLeft p span.r2{margin:0 5px 0 0; text-align:center; font-size:12px; background:#ccc;}
.rankLeft p span.r1{ background:#c00; color:#fff;}
</style>
<div id="leftad3" class="contentadBox_left"><div id="ac_wrap_112105" style="width:650px"><iframe src="http://entry.baidu.com/rp/home?psid=1000112&amp;pswidth=650&amp;psheight=120&amp;ifr=infr%3A1_cross%3A0_drs%3A1_pcs%3A1280x629_pss%3A1280x1691_cfv%3A0_cpl%3A5_chi%3A1_cce%3A1_cec%3AUTF8_tlm%3A1462263664_ecd%3A1_adw%3Aundefinedxundefined&amp;di=1000112&amp;rsi0=650&amp;rsi1=120&amp;title=%E7%94%9F%E6%80%81%E8%A1%A5%E5%81%BF%E6%8E%A2%E7%B4%A2%E5%80%99%E9%B8%9F%E4%BF%9D%E6%8A%A4%E6%96%B0%E6%9C%BA%E5%88%B6%20%E8%AE%A9%E5%80%99%E9%B8%9F%E5%B9%B3%E5%AE%89%E8%BF%94%E4%B9%A1(1)_%E5%85%89%E6%98%8E%E6%97%A5%E6%8A%A5%20_%E5%85%89%E6%98%8E%E7%BD%91&amp;ref=http%3A%2F%2Fnews.baidu.com%2Fns%3Fword%3D%25E7%2594%259F%25E6%2580%2581%25E8%25A1%25A5%25E5%2581%25BF%26pn%3D80%26cl%3D2%26ct%3D1%26tn%3Dnews%26rn%3D20%26ie%3Dutf-8%26bt%3D0%26et%3D0&amp;ltu=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;t=1462263664827" width="650" height="120" scrolling="no" frameborder="0" style="width: 650px; height: 120px; background-color: transparent;"></iframe><script type="text/javascript" id="BDEMBED_PSID1000112">
    /*创建于2015-11-10*/
    var cpro_psid = "1000112";
    var cpro_pswidth = 650;
    var cpro_psheight = 120;
</script>
<script type="text/javascript"></script><script type="text/javascript"></script><script type="text/javascript"></script><script type="text/javascript"></script><script type="text/javascript"></script><script type="text/javascript"></script></div></div>

<!-- 112105：通发-内-底部导量 类型：固定广告位 尺寸：650x90-->
<ins id="ac_js86_112105" style="display: none;"></ins><script type="text/javascript">
_acK({aid:112105,format:0,mode:1,gid:1,destid:"leftad3",serverbaseurl:"afp.csbew.com/"});
</script><script type="text/javascript">
ac_as_id = 112105;
window.afp_cur_query="?pv=1&sp=112105,1,0,0,0,1,1,21&ec=UTF-8&re=1280,800&jsv=7&cb=1206543312&seq=3&fs=3";ac_format = 0;
ac_mode = 1;
window.__trans__112105 = true;
ac_group_id = 1;
ac_server_base_url = "afpeng.csbew.com/";
</script>
<script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/k.js"></script><script></script><script type="text/javascript" src="http://afpeng.csbew.com/ex?a=112105&amp;sp=1&amp;cb=_acM.r&amp;u=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;ds=1280x800&amp;_=1462263664653&amp;fs=3&amp;pvid=b13c2ef51e715a83bae5d46e675c6961&amp;cg=ee84356f0e73cdd4963c7262d3570c76&amp;from_csbew=1" id="ac_js86_$1439246902"></script>





<!--24小时图片排行-->
<div class="contentColumnLeft">
			<div class="contentTitBarLeft">一周图片排行榜</div>
			<div class="contentBoxLeft">
			<div class="contentPicTxt_left01 rankLeft">
				<div class="contentPicArea black12" style="width:180px; padding-left:20px; float:left; text-align:left;">
				  <a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19921965.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160501/c03fd5535e16188fd7863c.jpg" border="0" width="140" height="100"></a><p><span class="r1">01</span><span><a href="http://photo.gmw.cn/2016-05/01/content_19921965.htm" target="_blank">这确定是一只狗？</a></span></p><a atremote="" href="http://skype.gmw.cn/activity/fools-day.html?utm_campaign=gmw&amp;utm_source=page&amp;utm_medium=imageph" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160331/c03fd5535e161866dedd31.jpg" border="0" width="140" height="100"></a><p><span class="r1">02</span><span><a href="http://skype.gmw.cn/activity/fools-day.html?utm_campaign=gmw&amp;utm_source=page&amp;utm_medium=imageph" target="_blank">愚人节话费降降降</a></span></p>
				</div>
				<div class="contentTxtArea black14" style="float:left;">
					<p><span class="r2">03</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19920228.htm" target="_blank">成都女留学生疑遭澳洲姨父杀害 身中20刀</a></span></p>
					<p><span class="r2">04</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19919798.htm" target="_blank">男子反串香妃起舞引蝶满场飞 满地蝴蝶惹人惊奇</a></span></p>
					<p><span class="r2">05</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19922713.htm" target="_blank">美女电梯间5秒KO色狼 她竟是拳王女友</a></span></p>
					<p><span class="r2">06</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19919635.htm" target="_blank">大学毕业生留念会堪比明星秀 走红毯还玩航拍</a></span></p>
					<p><span class="r2">07</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19919664.htm" target="_blank">西湖惊艳亮相首支女子巡逻队 游客：太拉风了</a></span></p>
					<p><span class="r2">08</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19919681.htm" target="_blank">有鬼？影像捕捉到一战时期老旧农舍内疑似幽灵</a></span></p>
					<p><span class="r2">09</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19921640.htm" target="_blank">肯尼亚焚烧105吨象牙和1.3吨犀牛角</a></span></p>
					<p style="border:none;"><span class="r2">10</span>
					  <span class="rankRightTit"><a atremote="" href="http://photo.gmw.cn/2016-05/01/content_19919654.htm" target="_blank">英国一村庄被孔雀占领了6年</a></span></p>
				</div>
				<div class="clear"></div>
			</div>
  </div>
</div>
<div id="leftad4" class="contentadBox_left"></div>
<div id="leftad5" class="contentadBox_left"></div>
</div>
    <div class="noMobile"><meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<div id="leftad6" class="noMobile contentadBox_left"></div>
<div id="leftad8" class="noMobile contentadBox_left"></div>
</div>

</div>
  <!-- tplID:8375 时政无广告右侧-->
<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<style type="text/css">
.contentPicTxt_right{padding:5px;}
.contentPicTxt_right img{ margin:0 5px 0 0; float:left;}
/* 右侧侧Tab01  3个栏目*/
ul#contentTabs_right01{width:308px;}
ul#contentTabs_right01 li{ float:left;}
ul#contentTabs_right01 li a{display:block;width:102px;border-bottom:1px solid #ccc;border-right:1px solid #ccc;height:30px; line-height:30px; text-align:center;text-decoration:none;outline:none;background:#f9f9f9;}
ul#contentTabs_right01 li a.current{background:#fff; border-bottom:none; font-weight:bold;}
ul#contentTabs_right01 li a.current:hover{text-decoration:none;cursor: default;}
ul#contentOutput_right01,ul#contentOutput_right01 li{width:308px; height:260px;overflow:hidden;}
/* 右侧侧Tab02 2个栏目*/
ul#contentTabs_right02{width:308px;}
ul#contentTabs_right02 li{ float:left;}
ul#contentTabs_right02 li a,ul#contentTabs_right01 li a{display:block;width:153px;border-bottom:1px solid #ccc;border-right:1px solid #ccc;height:30px; line-height:30px; text-align:center;text-decoration:none;outline:none;background:#f9f9f9;}
ul#contentTabs_right02 li a.current{background:#fff; border-bottom:none; font-weight:bold;}
ul#contentTabs_right02 li a.current:hover{text-decoration:none;cursor: default;}
ul#contentOutput_right02,ul#contentOutput_right02 li{width:308px; height:260px;overflow:hidden;}
/* 右侧排行*/
.rankRight p{ display:block; height:24px; margin:0; padding:0; border-bottom:1px dotted #cecece; clear:both;}
.rankRight p span{ display:block; float:left; height:24px; line-height:24px;}
.rankRight p span.rankRightTit{ width:220px; overflow:hidden;}
.rankRight p span.clickRate{ width:55px;color:#666;}
.rankRight p span.r1,.rankRight p span.r2{ width:18px; height:18px; line-height:18px;margin:3px 5px 0 0; text-align:center; font-size:12px;}
.rankRight p span.r1{ color:#c00;}
.contentRight{background:none;}
#searchText{width:140px; height:20px; line-height:20px; border:1px #ccc solid;}
#selectId{width:96px; height:22px; border:1px #ccc solid;}
#submitS{background:#123377; border:1px #ccc solid; width:50px; height:22px; line-height:22px; color:#fff; font-size:12px; cursor:pointer;}
</style>

<div class="contentRight">
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style>
#searchBar{padding-bottom:2px;}
#searchText{width:140px; height:20px; line-height:20px; border:1px #ccc solid;}
#selectId{width:96px; height:22px; border:1px #ccc solid;}
#submitS{background:#123377; border:1px #ccc solid; width:50px; height:24px; line-height:20px; color:#fff; font-size:12px; cursor:pointer;}
</style>
<div id="searchBar">
    <form id="form2" name="form2" method="post" target="_blank" onsubmit="change()">
        <table width="370" border="0" cellpadding="0" cellspacing="0">
            <tbody><tr>
            	<td width="153" align="left"> <input id="searchText" name="searchText" type="text"></td>
				<td width="102" align="left">
					<select name="selectId" id="selectId">
						<option value="0">站内搜索</option>
						<option value="1">光明网</option>
						<option value="2">光明报系</option>
					</select>
				</td>
            	<td width="55" align="right"><input id="submitS" type="submit" value="搜索"></td>
                <td align="right"><a href="http://skype.gmw.cn/"><img src="http://img.gmw.cn/pic/skypelogo.jpg" width="45" height="20" border="0"></a></td>
            </tr>
        </tbody></table>
    </form>
</div>

		<!--值班总编推荐-->
		<div class="contentColumnRight">
			<div class="contentBoxRight">
			<p><span class="navy12">[值班总编推荐]</span>
			  <span class="black12"><a atremote="" href="http://guancha.gmw.cn/2016-05/03/content_19937546.htm" target="_blank">公权力在莆田系深水中摸不着石头？</a><br></span>
			</p>
			<p><span class="navy12">[值班总编推荐]</span>
			  <span class="black12"><a atremote="" href="http://news.gmw.cn/2016-05/03/content_19929930.htm" target="_blank">我们该怎样办大学</a><br></span>
			</p>
			<p><span class="navy12">[值班总编推荐]</span>
			  <span class="black12"><a atremote="" href="http://news.gmw.cn/2016-04/29/content_19899753.htm" target="_blank">中国企业在德国汉诺威把握机遇</a><br></span>
			</p>
		  </div>
		</div>


        <!-- 20151113 豆子游戏 begin -->
        <div class="contentadBox_right">
            <!-- AFP两段式代码-公用代码 -->
			<script type="text/javascript" src="http://s.csbew.com/k.js"></script>
            <!-- 112411：通发-内-右侧-豆子 类型：固定广告位 尺寸：300x250-->
			<span style="overflow: visible; position: relative; display: block; width: 300px; height: 250px; border: 0px; text-align: left; background: none;"><span style="overflow: hidden; position: absolute; display: block; width: 300px; height: 250px; border: 0px; text-align: left; background: none;"><span style="overflow: hidden; position: absolute; display: block; width: 300px; height: 250px; border: 0px; text-align: left; background: none;"><a href="http://afptrack.csbew.com/clk?bid=0a67349c000057285f70105704ee5b33&amp;pid=mm_113716014_12970037_52772602&amp;cid=2482&amp;mid=3264&amp;oid=376&amp;productType=1&amp;target=http%3A%2F%2Fqp.gmw.cn%2Fgmw%2Findex_contentright.do" target="_blank" style="position: absolute; display: block; top: 0px; left: 0px; margin: 0px; padding: 0px; width: 300px; height: 250px; text-decoration: none; opacity: 0; z-index: 1; cursor: pointer; background: rgb(255, 255, 255);"></a><img id="ac_cs_112411_1" border="0" src="http://afp.alicdn.com/afp-creative/creative/u113716014/f023560c173b8bf7ab025326009e39d6.jpg" style="width: 300px; height: 250px;"></span></span></span><ins id="ac_js86_112411" style="display: none;"></ins><script type="text/javascript">
            _acK({aid:112411,format:0,mode:1,gid:1,serverbaseurl:"afp.csbew.com/"});
            </script><script type="text/javascript">
ac_as_id = 112411;
window.afp_cur_query="?pv=1&sp=112411,1,0,0,0,1,1,21&ec=UTF-8&re=1280,800&jsv=7&cb=3318938015&seq=4&fs=1";ac_format = 0;
ac_mode = 1;
window.__trans__112411 = true;
ac_group_id = 1;
ac_server_base_url = "afpeng.csbew.com/";
</script>
<script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/k.js"></script><script></script><script type="text/javascript" src="http://afpeng.csbew.com/ex?a=112411&amp;sp=1&amp;cb=_acM.r&amp;u=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;ds=1280x800&amp;_=1462263664979&amp;fs=1&amp;pvid=fcfcc423c29f02e622de68773c4e95a9&amp;cg=ac683cb997e5b7a560fb7b963f073ab9&amp;from_csbew=1" id="ac_js86_$9702609364"></script>

        </div>
        <!-- 20151113 豆子游戏 end -->

		<!-- 右侧Tab1 社会 博客 专题-->
		<div class="contentColumnRight">
			<ul id="contentTabs_right01" class="navy14">
				<li><a href="javascript:;" class="current">光明图片库</a></li>
				<li><a href="javascript:;" style=" border-right:none;" class="">纪　实</a></li>
			</ul>
			<div class="clear"></div>
			<ul id="contentOutput_right01">
				<li style="display: list-item;"><div class="contentBoxRight black12">
				  <div class="contentPicBox"><a atremote="" href="http://pic.gmw.cn/cameramanplay/489888/4297368/0.html" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160503/448a5ba8f885189240e408.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://pic.gmw.cn/cameramanplay/489888/4297368/0.html" target="_blank">“儿子娃娃”民族摔跤赛</a></div><div class="contentPicBox"><a atremote="" href="http://pic.gmw.cn/cameramanplay/2129379/4297365/0.html" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160503/448a5ba8f8851892406c07.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://pic.gmw.cn/cameramanplay/2129379/4297365/0.html" target="_blank">从江画里古村落</a></div><div class="contentPicBox"><a atremote="" href="http://pic.gmw.cn/cameramanplay/214866/4298354/0.html" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160503/448a5ba8f88518923fe506.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://pic.gmw.cn/cameramanplay/214866/4298354/0.html" target="_blank">民俗展演丰富农民生活</a></div><div class="contentPicBox"><a atremote="" href="http://pic.gmw.cn/cameramanplay/328851/4298372/0.html" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160503/448a5ba8f88518923f0f05.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://pic.gmw.cn/cameramanplay/328851/4298372/0.html" target="_blank">高速堵车 车主散步</a></div>
				</div>
				</li>
				<li style="display: none;"><div class="contentBoxRight black12">
					<div class="contentPicBox"><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855401.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160426/0023ae6686b2188904e93a.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855401.htm" target="_blank">梅葆玖表演踩空鞠躬接着演</a></div><div class="contentPicBox"><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855367.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160426/0023ae6686b21889048335.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855367.htm" target="_blank">揭秘平型关战役</a></div><div class="contentPicBox"><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855335.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160426/0023ae6686b21889043330.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855335.htm" target="_blank">长津湖战役：过于残酷</a></div><div class="contentPicBox"><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855240.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160426/0023ae6686b2188903da29.jpg" width="140" height="100" border="0"></a><br><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19855240.htm" target="_blank">张学良回应不抵抗将军之名</a></div>
					</div>
				</li>
			</ul>
			<!--右侧Tab1-->
			<script language="javascript">
					$(document).ready(function() {
						$.featureList(
							$("#contentTabs_right01 li a"),
							$("#contentOutput_right01 li"), {
								start_item:0
							}
						);
						/*
						// Alternative
						$('#tabs li a').featureList({
							output			:	'#output li',
							start_item		:	1
						});
						*/
					});
				</script>
		</div>
		<!--右侧Tab2 排行榜-->
		<div class="contentColumnRight">
			<ul id="contentTabs_right02" class="navy14">
				<li><a href="javascript:;" class="current">48小时点击排行</a></li>
				<li><a href="javascript:;" style=" border-right:none;" class="">热点话题排行</a></li>
			</ul>
			<div class="clear"></div>
			<ul id="contentOutput_right02" class="black12">
				<li style="display: list-item;">
					<div class="contentBoxRight rankRight">
					<p><span class="r1">01</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19767667.htm" target="_blank">黑养生馆称洗脚水治百病 大爷大妈排队喝</a></span><span class="clickRate"></span>
					</p>
					<p><span class="r1">02</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19762685.htm" target="_blank">面包车高速上爆胎失控 3人被甩飞2人身亡</a></span><span class="clickRate"></span></p>
					<p><span class="r1">03</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19762394.htm" target="_blank">媳妇比妈小1岁遭全家反对 母亲给儿子下跪</a></span><span class="clickRate"></span></p>
					<p><span class="r2">04</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19761303.htm" target="_blank">男子招嫖后嫌服务不周 报警“维权”</a></span><span class="clickRate"></span></p>
					<p><span class="r2">05</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760979.htm" target="_blank">大学生宿舍产子身亡 前一晚如厕支开同学</a></span><span class="clickRate"></span></p>
					<p><span class="r2">06</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760831.htm" target="_blank">实拍女子当街脱光质问男子 我和她谁好看</a></span><span class="clickRate"></span></p>
					<p><span class="r2">07</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760800.htm" target="_blank">女子勒死情人雇的哥背其尸体下楼</a></span><span class="clickRate"></span></p>
					<p><span class="r2">08</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760709.htm" target="_blank">专车接送招嫖民警一锅端 四男女被捉现行</a></span><span class="clickRate"></span></p>
					<p><span class="r2">09</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760013.htm" target="_blank">老太做场小手术 清单标明用上千袋注射液</a></span><span class="clickRate"></span></p>
					<p style="border:none;"><span class="r2">10</span>
					  <span class="rankRightTit"><a atremote="" href="http://legal.gmw.cn/2016-04/19/content_19760209.htm" target="_blank">千万富翁为减压提神 邀情人冰妹家中吸毒</a></span><span class="clickRate"></span></p>
				  </div>
				</li>
				<li style="display: none;">
					<div class="contentBoxRight rankRight">
					<p><span class="r1">01</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596855-1-1.html" target="_blank">强拉女大学生上车，街痞咋当上纪委书记</a></span>
					</p>
					<p><span class="r1">02</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596880-1-1.html" target="_blank">保安撞狗事件 爱狗没错但要守法</a></span>
					</p>
					<p><span class="r1">03</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596883-1-1.html" target="_blank">免费蹭网应成政府办事窗口的“标配”</a></span>
					</p>
					<p><span class="r2">04</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596893-1-1.html" target="_blank">乘客被打只赔3元呼唤专车须严管</a></span>
					</p>
					<p><span class="r2">05</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596894-1-1.html" target="_blank">毕业生求职奇葩被拒不见得是坏事</a></span>
					</p>
					<p><span class="r2">06</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596897-1-1.html" target="_blank">00后女孩将产子争议仅是情何以堪</a></span>
					</p>
					<p><span class="r2">07</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596941-1-1.html" target="_blank">创新创业专业，应争取“安居乐业”</a></span>
					</p>
					<p><span class="r2">08</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596946-1-1.html" target="_blank">抓好信访工作，凝聚建设美好中国强大力量</a></span>
					</p>
					<p><span class="r2">09</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596995-1-1.html" target="_blank">精准兜底扶贫 把好“最后一道保障线”</a></span>
					</p>
					<p style="border:none;"><span class="r2">10</span>
					  <span class="rankRightTit" style="width:275px"><a atremote="" href="http://bbs.gmw.cn/thread-3596960-1-1.html" target="_blank">“穿牛仔裤毁灭未来”，能再夸张点儿吗</a></span>
					</p>
				  </div>
				</li>
			</ul>
			<!--右侧Tab2-->
			<script language="javascript">
					$(document).ready(function() {
						$.featureList(
							$("#contentTabs_right02 li a"),
							$("#contentOutput_right02 li"), {
								start_item:0
							}
						);
						/*
						// Alternative
						$('#tabs li a').featureList({
							output			:	'#output li',
							start_item		:	1
						});
						*/
					});
				</script>
		</div>
		<!--军事广角-->
		<div class="contentColumnRight black12">
			<div class="contentTitBarRight">军事广角</div>
		  <div class="contentPicTxt_right">
		    <a atremote="" href="http://mil.gmw.cn/2016-04/29/content_19903094.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160429/bc305bc987e9188cfffc35.jpg" border="0" width="120" height="85" style="margin:5px 5px 0 5px;"></a>
		  <p class="black12">
		    ·<a href="http://mil.gmw.cn/2016-04/29/content_19903094.htm" target="_blank">越南女兵新式军服靓照</a><br>·<a href="http://mil.gmw.cn/2016-04/11/content_19660952.htm" target="_blank">俯瞰中国“野牛”登陆</a><br>·<a href="http://mil.gmw.cn/2016-03/25/content_19438324.htm" target="_blank">空警500预警机侧面照曝光</a><br>·<a href="http://mil.gmw.cn/2016-03/25/content_19438207.htm" target="_blank">辽宁舰航母最新全貌曝光</a><br>
		  </p>
            <div class="clear" style="height:10px;"></div>
            <a atremote="" href="http://mil.gmw.cn/2016-03/17/content_19321633.htm" target="_blank"><img atremote="" src="http://imgnews.gmw.cn/attachement/jpg/site2/20160317/bc305baebed81854485f56.jpg" border="0" width="120" height="85" style="margin:5px 5px 0 5px;"></a>
		  <p class="black12">
		    ·<a href="http://mil.gmw.cn/2016-03/17/content_19321633.htm" target="_blank">中国新建海警船美照</a><br>·<a href="http://mil.gmw.cn/2016-03/24/content_19422404.htm" target="_blank">A4腰？听听空军女神怎么说</a><br>·<a href="http://mil.gmw.cn/2016-02/16/content_18891863.htm" target="_blank">美军航母潜艇烤肉大会</a><br>·<a href="http://mil.gmw.cn/2015-12/05/content_17975608.htm" target="_blank">十大最失败的军事发明</a><br>
		  </p>
		  </div>
		<div class="clear"></div>
		</div>

		<!--看点·追踪-->
		<div class="contentColumnRight">
			<div class="contentTitBarRight">看点·追踪</div>
			<div class="contentPicTxt_right">
				<div class="contentPicTxt_right" style="padding:10px 10px 0;">
					<strong class="black12"><a atremote="" href="http://politics.gmw.cn/2016-04/26/content_19852375.htm" target="_blank">工信部拟取消手机漫游费</a></strong><p><span class="grey12_6">　　工信部官方微博“工信微报”回应，工信部将根据国家区域发展战略规划，推动企业逐步取消区域内手机漫游费。</span></p></div>
				<div class="line_dotted"></div>
				<p class="black12">
					<a atremote="" href="http://politics.gmw.cn/2016-04/12/content_19666715.htm"><font color="#333399">【国子监错别字】</font>缘何挂了10年？</a><br><a atremote="" href="http://politics.gmw.cn/2016-04/12/content_19666657.htm"><font color="#333399">【自愿退休】</font><font color="black">干部</font>"上能下"需自请"退"</a><br><a atremote="" href="http://politics.gmw.cn/2016-02/24/content_19010232.htm"><font color="#333399">【职业打假人】</font>维权效益不宜高估</a><br><a atremote="" href="http://politics.gmw.cn/2016-02/24/content_19010225.htm"><font color="#333399">【给孩子请假】</font>莫成“向学校逼假”</a><br><a atremote="" href="http://politics.gmw.cn/2016-02/24/content_19010202.htm"><font color="#333399">【推广街区制】</font>是楼市去库存利器？</a><br>
				</p>
		</div>
		</div>
	</div>
	<div class="clear"></div>
</div>

<div class="channel-mobileFooter noDesktop">
	<p><a href="http://wap.gmw.cn/">WAP版</a>|<a href="http://m.gmw.cn/">触屏版</a></p>
	<p>光明网版权所有</p>
</div>
<div class="noMobile">
	<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
	<div class="clear"></div>
	<div class="footLine"></div>
	<div class="black12" style="margin:11px auto 28px;padding:0;text-align:center;">
		<p style="line-height:30px;height:30px;"><a href="http://www.gmw.cn/node_21441.htm">光明日报社概况</a> | <a href="http://www.gmw.cn/aboutus.htm">关于光明网</a> | <a href="http://www.gmw.cn/content/node_8926.htm">报网动态</a> | <a href="http://www.gmw.cn/node_46280.htm">联系我们</a> | <a href="http://www.gmw.cn/node_46279.htm">法律声明</a> | <a href="http://www.gmw.cn/gm/">光明员工</a> | <a href="http://mail.gmw.cn/">光明网邮箱</a> | <a href="http://www.gmw.cn/map.htm">网站地图</a></p>
		<p style="line-height:30px;height:30px;">光明网版权所有</p>
	</div>
	<div id="thistime" style="display:none">
		<script type="text/javascript" src="http://img.gmw.cn/js/haf_gmw_2013.js"></script>
	</div>
	<!-- 天润 统计 -->
<script type="text/javascript">document.write(unescape("%3Cscript src='http://cl.webterren.com/webdig.js?z=7' type='text/javascript'%3E%3C/script%3E"));</script><script src="http://cl.webterren.com/webdig.js?z=7" type="text/javascript"></script>
<script type="text/javascript">wd_paramtracker("_wdxid=000000000000000000000000000000000000000000")</script>
<!-- 谷歌 统计 -->
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-20947729-1', 'auto');
  ga('require', 'displayfeatures');
  ga('send', 'pageview');
</script>
<script type="text/javascript">
_atrk_opts = { atrk_acct:"4+gli1aUCm00OA", domain:"gmw.cn",dynamic: true};
(function() { var as = document.createElement('script'); as.type = 'text/javascript'; as.async = true; as.src = "https://d31qbv1cthcecs.cloudfront.net/atrk.js"; var s = document.getElementsByTagName('script')[0];s.parentNode.insertBefore(as, s); })();
</script>
<noscript>&lt;img src="https://d5nxst8fruw4z.cloudfront.net/atrk.gif?account=4+gli1aUCm00OA" style="display:none" height="1" width="1" alt="" /&gt;</noscript>

</div>

<!-- 20160428 mail form pengbo -->
<!-- AFP两段式代码-公用代码 -->
<script type="text/javascript" src="http://afpmm.alicdn.com/g/mm/afp-cdn/JS/k.js"></script>


<!-- 52772462：人才-内-0像素 类型：固定 尺寸：0x1-->
<ins id="ac_js86_mm_113716014_12970037_52772462" style="display: none;"></ins><script type="text/javascript">
_acM({aid:"mm_113716014_12970037_52772462",format:1,mode:1,gid:1,serverbaseurl:"afpeng.alimama.com/"});
</script><script></script><script type="text/javascript" src="http://afpeng.alimama.com/ex?a=mm_113716014_12970037_52772462&amp;sp=1&amp;cb=_acM.r&amp;u=http%3A%2F%2Fnews.gmw.cn%2F2016-04%2F14%2Fcontent_19695837.htm&amp;ds=1280x800&amp;_=1462263665281&amp;fs=5&amp;pvid=abbdea1ee539c207a7e21f64a302005f&amp;cg=b7aea31bef5e4a382a27c8fe3135566d" id="ac_js86_$1971834805"></script><script type="text/javascript">document.write(unescape("%3Cscript src='http://img.gmw.cn/js/market/mooncake_final.js' type='text/javascript'%3E%3C/script%3E"));</script><script src="http://img.gmw.cn/js/market/mooncake_final.js" type="text/javascript"></script>


<audio controls="controls" style="display: none;"></audio><iframe src="http://www.gmw.cn/ad/world_content_float_0x0_52768431.html" width="0" height="0" scrolling="no" frameborder="0"></iframe><div id="bsBox" class="bsBox"><div class="bsClose">X</div><div class="bsTop"><div class="bsReturn">选择其他平台 &gt;&gt;</div><span style="margin-left:15px;">分享到</span><span class="bsPlatName"></span></div><div class="bsFrameDiv"><iframe class="bShareFrame" name="bsFrame705" frameborder="0" scrolling="no" allowtransparency="true"></iframe></div><div id="bsMorePanel" style="display: none;"></div></div><div id="ads"></div><div id="bsPanelHolder"><div id="bsPanel" style="display:none;"><div class="bsTitle"><a style="float:left;height:20px;line-height:20px;font-weight:bold;" class="bsSiteLink" target="_blank" href="http://www.bshare.cn/intro">分享到</a><a class="bsSiteLink" style="cursor:pointer;float:right;height:20px;line-height:20px;font-weight:bold;" onclick="document.getElementById('bsPanel').style.display='none';">X</a><div class="bsClear"></div></div><div class="bsClear"></div><div style="padding-left:8px;background:#fff;*height:244px;"><div style="height:47px;border-bottom:1px #ccc solid;padding:4px 0 4px 16px;margin-right:8px;_padding-left:12px;"><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'qqmb');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/qqmb.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">腾讯微博</div></a></div><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'gmweibo');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/gmweibo.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">光明微博</div></a></div><div class="bsRlogo" onmouseover="javascript:this.className='bsRlogoSel'" onmouseout="javascript:this.className='bsRlogo'"><a href="javascript:;" onclick="javascript:bShare.share(event,'facebook');return false;" style="text-decoration:none;line-height:120%;"><div style="cursor:pointer;width:24px;height:24px;margin:0 18px 2px;background:url(http://static.bshare.cn/frame/images//logos/m2/facebook.gif) no-repeat;"></div><div style="cursor:pointer;text-align:center;width:60px;height:16px !important;overflow:hidden;color:inherit;white-space:nowrap;line-height:120% !important">Facebook</div></a></div></div><div class="bsLogoLink"><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="一键通" onclick="javascript:bShare.share(event,'bsharesync');return false;" style="color:red;background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -288px;">一键通</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="QQ空间" onclick="javascript:bShare.share(event,'qzone');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1566px;">QQ空间</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="搜狐微博" onclick="javascript:bShare.share(event,'sohuminiblog');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1800px;">搜狐微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="新华微博" onclick="javascript:bShare.share(event,'xinhuamb');return false;" style="color:red;background:url(http://static.bshare.cn/frame/images//logos/s4/xinhuamb.png) no-repeat;">新华微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="手机" onclick="javascript:bShare.share(event,'shouji');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1710px;">手机</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="网易微博" onclick="javascript:bShare.share(event,'neteasemb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1332px;">网易微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="开心网" onclick="javascript:bShare.share(event,'kaixin001');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1008px;">开心网</a></div></div><div class="bsLogoLink"><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="新浪微博" onclick="javascript:bShare.share(event,'sinaminiblog');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1728px;">新浪微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="手机快传" onclick="javascript:bShare.share(event,'189share');return false;" style="width:48px;background:url(http://static.bshare.cn/frame/images//logos/s4/189share.png) no-repeat;">手机快传</a><div class="bsPopupAwd">奖</div></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="人人网" onclick="javascript:bShare.share(event,'renren');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1674px;">人人网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="天涯" onclick="javascript:bShare.share(event,'tianya');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1890px;">天涯</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="凤凰微博" onclick="javascript:bShare.share(event,'ifengmb');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -918px;">凤凰微博</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="朋友网" onclick="javascript:bShare.share(event,'qqxiaoyou');return false;" style="background:url(http://static.bshare.cn/frame/images//slogos_sprite8.png) no-repeat 0 -1548px;">朋友网</a></div><div class="bsLogo" onmouseover="javascript:this.className='bsLogoSel'" onmouseout="javascript:this.className='bsLogo'"><a href="javascript:;" title="微信" onclick="javascript:bShare.share(event,'weixin');return false;" style="background:url(http://static.bshare.cn/frame/images//logos/s4/weixin.png) no-repeat;">微信</a></div></div><div class="bsClear"></div></div><div style="height:20px;line-height:20px;padding:0 8px;border-top:1px solid #e8e8e8;color:#666;background:#f2f2f2;"><div class="buzzButton" style="float:left;">更多平台... <font style="font-weight:normal;">(133)</font></div><div id="bsPower" style="float:right;text-align:right;overflow:hidden;height:100%;"><a class="bsSiteLink" style="font-size:10px;vertical-align:text-bottom;line-height:24px;cursor:pointer;" href="http://www.bshare.cn" target="_blank"><span style="font-size:10px;vertical-align:text-bottom;"><span style="color:#f60;">b</span>Share</span></a></div></div></div></div></body><style type="text/css">#yddContainer{display:block;font-family:Microsoft YaHei;position:relative;width:100%;height:100%;top:-4px;left:-4px;font-size:12px;border:1px solid}#yddTop{display:block;height:22px}#yddTopBorderlr{display:block;position:static;height:17px;padding:2px 28px;line-height:17px;font-size:12px;color:#5079bb;font-weight:bold;border-style:none solid;border-width:1px}#yddTopBorderlr .ydd-sp{position:absolute;top:2px;height:0;overflow:hidden}.ydd-icon{left:5px;width:17px;padding:0px 0px 0px 0px;padding-top:17px;background-position:-16px -44px}.ydd-close{right:5px;width:16px;padding-top:16px;background-position:left -44px}#yddKeyTitle{float:left;text-decoration:none}#yddMiddle{display:block;margin-bottom:10px}.ydd-tabs{display:block;margin:5px 0;padding:0 5px;height:18px;border-bottom:1px solid}.ydd-tab{display:block;float:left;height:18px;margin:0 5px -1px 0;padding:0 4px;line-height:18px;border:1px solid;border-bottom:none}.ydd-trans-container{display:block;line-height:160%}.ydd-trans-container a{text-decoration:none;}#yddBottom{position:absolute;bottom:0;left:0;width:100%;height:22px;line-height:22px;overflow:hidden;background-position:left -22px}.ydd-padding010{padding:0 10px}#yddWrapper{color:#252525;z-index:10001;background:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ab20.png);}#yddContainer{background:#fff;border-color:#4b7598}#yddTopBorderlr{border-color:#f0f8fc}#yddWrapper .ydd-sp{background-image:url(chrome-extension://eopjamdnofihpioajgfdikhhbobonhbb/ydd-sprite.png)}#yddWrapper a,#yddWrapper a:hover,#yddWrapper a:visited{color:#50799b}#yddWrapper .ydd-tabs{color:#959595}.ydd-tabs,.ydd-tab{background:#fff;border-color:#d5e7f3}#yddBottom{color:#363636}#yddWrapper{min-width:250px;max-width:400px;}</style></html>'''

if __name__ == "__main__":
    new = NewsParse(getHtml5(), 'http://news.gmw.cn/2016-04/14/content_19695837.htm')
    print new.get_url()
    print new.get_content()
    print new.get_title()
    print new.get_dateline()
