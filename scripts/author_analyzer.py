# -*- coding: utf-8 -*-

from sys import argv

from furl import furl
from scrapy.selector import Selector
from simplejson import dumps

from utilities import (
    get_book,
    get_response,
    get_responses,
    get_number,
    get_string,
    get_url,
    set_rollbar_error
)


def get_authors(keyword):
    authors = []
    for response in get_responses([
        furl(
            'http://www.amazon.com/s'
        ).add({
            'page': index,
            'rh':
            'n:283155,p_n_feature_browse-bin:618073011,p_27:%(keyword)s' % {
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
            '//span[@class="a-size-small a-color-secondary"][text()="by "]/'
            'following-sibling::span[@class="a-size-small a-color-secondary"]/'
            'a[@class="a-link-normal a-text-normal"]'
        ):
            url = get_url('http://www.amazon.com%(href)s' % {
                'href': anchor.xpath('.//@href').extract()[0],
            })
            if url not in [author['url'] for author in authors]:
                authors.append({
                    'name': anchor.xpath('.//text()').extract()[0],
                    'url': url,
                })
    return authors


def get_author(url):
    name = ''
    description = ''
    photo = ''
    amazon_rank = {}
    earnings_per_month = 0.0
    twitter = {
        'profile_image_url': '',
        'screen_name': '',
        'tweet': '',
    }
    books = []
    response = get_response(url)
    if not response:
        return
    selector = Selector(text=response.text)
    try:
        name = get_string(selector.xpath(
            '//div[@id="ap-author-name"]/h1/text()'
        ).extract()[0])
    except IndexError:
        pass
    try:
        description = get_string(''.join(selector.xpath(
            '//div[@id="ap-bio"]/div/div/span/text()'
        ).extract()))
    except IndexError:
        pass
    try:
        photo = get_string(selector.xpath(
            '//img[@class="ap-author-image"]/@src'
        ).extract()[0])
    except IndexError:
        pass
    try:
        amazon_rank['Top 100 Authors'] = get_number(selector.xpath(
            '//div[@class="overallRank"]/text()'
        ).extract()[0])
    except IndexError:
        pass
    try:
        for div in selector.xpath(
            '//div[@class="browseNodeRanks"]/div[@class="nodeRank"]'
        ):
            string = get_string(
                div.xpath('string()').extract()[0]
            ).split(' in ')
            amazon_rank[string[1]] = get_number(string[0])
    except IndexError:
        pass
    try:
        twitter['screen_name'] = get_string(selector.xpath(
            '//span[@class="ap-tweet-handle"]/text()'
        ).extract()[0][1:])
    except IndexError:
        pass
    try:
        twitter['profile_image_url'] = get_string(selector.xpath(
            '//img[@class="ap-tweet-image"]/@src'
        ).extract()[0])
    except IndexError:
        pass
    try:
        twitter['tweet'] = get_string(selector.xpath(
            '//div[@class="a-box-group ap-tweet-content"]/span'
        ).xpath('string()').extract()[0])
    except IndexError:
        pass
    urls = []
    url_ = ''
    try:
        url_ = selector.xpath(
            '//div[@class="wwRefinements"]/ul/li'
            '/a[contains(text(), "Kindle Edition")]/@href'
        ).extract()[0]
    except IndexError:
        pass
    index = 0
    while True:
        index += 1
        if index >= 2:
            break
        response = get_response('http://www.amazon.com%(url_)s' % {
            'url_': url_,
        })
        if not response:
            break
        selector = Selector(text=response.text)
        for href in selector.xpath(
            '//h3[@class="title"]/a[@class="title"]/@href'
        ).extract():
            urls.append(href)
        url_ = ''
        try:
            url_ = get_url(get_string(selector.xpath(
                '//a[@id="pagnNextLink"]/@href'
            ).extract()[0]))
        except IndexError:
            pass
        if not url_:
            break
        url_ = furl(
            url_
        ).remove(
            'page'
        ).add({
            'page': index + 1
        }).url
    for response in get_responses(urls):
        if not response:
            continue
        book = get_book(response)
        books.append(book)
        earnings_per_month += (book['earnings_per_day'] * 30)
    if books:
        return {
            'amazon_rank': amazon_rank,
            'books': books,
            'description': description,
            'earnings_per_month': earnings_per_month,
            'name': name,
            'photo': photo,
            'twitter': twitter,
        }
    else:
        set_rollbar_error(
            '`books` variable empty in get_author '
            'function, url is %(url)s' % {
                'url': url,
            }
        )

if __name__ == '__main__':
    if argv[1] == 'get_authors':
        print dumps(get_authors(argv[2]))
    if argv[1] == 'get_author':
        print dumps(get_author(argv[2]))
