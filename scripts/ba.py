# -*- coding: utf-8 -*-

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
            '//h3[@class="title"]/a[@class="title"]'
        ):
            title = ''
            try:
                title = get_string(anchor.xpath('.//span/@title').extract()[0])
            except IndexError:
                try:
                    title = get_string(anchor.xpath('.//text()').extract()[0])
                except IndexError:
                    pass
            books.append({
                'book_cover_image': anchor.xpath(
                    './/../../../div[@class="image imageContainer"]/a/div/img/'
                    '@src'
                ).extract()[0],
                'title': title,
                'url': get_url(anchor.xpath('.//@href').extract()[0]),
            })
    return books


def get_items(url, keywords):
    items = []
    for keyword in keywords:
        rank = 0
        for index, book in enumerate(get_books(keyword)):
            if url == book['url']:
                rank = index + 1
                break
        items.append({
            'keyword': keyword,
            'rank': rank,
            'optimization': 'Low',
        })
    return items

if __name__ == '__main__':
    if argv[1] == 'get_books':
        print dumps(get_books(argv[2]))
    if argv[1] == 'get_book':
        print dumps(get_book(get_response(argv[2])))
    if argv[1] == 'get_items':
        print dumps(get_items(argv[2], loads(argv[3])))
