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

var is_development = function(){
    if(window.location.port == '5000'){
        return true;
    }

    return false;
};

var application = angular.module('application', []);

application.config(function ($httpProvider, $interpolateProvider) {
    $httpProvider.defaults.headers.post[
        'Content-Type'
    ] = 'application/x-www-form-urlencoded';
    $interpolateProvider.startSymbol('[!').endSymbol('!]');
});

application.directive('datepicker', function () {
    return {
        link: function (scope, element, attrs) {
            jQuery(element).datepicker({
                format: 'yyyy-mm-dd'
            }).on('changeDate', function (event) {
                angular.element(element).scope().publication_date_2 = moment(
                    new Date(event.date)
                ).format('YYYY-MM-DD');
                jQuery(element).datepicker('hide');
            });
        },
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
                placement: 'top'
            });
        },
        restrict: 'A'
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
                        '<span class="label label-important">'
                        +
                        two
                        +
                        '</span>'
                    );
                case 'Very Low':
                    return (
                        '<span class="label label-important">'
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
                        '<span class="label label-important">'
                        +
                        two
                        +
                        '</span>'
                    );
                case 'High':
                    return (
                        '<span class="label label-important">'
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

application.controller('aa', function ($attrs, $http, $rootScope, $scope) {
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
});

application.controller('ba', function ($attrs, $http, $rootScope, $scope) {
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

        $scope.book.spinner = true;

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
                url: $scope.book.url
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
});

application.controller('aks', function ($attrs, $http, $rootScope, $scope) {
    $scope.checkbox = false;
    $scope.country = 'com';
    $scope.keyword = '';
    $scope.focus = {
        keyword: true,
        suggestions: false
    };
    $scope.level = '1';
    $scope.mode = '1';
    $scope.search_alias = 'digital-text';
    $scope.spinner = false;
    $scope.suggestions = [];

    $scope.download = function () {
        $rootScope.$broadcast('download', {
            action: $attrs.urlDownload,
            json: JSON.stringify({
                keyword: $scope.keyword,
                suggestions: $scope.suggestions
            })
        });
    };

    $scope.process = function () {
        $scope.suggestions = [];
        if (!$scope.keyword.length) {
            $rootScope.$broadcast('open', {
                top: $attrs.error1Top,
                middle: $attrs.error1Middle
            });

            return;
        }
        if ($scope.level == 2) {
            if ($scope.keyword.indexOf(' ') !== -1) {
                $rootScope.$broadcast('open', {
                    top: $attrs.error2Top,
                    middle: $attrs.error2Middle
                });

                return;
            }
        }
        $scope.spinner = true;
        $http({
            data: jQuery.param({
                country: $scope.country,
                keyword: $scope.keyword,
                level: $scope.level,
                mode: $scope.mode,
                search_alias: $scope.search_alias
            }),
            method: 'POST',
            url: $attrs.urlXhr
        }).
        error(function (data, status, headers, config) {
            $scope.spinner = false;
            $rootScope.$broadcast('open', {
                top: $attrs.error3Top,
                middle: $attrs.error3Middle
            });
        }).
        success(function (data, status, headers, config) {
            $scope.spinner = false;
            if (data.length > 0) {
                $scope.suggestions = data;
                $scope.focus['suggestions'] = true;
                if ($scope.checkbox) {
                    $scope.download();
                }
            } else {
                $rootScope.$broadcast('open', {
                    top: $attrs.error3Top,
                    middle: $attrs.error3Middle
                });
            }
        });
    };

    $scope.$on('focus', function () {
        $scope.focus['keyword'] = true;
        $scope.focus['suggestions'] = false;
    });

    if (is_development()) {
        $scope.keyword = '1';
        $scope.process();
    }
});

application.controller('amazon_best_sellers_rank', function ($scope) {
    $scope.status = false;
});

application.controller('book', function ($scope) {
    $scope.status = false;
});

application.controller('category', function ($scope) {
    $scope.status = false;
});

application.controller('ce', function ($attrs, $http, $rootScope, $scope) {
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
    ];
    $scope.publication_dates = [
        'Any',
        'More Than',
        'Less Than',
    ];
    $scope.amazon_best_sellers_ranks = [
        'Any',
        'More Than',
        'Less Than',
    ];
    $scope.review_averages = [
        'Any',
        'More Than',
        'Less Than',
    ];
    $scope.appearances = [
        'Any',
        'More Than',
        'Less Than',
    ];
    $scope.counts = _.range(100, 0, -10);

    $scope.category = get_parameter('category_id') || $scope.categories[1][0];
    $scope.section = $scope.sections[0][0];
    $scope.print_length_1 = $scope.print_lengths[0];
    $scope.print_length_2 = 0;
    $scope.print_length_3 = 0;
    $scope.print_length_4 = 0;
    $scope.price_1 = $scope.prices[0];
    $scope.price_2 = 0;
    $scope.publication_date_1 = $scope.publication_dates[0];
    $scope.publication_date_2 = '';
    $scope.amazon_best_sellers_rank_1 = $scope.amazon_best_sellers_ranks[0];
    $scope.amazon_best_sellers_rank_2 = 0;
    $scope.review_average_1 = $scope.review_averages[0];
    $scope.review_average_2 = 0;
    $scope.appearance_1 = $scope.appearances[0];
    $scope.appearance_2 = 0;
    $scope.count = $scope.counts[0];

    $scope.spinner = false;
    $scope.error = false;
    $scope.contents = {};

    $scope.order_by = {
        'books': ['rank', false],
        'categories': ['frequency', true],
    };

    $scope.mode = 'table';

    $scope.process = function () {
        $scope.spinner = true;
        $scope.error = false;
        $scope.contents = {};
        $http({
            data: jQuery.param({
                amazon_best_sellers_rank_1: $scope.amazon_best_sellers_rank_1,
                amazon_best_sellers_rank_2: $scope.amazon_best_sellers_rank_2,
                category_id: $scope.category,
                count: $scope.count,
                print_length_1: $scope.print_length_1,
                print_length_2: $scope.print_length_2,
                print_length_3: $scope.print_length_3,
                print_length_4: $scope.print_length_4,
                appearance_1: $scope.appearance_1,
                appearance_2: $scope.appearance_2,
                price_1: $scope.price_1,
                price_2: $scope.price_2,
                publication_date_1: $scope.publication_date_1,
                publication_date_2: $scope.publication_date_2,
                review_average_1: $scope.review_average_1,
                review_average_2: $scope.review_average_2,
                section_id: $scope.section
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
            $scope.contents['chunks'] = $scope.contents['books'].get_chunks(3);
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
        return $scope.order_by[key][1]? 'desc': 'asc';
    };

    $scope.set_order_by = function (key, value) {
        if ($scope.order_by[key][0] == value) {
            $scope.order_by[key][1] = !$scope.order_by[key][1];
        } else {
            $scope.order_by[key][0] = value;
            $scope.order_by[key][1] = false;
        }
    };

    $scope.process();
});

application.controller('download', function ($element, $scope) {
    $scope.action = '';
    $scope.json = '';

    $scope.$on('download', function (event, options) {
        jQuery($element).attr('action', options.action);
        jQuery($element).find('[name="json"]').val(options.json);
        jQuery($element).submit();
    });
});

application.controller('kns_add', [
    '$attrs', '$rootScope', '$scope', function ($attrs, $rootScope, $scope) {
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
            if ($scope.count > 500) {
                return 'text-error';
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

application.controller('kns_simple', [
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
        $scope.amazon_best_sellers_rank_1 = $scope.amazon_best_sellers_ranks[0];
        $scope.amazon_best_sellers_rank_2 = 0;
        $scope.count = $scope.counts[0];

        $scope.keywords = [];
        $scope.order_by = [];
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
            return $scope.order_by[1]? 'desc': 'asc';
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

application.controller('modal', function (
    $attrs, $element, $rootScope, $scope
) {
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
});

application.controller('previous_versions', function ($scope) {
    $scope.status = false;
});

jQuery.ajaxSetup({
    cache: false,
    timeout: 600000
});

var body = function (context) {
    var keywords = jQuery('#keywords');
    if (!keywords.length) {
        return ;
    }

    var body = jQuery('#body');
    if (!body.length) {
        return ;
    }

    var get_bottom = function (context) {
        return parseInt(context.position().top + context.height(), 10);
    }

    one = get_bottom(keywords);
    two = get_bottom(body);
    if (one != two) {
        body.css('height', body.height() - (two - one) + 10);
    }
};

var ui = function () {
    if (is_development()) {
        return;
    }
    jQuery.ajax({
        dataType: 'html',
        error: function (jqXHR, textStatus, errorThrown) {
            ui();
        },
        success: function (data, textStatus, jqXHR) {
            var context = jQuery(data);
            jQuery('#top').append(context.find('.banner'));
            context.find('#content_area').find('#le_body_row_1').remove();
            jQuery('#bottom').append(
                context.find('#content_area').fadeIn('slow')
            );
            jQuery('#bottom').append(context.find('.footer').fadeIn('slow'));
        },
        type: 'GET',
        url: 'http://zonsidekick.com/toolspage/'
    });
};

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
    if (jQuery.cookie('kns-qsg') != 'Yes') {
        jQuery('[data-target="#kns-qsg"]').click();
    }
    if (jQuery.cookie('aks-qsg') != 'Yes') {
        jQuery('[data-target="#aks-qsg"]').click();
    }
    body();
    ui();
    zclip();
});
