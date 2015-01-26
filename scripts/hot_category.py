# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import Counter
from contextlib import closing
from operator import itemgetter
from os.path import isfile
from re import split

from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey, ThreadLocalMetaData
from ujson import dumps, loads

from keyword_analyzer import get_contents
from keyword_suggester import get_results
from suggested_keywords import get_suggested_keywords
from top_100_explorer import book, category, trend
from utilities import get_mysql_session

from sys import modules

if 'threading' in modules:
    del modules['threading']

parser = ArgumentParser()
parser.add_argument('--category', dest='category', required=True)
parser.add_argument(
    '--page-length',
    choices=['long', 'short'],
    dest='page_length',
    required=True,
)
parser.add_argument('--reset', action='store_true', dest='reset')
parser.add_argument(
    '--step', choices=range(1, 8), dest='step', required=False, type=int,
)
parser.set_defaults(reset=False)

arguments = parser.parse_args()
category_id = None
if arguments.category == 'all':
    category_id = 0
if arguments.category == 'fiction':
    category_id = 1846
if arguments.category == 'nonfiction':
    category_id = 2191

database = '%(category)s_%(page_length)s.db' % {
    'category': category_id,
    'page_length': arguments.page_length,
}
engine = create_engine(
    'sqlite:///../tmp/%(database)s' % {
        'database': database,
    },
    convert_unicode=True,
    echo=False,
)
base = declarative_base(bind=engine, metadata=ThreadLocalMetaData())


class step_1(base):
    __tablename__ = 'step_1'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)


class step_2(base):
    __tablename__ = 'step_2'
    id = Column(Integer, primary_key=True)
    word = Column(String(255), index=True)


class step_3(base):
    __tablename__ = 'step_3'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), index=True)


class step_4(base):
    __tablename__ = 'step_4'
    id = Column(Integer, primary_key=True)
    suggested_keyword = Column(String(255), index=True)


class step_5(base):
    __tablename__ = 'step_5'
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), index=True)
    average_length = Column(Float)
    average_price = Column(Float)
    buyer_behavior = Column(Float)
    competition = Column(Integer)
    count = Column(Integer)
    optimization = Column(Float)
    popularity = Column(Float)
    score = Column(Float)
    spend = Column(Float)


class step_6(base):
    __tablename__ = 'step_6'
    id = Column(Integer, primary_key=True)
    words = Column(Text, index=True)


class step_7(base):
    __tablename__ = 'step_7'
    id = Column(Integer, primary_key=True)
    step_6_id = Column(Integer, ForeignKey('step_6.id'), nullable=False)
    book_id = Column(Integer, nullable=False)

if not isfile(database) and not arguments.reset:
    base.metadata.create_all()


def get_sqlite_session():
    return sessionmaker(bind=engine)


def get_step_1_titles(category_id, print_length):
    titles = []
    session = get_mysql_session()()
    query = session.query(book)
    if print_length == 'short':
        query = query.filter(book.print_length < 100)
    if print_length == 'long':
        query = query.filter(book.print_length >= 100)
    if not category_id:
        return query.order_by(
            'id asc'
        ).execution_options(
            stream_results=True
        )
    query = query.join(trend)
    if category_id:
        query = query.filter(trend.category_id == category_id)
    for b in query.order_by(
        'apps_top_100_explorer_books.id asc'
    ).execution_options(
        stream_results=True
    ):
        titles.append(b.title)
    if not category_id:
        for c in session.query(
            category
        ).execution_options(
            stream_results=True
        ):
            for c_ in c.categories.order_by(
                'id asc'
            ).execution_options(
                stream_results=True
            ):
                for title in get_step_1_titles(c_.id, print_length):
                    titles.append(title.lower())
    else:
        c = session.query(category).get(category_id)
        for c_ in c.categories.order_by(
            'id asc'
        ).execution_options(
            stream_results=True
        ):
            for title in get_step_1_titles(c_.id, print_length):
                titles.append(title.lower())
    session.close()
    return titles


def get_step_2_words(items):
    return Counter([
        word
        for item in items
        for word in split(r'[^A-Za-z0-9]', item)
        if len(word) > 3
    ]).most_common(20)


def get_step_3_words(titles):
    step_3_words = []
    for title in titles:
        for word in get_results(title, 'com', 'digital-text'):
            if word not in step_3_words:
                step_3_words.append(word)
    return step_3_words


def get_step_4_words(step_3_words, titles):
    titles = ','.join(titles)
    titles = titles.lower()
    titles = titles.split(',')
    step_4_words = []
    step_4_words_ = []
    for word in step_3_words:
        if is_similar(titles, word):
            step_4_words_.append(
                get_suggested_keywords(word.split(' '))
            )
    for list_of_words in step_4_words_:
        for word in list_of_words:
            if word not in step_4_words:
                step_4_words.append(word)
    return step_4_words


def get_step_5_words(step_4_words):
    step_5_words = []
    for word in step_4_words:
        contents = get_contents(word, 'com')
        if contents:
            step_5_words.append({
                'average_length': contents['average_length'][0],
                'average_price': contents['average_price'][0],
                'buyer_behavior': contents['buyer_behavior'][0],
                'competition': contents['competition'][0],
                'count': contents['count'][0],
                'optimization': contents['optimization'][0],
                'popularity': contents['popularity'][0]
                if 'popularity' in contents else 0.0,
                'score': contents['score'][0],
                'spend': contents['spend'][0][0],
                'word': word,
            })
    return step_5_words


def get_step_6_words(step_5_words):
    return sorted(step_5_words, key=itemgetter('score'))[:20]


def set_step_1():
    with closing(get_sqlite_session()()) as session:
        session.query(step_1).delete()
        titles = get_step_1_titles(category_id, arguments.page_length)
        if titles:
            if category_id > 0:
                for title in titles:
                    session.add(step_1(**{
                        'title': title,
                    }))
            else:
                for title in titles:
                    session.add(step_1(**{
                        'title': title.title,
                    }))
            session.commit()
            return True


def set_step_2():
    with closing(get_sqlite_session()()) as session:
        session.query(step_2).delete()
        titles = []
        for record in session.query(step_1):
            titles.append(record.title)
        top_20_words = get_step_2_words(titles)
        top_20_words = [word for word, occurrence in top_20_words]
        for word in top_20_words:
            session.add(step_2(**{
                'word': word,
            }))
        session.commit()
        return True


def set_step_3():
    with closing(get_sqlite_session()()) as session:
        session.query(step_3).delete()
        words = []
        for record in session.query(step_2):
            words.append(record.word)
        for word in get_step_3_words(words):
            session.add(step_3(**{
                'keyword': word,
            }))
        session.commit()
        return True


def set_step_4():
    with closing(get_sqlite_session()()) as session:
        session.query(step_4).delete()
        titles = []
        for record in session.query(step_2):
            titles.append(record.word)
        words = []
        for record in session.query(step_3):
            words.append(record.keyword)
        for word in get_step_4_words(words, titles):
            session.add(step_4(**{
                'suggested_keyword': word,
            }))
        session.commit()
        return True


def set_step_5():
    with closing(get_sqlite_session()()) as session:
        session.query(step_5).delete()
        words = []
        for record in session.query(step_4):
            words.append(record.suggested_keyword)
        for record in get_step_5_words(words[0:5]):
            session.add(step_5(**{
                'average_length': record['average_length'],
                'average_price': record['average_price'],
                'buyer_behavior': record['buyer_behavior'],
                'competition': record['competition'],
                'count': record['count'],
                'optimization': record['optimization'],
                'popularity': record['popularity'],
                'score': record['score'],
                'spend': record['spend'],
                'keyword': record['word'],
            }))
        session.commit()
        return True


def set_step_6():
    with closing(get_sqlite_session()()) as session:
        session.query(step_6).delete()
        words = []
        for record in session.query(step_5):
            if record.score >= 20.00:
                words.append(record.keyword)
        list_of_lists = []
        for index, word in enumerate(words):
            status = False
            if not any(list_ for list_ in list_of_lists):
                list_of_lists.append([word])
                status = True
            else:
                for index_, words_ in enumerate(list_of_lists):
                    if is_similar(word.split(' '), ' '.join(words_)):
                        list_of_lists[index_].append(word)
                        status = True
                        break
                    else:
                        next_elements = ' '.join(
                            [word_ for word_ in words[(index + 1):]]
                        )
                        if (
                            is_similar(word.split(' '), next_elements)
                            and
                            is_similar(
                                next_elements.split(' '),
                                ' '.join(words_)
                            )
                        ):
                            list_of_lists[index_].append(word)
                            status = True
            if not status:
                list_of_lists.append([word])
        for group in list_of_lists:
            session.add(step_6(**{
                'words': dumps(group),
            }))
        session.commit()
        return True


def set_step_7():
    with closing(get_mysql_session()()) as mysql_session:
        with closing(get_sqlite_session()()) as session:
            session.query(step_7).delete()
            for group in session.query(step_6):
                books = []
                words = loads(group.words)
                for word in words:
                    query = mysql_session.query(
                        book
                    )
                    for word_ in word.split(' '):
                        query = query.filter(
                            book.title.like('%%%(title)s%%' % {
                                'title': word_,
                            })
                        )
                    for book_ in query.execution_options(stream_results=True):
                        books.append(book_.id)
                for book_id, frequency in Counter(books).most_common():
                    if (frequency == len(words)):
                        continue
                    session.add(step_7(**{
                        'step_6_id': group.id,
                        'book_id': book_id,
                    }))
            session.commit()
            return True


def has_step(number):
    with closing(get_sqlite_session()()) as session:
        if session.query(globals()['step_%(number)s' % {
            'number': number,
        }]).count():
            return True
    return False


def is_similar(word_1, word_2):
    intersection = set(word_1).intersection(word_2.split(' '))
    if len(intersection) >= 2:
        return True
    return False

if arguments.reset:
    base.metadata.drop_all()
    base.metadata.create_all()
    base.metadata.reflect(engine)
    exit()

if arguments.step:
    for index in range(1, arguments.step):
        if locals()['has_step'](index):
            continue
        if not locals()[
            'set_step_%(index)s' % {
                'index': index,
            }
        ]():
            raise Exception('Error: `set_step_%(index)s`' % {
                'index': index,
            })
    if not locals()[
        'set_step_%(step)s' % {
            'step': arguments.step,
        }
    ]():
        raise Exception('Error: `set_step_%(step)s`' % {
            'step': arguments.step,
        })
    exit()
