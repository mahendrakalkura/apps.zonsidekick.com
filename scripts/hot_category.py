# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, timedelta
from locale import LC_ALL, format, setlocale
from sys import modules
from unicodedata import normalize

from celery import Celery
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Style
from sqlalchemy.orm import backref, relationship

from keyword_analyzer import get_contents
from keyword_suggester import get_results
from suggested_keywords import get_suggested_keywords
from top_100_explorer import book, category, trend
from utilities import base, get_mysql_session, variables

if 'threading' in modules:
    del modules['threading']

setlocale(LC_ALL, 'en_US.UTF-8')

celery = Celery('hot_category')
celery.conf.update(
    BROKER=variables['broker'],
    BROKER_POOL_LIMIT=0,
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_ACKS_LATE=True,
    CELERY_IGNORE_RESULT=True,
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TASK_SERIALIZER='json',
    CELERYD_LOG_FORMAT='[%(asctime)s: %(levelname)s] %(message)s',
    CELERYD_POOL_RESTARTS=True,
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERYD_TASK_SOFT_TIME_LIMIT=3600,
    CELERYD_TASK_TIME_LIMIT=7200,
)

stopwords = stopwords.words('english')


class word(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_hot_category_words'


class keyword(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_hot_category_keywords'


class suggested_keyword(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_hot_category_suggested_keywords'


class group(base):
    __table_args__ = {
        'autoload': True,
    }
    __tablename__ = 'apps_hot_category_groups'

    suggested_keywords = relationship(
        'suggested_keyword',
        backref=backref('groups', lazy='dynamic'),
        lazy='dynamic',
        secondary='apps_hot_category_groups_suggested_keywords',
    )

    books = relationship(
        'book',
        backref=backref('groups', lazy='dynamic'),
        lazy='dynamic',
        secondary='apps_hot_category_groups_books',
    )


class group_suggested_keyword(base):
    __tablename__ = 'apps_hot_category_groups_suggested_keywords'
    __table_args__ = {
        'autoload': True,
    }

    group = relationship('group')
    suggested_keyword = relationship('suggested_keyword')


class group_book(base):
    __tablename__ = 'apps_hot_category_groups_books'
    __table_args__ = {
        'autoload': True,
    }

    group = relationship('group')
    book = relationship('book')


def get_titles(category_id, print_length):
    titles = []
    with closing(get_mysql_session()()) as session:
        query = session.query(book.title)
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
            'apps_top_100_explorer_books.id ASC',
        ).execution_options(
            stream_results=True,
        ):
            string = normalize(
                'NFKD', b.title.lower()
            ).encode('ascii', 'ignore').strip()
            if string:
                titles.append(string)
        if category_id:
            for c in session.query(
                category.id,
            ).filter(
                category.category_id == category_id,
            ).order_by(
                'id ASC',
            ).execution_options(
                stream_results=True,
            ):
                for string in get_titles(c.id, print_length):
                    titles.append(string)
    return titles


def step_1(category_id, print_length):
    print 'Step 1'
    with closing(get_mysql_session()()) as session:
        session.query(
            word,
        ).filter(
            word.category_id == category_id,
            word.print_length == print_length,
        ).delete(
            synchronize_session=False,
        )
        session.commit()
        for string, _ in sorted(Counter([
            string
            for title in get_titles(category_id, print_length)
            for string in word_tokenize(title)
            if len(string) > 3 and string not in stopwords
        ]).most_common(20), key=lambda item: (item[1], item[0], )):
            session.add(word(**{
                'category_id': category_id,
                'print_length': print_length,
                'string': string,
            }))
        session.commit()
    print 'Done'


def step_2_reset(category_id, print_length):
    print 'Step 2 :: Reset'
    with closing(get_mysql_session()()) as session:
        session.query(
            keyword,
        ).filter(
            keyword.category_id == category_id,
            keyword.print_length == print_length,
        ).delete(
            synchronize_session=False,
        )
        session.commit()
    print 'Done'


def step_2_queue(category_id, print_length):
    print 'Step 2 :: Queue'
    with closing(get_mysql_session()()) as session:
        strings = [
            instance.string
            for instance in session.query(
                word,
            ).filter(
                word.category_id == category_id,
                word.print_length == print_length,
            ).order_by(
                'id ASC',
            ).execution_options(
                stream_results=True,
            )
        ]
        for string in strings:
            step_2_process.delay(category_id, print_length, string, strings)
    print 'Done'


@celery.task
def step_2_process(category_id, print_length, string, strings):
    ss = get_results(string, 'com', 'digital-text')
    with closing(get_mysql_session()()) as session:
        for s in ss:
            if session.query(
                keyword,
            ).filter(
                keyword.category_id == category_id,
                keyword.print_length == print_length,
                keyword.string == s,
            ).count():
                continue
            if len(set(word_tokenize(s)).intersection(set(strings))) < 1:
                continue
            session.add(keyword(**{
                'category_id': category_id,
                'print_length': print_length,
                'string': s,
            }))
        session.commit()


def step_3_reset(category_id, print_length):
    print 'Step 3 :: Reset'
    with closing(get_mysql_session()()) as session:
        session.query(
            suggested_keyword,
        ).filter(
            suggested_keyword.category_id == category_id,
            suggested_keyword.print_length == print_length,
        ).delete(
            synchronize_session=False,
        )
        session.commit()
    print 'Done'


def step_3_queue(category_id, print_length):
    print 'Step 3 :: Queue'
    with closing(get_mysql_session()()) as session:
        for instance in session.query(
            keyword,
        ).order_by(
            'id ASC',
        ).filter(
            keyword.category_id == category_id,
            keyword.print_length == print_length,
        ).execution_options(
            stream_results=True,
        ):
            step_3_process.delay(category_id, print_length, instance.string)
    print 'Done'


@celery.task
def step_3_process(category_id, print_length, string):
    ss = get_suggested_keywords(word_tokenize(string))
    with closing(get_mysql_session()()) as session:
        for s in ss:
            if session.query(
                suggested_keyword,
            ).filter(
                suggested_keyword.category_id == category_id,
                suggested_keyword.print_length == print_length,
                suggested_keyword.string == s,
            ).count():
                continue
            session.add(suggested_keyword(**{
                'category_id': category_id,
                'print_length': print_length,
                'string': s,
            }))
        session.commit()


def step_4_reset(category_id, print_length):
    print 'Step 4 :: Reset'
    with closing(get_mysql_session()()) as session:
        session.query(
            suggested_keyword,
        ).filter(
            suggested_keyword.category_id == category_id,
            suggested_keyword.print_length == print_length,
        ).update(
            {
                'average_price': 0.00,
                'average_print_length': 0.00,
                'buyer_behavior': '',
                'competition': '',
                'count': 0,
                'optimization': '',
                'popularity': '',
                'score': 0.00,
                'spend': '',
            },
            synchronize_session=False,
        )
        session.commit()
    print 'Done'


def step_4_queue(category_id, print_length):
    print 'Step 4 :: Queue'
    with closing(get_mysql_session()()) as session:
        for instance in session.query(
            suggested_keyword,
        ).order_by(
            'id ASC',
        ).filter(
            suggested_keyword.category_id == category_id,
            suggested_keyword.print_length == print_length,
            suggested_keyword.score == 0.00,
        ).execution_options(
            stream_results=True,
        ):
            step_4_process.delay(
                category_id, print_length, instance.id, instance.string,
            )
    print 'Done'


@celery.task
def step_4_process(category_id, print_length, id, string):
    contents = get_contents(string, 'com')
    if not contents:
        return
    with closing(get_mysql_session()()) as session:
        instance = session.query(suggested_keyword).get(id)
        if not instance:
            return
        instance.count = contents['count'][0]
        instance.buyer_behavior = contents['buyer_behavior'][0]
        instance.competition = contents['competition'][0]
        instance.optimization = contents['optimization'][0]
        instance.popularity = contents['popularity'][0]
        instance.spend = contents['spend'][0][0]
        instance.average_price = contents['average_price'][0]
        instance.average_print_length = contents['average_length'][0]
        instance.score = contents['score'][0]
        session.add(instance)
        session.commit()


def step_5(category_id, print_length):
    print 'Step 5'
    with closing(get_mysql_session()()) as session:
        session.query(
            group,
        ).filter(
            group.category_id == category_id,
            group.print_length == print_length,
        ).delete(
            synchronize_session=False,
        )
        session.commit()
    with closing(get_mysql_session()()) as session:
        items = defaultdict(set)
        suggested_keywords = session.query(
            suggested_keyword,
        ).filter(
            suggested_keyword.category_id == category_id,
            suggested_keyword.print_length == print_length,
            suggested_keyword.score >= 70.00,
        ).order_by(
            'score DESC',
        ).execution_options(
            stream_results=True,
        )[0:10]
        range_ = range(len(suggested_keywords))
        for outer in range_:
            items[outer].add(suggested_keywords[outer])
            for inner in range(outer + 1, len(range_)):
                if suggested_keywords[inner].string in [
                    suggested_keyword_.string
                    for value in items.values()
                    for suggested_keyword_ in value
                ]:
                    continue
                if len(
                    set(
                        word
                        for word in word_tokenize(
                            suggested_keywords[outer].string
                        )
                        if word not in stopwords
                    ).intersection(
                        word
                        for word in word_tokenize(
                            suggested_keywords[inner].string
                        )
                        if word not in stopwords
                    )
                ) < 2:
                    continue
                items[outer].add(suggested_keywords[inner])
        for value in items.values():
            group_ = group(**{
                'category_id': category_id,
                'print_length': print_length,
            })
            for suggested_keyword_ in value:
                session.add(group_suggested_keyword(**{
                    'group': group_,
                    'suggested_keyword': suggested_keyword_,
                }))
        session.commit()
    with closing(get_mysql_session()()) as session:
        for group_ in session.query(
            group,
        ).filter(
            group.category_id == category_id,
            group.print_length == print_length,
        ).order_by(
            'id ASC',
        ).execution_options(
            stream_results=True,
        ):
            books = []
            for suggested_keyword_ in group_.suggested_keywords.order_by(
                'apps_hot_category_groups_suggested_keywords.id ASC',
            ).execution_options(
                stream_results=True,
            ):
                query = session.query(book)
                for word in word_tokenize(suggested_keyword_.string):
                    if word in stopwords:
                        continue
                    query = query.filter(book.title.like('%%%(word)s%%' % {
                        'word': word,
                    }))
                for book_ in query.order_by(
                    'id ASC',
                ).execution_options(
                    stream_results=True,
                ):
                    books.append(book_)
            if not books:
                continue
            count = max([
                frequency
                for book_, frequency in Counter(books).most_common()
            ])
            if not count > 1:
                continue
            for book_, frequency in Counter(books).most_common():
                if not frequency == count:
                    continue
                session.add(group_book(**{
                    'book': book_,
                    'group': group_,
                }))
        session.commit()
    print 'Done'


def xlsx(category_id, print_length):
    th_left = Style(
        alignment=Alignment(
            horizontal='left',
            indent=0,
            shrink_to_fit=False,
            text_rotation=0,
            vertical='center',
            wrap_text=False,
        ),
        font=Font(
            bold=True,
            italic=False,
            name='Calibri',
            size=12,
            strike=False,
            underline='none',
            vertAlign=None,
        ),
    )
    th_right = Style(
        alignment=Alignment(
            horizontal='right',
            indent=0,
            shrink_to_fit=False,
            text_rotation=0,
            vertical='center',
            wrap_text=False,
        ),
        font=Font(
            bold=True,
            italic=False,
            name='Calibri',
            size=12,
            strike=False,
            underline='none',
            vertAlign=None,
        ),
    )
    td_left = Style(
        alignment=Alignment(
            horizontal='left',
            indent=0,
            shrink_to_fit=False,
            text_rotation=0,
            vertical='center',
            wrap_text=False,
        ),
        font=Font(
            bold=False,
            italic=False,
            name='Calibri',
            size=10,
            strike=False,
            underline='none',
            vertAlign=None,
        ),
    )
    td_right = Style(
        alignment=Alignment(
            horizontal='right',
            indent=0,
            shrink_to_fit=False,
            text_rotation=0,
            vertical='center',
            wrap_text=False,
        ),
        font=Font(
            bold=False,
            italic=False,
            name='Calibri',
            size=10,
            strike=False,
            underline='none',
            vertAlign=None,
        ),
    )

    workbook = Workbook()

    for worksheet in workbook.worksheets:
        workbook.remove_sheet(worksheet)

    worksheet = workbook.create_sheet()
    worksheet.title = 'Step 1 - Top 20 Words'
    worksheet.cell('A1').style = th_left
    worksheet.cell('A1').value = 'String'
    with closing(get_mysql_session()()) as session:
        row = 1
        for instance in session.query(
            word,
        ).filter(
            word.category_id == category_id,
            word.print_length == print_length,
        ).order_by(
            'string ASC',
        ).execution_options(
            stream_results=True,
        ):
            row += 1
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).value = instance.string
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).style = td_left
    worksheet.column_dimensions['A'].width = 50

    worksheet = workbook.create_sheet()
    worksheet.title = 'Step 2 - KS (Combine)'
    worksheet.cell('A1').style = th_left
    worksheet.cell('A1').value = 'String'
    with closing(get_mysql_session()()) as session:
        row = 1
        for instance in session.query(
            keyword,
        ).filter(
            keyword.category_id == category_id,
            keyword.print_length == print_length,
        ).order_by(
            'string ASC',
        ).execution_options(
            stream_results=True,
        ):
            row += 1
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).value = instance.string
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).style = td_left
    worksheet.column_dimensions['A'].width = 50

    worksheet = workbook.create_sheet()
    worksheet.title = 'Step 3 & 4 - SK + KA'
    worksheet.cell('A1').style = th_left
    worksheet.cell('A1').value = 'String'
    worksheet.cell('B1').style = th_right
    worksheet.cell('B1').value = 'Count'
    worksheet.cell('C1').style = th_right
    worksheet.cell('C1').value = 'Buyer Behavior'
    worksheet.cell('D1').style = th_right
    worksheet.cell('D1').value = 'Competition'
    worksheet.cell('E1').style = th_right
    worksheet.cell('E1').value = 'Optimization'
    worksheet.cell('F1').style = th_right
    worksheet.cell('F1').value = 'Popularity'
    worksheet.cell('G1').style = th_right
    worksheet.cell('G1').value = 'Spend'
    worksheet.cell('H1').style = th_right
    worksheet.cell('H1').value = 'Average Price'
    worksheet.cell('I1').style = th_right
    worksheet.cell('I1').value = 'Average Print Length'
    worksheet.cell('J1').style = th_right
    worksheet.cell('J1').value = 'Score'
    with closing(get_mysql_session()()) as session:
        row = 1
        for instance in session.query(
            suggested_keyword,
        ).filter(
            suggested_keyword.category_id == category_id,
            suggested_keyword.print_length == print_length,
        ).order_by(
            'score DESC',
        ).execution_options(
            stream_results=True,
        ):
            row += 1
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).style = td_left
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).value = instance.string
            worksheet.cell('B%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('B%(row)s' % {
                'row': row,
            }).value = format('%d', instance.count, grouping=True)
            worksheet.cell('C%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('C%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.buyer_behavior), grouping=True,
            )
            worksheet.cell('D%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('D%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.competition), grouping=True,
            )
            worksheet.cell('E%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('E%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.optimization), grouping=True,
            )
            worksheet.cell('F%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('F%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.popularity), grouping=True,
            )
            worksheet.cell('G%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('G%(row)s' % {
                'row': row,
            }).value = format('%.2f', float(instance.spend), grouping=True)
            worksheet.cell('H%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('H%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.average_price), grouping=True,
            )
            worksheet.cell('I%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('I%(row)s' % {
                'row': row,
            }).value = format(
                '%.2f', float(instance.average_print_length), grouping=True,
            )
            worksheet.cell('J%(row)s' % {
                'row': row,
            }).style = td_right
            worksheet.cell('J%(row)s' % {
                'row': row,
            }).value = format('%.2f', float(instance.score), grouping=True)
    worksheet.column_dimensions['A'].width = 50
    worksheet.column_dimensions['B'].width = 15
    worksheet.column_dimensions['C'].width = 15
    worksheet.column_dimensions['D'].width = 15
    worksheet.column_dimensions['E'].width = 15
    worksheet.column_dimensions['F'].width = 15
    worksheet.column_dimensions['G'].width = 15
    worksheet.column_dimensions['H'].width = 15
    worksheet.column_dimensions['I'].width = 15
    worksheet.column_dimensions['J'].width = 15

    worksheet = workbook.create_sheet()
    worksheet.title = 'Step 5 - Groups'
    with closing(get_mysql_session()()) as session:
        number = 0
        row = 0
        for group_ in session.query(
            group,
        ).filter(
            group.category_id == category_id,
            group.print_length == print_length,
        ).order_by(
            'id ASC',
        ).execution_options(
            stream_results=True,
        ):
            number += 1
            row += 1
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).style = th_left
            worksheet.cell('A%(row)s' % {
                'row': row,
            }).value = 'Group %(number)s' % {
                'number': number,
            }
            for suggested_keyword_ in group_.suggested_keywords.order_by(
                'apps_hot_category_groups_suggested_keywords.id ASC',
            ).execution_options(
                stream_results=True,
            ):
                row += 1
                worksheet.append([suggested_keyword_.string])
            row += 1
            worksheet.append([''])
    worksheet.column_dimensions['A'].width = 50

    workbook.save('../tmp/%(category_id)s-%(print_length)s-report.xlsx' % {
        'category_id': arguments.category_id,
        'print_length': arguments.print_length,
    })

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '--category-id', dest='category_id', required=True, type=int,
    )
    parser.add_argument('--print-length', dest='print_length', required=True)
    parser.add_argument('--def', dest='def_', required=True)
    parser.set_defaults(reset=False)

    arguments = parser.parse_args()

    locals()[arguments.def_](arguments.category_id, arguments.print_length)
