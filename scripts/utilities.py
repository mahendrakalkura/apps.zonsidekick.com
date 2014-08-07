# -*- coding: utf-8 -*-

from os.path import dirname, join
from random import choice, randint
from re import sub

from MySQLdb import connect
from MySQLdb.cursors import DictCursor
from simplejson import loads

with open(join(
    dirname(__file__), '..', 'variables.json'
), 'r') as resource:
    variables = loads(resource.read())


def get_cleaned_string(string):
    string = string.replace("\n", ' ')
    string = string.replace("\r", ' ')
    string = string.replace("\t", ' ')
    string = sub(r'[ ]+', ' ', string)
    string = string.strip()
    return string


def get_mysql():
    mysql = connect(
        cursorclass=DictCursor,
        db=variables['mysql']['database'],
        host=variables['mysql']['host'],
        passwd=variables['mysql']['password'],
        use_unicode=variables['mysql']['use_unicode'],
        user=variables['mysql']['user'],
    )
    mysql.set_character_set('utf8')
    return mysql


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
        'http://': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 50),
        },
        'https://': 'http://72.52.91.120:%(port_number)s' % {
            'port_number': 9150 + randint(1, 50),
        },
    }


def is_development():
    return variables['application']['debug']
