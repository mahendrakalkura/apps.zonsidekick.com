# -*- coding: utf-8 -*-

from multiprocessing.pool import ThreadPool
from sys import argv

from requests import get
from requests.exceptions import RequestException
from simplejson import dumps, loads

from utilities import get_proxies


def get_contents(url, params):
    try:
        return get(
            url,
            allow_redirects=True,
            params=params,
            proxies=get_proxies(),
            timeout=10,
            verify=False
        ).text
    except:
        pass


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
        'client': 'amazon-search-ui',
        'fb': '1',
        'method': 'completion',
        'mkt': mkt,
        'q': q,
        'sc': '1',
        'search-alias': search_alias,
        'x': 'updateISSCompletion',
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
                result
                for result in results
                if all(
                    q in result
                    for q in qs
                )
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
        results = []
        pool = ThreadPool(50)
        for q in qs:
            mkt, url = get_mkt_and_url(country)
            results.append(pool.apply_async(
                get_contents, (url, get_params(mkt, q, search_alias))
            ))
        pool.close()
        pool.join()
        for result in results:
            try:
                for suggestion in loads(
                    result.get().replace(
                        'completion = ', ''
                    ).replace(
                        ';updateISSCompletion();', ''
                    )
                )[1]:
                    suggestion = suggestion.strip()
                    if suggestion:
                        if not suggestion in strings:
                            strings.append(suggestion)
            except IndexError:
                pass
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
