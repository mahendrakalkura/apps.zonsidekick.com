# -*- coding: utf-8 -*-

from gevent import monkey

monkey.patch_all()
monkey.patch_socket()
monkey.patch_ssl()

from collections import Counter
from csv import QUOTE_ALL, reader
from datetime import date, datetime
from locale import LC_ALL, format, setlocale
from logging import CRITICAL, getLogger
from math import sqrt
from os.path import dirname, join
from re import compile, sub
from sys import argv

from dateutil import relativedelta
from dateutil.parser import parse
from furl import furl
from numpy import mean
from rollbar import report_message
from scrapy.selector import Selector
from simplejson import dumps

from utilities import (
    get_mysql_connection,
    get_popularity,
    get_responses,
    get_string,
    get_sales,
    get_url as get_url_,
    get_words,
    timer,
)

getLogger('gevent').setLevel(CRITICAL)
getLogger('requests').setLevel(CRITICAL)

setlocale(LC_ALL, 'en_US.UTF-8')

points = {
    'buyer_behavior': {
        'Very High': 4,
        'High': 3,
        'Medium': 2,
        'Low': 1,
        'Very Low': 0,
    },
    'competition': {
        'Very High': 0,
        'High': 1,
        'Medium': 2,
        'Low': 3,
        'Very Low': 4,
    },
    'optimization': {
        'Very High': 0,
        'High': 1,
        'Medium': 2,
        'Low': 3,
        'Very Low': 4,
    },
    'spend': {
        'Very High': 4,
        'High': 3,
        'Medium': 2,
        'Low': 1,
        'Very Low': 0,
    },
    'popularity': {
        'Very High': 4,
        'High': 3,
        'Medium': 2,
        'Low': 1,
        'Very Low': 0,
    },
}


def get_keywords(reports):
    keywords = []
    mysql = get_mysql_connection()
    for report in reports:
        cursor = mysql.cursor()
        cursor.execute(
            '''
            SELECT `id`, `string`
            FROM `apps_keyword_analyzer_keywords`
            WHERE `report_id` = %(report_id)s AND `contents` IS NULL
            ORDER BY RAND()
            ''',
            {
                'report_id': report['id'],
            }
        )
        for row in cursor.fetchall():
            keywords.append({
                'country': report['country'],
                'id': row['id'],
                'string': row['string'],
            })
        cursor.close()
    mysql.close()
    return keywords


def get_reports(user):
    mysql = get_mysql_connection()
    cursor = mysql.cursor()
    cursor.execute(
        '''
        SELECT `id`, `country`
        FROM `apps_keyword_analyzer_reports`
        WHERE `user_id` = %(user_id)s
        ORDER BY `id` ASC
        ''',
        {
            'user_id': user['ID'],
        }
    )
    reports = cursor.fetchall()
    cursor.close()
    mysql.close()
    return reports


def get_users():
    mysql = get_mysql_connection()
    cursor = mysql.cursor()
    cursor.execute('SELECT `ID` FROM `wp_users` ORDER BY `ID` ASC')
    users = cursor.fetchall()
    cursor.close()
    mysql.close()
    return users


def main():
    mysql = get_mysql_connection()
    cursor = mysql.cursor()
    cursor.execute(
        '''
        DELETE FROM `apps_keyword_analyzer_reports`
        WHERE `timestamp` < NOW() - INTERVAL 30 DAY
        '''
    )
    cursor.close()
    mysql.commit()
    mysql.close()

    keywords = []
    for user in get_users():
        for keyword in get_keywords(get_reports(user)):
            keywords.append({
                'country': keyword['country'],
                'id': keyword['id'],
                'string': keyword['string'],
            })
            break

    mysql = get_mysql_connection()
    total = len(keywords)
    for index, keyword in enumerate(keywords):
        status = '-'
        contents = get_contents(keyword['string'], keyword['country'])
        if contents:
            status = '+'
            cursor = mysql.cursor()
            cursor.execute(
                '''
                UPDATE `apps_keyword_analyzer_keywords`
                SET `contents` = %(contents)s, `timestamp` = %(timestamp)s
                WHERE `id` = %(id)s
                ''',
                {
                    'contents': dumps(contents),
                    'id': keyword['id'],
                    'timestamp': datetime.utcnow(),
                }
            )
            cursor.close()
            mysql.commit()
        print (
            '%(datetime)s => [%(index)5d/%(total)5d] [%(status)s] %(id)09d: '
            '%(string)s %(country)s'
        ) % {
            'country': keyword['country'],
            'datetime': datetime.now().isoformat(' '),
            'id': keyword['id'],
            'index': index + 1,
            'status': status,
            'string': keyword['string'].encode('utf-8'),
            'total': total,
        }
    mysql.close()


def get_age(one, two):
    age = 0
    relative_delta = relativedelta.relativedelta(one, two)
    if relative_delta.years:
        age += relative_delta.years * 365
    if relative_delta.months:
        age += relative_delta.months * 30
    if relative_delta.days:
        age += relative_delta.days
    return age


def get_average(items):
    length = len(items)
    if length:
        return (sum(items) * 1.00) / (length * 1.00)
    return 0.00


def get_buyer_behavior(items):
    asins = {}
    for item in items:
        asins[item['asin']] = item['spend'][0]
    numbers = {
        '01:05': len(set([
            asin
            for item in items[0:5]
            for asin in item['related_items']
            if asin in asins
        ])),
        '01:48': len(set([
            asin
            for item in items
            for asin in item['related_items']
            if asin in asins
        ])),
    }
    number = 0.00
    if numbers['01:48']:
        number = (numbers['01:05'] * 100.00) / (numbers['01:48'] * 1.00)
    if number > 80.00:
        return number, 'Very High'
    if number > 60.00:
        return number, 'High'
    if number > 40.00:
        return number, 'Medium'
    if number > 20.00:
        return number, 'Low'
    return number, 'Very Low'


def get_competition(items):
    numbers = {
        'bottom': {
            '01:12': 0.00,
            '01:24': 0.00,
        },
        'top': {
            '01:01': 0.00,
            '01:05': 0.00,
            '01:12': 0.00,
        }
    }
    standard_deviation = 0.00
    spends = sorted([
        item['spend'][0] for item in items if item['spend'][0]
    ], reverse=True)
    total = sum(spends)
    if spends and total:
        numbers['top']['01:01'] = (
            (sum(spends[00:01]) * 1.00) / (total * 1.00)
        )
        numbers['top']['01:05'] = (
            (sum(spends[00:05]) * 1.00) / (total * 1.00)
        )
        numbers['top']['01:12'] = (
            (sum(spends[00:12]) * 1.00) / (total * 1.00)
        )
        standard_deviation = sqrt(get_average(map(
            lambda number: (number - get_average(spends)) ** 2, spends
        )))
        numbers['bottom']['01:12'] = (
            (sum(spends[::-1][00:12]) * 1.00) / (total * 1.00)
        )
        numbers['bottom']['01:24'] = (
            (sum(spends[::-1][00:24]) * 1.00) / (total * 1.00)
        )
    if numbers['top']['01:01'] > 75.00:
        return 10, 'Very High'
    if numbers['top']['01:05'] > 75.00:
        return 10, 'Very High'
    if numbers['top']['01:12'] > 90.00:
        return 10, 'Very High'
    if standard_deviation > 100.00:
        return 10, 'Very High'
    if numbers['top']['01:05'] > 50.00:
        return 8, 'High'
    if numbers['top']['01:12'] > 65.00:
        return 8, 'High'
    if numbers['bottom']['01:12'] > 10.00:
        return 6, 'Medium'
    if numbers['bottom']['01:24'] > 25.00:
        return 6, 'Medium'
    if numbers['bottom']['01:24'] < 50.00:
        return 4, 'Low'
    return 2, 'Very Low'


def get_contents(keyword, country):
    with timer('Step 1'):
        responses = get_responses([
            get_url(country, keyword, page) for page in ['1']
        ])
        if None in responses:
            return
    with timer('Step 2'):
        breadcrumb = ''
        for response in responses[0:1]:
            if '"noResultsTitle"' in response.text:
                return {
                    'average_length': [-1, 'N/A'],
                    'average_price': [-1, 'N/A'],
                    'buyer_behavior': [-1, 'N/A'],
                    'competition': [-1, 'N/A'],
                    'count': [0, '0'],
                    'items': [],
                    'matches': [0, 0],
                    'optimization': [-1, 'N/A'],
                    'popularity': (-1, 'N/A'),
                    'score': [-1, 'N/A'],
                    'spend': [[-1, 'N/A'], 'N/A'],
                    'words': [],
                }
            try:
                breadcrumb = Selector(text=response.text).xpath(
                    '//h2[@id="s-result-count"]/a/text()'
                ).extract()[0]
            except IndexError:
                try:
                    breadcrumb = Selector(text=response.text).xpath(
                        '//h2[@id="s-result-count"]/span/a/text()'
                    ).extract()[0]
                except IndexError:
                    pass
    with timer('Step 3'):
        count = 0
        if (
            breadcrumb == 'Kindle Store'
            or
            (country == 'co.jp' and 'Kindle' in breadcrumb)
            or
            (country == 'de' and breadcrumb == 'Kindle-Shop')
        ):
            for response in responses:
                if not count:
                    try:
                        count = int(
                            Selector(
                                text=response.text
                            ).xpath(
                                '//h2[@id="s-result-count"]'
                            ).xpath(
                                'string()'
                            ).extract()[0].strip().split(
                                ' '
                            )[0].replace(
                                '.', ''
                            ).replace(
                                ',', ''
                            ).replace(
                                u'件中', ''
                            )
                        )
                    except (IndexError, ValueError):
                        pass
                if not count:
                    try:
                        count = int(
                            Selector(
                                text=response.text
                            ).xpath(
                                '//h2[@id="s-result-count"]'
                            ).xpath(
                                'string()'
                            ).extract()[0].strip().split(
                                ' '
                            )[1].replace(
                                '.', ''
                            ).replace(
                                ',', ''
                            ).replace(
                                u'件中', ''
                            )
                        )
                    except (IndexError, ValueError):
                        pass
                if not count:
                    try:
                        count = int(
                            Selector(
                                text=response.text
                            ).xpath(
                                '//h2[@id="s-result-count"]'
                            ).xpath(
                                'string()'
                            ).extract()[0].strip().split(
                                ' '
                            )[2].replace(
                                '.', ''
                            ).replace(
                                ',', ''
                            ).replace(
                                u'件中', ''
                            )
                        )
                    except (IndexError, ValueError):
                        pass
        if not count:
            return {
                'average_length': [-1, 'N/A'],
                'average_price': [-1, 'N/A'],
                'buyer_behavior': [-1, 'N/A'],
                'competition': [-1, 'N/A'],
                'count': [0, '0'],
                'items': [],
                'matches': [0, 0],
                'optimization': [-1, 'N/A'],
                'popularity': (-1, 'N/A'),
                'score': [-1, 'N/A'],
                'spend': [[-1, 'N/A'], 'N/A'],
                'words': [],
            }
    with timer('Step 4'):
        count = (count, get_int(count))
        urls = []
        if (
            breadcrumb == 'Kindle Store'
            or
            (country == 'co.jp' and 'Kindle' in breadcrumb)
            or
            (country == 'de' and breadcrumb == 'Kindle-Shop')
        ):
            for response in responses:
                for href in Selector(
                    text=response.text
                ).xpath(
                    '//a[normalize-space(@class)="'
                    'a-link-normal s-access-detail-page a-text-normal'
                    '"]/@href'
                ).extract():
                    if not href.startswith('http'):
                        href = 'http://www.amazon.%(country)s%(href)s' % {
                            'country': country,
                            'href': href,
                        }
                    urls.append(href)
        if not urls:
            return {
                'average_length': [-1, 'N/A'],
                'average_price': [-1, 'N/A'],
                'buyer_behavior': [-1, 'N/A'],
                'competition': [-1, 'N/A'],
                'count': [0, '0'],
                'items': [],
                'matches': [0, 0],
                'optimization': [-1, 'N/A'],
                'popularity': (-1, 'N/A'),
                'score': [-1, 'N/A'],
                'spend': [[-1, 'N/A'], 'N/A'],
                'words': [],
            }
    with timer('Step 5'):
        responses = get_responses(urls[0:48])
        if not responses:
            return {
                'average_length': [-1, 'N/A'],
                'average_price': [-1, 'N/A'],
                'buyer_behavior': [-1, 'N/A'],
                'competition': [-1, 'N/A'],
                'count': [0, '0'],
                'items': [],
                'matches': [0, 0],
                'optimization': [-1, 'N/A'],
                'popularity': (-1, 'N/A'),
                'score': [-1, 'N/A'],
                'spend': [[-1, 'N/A'], 'N/A'],
                'words': [],
            }
    with timer('Step 6'):
        items = []
        index = 0
        for response in responses:
            if not response:
                continue
            index += 1
            try:
                selector = Selector(text=response.text)
            except AttributeError:
                continue
            asin = ''
            try:
                asin = get_string(
                    selector.xpath(
                        '//input[@name="ASIN.0"]/@value'
                    ).extract()[0]
                )
            except IndexError:
                pass
            author = {
                'name': '',
                'url': '',
            }
            if not author['name']:
                try:
                    author['name'] = get_string(selector.xpath(
                        '//span[@class="contributorNameTrigger"]/a/text()'
                    ).extract()[0])
                except IndexError:
                    pass
            if not author['name']:
                try:
                    author['name'] = get_string(selector.xpath(
                        '//h1[normalize-space(@class)="parseasinTitle"]/'
                        'following-sibling::span/a/text()'
                    ).extract()[0])
                except IndexError:
                    pass
            if not author['name']:
                try:
                    author['name'] = get_string(selector.xpath(
                        '//span[contains(@class, "author")]/a/text()'
                    ).extract()[0])
                except IndexError:
                    pass
            if not author['url']:
                try:
                    author['url'] = get_url_(get_string(selector.xpath(
                        '//span[@class="contributorNameTrigger"]/a/@href'
                    ).extract()[0]))
                except IndexError:
                    pass
            if not author['url']:
                try:
                    author['url'] = get_url_(get_string(
                        'http://www.amazon.%(country)s/%(href)s' % {
                            'country': country,
                            'href': selector.xpath(
                                '//h1'
                                '[normalize-space(@class)="parseasinTitle"]/'
                                'following-sibling::span/a/@href'
                            ).extract()[0]
                        }
                    ))
                except IndexError:
                    pass
            if not author['url']:
                try:
                    author['url'] = get_string(selector.xpath(
                        '//span[contains(@class, "author")]/a/@href'
                    ).extract()[0])
                except IndexError:
                    pass
            best_sellers_rank = 0
            try:
                best_sellers_rank = int(
                    get_string(
                        selector.xpath(
                            '//li[@id="SalesRank"]/text()'
                        ).extract()[1]
                    ).split(
                        ' '
                    )[0].replace(
                        '#', ''
                    ).replace(
                        ',', ''
                    ).replace(
                        '.', ''
                    )
                )
            except (IndexError, ValueError):
                try:
                    best_sellers_rank = int(
                        get_string(
                            selector.xpath(
                                '//span[@class="zg_hrsr_rank"]/text()'
                            ).extract()[0]
                        ).replace(
                            u'\u4f4d', ''
                        ).replace(
                            ',', ''
                        ).replace(
                            '#', ''
                        )
                    )
                except (IndexError, ValueError):
                    pass

            best_sellers_rank = (best_sellers_rank, get_int(best_sellers_rank))
            description = ''
            try:
                description = get_string(
                    selector.xpath(
                        '//div[@id="postBodyPS"]'
                    ).xpath('string()').extract()[0]
                )
            except IndexError:
                try:
                    description = get_string(
                        selector.xpath(
                            '//div[@class="productDescriptionWrapper"]'
                        ).xpath('string()').extract()[1]
                    )
                except IndexError:
                    try:
                        description = get_string(
                            selector.xpath(
                                '//div[@class="productDescriptionWrapper"]'
                            ).xpath('string()').extract()[0]
                        )
                    except IndexError:
                        try:
                            description = get_string(
                                selector.xpath(
                                    '//span[contains('
                                    '@class, "detail-description-text"'
                                    ')]'
                                ).xpath('string()').extract()[0]
                            )
                        except IndexError:
                            pass
            if not description:
                try:
                    description = get_string(' '.join(
                        selector.xpath(
                            '//div[contains(@id, "postBodyPS")]/../'
                            'preceding-sibling::noscript'
                        ).xpath('string()').extract()
                    ))
                except IndexError:
                    pass
            pages = 0
            try:
                pages = int(get_string(
                    selector.xpath(
                        '//b[contains(text(), "Print Length:")]/../text()'
                    ).extract()[0]
                ).split(' ')[0].replace(',', ''))
            except (IndexError, ValueError):
                try:
                    pages = int(
                        compile(r'(\d+)').search(
                            get_string(selector.xpath(
                                '//a[@id="pageCountAvailable"]/span/text()'
                            ).extract()[0])
                        ).group(1)
                    )
                except (IndexError, TypeError, ValueError):
                    pass
            pages = (pages, get_int(pages))
            price = 0.00
            if country != 'co.jp':
                if not price:
                    try:
                        price = float(
                            get_string(
                                selector.xpath(
                                    '//b[@class="priceLarge"]/text()'
                                ).extract()[0]
                            ).replace(
                                '$', ''
                            ).replace(
                                'Rs. ', ''
                            ).replace(
                                ',', ''
                            ).encode(
                                'utf-8'
                            ).replace(
                                '\xc2\xa3', ''
                            ).replace(
                                'EUR', ''
                            )
                        )
                    except (IndexError, ValueError):
                        pass
                if not price:
                    try:
                        price = float(
                            get_string(
                                selector.xpath(
                                    '//span[@class="priceLarge"]/text()'
                                ).extract()[0]
                            ).replace(
                                '$', ''
                            ).replace(
                                'Rs. ', ''
                            ).replace(
                                ',', ''
                            ).encode(
                                'utf-8'
                            ).replace(
                                '\xc2\xa3', ''
                            ).replace(
                                'EUR', ''
                            )
                        )
                    except (IndexError, ValueError):
                        pass
            else:
                if not price:
                    try:
                        price = float(get_string(selector.xpath(
                            '//b[@class="priceLarge"]/text()'
                        ).extract()[0]).replace(',', '').replace(u'\uffe5', ''))
                    except IndexError:
                        pass
                if not price:
                    try:
                        price = float(
                            get_string(
                                selector.xpath(
                                    '//span[@class="priceLarge"]/text()'
                                ).extract()[0]
                            ).replace(
                                ',', ''
                            ).replace(
                                u'\uffe5', ''
                            )
                        )
                    except IndexError:
                        pass
            if not price:
                try:
                    price = float(
                        get_string(
                            selector.xpath(
                                '//span[contains(@class, "a-color-price")]/'
                                'text()'
                            ).extract()[0]
                        ).replace(
                            '$', ''
                        ).replace(
                            'Rs. ', ''
                        ).replace(
                            ',', ''
                        ).encode(
                            'utf-8'
                        ).replace(
                            '\xc2\xa3', ''
                        ).replace(
                            'EUR', ''
                        )
                    )
                except (IndexError, ValueError):
                    pass
            price = (price, get_float(price))
            publication_date = ''
            try:
                publication_date = get_string(
                    selector.xpath(
                        '//input[@id="pubdate"]/@value'
                    ).extract()[0][0:10]
                )
            except IndexError:
                pass
            age = ''
            if publication_date:
                try:
                    age = get_int(get_age(
                        date.today(),
                        date(*tuple(map(int, publication_date.split('-'))))
                    ))
                except IndexError:
                    pass
            else:
                try:
                    publication_date = parse(get_string(selector.xpath(
                        '//b[contains(text(), "Publication Date")]/../text()'
                    ).extract()[0])).date()
                    age = get_int(get_age(date.today(), publication_date))
                    publication_date = publication_date.isoformat()
                except IndexError:
                    pass
            if not publication_date:
                try:
                    publication_date = compile('\((.*?)\)').search(
                        get_string(
                            selector.xpath(
                                '//b[contains(text(), "Publisher")'
                                'or '
                                'contains(text(), "Editore")]/../text()'
                            ).extract()[0]
                        )
                    ).group(1)
                    publication_date = sub(
                        '[gG]ennaio', 'January', publication_date
                    )
                    publication_date = sub(
                        '[fF]ebbraio', 'February', publication_date
                    )
                    publication_date = sub(
                        '[mM]arzo', 'March', publication_date
                    )
                    publication_date = sub(
                        '[aA]prile', 'April', publication_date
                    )
                    publication_date = sub(
                        '[mM]aggio', 'May', publication_date
                    )
                    publication_date = sub(
                        '[gG]iugno', 'June', publication_date
                    )
                    publication_date = sub(
                        '[lL]uglio', 'July', publication_date
                    )
                    publication_date = sub(
                        '[aA]gosto', 'August', publication_date
                    )
                    publication_date = sub(
                        '[sS]ettembre', 'September', publication_date
                    )
                    publication_date = sub(
                        '[oO]ttobre', 'October', publication_date
                    )
                    publication_date = sub(
                        '[nN]ovembre', 'November', publication_date
                    )
                    publication_date = sub(
                        '[dD]icembre', 'December', publication_date
                    )
                    publication_date = parse(
                        publication_date
                    ).date()
                    age = get_int(get_age(date.today(), publication_date))
                    publication_date = publication_date.isoformat()
                except (AttributeError, IndexError, TypeError, ValueError):
                    try:
                        publication_date = parse(compile('\((.*?)\)').search(
                            get_string(selector.xpath(
                                '//div[@class="content"]/ul/li[4]/text()'
                            ).extract()[0])
                        ).group(1)).date()
                        age = get_int(get_age(date.today(), publication_date))
                        publication_date = publication_date.isoformat()
                    except (AttributeError, IndexError, TypeError):
                        try:
                            publication_date = parse(compile(
                                '\((.*?)\)'
                            ).search(
                                get_string(selector.xpath(
                                    '//div[@class="content"]/ul/li[5]/text()'
                                ).extract()[0])
                            ).group(1)).date()
                            age = get_int(get_age(
                                date.today(), publication_date
                            ))
                            publication_date = publication_date.isoformat()
                        except (
                            AttributeError, IndexError, TypeError, ValueError
                        ):
                            try:
                                publication_date = compile('\((.*?)\)').search(
                                    get_string(selector.xpath(
                                        '//b[contains(text(), "Verlag")]/../'
                                        'text()'
                                    ).extract()[0])
                                ).group(1)
                                publication_date = sub(
                                    '[jJ]anuar', 'January', publication_date
                                )
                                publication_date = sub(
                                    '[fF]ebruar', 'February', publication_date
                                )
                                publication_date = sub(
                                    '[mM].rz', 'March', publication_date
                                )
                                publication_date = sub(
                                    '[mM]ai', 'May', publication_date
                                )
                                publication_date = sub(
                                    '[jJ]uni', 'June', publication_date
                                )
                                publication_date = sub(
                                    '[jJ]uli', 'July', publication_date
                                )
                                publication_date = sub(
                                    '[oO]ktober', 'October', publication_date
                                )
                                publication_date = sub(
                                    '[dD]ezember', 'December', publication_date
                                )
                                publication_date = parse(
                                    publication_date
                                ).date()
                                age = get_int(get_age(
                                    date.today(), publication_date
                                ))
                                publication_date = publication_date.isoformat()
                            except (AttributeError, IndexError, TypeError):
                                pass
            rank = (index, get_int(index))
            related_items = ''
            try:
                related_items = get_string(selector.xpath(
                    '//div[@id="purchaseData"]/text()'
                ).extract()[0]).split(',')
            except IndexError:
                pass
            spend = 0.00
            if best_sellers_rank[0] and price[0]:
                spend = get_sales(best_sellers_rank[0]) * price[0]
            spend = (spend, get_float(spend))
            stars = 0.0
            try:
                stars = float(
                    get_string(
                        selector.xpath(
                            '//div[@class="gry txtnormal acrRating"]/text()'
                        ).extract()[0]
                    ).split(' ')[0].replace(',', '').replace(u'つ星のうち', '')
                )
            except IndexError:
                try:
                    stars = float(get_string(
                        selector.xpath(
                            '//span[contains(@class, "swSprite")]/@title'
                        ).extract()[0][-3:]
                    ))
                except (IndexError, ValueError):
                    try:
                        stars = float(get_string(selector.xpath(
                            '//span[contains(@class, "swSprite")]/@title'
                        ).extract()[1])[0:3])
                    except (IndexError, ValueError):
                        pass
            stars = (stars, get_float(stars))
            title_1 = ''
            try:
                title_1 = get_string(
                    selector.xpath(
                        '//span[@id="btAsinTitle"]/text()'
                    ).extract()[0]
                )
            except IndexError:
                pass
            if not title_1:
                try:
                    title_1 = get_string(
                        selector.xpath(
                            '//span[@id="btAsinTitle"]/span/text()'
                        ).extract()[0]
                    )
                except IndexError:
                    pass
            if not title_1:
                try:
                    title_1 = get_string(
                        selector.xpath(
                            '//span[@id="productTitle"]/text()'
                        ).extract()[0]
                    )
                except IndexError:
                    pass
            title_2 = 'Partial'
            if keyword.lower() in title_1.lower():
                title_2 = 'Exact'
            if title_1:
                items.append({
                    'age': age,
                    'asin': asin,
                    'author': author,
                    'best_sellers_rank': best_sellers_rank,
                    'description': description,
                    'pages': pages,
                    'price': price,
                    'publication_date': publication_date,
                    'rank': rank,
                    'related_items': related_items,
                    'spend': spend,
                    'stars': stars,
                    'title': [title_1, title_2],
                    'url': response.url,
                })
        if not items:
            return {
                'average_length': [-1, 'N/A'],
                'average_price': [-1, 'N/A'],
                'buyer_behavior': [-1, 'N/A'],
                'competition': [-1, 'N/A'],
                'count': [0, '0'],
                'items': [],
                'matches': [0, 0],
                'optimization': [-1, 'N/A'],
                'popularity': (-1, 'N/A'),
                'score': [-1, 'N/A'],
                'spend': [[-1, 'N/A'], 'N/A'],
                'words': [],
            }
    with timer('Step 7'):
        price = sum([item['price'][0] for item in items])
        average_length = mean([
            item['pages'][0] for item in items if item['pages'][0]
        ] or [0.00])
        average_price = mean([
            item['price'][0] for item in items if item['price'][0]
        ] or [0.00])
        buyer_behavior = get_buyer_behavior(items) if price else (-1, 'N/A')
        competition = get_competition(items) if price else (-1, 'N/A')
        optimization = get_optimization(
            keyword, items
        ) if price else (-1, 'N/A')
        spend = get_spend(items) if price else ((-1, 'N/A'), 'N/A')
        popularity = get_popularity(keyword) if price else (-1, 'N/A')
    return {
        'average_length': (
            average_length, get_float(average_length)
        ) if price else (-1, 'N/A'),
        'average_price': (
            average_price, get_float(average_price)
        ) if price else (-1, 'N/A'),
        'buyer_behavior': buyer_behavior,
        'competition': competition,
        'count': count,
        'items': items,
        'matches': get_matches(items),
        'optimization': optimization,
        'popularity': popularity,
        'score': get_score(
            buyer_behavior, competition, optimization, popularity, spend,
        ) if price else (-1, 'N/A'),
        'spend': spend,
        'words': get_words([item['title'][0] for item in items], 10),
    }


def get_float(value):
    if not value:
        value = 0
    value = float(value)
    return format('%.2f', value, grouping=True)


def get_int(value):
    if not value:
        value = 0
    value = int(value)
    return format('%d', value, grouping=True)


def get_matches(items):
    matches = [0, 0]
    length = len(items)
    if length:
        matches[0] = len([
            item for item in items if item['title'][1] == 'Exact'
        ])
        matches[1] = length - matches[0]
    return matches


def get_optimization(keyword, items):
    description = Counter(' '.join([
        item['description'] for item in items[0:3]
    ]).split(' '))
    items = []
    for string in keyword.split(' '):
        if string in description:
            items.append(
                (description[string] * 100.00)
                /
                (sum(description.values()) * 1.00)
            )
        else:
            items.append(0.00)
    number = 0.00
    length = len(items)
    if length:
        number = (sum(items) * 1.00) / (length * 1.00)
    if number > 25.00 and number <= 35.00:
        return number, 'Very High'
    if number > 10.00 and number <= 25.00:
        return number, 'High'
    if number > 0.00 and number <= 10.00:
        return number, 'Medium'
    if number > 35.00:
        return number, 'Low'
    return number, 'Very Low'


def get_spend(items):
    number = sum([item['spend'][0] for item in items])
    number = (number, get_float(number))
    if number[0] >= 5000.00:
        return number, 'Very High'
    if number[0] >= 1000.00:
        return number, 'High'
    if number[0] >= 100.00:
        return number, 'Medium'
    if number[0] >= 10.00:
        return number, 'Low'
    return number, 'Very Low'


def get_score(buyer_behavior, competition, optimization, popularity, spend):
    score = 0.00
    key = '-'.join([
        competition[1],
        spend[1],
    ])
    with open(join(dirname(__file__), '1.csv'), 'r') as resource:
        for row in list(reader(
            resource,
            delimiter=',',
            doublequote=True,
            lineterminator='\n',
            quotechar='"',
            quoting=QUOTE_ALL,
            skipinitialspace=False,
        ))[1:]:
            if key == '-'.join([row[0], row[1]]):
                score += float(row[2])
                break
    key = '-'.join([
        buyer_behavior[1],
        optimization[1],
    ])
    with open(join(dirname(__file__), '2.csv'), 'r') as resource:
        for row in list(reader(
            resource,
            delimiter=',',
            doublequote=True,
            lineterminator='\n',
            quotechar='"',
            quoting=QUOTE_ALL,
            skipinitialspace=False,
        ))[1:]:
            if key == '-'.join([row[0], row[1]]):
                score += float(row[2])
                break
    score = score + (popularity[0] * 0.20)
    return score, get_float(score)


def get_url(country, keyword, page):
    if country == 'co.uk' or country == 'es' or country == 'fr':
        return furl(
            'http://www.amazon.co.uk/s/'
        ).add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:341677031,k:%(keyword)s,' % {
                'keyword': keyword,
            },
        }).url
    if country == 'co.jp':
        return furl(
            'http://www.amazon.co.jp/s/'
        ).add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:2250738051,k:%(keyword)s' % {
                'keyword': keyword,
            },
        }).url
    if country == 'de':
        return furl(
            'http://www.amazon.de/s/'
        ).add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:530484031,k:%(keyword)s' % {
                'keyword': keyword,
            },
        }).url
    if country == 'it':
        return furl(
            'http://www.amazon.it/s/'
        ).add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:818937031,k:%(keyword)s,' % {
                'keyword': keyword,
            },
        }).url
    return furl(
        'http://www.amazon.com/s/'
    ).add({
        'fromApp': 'gp/search',
        'fromPage': 'results',
        'keywords': keyword,
        'page': page,
        'rh': 'n:133140011,n:154606011,k:%(keyword)s' % {
            'keyword': keyword,
        },
        'version': 2,
    }).url


if __name__ == '__main__':
    if len(argv) == 3:
        contents = get_contents(argv[1], argv[2])
        if not contents:
            report_message(
                'get_contents()',
                extra_data={
                    'country': argv[2],
                    'keyword': argv[1],
                },
                level='critical',
            )
        print dumps(contents)
    else:
        main()
