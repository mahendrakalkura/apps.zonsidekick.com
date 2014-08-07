# -*- coding: utf-8 -*-

from gevent import monkey

monkey.patch_all()
monkey.patch_socket()
monkey.patch_ssl()

from collections import Counter
from csv import QUOTE_ALL, reader
from datetime import date, datetime
from locale import LC_ALL, format, setlocale
from math import sqrt
from os.path import dirname, join
from re import compile, sub

from dateutil import relativedelta
from dateutil.parser import parse
from furl import furl
from grequests import get, map as map_
from numpy import mean
from scrapy.selector import Selector
from simplejson import dumps

from utilities import get_cleaned_string, get_mysql, get_proxies

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
}


def get_keywords(requests):
    keywords = []
    mysql = get_mysql()
    for request in requests:
        cursor = mysql.cursor()
        cursor.execute(
            '''
            SELECT `id`, `string`
            FROM `tools_kns_keywords`
            WHERE `request_id` = %(request_id)s AND `contents` IS NULL
            ORDER BY `id` ASC
            ''', {
                'request_id': request['id'],
            }
        )
        for row in cursor.fetchall():
            keywords.append({
                'country': request['country'],
                'id': row['id'],
                'string': row['string'],
            })
        cursor.close()
    mysql.close()
    return keywords


def get_requests(user):
    mysql = get_mysql()
    cursor = mysql.cursor()
    cursor.execute(
        '''
        SELECT `id`, `country`
        FROM `tools_kns_requests`
        WHERE `user_id` = %(user_id)s
        ORDER BY `id` ASC
        ''', {
            'user_id': user['ID'],
        }
    )
    requests = cursor.fetchall()
    cursor.close()
    mysql.close()
    return requests


def get_responses(urls):
    responses = {}
    for url in urls:
        responses[url] = None
    index = 0
    while True:
        index += 1
        keys = [key for key in responses if not responses[key]]
        if not keys:
            return responses.values()
        if index >= 5:
            return responses.values()
        try:
            for response in map_(get(
                key,
                allow_redirects=True,
                headers={
                    'Accept': (
                        'text/html,application/xhtml+xml,application/xml;'
                        'q=0.9,*/*;q=0.8'
                    ),
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                    'Accept-Encoding': 'gzip,deflate,sdch',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Host': 'www.amazon.com',
                    'Referer': 'http://www.amazon.com',
                    'User-Agent': (
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 '
                        '(KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31'
                    ),
                },
                proxies=get_proxies(),
                timeout=300,
                verify=False,
            ) for key in keys):
                if (
                    response
                    and
                    response.status_code == 200
                    and
                    not 'Enter the characters you see below' in response.text
                ):
                    responses[response.request.url] = response
        except Exception:
            pass


def get_users():
    mysql = get_mysql()
    cursor = mysql.cursor()
    cursor.execute('SELECT `ID` FROM `wp_users` ORDER BY `ID` ASC')
    users = cursor.fetchall()
    cursor.close()
    mysql.close()
    return users


def main():
    mysql = get_mysql()
    cursor = mysql.cursor()
    cursor.execute(
        '''
        DELETE FROM `tools_kns_requests`
        WHERE `timestamp` < NOW() - INTERVAL 30 DAY
        '''
    )
    cursor.close()
    mysql.commit()
    mysql.close()

    keywords = []
    for user in get_users():
        for keyword in get_keywords(get_requests(user)):
            keywords.append({
                'country': keyword['country'],
                'id': keyword['id'],
                'string': keyword['string'],
            })
            break

    mysql = get_mysql()
    total = len(keywords)
    for index, keyword in enumerate(keywords):
        status = '-'
        contents = get_contents(keyword['string'], keyword['country'])
        if contents:
            status = '+'
            cursor = mysql.cursor()
            cursor.execute(
                '''
                UPDATE `tools_kns_keywords`
                SET `contents` = %(contents)s
                WHERE `id` = %(id)s
                ''',
                {
                    'contents': dumps(contents),
                    'id': keyword['id'],
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
    urls = []
    for page in ['1', '2', '3']:
        urls.append(get_url(country, keyword, page))
    responses = get_responses(urls)
    if None in responses:
        return
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
                'score': [-1, 'N/A'],
                'spend': [[-1, 'N/A'], 'N/A'],
            }
        try:
            breadcrumb = Selector(text=response.text).xpath(
                '//h2[@id="s-result-count"]/a/text()'
            ).extract()[0]
        except IndexError:
            pass
    count = 0
    if (
        breadcrumb == 'Kindle Store'
        or
        (country == 'co.jp' and 'Kindle' in breadcrumb)
        or
        (country == 'de' and breadcrumb == 'Kindle-Shop')
    ):
        for response in responses:
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
                        ',', ''
                    )
                )
                break
            except IndexError:
                pass
            except ValueError:
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
                        ',', ''
                    )
                )
    if not count:
        return
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
            for href in Selector(text=response.text).xpath(
                '//h3[@class="newaps"]/a/span[@class="lrg bold"]/../'
                '@href'
            ).extract():
                if not href.startswith('http'):
                    href = 'http://www.amazon.com%(href)s' % {
                        'href': href,
                    }
                urls.append(href)
    if not urls:
        return
    responses = get_responses(urls[0:48])
    if not responses:
        return
    items = []
    index = 0
    for response in responses:
        if not response:
            continue
        index += 1
        hxs = Selector(text=response.text)
        asin = ''
        try:
            asin = get_cleaned_string(
                hxs.xpath('//input[@name="ASIN.0"]/@value').extract()[0]
            )
        except IndexError:
            pass
        best_sellers_rank = 0
        try:
            best_sellers_rank = int(
                get_cleaned_string(
                    hxs.xpath(
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
                    get_cleaned_string(
                        hxs.xpath(
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
            description = get_cleaned_string(
                hxs.xpath(
                    '//div[@id="postBodyPS"]'
                ).xpath('string()').extract()[0]
            )
        except IndexError:
            try:
                description = get_cleaned_string(
                    hxs.xpath(
                        '//div[@class="productDescriptionWrapper"]'
                    ).xpath('string()').extract()[1]
                )
            except IndexError:
                pass
        pages = 0
        try:
            pages = int(get_cleaned_string(
                hxs.xpath(
                    '//b[contains(text(), "Print Length:")]/../text()'
                ).extract()[0]
            ).split(' ')[0].replace(',', ''))
        except (IndexError, ValueError):
            try:
                pages = int(
                    compile(r'(\d+)').search(
                        get_cleaned_string(hxs.xpath(
                            '//a[@id="pageCountAvailable"]/span/text()'
                        ).extract()[0])
                    ).group(1)
                )
            except (IndexError, ValueError):
                pass
        pages = (pages, get_int(pages))
        price = 0.00
        if country != 'co.jp':
            try:
                price = float(
                    get_cleaned_string(
                        hxs.xpath(
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
                try:
                    price = float(
                        get_cleaned_string(
                            hxs.xpath(
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
            try:
                price = float(get_cleaned_string(hxs.xpath(
                    '//b[@class="priceLarge"]/text()'
                ).extract()[0]).replace(',', '').replace(u'\uffe5', ''))
            except IndexError:
                pass
            if not price:
                try:
                    price = float(
                        get_cleaned_string(
                            hxs.xpath(
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
        price = (price, get_float(price))
        publication_date = ''
        try:
            publication_date = get_cleaned_string(
                hxs.xpath(
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
                publication_date = parse(compile('\((.*?)\)').search(
                    get_cleaned_string(
                        hxs.xpath(
                            '//b[contains(text(), "Publisher")]/../text()'
                        ).extract()[0]
                    )
                ).group(1)).date()
                age = get_int(get_age(date.today(), publication_date))
                publication_date = publication_date.isoformat()
            except (AttributeError, IndexError, ValueError):
                try:
                    publication_date = parse(compile('\((.*?)\)').search(
                        get_cleaned_string(hxs.xpath(
                            '//div[@class="content"]/ul/li[4]/text()'
                        ).extract()[0])
                    ).group(1)).date()
                    age = get_int(get_age(date.today(), publication_date))
                    publication_date = publication_date.isoformat()
                except (AttributeError, IndexError, ValueError):
                    try:
                        publication_date = compile('\((.*?)\)').search(
                            get_cleaned_string(hxs.xpath(
                                '//b[contains(text(), "Verlag")]/../text()'
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
                        publication_date = parse(publication_date).date()
                        age = get_int(get_age(
                            date.today(), publication_date
                        ))
                        publication_date = publication_date.isoformat()
                    except IndexError:
                        pass
        rank = (index, get_int(index))
        related_items = ''
        try:
            related_items = get_cleaned_string(hxs.xpath(
                '//div[@id="purchaseSimsData"]/text()'
            ).extract()[0]).split(',')
        except IndexError:
            pass
        spend = 0.00
        if best_sellers_rank[0] and price[0]:
            spend = get_sales(best_sellers_rank[0]) * price[0]
        spend = (spend, get_float(spend))
        stars = 0.0
        try:
            stars = float(get_cleaned_string(
                hxs.xpath(
                    '//div[@class="gry txtnormal acrRating"]/text()'
                ).extract()[0]
            ).split(' ')[0].replace(',', ''))
        except IndexError:
            try:
                stars = float(get_cleaned_string(
                    hxs.xpath(
                        '//span[contains(@class, "swSprite")]/@title'
                    ).extract()[0][-3:]
                ))
            except (IndexError, ValueError):
                try:
                    stars = float(get_cleaned_string(hxs.xpath(
                        '//span[contains(@class, "swSprite")]/@title'
                    ).extract()[1])[0:3])
                except (IndexError, ValueError):
                    pass
        stars = (stars, get_float(stars))
        title_1 = ''
        try:
            title_1 = get_cleaned_string(
                hxs.xpath('//span[@id="btAsinTitle"]/text()').extract()[0]
            )
        except IndexError:
            pass
        if not title_1:
            try:
                title_1 = get_cleaned_string(
                    hxs.xpath(
                        '//span[@id="btAsinTitle"]/span/text()'
                    ).extract()[0]
                )
            except IndexError:
                pass
        title_2 = 'Partial'
        if keyword.lower() in title_1.lower():
            title_2 = 'Exact'
        if description and title_1:
            items.append({
                'age': age,
                'asin': asin,
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
        return
    price = sum([item['price'][0] for item in items])
    average_length = mean([
        item['pages'][0] for item in items if item['pages'][0]
    ] or [0.00])
    average_price = mean([
        item['price'][0] for item in items if item['price'][0]
    ] or [0.00])
    buyer_behavior = get_buyer_behavior(items) if price else (-1, 'N/A')
    competition = get_competition(items) if price else (-1, 'N/A')
    optimization = get_optimization(keyword, items) if price else (-1, 'N/A')
    spend = get_spend(items) if price else ((-1, 'N/A'), 'N/A')
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
        'score': get_score(
            buyer_behavior, competition, optimization, spend
        ) if price else (-1, 'N/A'),
        'spend': spend,
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


def get_sales(best_sellers_rank):
    if best_sellers_rank == 1:
        return 3500
    if best_sellers_rank == 2:
        return 3500
    if best_sellers_rank == 3:
        return 3500
    if best_sellers_rank == 4:
        return 3500
    if best_sellers_rank == 5:
        return 3500
    if best_sellers_rank >= 6 and best_sellers_rank <= 10:
        return 2000 + ((best_sellers_rank - 6) * 300)
    if best_sellers_rank >= 11 and best_sellers_rank <= 20:
        return 2000 + ((best_sellers_rank - 11) * 150)
    if best_sellers_rank >= 21 and best_sellers_rank <= 65:
        return 650 + ((best_sellers_rank - 21) * 10)
    if best_sellers_rank >= 61 and best_sellers_rank <= 80:
        return 550 + ((best_sellers_rank - 61) * 5)
    if best_sellers_rank >= 81 and best_sellers_rank <= 200:
        return 300 + ((best_sellers_rank - 81) * 2)
    if best_sellers_rank >= 201 and best_sellers_rank <= 1000:
        return 100 + ((best_sellers_rank - 201) * 0.25)
    if best_sellers_rank >= 1001 and best_sellers_rank <= 2000:
        return 55 + ((best_sellers_rank - 1001) * 0.045)
    if best_sellers_rank >= 2001 and best_sellers_rank <= 3500:
        return 30 + ((best_sellers_rank - 2001) * 0.01)
    if best_sellers_rank >= 3501 and best_sellers_rank <= 8500:
        return 10 + ((best_sellers_rank - 3501) * 0.004)
    if best_sellers_rank >= 8501 and best_sellers_rank <= 40000:
        return 1 + ((best_sellers_rank - 8501) * 0.0003)
    if best_sellers_rank >= 40001 and best_sellers_rank <= 100000:
        return 0.1 + ((best_sellers_rank - 40001) * 0.000015)
    if best_sellers_rank >= 100001:
        return 0
    return 0


def get_score(buyer_behavior, competition, optimization, spend):
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
    return score, get_float(score)


def get_url(country, keyword, page):
    if (
        country == 'co.uk'
        or
        country == 'es'
        or
        country == 'fr'
        or
        country == 'it'
    ):
        return furl('http://www.amazon.co.uk/s/').add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:341677031,k:%(keyword)s,' % {
                'keyword': keyword,
            },
        }).url
    if country == 'co.jp':
        return furl('http://www.amazon.co.jp/s/').add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:2250738051,k:%(keyword)s' % {
                'keyword': keyword,
            },
        }).url
    if country == 'de':
        return furl('http://www.amazon.de/s/').add({
            'fromApp': 'gp/search',
            'fromPage': 'results',
            'keywords': keyword,
            'page': page,
            'rh': 'n:530484031,k:%(keyword)s' % {
                'keyword': keyword,
            },
        }).url
    return furl('http://www.amazon.com/s/').add({
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
    main()
