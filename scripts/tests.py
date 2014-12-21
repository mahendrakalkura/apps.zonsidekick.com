# -*- coding: utf-8 -*-

from smtplib import SMTP

from flask.ext.mail import Message

from author_analyzer import get_author, get_authors
from book_analyzer import get_books, get_items
from keyword_analyzer import get_contents
from keyword_suggester import get_results
from suggested_keywords import get_suggested_keywords
from utilities import get_book, get_response, variables


def author_analyzer_py_get_author():
    output = get_author('http://www.amazon.com/Stephen-King/e/B000AQ0842')
    if (
        type(output) == dict
        and
        output
        and
        'amazon_rank' in output
        and
        'books' in output
        and
        'description' in output
        and
        'earnings_per_month' in output
        and
        'name' in output
        and
        'photo' in output
        and
        'twitter' in output
    ):
        return True
    return False


def author_analyzer_py_get_authors():
    output = get_authors('stephen king')
    if (
        type(output) == list
        and
        output
        and
        'name' in output[0]
        and
        'url' in output[0]
    ):
        return True
    return False


def book_analyzer_py_get_book():
    output = get_book(get_response(
        'http://www.amazon.com/Mystery-John-Nichols-ebook/dp/B00O0998GE'
    ))
    if (
        type(output) == dict
        and
        output
        and
        'amazon_best_sellers_rank' in output
        and
        'author' in output
        and
        'book_cover_image' in output
        and
        'earnings_per_day' in output
        and
        'estimated_sales_per_day' in output
        and
        'price' in output
        and
        'print_length' in output
        and
        'publication_date' in output
        and
        'review_average' in output
        and
        'title' in output
        and
        'total_number_of_reviews' in output
        and
        'url' in output
    ):
        return True
    return False


def book_analyzer_py_get_books():
    output = get_books('mystery')
    if (
        type(output) == list
        and
        output
        and
        'title' in output[0]
        and
        'url' in output[0]
    ):
        return True
    return False


def book_analyzer_py_get_items():
    output = get_items(
        'http://www.amazon.com/Mystery-John-Nichols-ebook/dp/B00O0998GE',
        ['mystery']
    )
    if type(output) == list and len(output) > 0:
        return True
    return False


def keyword_analyzer_py():
    output = get_contents('stephen king', 'com')
    if (
        type(output) == dict
        and
        output
        and
        'average_length' in output
        and
        'average_price' in output
        and
        'buyer_behavior' in output
        and
        'competition' in output
        and
        'count' in output
        and
        'items' in output
        and
        'matches' in output
        and
        'optimization' in output
        and
        'popularity' in output
        and
        'score' in output
        and
        'spend' in output
        and
        'words' in output
    ):
        return True
    return False


def keyword_suggester_py():
    output = get_results('stephen king', 'com', 'digital-text')
    if type(output) == list and len(output) > 0:
        return True
    return False


def suggested_keywords_py():
    output = get_suggested_keywords(['stephen', 'king'])
    if type(output) == list and len(output) > 0:
        return True
    return False

if __name__ == '__main__':
    body = '\n'.join([
        'author_analyzer_py_get_authors: %(status)s' % {
            'status':
            'Success' if author_analyzer_py_get_authors() else 'Failure'
        },
        'author_analyzer_py_get_author: %(status)s' % {
            'status':
            'Success' if author_analyzer_py_get_author() else 'Failure'
        },
        'keyword_suggester_py: %(status)s' % {
            'status': 'Success' if keyword_suggester_py() else 'Failure'
        },
        'book_analyzer_py_get_books: %(status)s' % {
            'status': 'Success' if book_analyzer_py_get_books() else 'Failure'
        },
        'book_analyzer_py_get_book: %(status)s' % {
            'status': 'Success' if book_analyzer_py_get_book() else 'Failure'
        },
        'book_analyzer_py_get_items: %(status)s' % {
            'status': 'Success' if book_analyzer_py_get_items() else 'Failure'
        },

        'keyword_analyzer_py: %(status)s' % {
            'status': 'Success' if keyword_analyzer_py() else 'Failure'
        },
        'suggested_keywords_py: %(status)s' % {
            'status': 'Success' if suggested_keywords_py() else 'Failure'
        },
    ])
    resource = SMTP(variables['smtp']['host'], variables['smtp']['port'])
    resource.login(
        variables['smtp']['username'], variables['smtp']['password']
    )
    message = Message(
        'tests.py',
        bcc=['mahendrakalkura@gmail.com'],
        body=body,
        recipients=['ncroan@gmail.com'],
        sender=('Perfect Sidekick', 'support@perfectsidekick.com'),
    )
    resource.sendmail(message.sender, message.send_to, str(message))
    resource.quit()
