# -*- coding: utf-8 -*-

from datetime import date, timedelta
from sys import argv

from furl import furl
from scrapy.selector import Selector
from simplejson import loads
from sqlalchemy import or_
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql.expression import null

from utilities import (
    base, get_mysql_session, get_number, get_response, get_string, get_url,
)


class book(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_book_tracker_books'


class keyword(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_book_tracker_keywords'

    book = relationship(
        'book', backref=backref('keywords', cascade='all', lazy='dynamic'),
    )


class book_rank(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_book_tracker_books_ranks'

    book = relationship(
        'book', backref=backref('ranks', cascade='all', lazy='dynamic'),
    )


class keyword_rank(base):
    __tablename__ = 'apps_book_tracker_keywords_ranks'
    __table_args__ = {
        'autoload': True,
    }

    keyword = relationship(
        'keyword', backref=backref('ranks', cascade='all', lazy='dynamic'),
    )


def main():
    session = get_mysql_session()()

    date_ = date.today()

    for b in session.query(
        book,
    ).outerjoin(
        book_rank,
    ).filter(
        or_(book_rank.date != date_, book_rank.date == null()),
    ).order_by(
        'apps_book_tracker_books_ranks.id ASC',
    ):
        session.add(book_rank(**{
            'book': b,
            'date': date_,
            'number': get_book_rank(b.url),
        }))
        try:
            session.commit()
        except DBAPIError:
            session.rollback()
        except SQLAlchemyError:
            session.rollback()

    for k in session.query(
        keyword,
    ).outerjoin(
        keyword_rank,
    ).filter(
        or_(keyword_rank.date != date_, keyword_rank.date == null()),
    ).order_by(
        'apps_book_tracker_keywords_ranks.id ASC',
    ):
        session.add(keyword_rank(**{
            'date': date_,
            'keyword': k,
            'number': get_keyword_rank(k.string, k.book.url),
        }))
        try:
            session.commit()
        except DBAPIError:
            session.rollback()
        except SQLAlchemyError:
            session.rollback()

    thirty_days = date_ - timedelta(days=30)

    session.query(
        book_rank,
    ).filter(
        book_rank.date <= thirty_days,
    ).delete(synchronize_session=False)

    session.query(
        keyword_rank,
    ).filter(
        keyword_rank.date <= thirty_days,
    ).delete(synchronize_session=False)

    session.close()


def get_book_rank(url):
    response = get_response(get_url(url))
    if not response:
        return 0
    try:
        return get_number(
            get_string(
                Selector(
                    text=response.text,
                ).xpath(
                    '//li[@id="SalesRank"]/text()'
                ).extract()[1]
            ).split(' ')[0].strip()
        )
    except IndexError:
        pass
    return 0


def get_keyword_rank(string, url):
    response = get_response(
        furl(
            'http://www.amazon.com/s'
        ).add({
            'keywords': string,
            'page': '1',
            'rh': 'n:133140011,k:%(keyword)s' % {
                'keyword': string,
            },
        }).url
    )
    if not response:
        return 0
    for rank, u in enumerate(
        Selector(
            text=response.text,
        ).xpath(
            '//div[@class="a-row a-spacing-small"]/a/@href',
        ).extract()
    ):
        if get_url(u) == url:
            return rank + 1
    return 0


if __name__ == '__main__':
    main()
