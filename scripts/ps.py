# -*- coding: utf-8 -*-

from re import compile, sub
from socket import timeout
from string import lowercase

from requests import get
from requests.exceptions import RequestException
from scrapy.selector import Selector
from simplejson import loads
from simplejson.decoder import JSONDecodeError
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from utilities import (
    get_mysql_session,
    get_number,
    get_proxies,
    get_string,
    get_user_agent,
    popular_search,
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
    pss = []
    for alphabet in lowercase:
        contents = get_contents(
            'http://completion.amazon.com/search/complete?xcat=2&'
            'search-alias=aps&mkt=1&q=books%%20like%%20%(alphabet)s' % {
                'alphabet': alphabet,
            }
        )
        try:
            contents = loads(contents)
        except JSONDecodeError:
            pass
        if not contents:
            continue
        for keyword in contents[1]:
            if not keyword.startswith('books like'):
                continue
            keyword = get_string(keyword.replace('books like', ''))
            response = get_contents(
                'http://www.amazon.com/s/field-keywords='
                '%(keyword)s&prefix=%(keyword)s' % {
                    'keyword': keyword,
                }
            )
            if not response:
                continue
            keyword = get_string(sub(
                '[,\-+\.@\(\)";:\'/]+', '', keyword.lower()
            ))
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
                book_cover_image = ''
                title = ''
                author = ''
                amazon_best_sellers_rank = {}
                selector = Selector(text=response)
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
                    title = get_string(selector.xpath(
                        '//span[@id="btAsinTitle" or '
                        '@id="productTitle"]/text()'
                    ).extract()[0])
                except IndexError:
                    pass
                try:
                    author = get_string(selector.xpath(
                        '//h1[@class="parseasinTitle "]/'
                        'following-sibling::span/a/text()'
                    ).extract()[0])
                except IndexError:
                    pass
                if not keyword in get_string(sub(
                    '[,\-+\.@\(\)";:\'/]+', '', title.lower().split(':')[0]
                )) and not keyword in get_string(sub(
                    '[,\-+\.@\(\)";:\'/]+', '', author.lower().split(':')[0]
                )):
                    continue
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
                pss.append(popular_search(**{
                    'amazon_best_sellers_rank': amazon_best_sellers_rank,
                    'book_cover_image': book_cover_image,
                    'title': title,
                    'url': url,
                }))
    session = get_mysql_session()
    s = session()
    s.query(popular_search).delete()
    try:
        s.commit()
    except DBAPIError:
        s.rollback()
    except SQLAlchemyError:
        s.rollback()
    s.close()
    s = session()
    s.add_all(pss)
    try:
        s.commit()
    except DBAPIError:
        s.rollback()
    except SQLAlchemyError:
        s.rollback()
    s.close()
