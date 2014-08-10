# -*- coding: utf-8 -*-

from datetime import datetime
from re import compile, sub

from dateutil.parser import parse
from furl import furl
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.item import Item, Field
from scrapy.selector import Selector
from simplejson import loads
from simplejson.scanner import JSONDecodeError
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy import Column, Integer
from sqlalchemy.orm import backref, relationship

from utilities import (
    base,
    get_mysql_session,
    get_number,
    get_proxies,
    get_string,
    get_sales,
    get_url,
    get_user_agent,
    is_development,
    json,
    mutators_dict,
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


class category(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'tools_ce_categories'

    id = Column(Integer(), primary_key=True)

    category = relationship(
        'category',
        backref=backref(
            'categories', cascade='all', lazy='dynamic',
        ),
        remote_side=id,
    )


class section(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'tools_ce_sections'


class book(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'tools_ce_books'

    amazon_best_sellers_rank = Column(mutators_dict.as_mutable(json))


class review(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'tools_ce_reviews'

    book = relationship(
        'book', backref=backref('reviews', cascade='all', lazy='dynamic'),
    )


class referral(base):
    __tablename__ = 'tools_ce_referrals'
    __table_args__ = {
        'autoload': True,
    }

    book = relationship(
        'book', backref=backref('referrals', cascade='all', lazy='dynamic'),
    )


class trend(base):
    __tablename__ = 'tools_ce_trends'
    __table_args__ = {
        'autoload': True,
    }

    category = relationship(
        'category', backref=backref('trends', cascade='all', lazy='dynamic'),
    )
    section = relationship(
        'section', backref=backref('trends', cascade='all', lazy='dynamic'),
    )
    book = relationship(
        'book', backref=backref('trends', cascade='all', lazy='dynamic'),
    )


class Book(Item):
    url = Field()
    title = Field()
    author = Field()
    price = Field()
    publication_date = Field()
    print_length = Field()
    days_in_the_top_100 = Field()
    amazon_best_sellers_rank = Field()
    estimated_sales_per_day = Field()
    earnings_per_day = Field()
    total_number_of_reviews = Field()
    review_average = Field()
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


class Trend(Item):
    category = Field()
    section = Field()
    book = Field()
    date_and_time = Field()
    rank = Field()


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
            session.add(b)
        if isinstance(item, Review):
            b = self.get_book(session, item['book'])
            session.add(b)
            if not session.query(
                review,
            ).filter(
                review.book == b,
                review.author == item['author'],
                review.date == item['date'],
            ).count():
                session.add(review(**{
                    'author': item['author'],
                    'body': item['body'],
                    'book': b,
                    'date': item['date'],
                    'stars': item['stars'],
                    'subject': item['subject'],
                }))
        if isinstance(item, Referral):
            b = self.get_book(session, item['book'])
            session.add(b)
            if not session.query(
                referral,
            ).filter(
                referral.book == b,
                referral.url == item['url'],
            ).count():
                session.add(referral(**{
                    'author': item['author'],
                    'book': b,
                    'price': item['price'],
                    'review_average': item['review_average'],
                    'title': item['title'],
                    'total_number_of_reviews': item['total_number_of_reviews'],
                    'url': item['url']
                }))
        if isinstance(item, Trend):
            c = self.get_category(session, item['category'])
            session.add(c)
            s = self.get_section(session, item['section'])
            session.add(s)
            b = self.get_book(session, item['book'])
            session.add(b)
            if not session.query(
                trend,
            ).filter(
                trend.category == c,
                trend.section == s,
                trend.book == b,
                trend.date_and_time == item['date_and_time'],
            ).count():
                session.add(trend(**{
                    'book': b,
                    'category': c,
                    'date_and_time': item['date_and_time'],
                    'rank': item['rank'],
                    'section': s,
                }))
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
            book.url == dictionary['url'],
        ).first()
        if not b:
            b = book(**{
                'url': dictionary['url'],
            })
        b.author = dictionary['author']
        b.title = dictionary['title']
        b.price = dictionary['price']
        b.publication_date = dictionary['publication_date']
        b.print_length = dictionary['print_length']
        b.days_in_the_top_100 = dictionary['days_in_the_top_100']
        b.amazon_best_sellers_rank = dictionary['amazon_best_sellers_rank']
        b.estimated_sales_per_day = dictionary['estimated_sales_per_day']
        b.earnings_per_day = dictionary['earnings_per_day']
        b.total_number_of_reviews = dictionary['total_number_of_reviews']
        b.review_average = dictionary['review_average']
        return b

    def get_category(self, session, dictionary):
        return session.query(
            category,
        ).filter(
            category.url==sub(r'/gp/.*?/', '/gp/zgbs/', dictionary['url']),
        ).first()

    def get_section(self, session, dictionary):
        return session.query(
            section,
        ).filter(
            section.slug==dictionary['slug'],
        ).first()


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

    def __init__(self, *args, **kwargs):
        super(Spider, self).__init__(*args, **kwargs)
        self.start_urls = []
        session = get_mysql_session()()
        ss = session.query(section).order_by('id asc').all()
        for c in session.query(
            category,
        ).filter(
            category.category==None,
        ).order_by('id asc').all():
            for s in ss:
                self.start_urls.append(sub(
                    r'/zgbs/', '/%(slug)s/' % {
                        'slug': s.slug,
                    }, c.url
                ))
            if is_development():
                break
        session.close()

    def parse_pages(self, response):
        selector = None
        try:
            selector = Selector(response)
        except AttributeError:
            pass
        if not selector:
            return
        category_url = ''
        try:
            category_url = get_url(response.url)
        except IndexError:
            pass
        section_slug = response.url.split('/')[4]
        days_in_the_top_100 = 0
        for div in selector.xpath(
            '//div[@id="zg_centerListWrapper"]/div[@class="zg_itemImmersion"]'
        ):
            try:
                days_in_the_top_100 = int(get_number(get_string(div.xpath(
                    './/div/div/table/tr/td[@class="zg_daysInList"]/text()'
                ).extract()[0].split(' ')[0])))
            except IndexError:
                pass
            yield Request(
                callback=self.parse_book,
                dont_filter=True,
                meta={
                    'category': {
                        'url': category_url,
                    },
                    'days_in_the_top_100': days_in_the_top_100,
                    'rank': int(get_number(get_string(div.xpath(
                        './/div[@class="zg_rankDiv"]/'
                        'span[@class="zg_rankNumber"]/text()'
                    ).extract()[0][:-1]))),
                    'section': {
                        'slug': section_slug,
                    },
                },
                priority=100,
                url=get_string(div.xpath(
                    './/div[@class="zg_itemWrapper"]/'
                    'div[@class="zg_image"]/'
                    'div[@class="zg_itemImageImmersion"]/a/'
                    '@href'
                ).extract()[0]),
            )

    def parse_book(self, response):
        url = get_url(response.url)
        title = ''
        author = ''
        price = 0.00
        publication_date = ''
        print_length = 0
        days_in_the_top_100 = response.meta['days_in_the_top_100']
        amazon_best_sellers_rank = {}
        estimated_sales_per_day = 0
        earnings_per_day = 0.00
        total_number_of_reviews = 0
        review_average = 0.00
        reviews = []
        referrals = []
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
            print_length = int(get_number(get_string(selector.xpath(
                '//b[contains(text(), "Print Length")]/../text()'
            ).extract()[0])))
        except IndexError:
            try:
                print_length = int(get_number(get_string(selector.xpath(
                    '//li[contains(text(), "Length")]/a/span/text()'
                ).extract()[0])))
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
                    u'in\xa0', ''
                ).replace(
                    'Paid Kindle Store', 'Paid in Kindle Store'
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
                    ).replace(
                        u'in\xa0', ''
                    ).replace(
                        'Paid Kindle Store', 'Paid in Kindle Store'
                    )
                ] = int(get_number(get_string(li.xpath(
                    './/span[@class="zg_hrsr_rank"]/text()'
                ).extract()[0])))
        except IndexError:
            pass
        if amazon_best_sellers_rank:
            try:
                estimated_sales_per_day = get_sales(
                    amazon_best_sellers_rank['Paid in Kindle Store']
                )
            except KeyError:
                pass
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
        if url:
            book = {
                'amazon_best_sellers_rank': amazon_best_sellers_rank,
                'author': author,
                'days_in_the_top_100': days_in_the_top_100,
                'earnings_per_day': earnings_per_day,
                'estimated_sales_per_day': estimated_sales_per_day,
                'price': price,
                'print_length': print_length,
                'publication_date': publication_date,
                'referrals': referrals,
                'review_average': review_average,
                'reviews': reviews,
                'title': title,
                'total_number_of_reviews': total_number_of_reviews,
                'url': url,
            }
            yield Book(book)
            if reviews:
                yield Request(
                    callback=self.parse_reviews_1,
                    meta={
                        'book': book,
                    },
                    priority=1,
                    url=reviews,
                )
            if referrals:
                yield Request(
                    callback=self.parse_referrals,
                    meta={
                        'book': book,
                    },
                    priority=10,
                    url=furl(
                        'http://www.amazon.com/gp/product/features/'
                        'similarities/shoveler/cell-render.html/'
                    ).add({
                        'id': referrals,
                    }).url,
                )
            yield Trend({
                'book': book,
                'category': response.meta['category'],
                'section': response.meta['section'],
                'date_and_time': datetime.now().strftime('%Y-%m-%d %H:00:00'),
                'rank': response.meta['rank'],
            })

    def parse_reviews_1(self, response):
        selector = Selector(response)
        for text in [
            '1 star',
            '2 star',
            '3 star',
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
                    callback=self.parse_reviews_2,
                    meta={
                        'book': response.meta['book'],
                    },
                    priority=1,
                    url=href,
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
        '''
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
                priority=1,
                url=next,
            )
        '''
        # TO BE REMOVED

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
                url = get_url('http://www.amazon.com%(href)s' % {
                    'href': get_string(selector.xpath(
                        '//a[@class="sim-img-title"]/@href'
                    ).extract()[0])
                })
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
