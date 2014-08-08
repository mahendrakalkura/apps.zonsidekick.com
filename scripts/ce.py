# -*- coding: utf-8 -*-

from datetime import datetime
from re import compile

from dateutil.parser import parse
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.item import Item, Field
from scrapy.selector import Selector
from simplejson import loads
from simplejson.scanner import JSONDecodeError
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from utilities import (
    book,
    get_mysql_session,
    get_number,
    get_proxies,
    get_string,
    get_sales,
    get_user_agent,
    referral,
    review,
    trend,
)

BOT_NAME = get_user_agent()
CONCURRENT_ITEMS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS = 16
DOWNLOADER_MIDDLEWARES = {
    'ce.Middleware': 400,
    'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware': 500,
    'scrapy.contrib.downloadermiddleware.redirect.RedirectMiddleware': 600,
    (
        'scrapy.contrib.downloadermiddleware.httpcompression.'
        'HttpCompressionMiddleware'
    ): 800,
    'scrapy.contrib.downloadermiddleware.httpcache.HttpCacheMiddleware': 900,
}
DOWNLOAD_TIMEOUT = 60
HTTPCACHE_ENABLED = False
ITEM_PIPELINES = {
    'ce.Pipeline': 100,
}
LOG_LEVEL = 'INFO'
SPIDER_MODULES = [
    'ce',
]
USER_AGENT = BOT_NAME


class Book(Item):
    url = Field()
    title = Field()
    author = Field()
    price = Field()
    publication_date = Field()
    print_length = Field()
    amazon_best_sellers_rank = Field()
    estimated_sales_per_day = Field()
    earnings_per_day = Field()
    total_number_of_reviews = Field()
    review_average = Field()
    section = Field()
    reviews = Field()
    referrals = Field()
    trend = Field()


class Review(Item):
    book = Field()
    author = Field()
    date = Field()
    subject = Field()
    body = Field()
    stars = Field()


class Referral(Item):
    book = Field()
    url = Field()
    title = Field()
    author = Field()
    price = Field()
    total_number_of_reviews = Field()
    review_average = Field()


class Middleware(object):

    def process_request(self, request, spider):
        request.meta['proxy'] = get_proxies()['http']


class Pipeline(object):

    def __init__(self):
        self.session = get_mysql_session()

    def process_item(self, item, spider):
        session = self.session()
        if isinstance(item, Book):
            b = self.get_book(session, item)
        if isinstance(item, Review):
            b = self.get_book(session, item['book'])
            if not session.query(
                review,
            ).filter(
                review.book == b,
                review.author == item['author'],
            ).count():
                b.reviews.append(review(**{
                    'author': item['author'],
                    'body': item['body'],
                    'date': item['date'],
                    'stars': item['stars'],
                    'subject': item['subject'],
                }))
        if isinstance(item, Referral):
            b = self.get_book(session, item['book'])
            if not session.query(
                referral,
            ).filter(
                referral.book == b,
                referral.url == item['url'],
            ).count():
                b.referrals.append(referral(**{
                    'author': item['author'],
                    'price': item['price'],
                    'review_average': item['review_average'],
                    'title': item['title'],
                    'total_number_of_reviews': item['total_number_of_reviews'],
                    'url': item['url']
                }))
        session.add(b)
        try:
            session.commit()
        except DBAPIError:
            session.rollback()
        except SQLAlchemyError:
            session.rollback()
        finally:
            session.close()
        return item

    def get_book(self, session, dictionary):
        b = session.query(
            book,
        ).filter(
            book.author == dictionary['author'],
            book.section == dictionary['section'],
            book.title == dictionary['title'],
            book.url == dictionary['url'],
        ).first()
        if not b:
            b = book(**{
                'author': dictionary['author'],
                'section': dictionary['section'],
                'title': dictionary['title'],
                'url': dictionary['url'],
            })
        b.price = dictionary['price']
        b.publication_date = dictionary['publication_date']
        b.print_length = dictionary['print_length']
        b.amazon_best_sellers_rank = dictionary['amazon_best_sellers_rank']
        b.estimated_sales_per_day = dictionary['estimated_sales_per_day']
        b.earnings_per_day = dictionary['earnings_per_day']
        b.total_number_of_reviews = dictionary['total_number_of_reviews']
        b.review_average = dictionary['review_average']
        b.section = dictionary['section']
        if not session.query(
            trend,
        ).filter(
            trend.book == b,
            trend.date_and_time == dictionary['trend']['date_and_time'],
        ).count():
            b.trends.append(trend(**{
                'date_and_time': dictionary['trend']['date_and_time'],
                'rank': dictionary['trend']['rank'],
            }))
        return b


class Spider(CrawlSpider):
    allowed_domains = [
        'amazon.com',
    ]
    name = 'ce'
    rules = (
        Rule(
            SgmlLinkExtractor(
                restrict_xpaths=(
                    '//ol[@class="zg_pagination"]',
                ),
            ),
            callback='parse_pages',
        ),
    )
    start_urls = [
        'http://www.amazon.com/Best-Sellers-Kindle-Store-eBooks/zgbs/'
        'digital-text/154606011/ref=zg_bs_unv_kstore_2_154607011_1',
    ]

    def parse_pages(self, response):
        selector = None
        try:
            selector = Selector(response)
        except AttributeError:
            pass
        if not selector:
            return
        section = ''
        try:
            section = get_string(selector.xpath(
                '//li[@id="zg_tabTitle"]/h3/text()'
            ).extract()[0])
        except IndexError:
            pass
        if not section:
            return
        for div in selector.xpath(
            '//div[@id="zg_centerListWrapper"]/div[@class="zg_itemImmersion"]'
        ):
            yield Request(
                get_string(div.xpath(
                    './/div[@class="zg_itemWrapper"]/'
                    'div[@class="zg_image"]/'
                    'div[@class="zg_itemImageImmersion"]/a/'
                    '@href'
                ).extract()[0]),
                callback=self.parse_book,
                meta={
                    'rank': int(get_number(get_string(div.xpath(
                        './/div[@class="zg_rankDiv"]/'
                        'span[@class="zg_rankNumber"]/text()'
                    ).extract()[0][:-1]))),
                    'section': section,
                },
            )

    def parse_book(self, response):
        url = response.url
        title = ''
        author = ''
        price = 0.00
        publication_date = ''
        print_length = 0
        amazon_best_sellers_rank = {}
        estimated_sales_per_day = 0
        earnings_per_day = 0.00
        total_number_of_reviews = 0
        review_average = 0.00
        section = response.meta['section']
        reviews = []
        referrals = []
        trend = {}
        selector = Selector(response)
        try:
            title = get_string(selector.xpath(
                '//span[@id="btAsinTitle"]/text()'
            ).extract()[0])
        except IndexError:
            pass
        try:
            author = get_string(selector.xpath(
                '//span[@class="contributorNameTrigger"]/a/text()'
            ).extract()[0])
        except IndexError:
            try:
                author = get_string(selector.xpath(
                    '//h1[@class="parseasinTitle "]/'
                    'following-sibling::span/a/text()'
                ).extract()[0])
            except IndexError:
                pass
        try:
            price = float(get_number(get_string(selector.xpath(
                '//td[contains(text(), "Kindle Price")]'
                '/following-sibling::td/b/text()'
            ).extract()[0])))
        except IndexError:
            pass
        try:
            publication_date = get_string(selector.xpath(
                '//input[@id="pubdate"]/@value'
            ).extract()[0][0:10])
        except IndexError:
            pass
        try:
            print_length = int(get_number(get_string(
                selector.xpath(
                    '//b[contains(text(), "Print Length")]/../text()'
                ).extract()[0]
            )))
        except IndexError:
            try:
                print_length = int(get_number(get_string(
                    selector.xpath(
                        '//li[contains(text(), "Length")]/a/span/text()'
                    ).extract()[0]
                )))
            except IndexError:
                pass
        try:
            text = get_string(selector.xpath(
                '//li[@id="SalesRank"]/text()'
            ).extract()[1]).split(' ', 1)
            amazon_best_sellers_rank[get_string(
                text[1].replace(
                    u'in ', ''
                ).replace(
                    '(', ''
                ).replace(
                    ')', ''
                )
            )] = int(get_number(get_string(text[0])))
        except IndexError:
            pass
        try:
            for li in selector.xpath(
                '//ul[@class="zg_hrsr"]/li[@class="zg_hrsr_item"]'
            ):
                amazon_best_sellers_rank[
                    get_string(
                        li.xpath(
                            './/span[@class="zg_hrsr_ladder"]'
                        ).xpath(
                            'string()'
                        ).extract()[0]
                    ).replace(u'in\xa0', '')
                ] = int(get_number(get_string(li.xpath(
                    './/span[@class="zg_hrsr_rank"]/text()'
                ).extract()[0])))
        except IndexError:
            pass
        if amazon_best_sellers_rank:
            estimated_sales_per_day = get_sales(min(
                amazon_best_sellers_rank.values()
            ))
            earnings_per_day = estimated_sales_per_day * price
        try:
            total_number_of_reviews = int(get_number(get_string(
                compile('all\s*([^\s]*)').search(selector.xpath(
                    '//a[@id="revSAR"]/text()'
                ).extract()[0]).group(1)
            )))
        except (AttributeError, IndexError):
            pass
        try:
            review_average = float(get_number(get_string(selector.xpath(
                '//div[@class="gry txtnormal acrRating"]/text()'
            ).extract()[0].split(' ')[0])))
        except IndexError:
            pass
        try:
            reviews = selector.xpath(
                u'//a[@id="seeAllReviewsUrl"]/@href'
            ).extract()[0]
        except IndexError:
            pass
        try:
            referrals = get_string(selector.xpath(
                '//div[@id="purchaseSimsData"]/text()'
            ).extract()[0])
        except IndexError:
            pass
        trend = {
            'date_and_time': datetime.now().strftime('%Y-%m-%d %H:00:00'),
            'rank': response.meta['rank'],
        }
        book = {
            'amazon_best_sellers_rank': amazon_best_sellers_rank,
            'author': author,
            'earnings_per_day': earnings_per_day,
            'estimated_sales_per_day': estimated_sales_per_day,
            'price': price,
            'print_length': print_length,
            'publication_date': publication_date,
            'referrals': referrals,
            'review_average': review_average,
            'reviews': reviews,
            'section': section,
            'title': title,
            'total_number_of_reviews': total_number_of_reviews,
            'trend': trend,
            'url': url,
        }
        if url and title and author:
            yield Book(book)
            if reviews:
                yield Request(
                    reviews,
                    callback=self.parse_reviews_1,
                    meta={
                        'book': book,
                    },
                )
            if referrals:
                yield Request(
                    callback=self.parse_referrals,
                    meta={
                        'book': book,
                    },
                    url=(
                        'http://www.amazon.com/gp/product/features/'
                        'similarities/shoveler/cell-render.html/'
                        'ref=pd_sim_kstore?id=%(referrals)s&'
                        'refTag=pd_sim_kstore&wdg=ebooks_display_on_website&'
                        'shovelerName=purchase'
                    ) % {
                        'referrals': referrals,
                    }
                )

    def parse_reviews_1(self, response):
        selector = Selector(response)
        for text in [
            '1 star',
            '2 star',
            '3 star',
            '4 star',
            '5 star',
        ]:
            href = None
            try:
                href = selector.xpath(
                    '//a[contains(text(), "%(text)s")]/@href' % {
                        'text': text,
                    }
                ).extract()[0]
            except IndexError:
                pass
            if href and href.startswith('http'):
                yield Request(
                    href,
                    callback=self.parse_reviews_2,
                    meta={
                        'book': response.meta['book'],
                    },
                )
                break

    def parse_reviews_2(self, response):
        selector = Selector(response)
        for div in selector.xpath('//div[@style="margin-left:0.5em;"]'):
            author = ''
            date = ''
            subject = ''
            body = ''
            stars = 0
            try:
                author = get_string(div.xpath(
                    './/div/div/div/a/span[@style="font-weight: bold;"]/text()'
                ).extract()[0])
            except IndexError:
                pass
            try:
                date = parse(get_string(div.xpath(
                    './/span[@style="vertical-align:middle;"]/nobr/text()'
                ).extract()[0])).date()
            except IndexError:
                pass
            try:
                subject = get_string(div.xpath(
                    './/span[@style="vertical-align:middle;"]/b/text()'
                ).extract()[0])
            except IndexError:
                pass
            try:
                body = get_string(div.xpath(
                    './/div[@class="reviewText"]'
                ).xpath('string()').extract()[0])
            except IndexError:
                pass
            try:
                stars = int(get_number(get_string(div.xpath(
                    './/span[@style="margin-right:5px;"]/span/span/text()'
                ).extract()[0].split(' ')[0].split('.')[0])))
            except IndexError:
                pass
            if author:
                yield Review({
                    'author': author,
                    'body': body,
                    'book': response.meta['book'],
                    'date': date.isoformat(),
                    'stars': stars,
                    'subject': subject,
                })
        next = ''
        try:
            next = selector.xpath(
                u'//a[contains(text(), "Next ›")]/@href'
            ).extract()[0]
        except IndexError:
            pass
        if next:
            yield Request(
                callback=self.parse_reviews_2,
                meta={
                    'book': response.meta['book'],
                },
                url=next,
            )

    def parse_referrals(self, response):
        rs = []
        try:
            rs = loads(get_string(response.body))
        except JSONDecodeError:
            pass
        for r in rs:
            url = ''
            title = ''
            author = ''
            price = 0.00
            total_number_of_reviews = 0
            review_average = 0.00
            selector = Selector(text=get_string(r['content']))
            try:
                url = 'http://www.amazon.com%(href)s' % {
                    'href': get_string(selector.xpath(
                        '//a[@class="sim-img-title"]/@href'
                    ).extract()[0])
                }
            except IndexError:
                pass
            try:
                title = get_string(selector.xpath(
                    '//a[@class="sim-img-title"]'
                ).xpath('string()').extract()[0])
            except IndexError:
                pass
            try:
                author = get_string(selector.xpath(
                    '//div[@class="byline"]/a/text()'
                ).extract()[0])
            except IndexError:
                pass
            try:
                price = float(get_number(get_string(selector.xpath(
                    '//span[@class="price"]//text()'
                ).extract()[0])))
            except IndexError:
                pass
            try:
                total_number_of_reviews = int(get_number(get_string(
                    selector.xpath(
                        '//span[@class="crAvgStars"]/a/text()'
                    ).extract()[0]
                )))
            except IndexError:
                pass
            try:
                review_average = float(get_number(get_string(selector.xpath(
                    '//span[contains(@class, "auiTestSprite")]/span/text()'
                ).extract()[0].replace(' out of 5 stars', ''))))
            except IndexError:
                pass
            if url:
                yield Referral({
                    'author': author,
                    'book': response.meta['book'],
                    'price': price,
                    'review_average': review_average,
                    'title': title,
                    'total_number_of_reviews': total_number_of_reviews,
                    'url': url,
                })
