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
    KEY_CHAR = set([u'、', u'，', u'。', u'记者', u'专电'])

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
        if self.content :
            for ele, weight in reversed(self.htmlSeq[:self.content_begin]):
                if weight < 0:continue
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
            return ""
        text = []
        for ele, value in self.htmlSeq[begin:end + 1]:
            if value < 0:
                if re.search("<\s*/?(p)|(br)[^>]*>", ele):
                    text.append("<br/>")
            else:
                text.append(ele)
        self.content_begin ,self.content_end = begin, end
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

        for char in ele:
            if char in self.KEY_CHAR:
                wight += 500
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


if __name__ == "__main__":
    new = NewsParse(getHtml(), 'http://finance.sina.com.cn/roll/2016-04-04/doc-ifxqxcnz9093681.shtml')
    print new.get_url()
    print new.get_content()
    print new.get_title()
    print new.get_dateline()
