# -*- coding: utf-8 -*-

from furl import furl
from os.path import dirname, join
from random import choice, randint
from re import compile, sub
from socket import timeout

from grequests import get as get_, map as map_
from MySQLdb import connect
from MySQLdb.cursors import DictCursor
from requests import get
from requests.exceptions import RequestException
from scrapy.selector import Selector
from simplejson import JSONDecodeError, dumps, loads
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ThreadLocalMetaData
from sqlalchemy.types import TEXT, TypeDecorator

with open(join(dirname(__file__), '..', 'variables.json'), 'r') as resource:
    variables = loads(resource.read())

engine = create_engine(
    URL(**{
        'database': variables['mysql']['database'],
        'drivername': 'mysql+mysqldb',
        'host': variables['mysql']['host'],
        'password': variables['mysql']['password'],
        'username': variables['mysql']['user'],
    }),
    connect_args={
        'charset': 'utf8',
    },
    convert_unicode=True,
    encoding='utf-8',
)
base = declarative_base(bind=engine, metadata=ThreadLocalMetaData())


class json(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return dumps(value)

    def process_result_value(self, value, dialect):
        return loads(value)


class mutators_dict(Mutable, dict):

    @classmethod
    def coerce(class_, key, value):
        if not isinstance(value, mutators_dict):
            if isinstance(value, dict):
                return mutators_dict(value)
            return Mutable.coerce(key, value)
        return value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()


def get_amazon_best_sellers_rank(selector):
    amazon_best_sellers_rank = {}
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
                '(', ''
            ).replace(
                ')', ''
            ).replace(
                'Free Kindle Store', 'Free in Kindle Store'
            ).replace(
                'Paid Kindle Store', 'Paid in Kindle Store'
            )
        )] = int(get_number(get_string(text[0])))
    except IndexError:
        pass
    try:
        for li in selector.xpath(
            '//ul[@class="zg_hrsr"]/li[@class="zg_hrsr_item"]'
        ):
            amazon_best_sellers_rank[get_string(
                li.xpath(
                    './/span[@class="zg_hrsr_ladder"]'
                ).xpath(
                    'string()'
                ).extract()[0].replace(
                    u'in ', ''
                ).replace(
                    u'in\xa0', ''
                ).replace(
                    '(', ''
                ).replace(
                    ')', ''
                ).replace(
                    'Free Kindle Store', 'Free in Kindle Store'
                ).replace(
                    'Paid Kindle Store', 'Paid in Kindle Store'
                )
            )] = int(get_number(get_string(li.xpath(
                './/span[@class="zg_hrsr_rank"]/text()'
            ).extract()[0])))
    except IndexError:
        pass
    return amazon_best_sellers_rank


def get_book(response):
    book_cover_image = ''
    title = ''
    author = ''
    price = 0.0
    publication_date = ''
    print_length = ''
    amazon_best_sellers_rank = {}
    estimated_sales_per_day = 0.0
    earnings_per_day = 0.0
    total_number_of_reviews = ''
    review_average = ''
    selector = Selector(text=response.text)
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
                '//img[@id="imgBlkFront" or '
                '@id="main-image"]/@rel'
            ).extract()[0])
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
            '//span[@class="contributorNameTrigger"]/a/text()'
        ).extract()[0])
    except IndexError:
        try:
            author = get_string(selector.xpath(
                '//h1[@class="parseasinTitle "]/following-sibling::span/a/'
                'text()'
            ).extract()[0])
        except IndexError:
            pass
    try:
        price = float(get_number(get_string(selector.xpath(
            '//span[@class="price"]//text()'
        ).extract()[0])))
    except IndexError:
        try:
            price = float(get_number(get_string(selector.xpath(
                '//td[contains(text(), "Kindle Price")]/'
                'following-sibling::td/b/text()'
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
            estimated_sales_per_day = float(get_sales(
                amazon_best_sellers_rank['Paid in Kindle Store']
            ))
        except KeyError:
            pass
    earnings_per_day = estimated_sales_per_day * price
    try:
        total_number_of_reviews = int(get_number(get_string(selector.xpath(
            '//span[@class="crAvgStars"]/a/text()'
        ).extract()[0])))
    except IndexError:
        pass
    try:
        review_average = float(get_number(get_string(selector.xpath(
            '//div[@class="gry txtnormal acrRating"]/text()'
        ).extract()[0].split(' ')[0])))
    except IndexError:
        pass
    return {
        'amazon_best_sellers_rank': amazon_best_sellers_rank,
        'author': author,
        'book_cover_image': book_cover_image,
        'earnings_per_day': earnings_per_day,
        'estimated_sales_per_day': estimated_sales_per_day,
        'price': price,
        'print_length': print_length,
        'publication_date': publication_date,
        'review_average': review_average,
        'title': title,
        'total_number_of_reviews': total_number_of_reviews,
        'url': response.url,
    }


def get_headers():
    return {
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ),
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.amazon.com',
        'Referer': 'http://www.amazon.com',
        'User-Agent': get_user_agent(),
    }


def get_mysql_connection():
    mysql = connect(
        cursorclass=DictCursor,
        db=variables['mysql']['database'],
        host=variables['mysql']['host'],
        passwd=variables['mysql']['password'],
        use_unicode=True,
        user=variables['mysql']['user'],
    )
    mysql.set_character_set('utf8')
    return mysql


def get_mysql_session():
    return sessionmaker(bind=engine)


def get_number(number):
    number = sub(r'[^0-9\.]', '', number)
    number = number.strip()
    return number


def get_popularity(keyword):
    kps = 0.00
    sp = 0
    src = 0
    trb = 0
    spr = 0
    length = len(keyword)
    for index in range(0, length):
        keywords = {
            'premium': [],
            'non-premium': [],
        }
        response = get_response(
            furl(
                'http://completion.amazon.com/search/complete'
            ).add({
                'mkt': '1',
                'q': keyword[0:index + 1],
                'search-alias': 'digital-text',
                'xcat': '2',
            }).url
        )
        if not response:
            continue
        contents = []
        try:
            contents = loads(response)
        except JSONDecodeError:
            pass
        if not contents:
            continue
        for i, item in enumerate(contents[2]):
            key = 'non-premium'
            if isinstance(item, dict) and 'nodes'in item and item['nodes']:
                key = 'premium'
            keywords[key].append(contents[1][i])
        if not kps and not sp and not src:
            if keyword in keywords['non-premium']:
                kps = ((index + 1) * 100.00) / (length * 1.00)
                src = len(keywords['non-premium'])
                sp = contents[1].index(keyword)
        if not trb:
            total = len(keywords['premium'])
            if total:
                if keyword in keywords['premium']:
                    rank = contents[1].index(keyword)
                    trb = (((total - rank) * 100.00) / (total * 1.00))
        if kps and sp and src and trb:
            break
    if src:
        spr = (((src - sp) * 100.00) / (src * 1.00))
        if sp != 1:
            spr = spr * 0.75
    return (kps * 0.80) + (spr * 0.10) + (trb * 0.10)


def get_proxies():
    if is_development():
        return {}
    return {
        'http': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 100),
        },
        'https': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 100),
        },
    }


def get_response(url):
    index = 0
    while True:
        index += 1
        if index >= 5:
            return ''
        try:
            response = get(
                url,
                allow_redirects=True,
                headers=get_headers(),
                proxies=get_proxies(),
                timeout=get_timeout(),
                verify=False,
            )
            if (
                response
                and
                response.status_code == 200
                and
                'Enter the characters you see below' not in response.text
            ):
                return response.text
        except (RequestException, timeout):
            pass
    return ''


def get_responses(urls):
    responses = {}
    for url in urls:
        responses[url] = None
    index = 0
    while True:
        keys = [key for key in responses if not responses[key]]
        if not keys:
            return responses.values()
        index += 1
        if index >= 5:
            return responses.keys()
        try:
            for response in map_(get_(
                key,
                allow_redirects=True,
                headers=get_headers(),
                proxies=get_proxies(),
                timeout=get_timeout(),
                verify=False,
            ) for key in keys):
                if (
                    response
                    and
                    response.status_code == 200
                    and
                    'Enter the characters you see below' not in response.text
                ):
                    responses[response.request.url] = response
        except Exception:
            pass


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


def get_string(string):
    string = string.replace("\n", ' ')
    string = string.replace("\r", ' ')
    string = string.replace("\t", ' ')
    string = sub(r'[ ]+', ' ', string)
    string = string.strip()
    return string


def get_timeout():
    return 30


def get_url(url):
    url = sub(r'/Best-Sellers-.*?/', '/gp/', url)
    url = sub(r'ref=.*$', '', url)
    return url


def get_user_agent():
    return choice([
        'Mozilla/4.0 (compatible; MSIE 6.0b; Windows NT 5.1)',
        'Mozilla/4.0 (compatible; MSIE 6.0b; Windows NT 5.1; DigExt)',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/31.0.1650.16 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 '
        'Firefox/29.0',
        'Mozilla/5.0 (Windows NT 6.2; rv:21.0) Gecko/20130326 Firefox/21.0',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
        'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))',
        'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
        'Mozilla/5.0 (X11; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:21.0) Gecko/20130331 '
        'Firefox/21.0',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',
    ])


def is_development():
    return variables['application']['debug']
