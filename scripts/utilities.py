# -*- coding: utf-8 -*-

from os.path import dirname, join
from random import choice, randint
from re import sub

from MySQLdb import connect
from MySQLdb.cursors import DictCursor
from simplejson import dumps, loads
from sqlalchemy import create_engine, Column
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.schema import ThreadLocalMetaData
from sqlalchemy.types import TEXT, TypeDecorator

with open(join(
    dirname(__file__), '..', 'variables.json'
), 'r') as resource:
    variables = loads(resource.read())

engine = create_engine(URL(**{
    'database': variables['mysql']['database'],
    'drivername': 'mysql+mysqldb',
    'host': variables['mysql']['host'],
    'password': variables['mysql']['password'],
    'username': variables['mysql']['user'],
}), connect_args={
    'charset': 'utf8',
}, convert_unicode=True, encoding='utf-8')
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

    book = relationship(
        'book', backref=backref('trends', cascade='all', lazy='dynamic'),
    )


def get_string(string):
    string = string.replace("\n", ' ')
    string = string.replace("\r", ' ')
    string = string.replace("\t", ' ')
    string = sub(r'[ ]+', ' ', string)
    string = string.strip()
    return string


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


def get_proxies():
    if not is_development():
        item = choice([
            '173.234.250.113:3128',
            '173.234.250.254:3128',
            '173.234.250.31:3128',
            '173.234.250.71:3128',
            '173.234.250.78:3128',
            '173.234.57.122:3128',
            '173.234.57.152:3128',
            '173.234.57.199:3128',
            '173.234.57.22:3128',
            '173.234.57.254:3128',
            '173.234.57.40:3128',
            '173.234.57.96:3128',
        ])
        return {
            'http': 'http://%(item)s' % {
                'item': item,
            },
            'https': 'http://%(item)s' % {
                'item': item,
            },
        }
    return {
        'http': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 50),
        },
        'https': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 50),
        },
    }


def is_development():
    return variables['application']['debug']
