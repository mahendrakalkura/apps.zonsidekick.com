# -*- coding: utf-8 -*-

from datetime import datetime
from re import compile
from socket import timeout
from string import lowercase

from furl import furl
from requests import get
from requests.exceptions import RequestException
from scrapy.selector import Selector
from simplejson import loads
from simplejson.decoder import JSONDecodeError
from sqlalchemy import Column
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import backref, relationship

from utilities import (
    base,
    get_mysql_session,
    get_number,
    get_proxies,
    get_string,
    get_user_agent,
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


def get_contents(url):
    index = 0
    while True:
        index += 1
        if index >= 5:
            return ''
        try:
            response = get(
                url,
                headers={
                    'User-Agent': get_user_agent(),
                },
                proxies=get_proxies(),
                timeout=300,
            )
            if response and response.status_code == 200:
                return response.text
        except (RequestException, timeout):
            pass
    return ''

if __name__ == '__main__':
    session = get_mysql_session()()
    bs = []
    date_and_time = datetime.now().strftime('%Y-%m-%d %H:00:00')
    for q in [
        'books like',
        'books similar to',
    ]:
        for alphabet in lowercase:
            contents = None
            try:
                contents = loads(get_contents(
                    furl('http://completion.amazon.com/search/complete').add({
                        'mkt': '1',
                        'q': '%(q)s %(alphabet)s' % {
                            'alphabet': alphabet,
                            'q': q,
                        },
                        'search-alias': 'digital-text',
                        'xcat': '2',
                    }).url
                ))
            except JSONDecodeError:
                pass
            if not contents:
                continue
            for keyword in contents[1]:
                if not keyword.startswith(q):
                    continue
                keyword = get_string(keyword.replace(q, ''))
                response = get_contents(
                    furl('http://www.amazon.com/s/').add({
                        'field-keywords': keyword,
                        'url': 'search-alias=digital-text',
                    }).url
                )
                if not response:
                    continue
                selector = Selector(text=response)
                url = ''
                try:
                    url = selector.xpath(
                        '//div[@id="result_0"]/h3[@class="newaps"]/a/@href'
                    ).extract()[0]
                except IndexError:
                    pass
                if not url:
                    continue
                response = get_contents(url)
                if response:
                    title = ''
                    book_cover_image = ''
                    amazon_best_sellers_rank = {}
                    selector = Selector(text=response)
                    try:
                        title = get_string(selector.xpath(
                            '//span[@id="btAsinTitle" or '
                            '@id="productTitle"]/text()'
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
                            book_cover_image = get_string(
                                selector.xpath(
                                    '//img[@id="imgBlkFront" or '
                                    '@id="main-image"]/@rel'
                                ).extract()[0]
                            )
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
                        book.url==url,
                    ).first()
                    if not b:
                        b = book(**{
                            'amazon_best_sellers_rank': amazon_best_sellers_rank,
                            'book_cover_image': book_cover_image,
                            'title': title,
                            'url': url,
                        })
                    bs.append(b)
            if is_development():
                break
    for b in bs:
        session.add(b)
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
