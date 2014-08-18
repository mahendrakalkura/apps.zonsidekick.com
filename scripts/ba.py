# -*- coding: utf-8 -*-

from furl import furl
from scrapy.selector import Selector

from utilities import get_book, get_contents, get_url


def get_books(keyword):
    books = []
    for index in range(1, 4):
        response = get_contents(furl('http://www.amazon.com/s').add({
            'keywords': keyword,
            'page': index,
            'rh': 'n:283155,p_n_feature_browse-bin:618073011,k:%(keyword)s' % {
                'keyword': keyword,
            },
            'sort': 'relevanceexprank',
        }).url)
        if response:
            for anchor in Selector(text=response).xpath(
                '//h3[@class="title"]/a[@class="title"]'
            ):
                books.append({
                    'name': anchor.xpath('.//text()').extract()[0],
                    'url': anchor.xpath('./@href').extract()[0],
                })
    return books


def get_ranks(url, keywords=[]):
    url = get_url(url)
    ranks = {}
    for keyword in keywords:
        ranks[keyword] = 0
    for keyword in keywords:
        for index, book in enumerate(get_books(keyword)):
            if url == get_url(book['url']):
                ranks[keyword] = index + 1
                break
    return ranks

for book in get_books('Hunger Games'):
    print get_book(book['url'])

print get_ranks(
    'http://www.amazon.com/Effective-Specific-Improve-Programs-Designs-ebook'
    '/dp/B004V4420U/ref=sr_1_10?s=digital-text&ie=UTF8',
    ['c program', 'C++']
)
