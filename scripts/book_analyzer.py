# -*- coding: utf-8 -*-

from collections import OrderedDict
from sys import argv

from furl import furl
from scrapy.selector import Selector
from simplejson import dumps, loads

from utilities import (
    get_book, get_response, get_responses, get_string, get_url,
)


def get_books(keyword):
    books = []
    for response in get_responses([
        furl(
            'http://www.amazon.com/s'
        ).add({
            'keywords': keyword,
            'page': index,
            'rh': 'n:283155,p_n_feature_browse-bin:618073011,k:%(keyword)s' % {
                'keyword': keyword,
            },
        }).url
        for index in range(1, 4)
    ]):
        if not response:
            continue
        for anchor in Selector(
            text=response.text
        ).xpath(
            '//a[@class="a-link-normal s-access-detail-page a-text-normal"]'
        ):
            title = ''
            try:
                title = get_string(anchor.xpath('.//@title').extract()[0])
            except IndexError:
                try:
                    title = get_string(anchor.xpath('.//h2/text()').extract()[0])
                except IndexError:
                    pass
            books.append({
                'book_cover_image': anchor.xpath(
                    './/../../../div/div/div/a/img/@src'
                ).extract()[0],
                'title': title,
                'url': get_url(anchor.xpath('.//@href').extract()[0]),
            })
    return books


def get_items(url, keywords):
    items = OrderedDict({})
    for keyword in keywords:
        items[keyword] = {
            'keyword': keyword,
            'optimization': 'Low',
            'rank': 0,
        }
        for index, book in enumerate(get_books(keyword)):
            if url == book['url']:
                items[keyword] = {
                    'keyword': keyword,
                    'optimization': get_optimization(keyword, book['title']),
                    'rank': index + 1,
                }
                break
    return items.values()


def get_optimization(keyword, title):
    if keyword in title:
        return 'High'
    if ' ' in keyword:
        words = keyword.split(' ')
        if any(word in title for word in words):
            return 'Medium'
    return 'Low'

if __name__ == '__main__':
    if argv[1] == 'get_books':
        print dumps(get_books(argv[2]))
    if argv[1] == 'get_book':
        print dumps(get_book(get_response(argv[2])))
    if argv[1] == 'get_items':
        print dumps(get_items(argv[2], loads(argv[3])))
