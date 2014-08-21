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
    __tablename__ = 'tools_ps_books'

    amazon_best_sellers_rank = Column(mutators_dict.as_mutable(json))


class trend(base):
    __tablename__ = 'tools_ps_trends'
    __table_args__ = {
        'autoload': True,
    }

    book = relationship(
        'book', backref=backref('trends', cascade='all', lazy='dynamic'),
    )


if __name__ == '__main__':
    session = get_mysql_session()()
    bs = []
    date_and_time = datetime.now().strftime('%Y-%m-%d %H:00:00')
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
        for q in [
            'books like',
            'books similar to',
        ]
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
            if not keyword.startswith(q):
                continue
            keyword = get_string(keyword.replace(q, ''))
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
                    '//div[@id="result_0"]/h3[@class="newaps"]/a/@href'
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
                b = session.query(
                    book,
                ).filter(
                    book.url == url,
                ).first()
                if not b:
                    b = book(**{
                        'url': url,
                    })
                b.title = title
                b.book_cover_image = book_cover_image
                b.amazon_best_sellers_rank = amazon_best_sellers_rank
                bs.append(b)
    for b in bs:
        session.add(b)
        if not session.query(
            trend,
        ).filter(
            trend.book == b,
            trend.date_and_time == date_and_time,
        ).count():
            session.add(trend(**{
                'book': b,
                'date_and_time': date_and_time,
            }))
    try:
        session.commit()
    except DBAPIError:
        session.rollback()
    except SQLAlchemyError:
        session.rollback()
    session.close()
