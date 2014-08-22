# -*- coding: utf-8 -*-

from sys import argv

from furl import furl
from simplejson import dumps, JSONDecodeError, loads

from utilities import get_responses


def get_mkt_and_url(country):
    if country == 'com':
        return 1, get_url('com')
    if country == 'co.uk':
        return 3, get_url('co.uk')
    if country == 'es':
        return 44551, get_url('co.uk')
    if country == 'fr':
        return 5, get_url('co.uk')
    if country == 'it':
        return 35691, get_url('co.uk')
    if country == 'com.br':
        return 526970, get_url('com')
    if country == 'ca':
        return 7, get_url('com')
    if country == 'de':
        return 4, get_url('co.uk')
    if country == 'co.jp':
        return 6, get_url('co.jp')
    return 1, get_url('com')


def get_params(mkt, q, search_alias):
    return {
        'mkt': mkt,
        'q': q,
        'search-alias': search_alias,
        'xcat': '0',
    }


def get_results(country, level, mode, q, search_alias):
    results = []
    if mode == 1:
        results = get_suggestions(country, level, q, search_alias)
    if mode == 2:
        qs = q.split(' ')
        if len(qs) <= 10:
            results = []
            results += get_suggestions(country, level, q, search_alias)
            for q in qs:
                results += get_suggestions(country, level, q, search_alias)
            results = [
                result for result in results if all(q in result for q in qs)
            ]
        else:
            results = get_suggestions(country, level, q, search_alias)
    return sorted(set(results))


def get_suggestions(country, level, q, search_alias):
    strings = []
    strings.append(q)
    alphabets = map(chr, range(97, 123))
    while level:
        qs = []
        for string in strings:
            for alphabet in alphabets:
                qs.append('%(string)s %(alphabet)s' % {
                    'alphabet': alphabet,
                    'string': string,
                })
        urls = []
        for q in qs:
            mkt, url = get_mkt_and_url(country)
            urls.append(furl(url).add(get_params(mkt, q, search_alias)).url)
        for response in get_responses(urls):
            if not response:
                continue
            contents = ''
            try:
                contents = loads(response.text)
            except JSONDecodeError:
                pass
            if not contents:
                continue
            for suggestion in contents[1]:
                if suggestion not in strings:
                    strings.append(suggestion)
        level -= 1
    return strings


def get_url(sub_domain):
    return 'http://completion.amazon.%(sub_domain)s/search/complete' % {
        'sub_domain': sub_domain,
    }

if __name__ == '__main__':
    print dumps(get_results(
        argv[1], int(argv[2]), int(argv[3]), argv[4], argv[5]
    ))
