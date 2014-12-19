# -*- coding: utf-8 -*-

from logging import DEBUG, getLogger, StreamHandler

from webassets import Bundle, Environment
from webassets.script import CommandLineEnvironment
from webassets.script import CommandLineEnvironment

logger = getLogger('webassets')
logger.setLevel(DEBUG)
logger.addHandler(StreamHandler())

environment = Environment()

environment.cache = False
environment.debug = False
environment.directory = '../'
environment.manifest = False
environment.url = '../'
environment.url_expire = True
environment.versions = 'hash'

environment.register('javascripts', Bundle(
    'vendor/jquery/dist/jquery.min.js',
    'vendor/jquery-cookie/jquery.cookie.js',
    'vendor/angular/angular.min.js',
    'vendor/angular-encode-uri/dist/angular-encode-uri.min.js',
    'vendor/angular-queue/angular-queue.js',
    'vendor/angular-scroll/angular-scroll.min.js',
    'vendor/lodash/dist/lodash.min.js',
    'vendor/moment/min/moment-with-locales.min.js',
    'vendor/pixeladmin/html/assets/javascripts/bootstrap.min.js',
    'vendor/pixeladmin/html/assets/javascripts/ie.min.js',
    'vendor/pixeladmin/html/assets/javascripts/pixel-admin.min.js',
    'vendor/jquery-zclip/jquery.zclip.js',
    'javascripts/all.js',
    filters='rjsmin',
    output='assets/javascripts.js',
))
environment.register('stylesheets', Bundle(
    'vendor/pixeladmin/html/assets/stylesheets/bootstrap.css',
    'vendor/pixeladmin/html/assets/stylesheets/pixel-admin.css',
    'vendor/pixeladmin/html/assets/stylesheets/widgets.css',
    'vendor/pixeladmin/html/assets/stylesheets/pages.css',
    'vendor/pixeladmin/html/assets/stylesheets/rtl.css',
    'vendor/pixeladmin/html/assets/stylesheets/themes.css',
    'stylesheets/all.css',
    filters='cssmin,cssrewrite',
    output='assets/stylesheets.css',
))

CommandLineEnvironment(environment, logger).build()
