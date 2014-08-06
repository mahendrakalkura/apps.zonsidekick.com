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
$ mkdir zonsidekick.com
$ mysql -h {{ host }} -p{{ password }} -u {{ user }}
> CREATE DATABASE `zonsidekick.com`;
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/structure.sql
$ mysql -h {{ host }} -p{{ password }} -u {{ user }} zonsidekick.com < files/data.sql
```

Step 3:

```
$ mkdir zonsidekick.com
$ composer install
$ bower install
```

Step 4:

```
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
$ python aks.py ...
$ python kns.py ...
```
