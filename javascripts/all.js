Array.prototype.get_chunks = function (length) {
    var array = this;
    return [].concat.apply([], array.map(function (value, key) {
        return key % length? []: [array.slice(key, key + length)];
    }));
}

var get_parameter = function (name) {
    var pattern = new RegExp('[\\?&]' + name + '=([^&#]*)', 'gi');
    var results = pattern.exec(window.location.search);
    return results == null? '': decodeURIComponent(
        results[1].replace(/\+/gi, ' ')
    );
};

var is_development = function () {
    if(window.location.port == '5000'){
        return true;
    }

    return false;
};

var application = angular.module('application', [
    'duScroll', 'ngQueue', 'rt.encodeuri',
]);

application.config(function ($httpProvider, $interpolateProvider) {
    $httpProvider.defaults.headers.post[
        'Content-Type'
    ] = 'application/x-www-form-urlencoded';
    $interpolateProvider.startSymbol('[!').endSymbol('!]');
});

application.directive('datepicker', function () {
    return {
        link: function (scope, element, attrs, ngModel) {
            jQuery(element).datepicker({
                format: 'yyyy-mm-dd'
            }).on('changeDate', function (event) {
                scope.$apply(function () {
                    ngModel.$setViewValue(moment(
                        new Date(event.date)
                    ).format('YYYY-MM-DD'));
                });
                jQuery(element).datepicker('hide');
            });
        },
        require: 'ngModel',
        restrict: 'A'
    };
});

application.directive('ngFocus', function ($timeout) {
    return {
        link: function (scope, element, attrs) {
            scope.$watch(attrs.ngFocus, function (value) {
                if (angular.isDefined(value) && value) {
                    $timeout(function () {
                        element[0].focus();
                    });
                }
            }, true);
            element.bind('blur', function () {
                if (angular.isDefined(attrs.ngOnBlur)) {
                    scope.$apply(attrs.ngOnBlur);
                }
            });
        }
    };
});

application.directive('popover', function () {
    return {
        link: function (scope, element, attrs) {
            jQuery(element).popover({
                container: 'body',
                content: jQuery(element).find('div').contents(),
                html: true,
                placement: 'bottom'
            });
        },
        restrict: 'A'
    };
});

application.filter('html', function ($sce) {
    return function (html) {
        return $sce.trustAsHtml(html);
    };
});

application.filter('label', function () {
    return function (one, two, status) {
        if (status) {
            switch (one) {
                case 'Very High':
                    return (
                        '<span class="label label-success">' + two + '</span>'
                    );
                case 'High':
                    return (
                        '<span class="label label-success">' + two + '</span>'
                    );
                case 'Medium':
                    return (
                        '<span class="label label-warning">' + two + '</span>'
                    );
                case 'Low':
                    return (
                        '<span class="label label-danger">'
                        +
                        two
                        +
                        '</span>'
                    );
                case 'Very Low':
                    return (
                        '<span class="label label-danger">'
                        +
                        two
                        +
                        '</span>'
                    );
                default:
                    break;
            }
        } else {
            switch (one) {
                case 'Very High':
                    return (
                        '<span class="label label-danger">'
                        +
                        two
                        +
                        '</span>'
                    );
                case 'High':
                    return (
                        '<span class="label label-danger">'
                        +
                        two
                        +
                        '</span>'
                    );
                case 'Medium':
                    return (
                        '<span class="label label-warning">' + two + '</span>'
                    );
                case 'Low':
                    return (
                        '<span class="label label-success">' + two + '</span>'
                    );
                case 'Very Low':
                    return (
                        '<span class="label label-success">' + two + '</span>'
                    );
                default:
                    break;
            }
        }

        return two;
    }
});

application.filter('slice', function () {
    return function (list, start, stop) {
        if (typeof(list) == 'undefined') {
            return [];
        }

        return list.slice(start, stop);
    };
});

application.controller('amazon_best_sellers_rank', [
    '$scope',
    function ($scope) {
        $scope.status = false;
    }
]);

application.controller('author_analyzer', [
    '$attrs',
    '$document',
    '$http',
    '$rootScope',
    '$scope',
    function ($attrs, $document, $http, $rootScope, $scope) {
        $scope.keyword = '';
        $scope.authors = {
            'contents': [],
            'spinner': false
        };
        $scope.author = {
            'contents': '',
            'spinner': false
        };

        $scope.get_authors = function () {
            $scope.authors.contents = [];
            $scope.authors.spinner = false;
            $scope.author.contents = '';
            $scope.author.spinner = false;

            if (!$scope.keyword.length) {
                $rootScope.$broadcast('open', {
                    top: $attrs.error1Top,
                    middle: $attrs.error1Middle
                });

                return;
            }

            $scope.authors.spinner = true;

            $http({
                data: jQuery.param({
                    keyword: $scope.keyword
                }),
                method: 'POST',
                url: $attrs.urlAuthors
            }).
            error(function (data, status, headers, config) {
                $scope.authors.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.authors.spinner = false;
                if (data.length > 0) {
                    $scope.authors.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        $scope.get_author = function (url) {
            $scope.author.contents = '';
            $scope.author.spinner = false;

            $scope.author.spinner = true;

            $document.scrollToElement(angular.element(
                document.getElementById('scroll')
            ));

            $http({
                data: jQuery.param({
                    url: url
                }),
                method: 'POST',
                url: $attrs.urlAuthor
            }).
            error(function (data, status, headers, config) {
                $scope.author.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.author.spinner = false;
                if (typeof(data) === 'object') {
                    $scope.author.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        if ($attrs.url.length) {
            $scope.get_author($attrs.url);
        }
    }
]);

application.controller('book', [
    '$scope',
    function ($scope) {
        $scope.status = false;
    }
]);

application.controller('book_analyzer', [
    '$attrs',
    '$document',
    '$http',
    '$rootScope',
    '$scope',
    function ($attrs, $document, $http, $rootScope, $scope) {
        $scope.keyword = '';
        $scope.books = {
            'contents': [],
            'spinner': false
        };
        $scope.book = {
            'contents': '',
            'spinner': false
        };
        $scope.items = {
            'contents': '',
            'spinner': false
        };
        $scope.keywords = '';

        $scope.get_books = function () {
            $scope.books.contents = [];
            $scope.books.spinner = false;
            $scope.book.contents = '';
            $scope.book.spinner = false;
            $scope.items.contents = '';
            $scope.items.spinner = false;

            if (!$scope.keyword.length) {
                $rootScope.$broadcast('open', {
                    top: $attrs.error1Top,
                    middle: $attrs.error1Middle
                });

                return;
            }

            $scope.books.spinner = true;

            $http({
                data: jQuery.param({
                    keyword: $scope.keyword
                }),
                method: 'POST',
                url: $attrs.urlBooks
            }).
            error(function (data, status, headers, config) {
                $scope.books.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.books.spinner = false;
                if (data.length > 0) {
                    $scope.books.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        $scope.get_book = function (url) {
            $scope.book.contents = '';
            $scope.book.spinner = false;
            $scope.items.contents = '';
            $scope.items.spinner = false;

            $scope.book.spinner = true;

            $document.scrollToElement(angular.element(
                document.getElementById('scroll')
            ));

            $http({
                data: jQuery.param({
                    url: url
                }),
                method: 'POST',
                url: $attrs.urlBook
            }).
            error(function (data, status, headers, config) {
                $scope.book.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.book.spinner = false;
                if (typeof(data) === 'object') {
                    $scope.book.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        $scope.get_items = function () {
            $scope.items.contents = '';
            $scope.items.spinner = false;

            $scope.items.spinner = true;

            $http({
                data: jQuery.param({
                    keywords: $scope.keywords,
                    url: $scope.book.contents.url
                }),
                method: 'POST',
                url: $attrs.urlItems
            }).
            error(function (data, status, headers, config) {
                $scope.items.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.items.spinner = false;
                if (typeof(data) === 'object') {
                    $scope.items.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        if ($attrs.url.length) {
            $scope.get_book($attrs.url);
        }
    }
]);

application.controller('category', [
    '$scope',
    function ($scope) {
        $scope.status = false;
    }
]);

application.controller('download', [
    '$element',
    '$scope',
    function ($element, $scope) {
        $scope.action = '';
        $scope.json = '';

        $scope.$on('download', function (event, options) {
            jQuery($element).attr('action', options.action);
            jQuery($element).find('[name="json"]').val(options.json);
            jQuery($element).submit();
        });
    }
]);

application.controller('keyword_analyzer_multiple_add', [
    '$attrs',
    '$rootScope',
    '$scope',
    function ($attrs, $rootScope, $scope) {
        $scope.count = 500;
        $scope.focus = {
            keywords: true
        };
        $scope.keywords = '';

        $scope.submit = function ($event) {
            if ($scope.count >= 500) {
                $rootScope.$broadcast('open', {
                    top: $attrs.errorTop1,
                    middle: $attrs.errorMiddle1
                });
                $event.preventDefault();
            }
            if ($scope.count < 0) {
                $rootScope.$broadcast('open', {
                    top: $attrs.errorTop2,
                    middle: $attrs.errorMiddle2
                });
                $event.preventDefault();
            }
        };

        $scope.get_class = function () {
            console.log($scope.count);
            if ($scope.count < 1) {
                return 'text-danger';
            }
            return 'text-info';
        };

        $scope.$watch('keywords', function (new_value, old_value) {
            if (typeof(new_value) == 'undefined') {
                $scope.count = 500;
                return;
            }
            new_value = $.trim(new_value);
            if (new_value == '') {
                $scope.count = 500;
                return;
            }
            $scope.count = 500 - new_value.split(/\r|\n|\r\n/g).length;
        }, true);

        $scope.$on('focus', function () {
            $scope.focus['keywords'] = true;
        });
    }
]);

application.controller('keyword_analyzer_multiple_simple', [
    '$attrs',
    '$filter',
    '$http',
    '$rootScope',
    '$scope',
    '$timeout',
    function ($attrs, $filter, $http, $rootScope, $scope, $timeout) {
        $scope.books = [
            'Any',
            'More Than',
            'Less Than',
        ];
        $scope.amazon_best_sellers_ranks = [
            'Any',
            'More Than',
            'Less Than',
        ];
        $scope.counts = _.range(48, 0, -12);

        $scope.books_1 = $scope.books[0];
        $scope.books_2 = 0;
        $scope.amazon_best_sellers_rank_1
            = $scope.amazon_best_sellers_ranks[0];
        $scope.amazon_best_sellers_rank_2 = 0;
        $scope.count = $scope.counts[0];

        $scope.keywords = [];
        $scope.order_by = [];
        $scope.order_by_ = ['title[0]', 0];
        $scope.user_email = $attrs.userEmail;

        $scope.statuses = {};

        $scope.email = function (email) {
            jQuery(
                '[data-original-title="Simple Report + Detailed Report"]'
            ).popover('hide');
            $http({
                data: jQuery.param({
                    email: email,
                    logo: ''
                }),
                method: 'POST',
                url: $attrs.urlEmail
            }).
            error(function (data, status, headers, config) {
                $scope.email(email);
            }).
            success(function (data, status, headers, config) {
            });
            $rootScope.$broadcast('open', {
                top: $attrs.emailTop,
                middle: $attrs.emailMiddle
            });
        };

        $scope.process = function () {
            $http({
                method: 'POST',
                url: $attrs.urlXhr
            }).
            error(function (data, status, headers, config) {
                $timeout($scope.process, 15000);
            }).
            success(function (data, status, headers, config) {
                $scope.keywords = data;
                var status = (
                    $scope.keywords.length
                    &&
                    _.filter($scope.keywords, function (model) {
                        return model['others'] == null;
                    }).length == 0
                )? true: false;
                if (!status) {
                    $timeout($scope.process, 15000);
                }
            });

            return;
        };

        $scope.get_keywords = function () {
            var keywords = $scope.keywords;
            keywords = $filter('filter')(keywords, function (keyword) {
                if (keyword.contents == null) {
                    return true;
                }
                var count = 0;
                var books = keyword.contents.items.slice(
                    0, $scope.count
                ).filter(
                    function (book) {
                        var status = false;
                        switch ($scope.amazon_best_sellers_rank_1) {
                            case 'More Than':
                                if (
                                    book.best_sellers_rank[0]
                                    >
                                    $scope.amazon_best_sellers_rank_2
                                ) {
                                    status = true;
                                }
                                break;
                            case 'Less Than':
                                if (
                                    book.best_sellers_rank[0]
                                    <
                                    $scope.amazon_best_sellers_rank_2
                                ) {
                                    status = true;
                                }
                                break;
                            default:
                                status = true;
                                break;
                        }
                        return status;
                    }
                );
                var status = false;
                switch ($scope.books_1) {
                    case 'More Than':
                        if (books.length > $scope.books_2) {
                            status = true;
                        }
                        break;
                    case 'Less Than':
                        if (books.length < $scope.books_2) {
                            status = true;
                        }
                        break;
                    default:
                        status = true;
                        break;
                }

                return status;
            });
            if ($scope.order_by.length) {
                keywords = $filter('orderBy')(
                    keywords, $scope.order_by[0], $scope.order_by[1]
                );
            }
            return keywords;
        };

        $scope.get_order_by = function () {
            return $scope.order_by[1]?
                'fa-sort-amount-desc': 'fa-sort-amount-asc';
        };

        $scope.set_order_by = function (th) {
            if ($scope.order_by[0] == th) {
                $scope.order_by[1] = !$scope.order_by[1];
            } else {
                $scope.order_by[0] = th;
                $scope.order_by[1] = false;
            }
            $scope.keywords = $filter('orderBy')(
                $scope.keywords, $scope.order_by[0], $scope.order_by[1]
            );
        };

        $scope.get_order_by_ = function () {
            return $scope.order_by_[1]?
                'fa-sort-amount-desc': 'fa-sort-amount-asc';
        };

        $scope.set_order_by_ = function (th) {
            if ($scope.order_by_[0] == th) {
                $scope.order_by_[1] = !$scope.order_by_[1];
            } else {
                $scope.order_by_[0] = th;
                $scope.order_by_[1] = false;
            }
        };

        $scope.get_words = function () {
            var words = [];
            jQuery.each($scope.keywords, function (key, value) {
                if (typeof(value.contents.words) !== 'undefined') {
                    jQuery.each(value.contents.words, function (k, v) {
                        words.push(v);
                    });
                }
            });
            words = _.sortBy(_.uniq(words), function (word) {
                return word[1]
            }).reverse().slice(0, 10);
            return words;
        };

        $scope.is_finished = function () {
            var status = true;
            for (var index in $scope.keywords) {
                if (index == 'get_chunks') {
                    continue;
                }
                if ($scope.keywords[index].contents == null) {
                    status = false;
                }
            }
            return status;
        };

        jQuery(document).on('click', '.popover-pdf', function () {
            jQuery(
                '[data-original-title="Detailed Report - Brandable"]'
            ).popover('hide');
            $rootScope.$broadcast('open', {
                top: $attrs.pdfTop,
                middle: $attrs.pdfMiddle
            });
            window.location.href = jQuery(this).attr('data-url');
        });

        jQuery(document).on('click', '.popover-email', function () {
            $scope.email(jQuery(this).prev().val());
        });

        $scope.process();
    }
]);

application.controller('keyword_analyzer_single', [
    '$attrs',
    '$http',
    '$rootScope',
    '$scope',
    function ($attrs, $http, $rootScope, $scope) {
        $scope.countries = jQuery.parseJSON($attrs.countries);

        $scope.keyword = '';
        $scope.country = $scope.countries[0][0];

        $scope.contents = '';
        $scope.order_by = [];

        $scope.spinner = false;

        $scope.process = function () {
            $scope.contents = '';
            $scope.spinner = false;

            if (!$scope.keyword.length) {
                $rootScope.$broadcast('open', {
                    top: $attrs.error1Top,
                    middle: $attrs.error1Middle
                });

                return;
            }

            $scope.spinner = true;

            $http({
                data: jQuery.param({
                    country: $scope.country,
                    keyword: $scope.keyword
                }),
                method: 'POST',
                url: $attrs.url
            }).
            error(function (data, status, headers, config) {
                $scope.spinner = false;
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });
            }).
            success(function (data, status, headers, config) {
                $scope.spinner = false;
                if (typeof(data) == 'object') {
                    $scope.contents = data;
                } else {
                    $rootScope.$broadcast('open', {
                        top: $attrs.error2Top,
                        middle: $attrs.error2Middle
                    });
                }
            });
        };

        $scope.get_order_by = function () {
            return $scope.order_by[1]?
                'fa-sort-amount-desc': 'fa-sort-amount-asc';
        };

        $scope.set_order_by = function (th) {
            if ($scope.order_by[0] == th) {
                $scope.order_by[1] = !$scope.order_by[1];
            } else {
                $scope.order_by[0] = th;
                $scope.order_by[1] = false;
            }
        };
    }
]);

application.controller('keyword_suggester', [
    '$attrs',
    '$http',
    '$queue',
    '$rootScope',
    '$scope',
    function ($attrs, $http, $queue, $rootScope, $scope) {
        $scope.download = function () {
            $rootScope.$broadcast('download', {
                action: $attrs.urlDownload,
                json: JSON.stringify({
                    suggestions: $scope.suggestions
                })
            });
        };

        $scope.reset = function () {
            $scope.modes = [
                'Suggest',
                'Combine',
            ];

            $scope.keywords = '';
            $scope.country = 'com';
            $scope.mode = $scope.modes[0];
            $scope.search_alias = 'digital-text';

            $scope.checkbox = false;
            $scope.focus = {
                keywords: true,
                suggestions: false
            };

            $scope.spinner = false;
            $scope.rows = '';
            $scope.statuses = {};
            $scope.suggestions = [];

            window.clearInterval($scope.interval);
        };

        $scope.submit = function () {
            $scope.suggestions = [];
            if (!$scope.keywords.length) {
                $rootScope.$broadcast('open', {
                    top: $attrs.error1Top,
                    middle: $attrs.error1Middle
                });

                return;
            }

            $scope.spinner = true;
            var queue = $queue.queue(function (keyword) {
                $http({
                    data: jQuery.param({
                        country: $scope.country,
                        keyword: keyword,
                        search_alias: $scope.search_alias
                    }),
                    method: 'POST',
                    url: $attrs.urlXhr
                }).
                error(function (data, status, headers, config) {
                    $scope.statuses[keyword] = -1;
                }).
                success(function (data, status, headers, config) {
                    jQuery.each(data, function (key, value) {
                        if ($scope.mode == 'Suggest') {
                            $scope.suggestions.push(value);
                        }
                        if ($scope.mode == 'Combine') {
                            var count = 0;
                            jQuery.each(value.split(' '), function (k, v) {
                                jQuery.each(
                                    $scope.keywords.toLowerCase().split('\n'),
                                    function () {
                                        if (this == v) {
                                            count += 1;
                                        }
                                    }
                                );
                            });
                            if (count >= 2) {
                                $scope.suggestions.push(value);
                            }
                        }
                    });
                    $scope.suggestions = _.uniq($scope.suggestions);
                    $scope.suggestions.sort();
                    $scope.statuses[keyword] = 1;
                });
            }, {
                complete: function () {},
                delay: 0,
                paused: true
            });
            $scope.rows = _.uniq(_.filter(
                $scope.keywords.toLowerCase().split('\n'), function (keyword) {
                    return jQuery.trim(keyword).length;
                }
            ));
            $scope.statuses = {};
            jQuery.each($scope.rows, function (key, value) {
                queue.add(value);
                $scope.statuses[value] = 0;
            });
            queue.start();
            $scope.interval = window.setInterval(function () {
                if (_.values($scope.statuses).indexOf(0) === -1) {
                    window.clearInterval($scope.interval);
                    if ($scope.suggestions.length) {
                        $scope.focus['suggestions'] = true;
                        if ($scope.checkbox) {
                            $scope.download();
                        }
                        return;
                    }
                    $rootScope.$broadcast('open', {
                        top: $attrs.error3Top,
                        middle: $attrs.error3Middle
                    });
                }
            }, 1000);
        };

        $scope.$on('focus', function () {
            $scope.focus['keywords'] = true;
            $scope.focus['suggestions'] = false;
        });

        $scope.reset();

        if ($attrs.keywords.length) {
            $scope.keywords = $attrs.keywords;
        }
        if ($attrs.mode.length) {
            $scope.mode = $attrs.mode;
        }
    }
]);

application.controller('modal', [
    '$attrs',
    '$element',
    '$rootScope',
    '$scope',
    function ($attrs, $element, $rootScope, $scope) {
        $scope.top = '';
        $scope.middle = '';

        $scope.click = function () {
            jQuery($element).modal('hide');
            $scope.top = '';
            $scope.middle = '';
            $rootScope.$broadcast('focus');
            $rootScope.$emit('focus');

            return false;
        };

        $scope.$on('open', function (event, options) {
            $scope.top = options.top;
            $scope.middle = options.middle;
            $rootScope.$$phase || $rootScope.$apply();
            jQuery($element).modal('show');
        });
    }
]);

application.controller('previous_versions', [
    '$scope',
    function ($scope) {
        $scope.status = false;
    }
]);

application.controller('suggested_keywords', [
    '$attrs',
    '$http',
    '$scope',
    function ($attrs, $http, $scope) {
        $scope.items = [];
        $scope.spinner = false;
        $scope.error = false;

        $scope.process = function (words) {
            $scope.items = [];
            $scope.spinner = true;
            $scope.error = false;
            $http({
                data: jQuery.param({
                    keywords: _.map(words, function (word) {
                        return word[0];
                    }).join(',')
                }),
                method: 'POST',
                url: $attrs.urlsSuggestedKeywords
            }).
            error(function (data, status, headers, config) {
                $scope.items = [];
                $scope.spinner = false;
                $scope.error = true;
            }).
            success(function (data, status, headers, config) {
                $scope.items = data;
                $scope.spinner = false;
                $scope.error = false;
            });

            return;
        };

        $scope.get_more_suggestions = function (keywords, mode) {
            jQuery('<form/>', {
                action: $attrs.urlsKeywordSuggester,
                target: '_blank',
                method: 'POST'
            }).append(
                jQuery('<input/>', {
                    'name': 'keywords',
                    'type': 'hidden',
                    'val': keywords.join('\n')
                })
            ).append(
                jQuery('<input/>', {
                    'name': 'mode',
                    'type': 'hidden',
                    'val': mode
                })
            ).submit();
        };

        $scope.get_words = function (words) {
            return _.map(words, function (word) {
                return word[0];
            });
        };
    }
]);

application.controller('top_100_explorer', [
    '$attrs',
    '$http',
    '$rootScope',
    '$scope',
    function ($attrs, $http, $rootScope, $scope) {
        $scope.categories = jQuery.parseJSON($attrs.categories);
        $scope.sections = jQuery.parseJSON($attrs.sections);
        $scope.print_lengths = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.prices = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.publication_dates = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.amazon_best_sellers_ranks = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.review_averages = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.appearances = [
            'Any',
            'More Than',
            'Less Than',
            'Between',
        ];
        $scope.counts = _.range(100, 0, -10);

        $scope.spinner = false;
        $scope.error = false;
        $scope.contents = {};

        $scope.order_by = {
            'books': ['rank', false],
            'categories': ['frequency', true],
        };

        $scope.mode = 'table';

        $scope.process = function (category_id) {
            var fields = [];
            jQuery.each({
                amazon_best_sellers_rank_1: $scope.amazon_best_sellers_rank_1,
                amazon_best_sellers_rank_2: $scope.amazon_best_sellers_rank_2,
                amazon_best_sellers_rank_3: $scope.amazon_best_sellers_rank_3,
                amazon_best_sellers_rank_4: $scope.amazon_best_sellers_rank_4,
                category_id: category_id,
                count: $scope.count,
                print_length_1: $scope.print_length_1,
                print_length_2: $scope.print_length_2,
                print_length_3: $scope.print_length_3,
                print_length_4: $scope.print_length_4,
                appearance_1: $scope.appearance_1,
                appearance_2: $scope.appearance_2,
                appearance_3: $scope.appearance_3,
                appearance_4: $scope.appearance_4,
                price_1: $scope.price_1,
                price_2: $scope.price_2,
                price_3: $scope.price_3,
                price_4: $scope.price_4,
                publication_date_1: $scope.publication_date_1,
                publication_date_2: $scope.publication_date_2,
                publication_date_3: $scope.publication_date_3,
                publication_date_4: $scope.publication_date_4,
                review_average_1: $scope.review_average_1,
                review_average_2: $scope.review_average_2,
                review_average_3: $scope.review_average_3,
                review_average_4: $scope.review_average_4,
                section_id: $scope.section_id
            }, function (name, val) {
                fields.push(jQuery('<input/>', {
                    'name': name,
                    'type': 'hidden',
                    'val': val
                }))
            });
            jQuery('<form/>', {
                target: '_blank',
                method: 'POST'
            }).append(fields).submit();
        };

        $scope.reset = function () {
            $scope.category_id = $attrs.categoryId || $scope.categories[1][0];
            $scope.section_id = $attrs.sectionId || $scope.sections[0][0];
            $scope.print_length_1
                = $attrs.printLength1 || $scope.print_lengths[0];
            $scope.print_length_2 = parseInt($attrs.printLength2, 10) || 0;
            $scope.print_length_3 = parseInt($attrs.printLength3, 10) || 0;
            $scope.print_length_4 = parseInt($attrs.printLength4, 10) || 0;
            $scope.price_1 = $attrs.price1 || $scope.prices[0];
            $scope.price_2 = parseInt($attrs.price2, 10) || 0;
            $scope.price_3 = parseInt($attrs.price3, 10) || 0;
            $scope.price_4 = parseInt($attrs.price4, 10) || 0;
            $scope.publication_date_1
                = $attrs.publicationDate1 || $scope.publication_dates[0];
            $scope.publication_date_2 = $attrs.publicationDate2 || '';
            $scope.publication_date_3 = $attrs.publicationDate3 || '';
            $scope.publication_date_4 = $attrs.publicationDate4 || '';
            $scope.amazon_best_sellers_rank_1 =
                $attrs.amazonBestSellersRank1
                ||
                $scope.amazon_best_sellers_ranks[0];
            $scope.amazon_best_sellers_rank_2
                = parseInt($attrs.amazonBestSellersRank2, 10) || 0;
            $scope.amazon_best_sellers_rank_3
                = parseInt($attrs.amazonBestSellersRank3, 10) || 0;
            $scope.amazon_best_sellers_rank_4
                = parseInt($attrs.amazonBestSellersRank4, 10) || 0;
            $scope.review_average_1
                = $attrs.reviewAverage1 || $scope.review_averages[0];
            $scope.review_average_2 = parseInt($attrs.reviewAverage2, 10) || 0;
            $scope.review_average_3 = parseInt($attrs.reviewAverage3, 10) || 0;
            $scope.review_average_4 = parseInt($attrs.reviewAverage4, 10) || 0;
            $scope.appearance_1 = $attrs.appearance1 || $scope.appearances[0];
            $scope.appearance_2 = parseInt($attrs.appearance2, 10) || 1;
            $scope.appearance_3 = parseInt($attrs.appearance3, 10) || 1;
            $scope.appearance_4 = parseInt($attrs.appearance4, 10) || 1;
            $scope.count = parseInt($attrs.count, 10) || $scope.counts[0];

            jQuery('#category_id').select2('val', $scope.category_id);
            jQuery('#section_id').select2('val', $scope.section_id);
            jQuery('#print_length').select2('val', $scope.print_length_1);
            jQuery('#price').select2('val', $scope.price_1);
            jQuery(
                '#publication_date'
            ).select2('val', $scope.publication_date_1);
            jQuery(
                '#amazon_best_sellers_rank'
            ).select2('val', $scope.amazon_best_sellers_rank_1);
            jQuery('#review_average').select2('val', $scope.review_average_1);
            jQuery('#appearance').select2('val', $scope.appearance_1);
            jQuery('#count').select2('val', $scope.count);

            $scope.submit();
        };

        $scope.submit = function () {
            $scope.spinner = true;
            $scope.error = false;
            $scope.contents = {};
            $http({
                data: jQuery.param({
                    amazon_best_sellers_rank_1:
                    $scope.amazon_best_sellers_rank_1,
                    amazon_best_sellers_rank_2:
                    $scope.amazon_best_sellers_rank_2,
                    amazon_best_sellers_rank_3:
                    $scope.amazon_best_sellers_rank_3,
                    amazon_best_sellers_rank_4:
                    $scope.amazon_best_sellers_rank_4,
                    category_id: $scope.category_id,
                    count: $scope.count,
                    print_length_1: $scope.print_length_1,
                    print_length_2: $scope.print_length_2,
                    print_length_3: $scope.print_length_3,
                    print_length_4: $scope.print_length_4,
                    appearance_1: $scope.appearance_1,
                    appearance_2: $scope.appearance_2,
                    appearance_3: $scope.appearance_3,
                    appearance_4: $scope.appearance_4,
                    price_1: $scope.price_1,
                    price_2: $scope.price_2,
                    price_3: $scope.price_3,
                    price_4: $scope.price_4,
                    publication_date_1: $scope.publication_date_1,
                    publication_date_2: $scope.publication_date_2,
                    publication_date_3: $scope.publication_date_3,
                    publication_date_4: $scope.publication_date_4,
                    review_average_1: $scope.review_average_1,
                    review_average_2: $scope.review_average_2,
                    review_average_3: $scope.review_average_3,
                    review_average_4: $scope.review_average_4,
                    section_id: $scope.section_id
                }),
                method: 'POST',
                url: $attrs.url
            }).
            error(function (data, status, headers, config) {
                $scope.spinner = false;
                $scope.error = true;
            }).
            success(function (data, status, headers, config) {
                $scope.spinner = false;
                $scope.error = !data.books.length;
                $scope.contents = data;
                $scope.contents[
                    'chunks'
                ] = $scope.contents['books'].get_chunks(3);
                for (var index in $scope.contents['categories']) {
                    $scope.contents['categories'][index]['id'] = 0;
                    if (
                        $scope.contents['categories'][index]['title']
                        ==
                        'Paid in Kindle Store'
                    ) {
                        $scope.contents['categories'][index]['id'] = 1;
                    } else {
                        for (var i in $scope.categories) {
                            if (
                                $scope.contents['categories'][index]['title']
                                ==
                                $scope.categories[i][1]
                            ) {
                                $scope.contents[
                                    'categories'
                                ][index]['id'] = $scope.categories[i][0];
                                break;
                            }
                        }
                    }
                }
            });

            return;
        };

        $scope.get_order_by = function (key) {
            return $scope.order_by[key][1]?
                'fa-sort-amount-desc': 'fa-sort-amount-asc';
        };

        $scope.set_order_by = function (key, value) {
            if ($scope.order_by[key][0] == value) {
                $scope.order_by[key][1] = !$scope.order_by[key][1];
            } else {
                $scope.order_by[key][0] = value;
                $scope.order_by[key][1] = false;
            }
        };

        $scope.reset();
    }
]);

jQuery.ajaxSetup({
    cache: false,
    timeout: 600000
});

var zclip = function () {
    var refresh = function () {
        if (element.is(':hidden')) {
            if (!element.data('zclip')) {
                return;
            }
            element.zclip('remove');
            element.data('zclip', false);
        } else {
            if (element.data('zclip')) {
                return;
            }
            element.zclip({
                afterCopy: function () {},
                beforeCopy: function () {},
                copy: function () {
                    return element.attr('data-value');
                },
                path: (
                    jQuery('body').attr('data-url')
                    +
                    '/vendor/jquery-zclip/ZeroClipboard.swf'
                )
            });
            element.data('zclip', true);
        }
    };

    var element = jQuery('.copy-all');

    setInterval(refresh, 500);
};

jQuery(function () {
    jQuery('body').tooltip({
        container: jQuery('body'),
        selector: '[data-toggle="tooltip"]'
    });
    jQuery('select.select2').select2({
        placeholder: 'Select an option...'
    });
    jQuery('.got-it').click(function () {
        jQuery.cookie(jQuery(this).parents('.modal').attr('id'), 'Yes');
    });
    jQuery('.well').height(
        Math.max.apply(
            null,
            jQuery('.well').map(function () {
                return jQuery(this).height();
            }).get()
        )
    );
    if (jQuery.cookie('keyword_analyzer_multiple') != 'Yes') {
        jQuery('[data-target="#modal-keyword-analyzer-multiple"]').click();
    }
    if (jQuery.cookie('keyword_suggester') != 'Yes') {
        jQuery('[data-target="#modal-keyword-suggester"]').click();
    }
    zclip();
    window.PixelAdmin.start([]);
});
