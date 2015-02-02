# -*- coding: utf-8 -*-

from logging import DEBUG, getLogger, StreamHandler
from sys import argv

from webassets import Bundle, Environment
from webassets.script import CommandLineEnvironment

from utilities import variables

logger = getLogger('webassets')
logger.setLevel(DEBUG)
logger.addHandler(StreamHandler())

environment = Environment()

environment.cache = False
environment.debug = variables['application']['debug']
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
    'vendor/highcharts/highcharts.src.js',
    'vendor/lodash/dist/lodash.min.js',
    'vendor/moment/min/moment-with-locales.min.js',
    'vendor/pixeladmin/html/assets/javascripts/bootstrap.min.js',
    'vendor/pixeladmin/html/assets/javascripts/ie.min.js',
    'vendor/pixeladmin/html/assets/javascripts/pixel-admin.min.js',
    'vendor/jquery-zclip/jquery.zclip.js',
    'vendor/angular-rollbar/angular-rollbar.js',
    'javascripts/all.js',
    filters=None if environment.debug else 'rjsmin',
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
    filters='cssrewrite' if environment.debug else 'cssmin,cssrewrite',
    output='assets/stylesheets.css',
))

if __name__ == '__main__':
    if argv[1] == 'build':
        CommandLineEnvironment(environment, logger).build()
    if argv[1] == 'watch':
        CommandLineEnvironment(environment, logger).watch()
