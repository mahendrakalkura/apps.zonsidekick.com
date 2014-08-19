# -*- coding: utf-8 -*-

from furl import furl
from scrapy.selector import Selector

from utilities import get_book, get_contents, get_number, get_string, get_url


def get_authors(name):
    authors = []
    for index in range(1, 4):
        response = get_contents(
            furl('http://www.amazon.com/s').add({
                'ie': 'UTF8',
                'page': index,
                'rh':
                'n:283155,p_n_feature_browse-bin:618073011,p_27:%(name)s' % {
                    'name': name,
                },
            }).url
        )
        if response:
            for anchor in Selector(
                text=response
            ).xpath(
                '//span[@class="ptBrand"]/a'
            ):
                authors.append({
                    'url': get_url('http://www.amazon.com%(href)s' % {
                        'href': anchor.xpath('.//@href').extract()[0],
                    }),
                    'name': anchor.xpath('.//text()').extract()[0],
                })
    return authors


def get_author(url):
    name = ''
    description = ''
    photo = ''
    amazon_rank = {}
    earnings_per_month = 0.0
    twitter = {
        'screen_name': '',
        'profile_image_url': '',
        'tweet': {
            'text': '',
        }
    }
    books = []
    response = get_contents(url)
    if response:
        selector = Selector(text=response)
        try:
            name = get_string(selector.xpath(
                '//h1[@id="EntityName"]/b/text()'
            ).extract()[0])
        except IndexError:
            pass
        try:
            description = get_string(' '.join(selector.xpath(
                '//div[contains(@class, "artistCentralBio")]/p/text()'
            ).extract()).replace('Print this', ''))
        except IndexError:
            pass
        try:
            photo = get_string(selector.xpath(
                '//img[@id="artistCentralGallery_image0"]/@src'
            ).extract()[0])
        except IndexError:
            pass
        try:
            amazon_rank[
                'Top 100 Authors'
            ] = get_number(selector.xpath(
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
                amazon_rank[string[1]] = get_number(
                    string[0]
                )
        except IndexError:
            pass
        try:
            twitter['screen_name'] = get_string(selector.xpath(
                '//p[@class="tweetScreenName"]/a/text()'
            ).extract()[0])
        except IndexError:
            pass
        try:
            twitter['profile_image_url'] = get_string(selector.xpath(
                '//a[@class="tweetProfileImage"]/img/@src'
            ).extract()[0])
        except IndexError:
            pass
        try:
            twitter['tweet_text'] = get_string(selector.xpath(
                '//p[@class="tweetText"]'
            ).xpath('string()').extract()[0])
        except IndexError:
            pass
        urls = []
        url = ''
        try:
            url = selector.xpath(
                '//div[@class="wwRefinements"]/ul/li'
                '/a[contains(text(), "Kindle Edition")]/@href'
            ).extract()[0]
        except IndexError:
            pass
        index = 0
        while True:
            if not url:
                break
            index += 1
            response = get_contents('http://www.amazon.com%(url)s' % {
                'url': url,
            })
            if not response:
                break
            selector = Selector(text=response)
            for href in selector.xpath(
                '//h3[@class="title"]/a[@class="title"]/@href'
            ).extract():
                urls.append(href)
            url = ''
            if selector.xpath('//a[@class="pagnNext"]/@href').extract():
                url = furl(url).remove('page').add({
                    'page': index + 1
                }).url
        for url in urls:
            book = get_book(url)
            books.append(book)
            earnings_per_month += (book['earnings_per_day'] * 30)
        return {
            'amazon_rank': amazon_rank,
            'books': books,
            'description': description,
            'earnings_per_month': earnings_per_month,
            'name': name,
            'photo': photo,
            'twitter': twitter,
        }
