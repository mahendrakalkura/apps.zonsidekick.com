# -*- coding: utf-8 -*-

from ujson import dumps
from rollbar import report_message

from keyword_suggester import get_results
from utilities import get_mysql_connection


def main():
    mysql = get_mysql_connection()
    cursor = mysql.cursor()
    cursor.execute(
        '''
        SELECT * FROM `apps_keyword_suggester` WHERE `strings` IS NULL
        '''
    )
    for row in cursor:
        results = get_results(
            row['string'], row['country'], row['search_alias']
        )
        if not results:
            report_message(
                'free -> main()',
                extra_data={
                    'country': row['country'],
                    'search_alias': row['search_alias'],
                    'string': row['string'],
                }
            )
            continue
        cursor.execute(
            '''
            UPDATE `apps_keyword_suggester` SET `strings` = %(results)s
            WHERE `id` = %(id)s
            ''',
            {
                'id': row['id'],
                'results': dumps(results),
            }
        )
    cursor.close()
    mysql.commit()

if __name__ == '__main__':
    main()
