# -*- coding: utf-8 -*-

from datetime import datetime
from re import compile
from string import lowercase

from furl import furl
from scrapy.selector import Selector
from simplejson import JSONDecodeError, loads
from sqlalchemy import Column
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import backref, relationship

from utilities import (
    base,
    get_amazon_best_sellers_rank,
    get_mysql_session,
    get_popularity,
    get_response,
    get_responses,
    get_string,
    get_url,
    is_development,
    json,
    mutators_dict,
)


class book(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_popular_searches_books'

    amazon_best_sellers_rank = Column(mutators_dict.as_mutable(json))


class trend(base):
    __tablename__ = 'apps_popular_searches_trends'
    __table_args__ = {
        'autoload': True,
    }

    keywords = Column(mutators_dict.as_mutable(json))

    book = relationship(
        'book', backref=backref('trends', cascade='all', lazy='dynamic'),
    )


if __name__ == '__main__':
    session = get_mysql_session()()
    items = []
    date_and_time = datetime.now().strftime('%Y-%m-%d %H:00:00')
    qs = [
        'books like',
        'books similar to',
    ]
    urls = [
        furl(
            'http://completion.amazon.com/search/complete'
        ).add({
            'mkt': '1',
            'q': '%(q)s %(alphabet)s' % {
                'alphabet': alphabet,
                'q': q,
            },
            'search-alias': 'digital-text',
            'xcat': '2',
        }).url
        for alphabet in lowercase
        for q in qs
    ]
    if is_development():
        urls = urls[0:5]
    for response in get_responses(urls):
        if not response:
            continue
        contents = None
        try:
            contents = loads(response.text)
        except JSONDecodeError:
            pass
        if not contents:
            continue
        for keyword in contents[1]:
            if not len([q for q in qs if keyword.startswith(q)]):
                continue
            for q in qs:
                keyword = keyword.replace(q, '')
            keyword = get_string(keyword)
            response = get_response(
                furl(
                    'http://www.amazon.com/s/'
                ).add({
                    'field-keywords': keyword,
                    'url': 'search-alias=digital-text',
                }).url
            )
            if not response:
                continue
            selector = Selector(text=response.text)
            url = ''
            try:
                url = get_url(selector.xpath(
                    '//a[normalize-space(@class)="'
                    'a-link-normal s-access-detail-page a-text-normal'
                    '"]/@href'
                ).extract()[0])
            except IndexError:
                pass
            if not url:
                continue
            response = get_response(url)
            if response:
                title = ''
                book_cover_image = ''
                amazon_best_sellers_rank = {}
                selector = Selector(text=response.text)
                try:
                    title = get_string(selector.xpath(
                        '//span[@id="btAsinTitle" or @id="productTitle"]/'
                        'text()'
                    ).extract()[0])
                except IndexError:
                    pass
                try:
                    book_cover_image = get_string(
                        compile(
                            r'\[\{"mainUrl":"([^"]*)'
                        ).search(
                            '\n'.join(
                                selector.xpath(
                                    '//script'
                                ).xpath(
                                    'string()'
                                ).extract()
                            )
                        ).group(1)
                    )
                except AttributeError:
                    try:
                        book_cover_image = get_string(selector.xpath(
                            '//img[@id="imgBlkFront" or @id="main-image"]/'
                            '@rel'
                        ).extract()[0])
                    except IndexError:
                        pass
                amazon_best_sellers_rank = get_amazon_best_sellers_rank(
                    selector
                )
                if (
                    not url
                    or
                    not title
                    or
                    not book_cover_image
                    or
                    not amazon_best_sellers_rank
                ):
                    continue
                items.append({
                    'amazon_best_sellers_rank': amazon_best_sellers_rank,
                    'book_cover_image': book_cover_image,
                    'keyword': keyword,
                    'title': title,
                    'url': url,
                })
    for item in items:
        b = session.query(
            book,
        ).filter(
            book.url == item['url'],
        ).first()
        if not b:
            b = book(**{
                'url': item['url'],
            })
        b.title = item['title']
        b.book_cover_image = item['book_cover_image']
        b.amazon_best_sellers_rank = item['amazon_best_sellers_rank']
        session.add(b)
        t = session.query(
            trend,
        ).filter(
            trend.book == b,
            trend.date_and_time == date_and_time,
        ).first()
        if not t:
            t = trend(**{
                'book': b,
                'date_and_time': date_and_time,
            })
        if not t.keywords:
            t.keywords = {}
        if not item['keyword'] in t.keywords:
            t.keywords[item['keyword']] = get_popularity(item['keyword'])[0]
        session.add(t)
    try:
        session.commit()
    except DBAPIError:
        session.rollback()
    except SQLAlchemyError:
        session.rollback()
    session.close()
