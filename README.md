How to install?
===============

Step 1:

```
$ mkdir zonsidekick.com
$ cd zonsidekick
$ git clone git@bitbucket.org:mahendrakalkura/zonsidekick.com.git .
$ cp variables.json.sample variables.json # edit variables.json as required
```

Step 2:

```
$ cd zonsidekick.com
$ mysql -h {{ host }} -p{{ password }} -u {{ user }}
> CREATE DATABASE `zonsidekick.com`;
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/1.sql
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/2.sql
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/3.sql
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/4.sql
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/5.sql
```

Step 3:

```
$ cd zonsidekick.com
$ composer install
$ bower install
```

Step 4:

```
$ cd zonsidekick.com
$ mkvirtualenv zonsidekick.com
$ workon zonsidekick.com
$ pip install -r requirements.txt
```

How to run?
===========

Step 1:

```
$ cd zonsidekick.com
$ php -S 0.0.0.0:5000
```

Step 2:

```
$ cd zonsidekick.com
$ workon zonsidekick.com
$ cd scripts
$ python aks.py ...
$ python kns.py ...
```

Others (only for the server)
============================

crontab:

```
0 */6 * * * cd {{ path }} && {{ virtualenv }}/scrapy crawl ce
0 * * * * supervisorctl restart kns
*/30 * * * * cd {{ path }}/scripts && {{ virtualenv }}/python ps.py
```

supervisor:

```
[program:kns]
autorestart=true
autostart=true
command={{ virtualenv }}/python kns.py
directory=cd {{ path }}/scripts
startsecs=0
```
