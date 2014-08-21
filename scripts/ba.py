# -*- coding: utf-8 -*-

from furl import furl
from scrapy.selector import Selector

from utilities import get_responses, get_string, get_url


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
            name = ''
            try:
                name = get_string(anchor.xpath('.//span/@title').extract()[0])
            except IndexError:
                try:
                    name = get_string(anchor.xpath('.//text()').extract()[0])
                except IndexError:
                    pass
            books.append({
                'book_cover_image': anchor.xpath(
                    './/../../../div[@class="image imageContainer"]/a/div/img/'
                    '@src'
                ).extract()[0],
                'name': name,
                'url': get_url(anchor.xpath('.//@href').extract()[0]),
            })
    return books


def get_ranks(url, keywords):
    ranks = {}
    for keyword in keywords:
        ranks[keyword] = 0
    for keyword in keywords:
        for index, book in enumerate(get_books(keyword)):
            if url == book['url']:
                ranks[keyword] = index + 1
                break
    return ranks
