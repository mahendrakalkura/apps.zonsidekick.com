# -*- coding: utf-8 -*-

from furl import furl
from scrapy.selector import Selector
from sys import argv

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
            for anchor in Selector(text=response).xpath(
                '//span[@class="ptBrand"]/a'
            ):
                author = 'http://www.amazon.com%(href)s' % {
                    'href': anchor.xpath('.//@href').extract()[0],
                }
                author = get_url(author)
                if not author in authors:
                    authors.append(author)
    return authors


def get_author(url):
    amazon_authors_rank = {}
    author = ''
    books = []
    description = ''
    earnings = 0
    earnings_per_month = 0.0
    photo = ''
    twitter = {}
    response = get_contents(url)
    if response:
        urls = []
        selector = Selector(text=response)
        try:
            author = get_string(selector.xpath(
                '//h1[@id="EntityName"]/b/text()'
            ).extract()[0])
        except:
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
            amazon_authors_rank[
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
                string_ = get_string(
                    div.xpath('string()').extract()[0]
                ).split(' in ')
                amazon_authors_rank[string_[1]] = get_number(
                    string_[0]
                )
        except IndexError:
            pass
        try:
            twitter['screen_name'] = get_string(selector.xpath(
                '//p[@class="tweetScreenName"]/a/text()'
            ).extract()[0])
        except IndexError:
            twitter['screen_name'] = ''
        try:
            twitter['profile_image_url'] = get_string(selector.xpath(
                '//a[@class="tweetProfileImage"]/img/@src'
            ).extract()[0])
        except IndexError:
            twitter['profile_image_url'] = ''
        try:
            twitter['tweet_text'] = get_string(selector.xpath(
                '//p[@class="tweetText"]'
            ).xpath('string()').extract()[0])
        except IndexError:
            twitter['tweet_text'] = ''
        try:
            kindle_url = selector.xpath(
                '//div[@class="wwRefinements"]/ul/li'
                '/a[contains(text(), "Kindle Edition")]/@href'
            ).extract()[0]
        except IndexError:
            kindle_url = ''
        index = 1
        while True:
            if not kindle_url:
                break
            response_ = get_contents(
                'http://www.amazon.com%(kindle_url)s' % {
                    'kindle_url': kindle_url,
                }
            )
            if not response_:
                break
            selector = Selector(text=response_)
            for href in selector.xpath(
                '//h3[@class="title"]/a[@class="title"]/@href'
            ).extract():
                urls.append(href)
            if selector.xpath('//a[@class="pagnNext"]/@href').extract():
                kindle_url = furl(
                    kindle_url
                ).remove(
                    'page'
                ).add({
                    'page': index + 1
                }).url
            else:
                kindle_url = ''
            index += 1
            response_ = ''
        for url_ in urls:
            book = get_book(url_)
            earnings += book['earnings_per_day']
            books.append(book)
        earnings_per_month = earnings * 30
        return {
            'amazon_authors_rank': amazon_authors_rank,
            'author': author,
            'books': books,
            'description': description,
            'earnings_per_month': earnings_per_month,
            'photo': photo,
            'twitter': twitter,
            'url': url,
        }


if __name__ == '__main__':
    for url in get_authors(argv[1]):
        print get_author(url)
