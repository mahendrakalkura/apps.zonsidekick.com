# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from smtplib import SMTP

from aa import get_author, get_authors
from aks import get_results
from ba import get_books, get_items
from kns import get_contents
from sk import get_suggested_keywords
from utilities import get_book, get_response


def aa_py_get_authors():
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
    else:
        return False


def aa_py_get_author():
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
    else:
        return False


def aks_py():
    output = get_results('stephen king', 'com', 'digital-text')
    if type(output) == list and len(output) > 0:
        return True
    else:
        return False


def ba_py_get_books():
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
    else:
        return False


def ba_py_get_book():
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
    else:
        return False


def ba_py_get_items():
    output = get_items(
        'http://www.amazon.com/Mystery-John-Nichols-ebook/dp/B00O0998GE',
        ['mystery']
    )
    if type(output) == list and len(output) > 0:
        return True
    else:
        return False


def kns_py():
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
    else:
        return False


def sk_py():
    output = get_suggested_keywords(['stephen', 'king'])
    if type(output) == list and len(output) > 0:
        return True
    else:
        return False


if __name__ == '__main__':
    body = '\n'.join([
        'aa_py_get_authors: %(status)s' % {
            'status': 'Success' if aa_py_get_authors() else 'Failure'
        },
        'aa_py_get_author: %(status)s' % {
            'status': 'Success' if aa_py_get_author() else 'Failure'
        },
        'aks_py: %(status)s' % {
            'status': 'Success' if aks_py() else 'Failure'
        },
        'ba_py_get_books: %(status)s' % {
            'status': 'Success' if ba_py_get_books() else 'Failure'
        },
        'ba_py_get_book: %(status)s' % {
            'status': 'Success' if ba_py_get_book() else 'Failure'
        },
        'ba_py_get_items: %(status)s' % {
            'status': 'Success' if ba_py_get_items() else 'Failure'
        },

        'kns_py: %(status)s' % {
            'status': 'Success' if kns_py() else 'Failure'
        },
        'sk_py: %(status)s' % {
            'status': 'Success' if sk_py() else 'Failure'
        },
    ])
    resource = SMTP(
        'smtp.mandrillapp.com', 587
    )
    resource.login(
        'ncroan', 'teFUcZodZBU6lAsr86irtA'
    )
    message = MIMEText(body)
    message['Subject'] = 'Automated Testing'
    message['From'] = 'ncroan@gmail.com'
    message['To'] = 'mahendrakalkura@gmail.com'
    resource.sendmail(
        message['From'], message['To'], message.as_string()
    )
    resource.quit()
