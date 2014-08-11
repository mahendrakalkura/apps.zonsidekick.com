# -*- coding: utf-8 -*-

from datetime import datetime
from re import compile, sub

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.item import Item, Field
from scrapy.selector import Selector
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy import Column, Integer
from sqlalchemy.orm import backref, relationship

from utilities import (
    base,
    get_amazon_best_sellers_rank,
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
    trend = Field()


class Trend(Item):
    category = Field()
    section = Field()
    book = Field()
    date = Field()
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
                trend.date == item['date'],
            ).count():
                session.add(trend(**{
                    'book': b,
                    'category': c,
                    'date': item['date'],
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
        if not b.author or dictionary['author']:
            b.author = dictionary['author']
        if not b.title or dictionary['title']:
            b.title = dictionary['title']
        if not b.price or dictionary['price']:
            b.price = dictionary['price']
        if not b.publication_date or dictionary['publication_date']:
            b.publication_date = dictionary['publication_date']
        if not b.print_length or dictionary['print_length']:
            b.print_length = dictionary['print_length']
        if not b.days_in_the_top_100 or dictionary['days_in_the_top_100']:
            b.days_in_the_top_100 = dictionary['days_in_the_top_100']
        if (
            not b.amazon_best_sellers_rank
            or
            dictionary['amazon_best_sellers_rank']
        ):
            b.amazon_best_sellers_rank = dictionary['amazon_best_sellers_rank']
        if (
            not b.estimated_sales_per_day
            or
            dictionary['estimated_sales_per_day']
        ):
            b.estimated_sales_per_day = dictionary['estimated_sales_per_day']
        if not b.earnings_per_day or dictionary['earnings_per_day']:
            b.earnings_per_day = dictionary['earnings_per_day']
        if (
            not b.total_number_of_reviews
            or
            dictionary['total_number_of_reviews']
        ):
            b.total_number_of_reviews = dictionary['total_number_of_reviews']
        if not b.review_average or dictionary['review_average']:
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
        urls = []
        for c_1 in session.query(
            category,
        ).filter(
            category.category==None,
        ).order_by('id asc').all():
            urls.append(c_1.url)
            for c_2 in session.query(
                category,
            ).filter(
                category.category==c_1,
            ).order_by('id asc').all():
                urls.append(c_2.url)
        if is_development():
            urls = urls[0:1]
        ss = session.query(section).order_by('id asc').all()
        for url in urls:
            for s in ss:
                self.start_urls.append(sub(
                    r'/zgbs/', '/%(slug)s/' % {
                        'slug': s.slug,
                    }, url
                ))
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
        amazon_best_sellers_rank = get_amazon_best_sellers_rank(selector)
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
                'review_average': review_average,
                'title': title,
                'total_number_of_reviews': total_number_of_reviews,
                'url': url,
            }
            yield Book(book)
            yield Trend({
                'book': book,
                'category': response.meta['category'],
                'section': response.meta['section'],
                'date': datetime.now().date().isoformat(),
                'rank': response.meta['rank'],
            })
