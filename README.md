How to install?
===============

Step 1
------

```
$ mkdir apps.zonsidekick.com
$ cd zonsidekick
$ git clone --recursive git@bitbucket.org:mahendrakalkura/apps.zonsidekick.com.git .
$ cp variables.json.sample variables.json # edit variables.json as required
```

Step 2
------

```
$ cd apps.zonsidekick.com
$ mysql -e 'CREATE DATABASE `apps.zonsidekick.com`'
$ mysql apps.zonsidekick.com < files/1.sql
```

Step 3
------

```
$ cd apps.zonsidekick.com
$ composer install
$ bower install
```

Step 4
------

```
$ cd apps.zonsidekick.com
$ mkvirtualenv apps.zonsidekick.com
$ pip install -r requirements.txt
```

Step 5
------

```
$ cd apps.zonsidekick.com/vendor/pixeladmin
$ npm install
$ grunt compile-js
$ grunt compile-less
$ grunt compile-sass
```

Step 6
------

```
$ cd apps.zonsidekick.com
$ workon apps.zonsidekick.com
$ cd scripts
$ python assets.py build
```

How to run?
===========

```
$ cd apps.zonsidekick.com
$ php -S 0.0.0.0:5000
```

Others
======

crontab
-------

```
*/30 * * * * cd {{ path }}/scripts && {{ virtualenv }}/python popular_searches.py
0 */6 * * * cd {{ path }} && {{ virtualenv }}/scrapy crawl top_100_explorer
```

supervisor
----------

```
[program:book_tracker]
autorestart=true
autostart=true
command={{ virtualenv }}/python book_tracker.py
directory=cd {{ path }}/scripts
startsecs=0
```

```
[program:keyword_analyzer]
autorestart=true
autostart=true
command={{ virtualenv }}/python keyword_analyzer.py
directory=cd {{ path }}/scripts
startsecs=0
```
