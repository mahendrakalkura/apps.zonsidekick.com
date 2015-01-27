# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import Counter
from contextlib import closing
from datetime import date, timedelta
from os.path import isfile

from nltk.tokenize import word_tokenize
from progressbar import ProgressBar
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
    string = Column(String(255), index=True)
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
    keywords = Column(Text, index=True)


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
    titles = set()
    with closing(get_mysql_session()()) as session:
        query = session.query(book)
        if print_length == 'short':
            query = query.filter(book.print_length < 100)
        if print_length == 'long':
            query = query.filter(book.print_length >= 100)
        if category_id:
            query = query.join(
                trend,
            ).filter(
                trend.category_id == category_id,
                trend.date == date.today() - timedelta(days=1),
            )
        for b in query.order_by(
            'apps_top_100_explorer_books.id asc',
        ).execution_options(
            stream_results=True,
        ):
            titles.add(b.title.lower())
        if category_id:
            for c in session.query(
                category,
            ).filter(
                category.category_id == category_id,
            ).order_by(
                'id asc',
            ).execution_options(
                stream_results=True,
            ):
                for title in get_step_1_titles(c.id, print_length):
                    titles.add(title)
    return sorted(titles)


def get_step_2_words(titles):
    return sorted(Counter([
        word
        for title in titles
        for word in word_tokenize(title)
        if len(word) > 3
    ]).most_common(20))


def get_step_3_keywords(words):
    keywords = set()
    with ProgressBar(maxval=len(words)) as progress:
        for index, _ in enumerate(words):
            for keyword in get_results(words[index], 'com', 'digital-text'):
                if len(
                    set(word_tokenize(keyword)).intersection(set(words))
                ) >= 2:
                    keywords.add(keyword)
                progress.update(index)
    return sorted(keywords)


def get_step_4_suggested_keywords(keywords):
    suggested_keywords = set()
    with ProgressBar(maxval=len(keywords)) as progress:
        for index, _ in enumerate(keywords):
            for suggested_keyword in get_suggested_keywords(
                word_tokenize(keywords[index])
            ):
                suggested_keywords.add(suggested_keyword)
            progress.update(index)
    return sorted(suggested_keywords)


def get_step_5_keywords(suggested_keywords):
    keywords = []
    with ProgressBar(maxval=len(suggested_keywords)) as progress:
        for index, _ in enumerate(suggested_keywords):
            contents = get_contents(suggested_keywords[index], 'com')
            if contents:
                keywords.append({
                    'average_length': contents['average_length'][0],
                    'average_price': contents['average_price'][0],
                    'buyer_behavior': contents['buyer_behavior'][0],
                    'competition': contents['competition'][0],
                    'count': contents['count'][0],
                    'optimization': contents['optimization'][0],
                    'popularity': contents['popularity'][0],
                    'score': contents['score'][0],
                    'spend': contents['spend'][0],
                    'string': suggested_keywords[index],
                })
            progress.update(index)
    return keywords


def set_step_1():
    print 'Step 1'
    with closing(get_sqlite_session()()) as session:
        session.query(step_1).delete()
        for title in get_step_1_titles(category_id, arguments.page_length):
            session.add(step_1(**{
                'title': title,
            }))
        session.commit()
    print 'Done'
    return True


def set_step_2():
    print 'Step 2'
    with closing(get_sqlite_session()()) as session:
        session.query(step_2).delete()
        for word in [
            word
            for word, _ in get_step_2_words([
                instance.title
                for instance in session.query(
                    step_1,
                ).execution_options(
                    stream_results=True,
                )
            ])
        ]:
            session.add(step_2(**{
                'word': word,
            }))
        session.commit()
    print 'Done'
    return True


def set_step_3():
    print 'Step 3'
    with closing(get_sqlite_session()()) as session:
        session.query(step_3).delete()
        for keyword in get_step_3_keywords([
            instance.word
            for instance in session.query(
                step_2,
            ).execution_options(
                stream_results=True,
            )
        ]):
            session.add(step_3(**{
                'keyword': keyword,
            }))
        session.commit()
    print 'Done'
    return True


def set_step_4():
    print 'Step 4'
    with closing(get_sqlite_session()()) as session:
        session.query(step_4).delete()
        for suggested_keyword in get_step_4_suggested_keywords([
            instance.keyword
            for instance in session.query(
                step_3,
            ).execution_options(
                stream_results=True,
            )
        ]):
            session.add(step_4(**{
                'suggested_keyword': suggested_keyword,
            }))
        session.commit()
    print 'Done'
    return True


def set_step_5():
    print 'Step 5'
    with closing(get_sqlite_session()()) as session:
        session.query(step_5).delete()
        for keyword in get_step_5_keywords([
            instance.suggested_keyword
            for instance in session.query(
                step_4,
            ).execution_options(
                stream_results=True,
            )
        ]):
            session.add(step_5(**{
                'average_length': keyword['average_length'],
                'average_price': keyword['average_price'],
                'buyer_behavior': keyword['buyer_behavior'],
                'competition': keyword['competition'],
                'count': keyword['count'],
                'keyword': keyword['word'],
                'optimization': keyword['optimization'],
                'popularity': keyword['popularity'],
                'score': keyword['score'],
                'spend': keyword['spend'],
            }))
        session.commit()
    print 'Done'
    return True


# TODO
def set_step_6():
    print 'Step 6'
    with closing(get_sqlite_session()()) as session:
        session.query(step_6).delete()
        keywords = [
            instance.string
            for instance in session.query(
                step_5,
            ).filter(
                step_5.score >= 70.00,
            ).execution_options(
                stream_results=True,
            )[0:10]
        ]
        groups = []
        for index, _ in enumerate(keywords):
            status = False
            if not any(list_ for list_ in groups):
                groups.append([keywords[index]])
                status = True
            else:
                for index_, words_ in enumerate(groups):
                    if is_similar(
                        keywords[index].split(' '), ' '.join(words_)
                    ):
                        groups[index_].append(keywords[index])
                        status = True
                        break
                    else:
                        next_elements = ' '.join(
                            [word_ for word_ in keywords[(index + 1):]]
                        )
                        if (
                            is_similar(
                                keywords[index].split(' '), next_elements
                            )
                            and
                            is_similar(
                                next_elements.split(' '),
                                ' '.join(words_)
                            )
                        ):
                            groups[index_].append(keywords[index])
                            status = True
            if not status:
                groups.append([keywords[index]])
        for group in groups:
            session.add(step_6(**{
                'keywords': dumps(group),
            }))
        session.commit()
    print 'Done'
    return True


def set_step_7():
    print 'Step 7'
    with closing(get_sqlite_session()()) as session:
        session.query(step_7).delete()
    step_6_instances = []
    with closing(get_sqlite_session()()) as session:
        step_6_instances = [
            {
                'id': instance.id,
                'keywords': loads(instance.keywords),
            }
            for instance in session.query(
                step_6,
            ).execution_options(
                stream_results=True,
            )
        ]
    step_7_instances = []
    with closing(get_mysql_session()()) as session:
        for instance in step_6_instances:
            books = []
            for keyword in instance['keywords']:
                query = session.query(book)
                for word in word_tokenize(keyword):
                    query = query.filter(
                        book.title.like('%%%(word)s%%' % {
                            'word': word,
                        })
                    )
                for b in query.execution_options(stream_results=True):
                    books.append(b.id)
            for book_id, frequency in Counter(books).most_common():
                if frequency == len(instance['keywords']):
                    step_7_instances.append({
                        'book_id': book_id,
                        'step_6_id': instance['id'],
                    })
    with closing(get_sqlite_session()()) as session:
        for instance in step_7_instances:
            session.add(step_7(**instance))
        session.commit()
    print 'Done'
    return True


def has_step(number):
    with closing(get_sqlite_session()()) as session:
        if session.query(globals()['step_%(number)s' % {
            'number': number,
        }]).count():
            return True
    return False


def is_similar(word_1, word_2):
    if len(
        set(word_tokenize(word_1)).intersection(word_tokenize(word_2))
    ) >= 2:
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
