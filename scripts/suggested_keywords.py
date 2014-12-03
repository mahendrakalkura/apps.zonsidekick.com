# -*- coding: utf-8 -*-

from sys import argv

from furl import furl
from simplejson import dumps, JSONDecodeError, loads

from utilities import get_responses


def get_suggested_keywords(original_keywords):
    suggested_keywords = []
    original_keywords = [
        original_keyword.lower() for original_keyword in original_keywords
    ]
    for response in get_responses([
        furl(
            'http://completion.amazon.com/search/complete'
        ).add({
            'mkt': '1',
            'q': original_keyword,
            'search-alias': 'digital-text',
            'xcat': '2',
        }).url
        for original_keyword in original_keywords
    ]):
        if not response:
            continue
        contents = ''
        try:
            contents = loads(response.text)
        except JSONDecodeError:
            pass
        if not contents:
            continue
        for keyword in contents[1]:
            if ' ' not in keyword:
                continue
            words = keyword.split(' ')
            if len([word for word in words if word in original_keywords]) >= 2:
                if keyword not in suggested_keywords:
                    suggested_keywords.append(keyword)
    return suggested_keywords

if __name__ == '__main__':
    print dumps(get_suggested_keywords(argv[1].split(',')))
