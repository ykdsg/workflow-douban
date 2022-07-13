# coding: utf-8
import configparser
import json
import os
import sys
import urllib.request
from typing import List
from urllib import request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

from lxml import etree
from lxml.etree import _ElementTree

config = configparser.ConfigParser()
config.read('conf')
max_items = config.getint('base', 'max_items') if config.has_option('base', 'max_items') else 20
auto_sort = config.getboolean('base', 'auto_sort') if config.has_option('base', 'auto_sort') else False
quick_search = config.get('base', 'quick_search') if config.has_option('base', 'quick_search') else 'book'
apikey = config.get('base', 'apikey') if config.has_option('base', 'apikey') else ''

selection = os.getenv('selection') if os.getenv('selection') else quick_search

query = sys.argv[1]

tip = 'Go to Douban'

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7,en-GB;q=0.6,de-DE;q=0.5,de;q=0.4',
    'Cache-Control': 'no-cache',
    'Host': 'www.douban.com',

}
catMap = {
    'book': 1001,
    'movie': 1002,
    'music': 1003,
    'user': 1005
}


def get_raw(url):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:25.0) Gecko/20100101 Firefox/25.0'
    headers = {'User-Agent': user_agent}
    req = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(req)
    res = json.loads(response.read())
    return res


def gen_url(sel, q):
    base_url = 'https://www.douban.com/search?'
    params = dict()
    params['q'] = q
    cat = catMap.get(sel, '')
    params['cat'] = cat
    url = base_url + urlencode(params)
    return url


def requestUrl(url: str) -> str:
    req = request.Request(url=url, headers=headers, method='GET')
    try:
        response = request.urlopen(req)
    except HTTPError as e:
        print(e.reason, e.code, e.headers, sep='\n')
        return ''
    except URLError as e:
        print(e.reason)
        return ''
    html = response.read().decode('utf-8', "ignore")
    return html


class ItemInfo():
    def __init__(self):
        self.name = ''
        self.url = ''
        self.ratingNum = ''
        self.subTitle = ''
        self.imgUrl = ''


def parseStructure(html: str) -> List[ItemInfo]:
    res = []
    if html is None or len(html) == 0:
        return res
    elementTree: _ElementTree = etree.HTML(html)
    resultList: List[_ElementTree] = elementTree.xpath('//div[@class="result-list"]/div[@class="result"]')
    if len(resultList)==0:
        return res

    for result in resultList:
        item = ItemInfo()
        item.imgUrl = result.xpath('./div[@class="pic"]/a/img/@src')[0]
        item.name = result.xpath('./div[2]/div/h3/a/text()')[0]
        item.url = result.xpath('./div[2]/div/h3/a/@href')[0]
        item.ratingNum = result.xpath('./div[2]/div/div/span[2]/text()')[0]
        subTitleText = result.xpath('./div[2]/div/div/span[@class="subject-cast"]/text()')
        if len(subTitleText) > 0:
            item.subTitle = subTitleText[0]
        res.append(item)

    return res


def getInfoList() -> List[ItemInfo]:
    html = requestUrl(gen_url(selection, query))
    infoList = parseStructure(html)
    return infoList


# 获取解析的信息，从网页的结构看，书籍和电影是一样的
def info():
    res = []
    infoList = getInfoList()
    for info in infoList:
        item = dict()
        item['arg'] = info.url
        item['title'] = info.name
        item['subtitle'] = '%s-%s' % (info.ratingNum, info.subTitle)
        item['quicklookurl'] = info.imgUrl
        iconPath = 'image/' + selection + '_item.png'
        item['icon'] = dict(path=iconPath)
        res.append(item)
    return res


def gen_first_item(sel):
    cat = catMap.get(sel, '')
    base_url = 'https://www.douban.com/search'
    params = dict(q=query, cat=cat) if cat else dict(q=query)
    url = base_url + '?' + urlencode(params)
    item0 = dict()
    item0['uid'] = sel
    item0['title'] = tip
    item0['subtitle'] = 'Go to Douban search directly'
    item0['arg'] = url
    item0['icon'] = dict(path='image/douban_item.png')
    return item0


def main():
    global tip
    items = [gen_first_item(selection)]
    items += info()
    if len(items) == 1:
        tip = 'Nothing Found'
    elif query == '':
        tip = 'Go to Douban'

    items[0]['title'] = tip
    j = json.dumps({'items': items})
    print(j)


if __name__ == '__main__':
    main()
