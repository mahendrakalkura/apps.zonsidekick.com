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
    rows = cursor.fetchall()
    cursor.close()
    for row in rows:
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
        cursor = mysql.cursor()
        cursor.execute(
            '''
            UPDATE `apps_keyword_suggester`
            SET `strings` = %(results)s, `timestamp` = NOW()
            WHERE `id` = %(id)s
            ''',
            {
                'id': row['id'],
                'results': dumps(results),
            }
        )
        cursor.close()
        mysql.commit()

    cursor = mysql.cursor()
    cursor.execute(
        '''
        DELETE FROM apps_keyword_suggester
        WHERE `timestamp` < DATE_SUB(NOW(), INTERVAL 7 DAY)
        '''
    )
    cursor.close()
    mysql.commit()

if __name__ == '__main__':
    main()
