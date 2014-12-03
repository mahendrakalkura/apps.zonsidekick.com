<?php

date_default_timezone_set('UTC');

function usort_categories($one, $two)
{
    $one_frequency = intval($one['frequency']);
    $two_frequency = intval($two['frequency']);
    if ($one_frequency != $two_frequency) {
        return ($one_frequency < $two_frequency) ? 1 : -1;
    }

    $one_title = $one['title'];
    $two_title = $two['title'];
    if ($one_title != $two_title) {
        return ($one_title < $two_title) ? -1 : 1;
    }

    return 0;
}

function usort_keywords_1($one, $two)
{
    $one = floatval($one['contents']['score'][0]);
    $two = floatval($two['contents']['score'][0]);
    if ($one == $two) {
        return 0;
    }

    return ($one > $two) ? -1 : 1;
}

function usort_keywords_2($one, $two)
{
    $one_position = intval($one['position']);
    $two_position = intval($two['position']);
    if ($one_position != $two_position) {
        return ($one_position < $two_position) ? -1 : 1;
    }

    $one_score = $one['contents']['score'][0];
    $two_score = $two['contents']['score'][0];
    if ($one_score != $two_score) {
        return ($one_score > $two_score) ? -1 : 1;
    }

    return 0;
}

function usort_logos($one, $two)
{
    $one = strtolower($one['file_name']);
    $two = strtolower($two['file_name']);
    if ($one == $two) {
        return 0;
    }

    return ($one < $two) ? -1 : 1;
}

function usort_popular_searches($one, $two)
{
    $one = array_sum(array_values($one['keywords']));
    $two = array_sum(array_values($two['keywords']));
    if ($one != $two) {
        return ($one > $two) ? -1 : 1;
    }

    return 0;
}

function get_category($application, $category_id) {
    $categories = array();
    while (true) {
        $query = <<<EOD
SELECT `category_id`, `title`
FROM `tools_ce_categories`
WHERE `id` = ?
EOD;
        $record = $application['db']->fetchAssoc($query, array(
            $category_id,
        ));
        $categories[] = $record['title'];
        $category_id = $record['category_id'];
        if (!$category_id) {
            break;
        }
    }

    return implode(' > ', array_reverse($categories));
}

function get_categories($application, $category_id, $prefixes) {
    $categories = array();
    if (count($prefixes) >= 3) {
        return $categories;
    }
    if ($category_id) {
        $query = <<<EOD
SELECT *
FROM `tools_ce_categories`
WHERE `category_id` = ?
ORDER BY `title` ASC
EOD;
    } else {
        $query = <<<EOD
SELECT *
FROM `tools_ce_categories`
WHERE `category_id` IS NULL
ORDER BY `title` ASC
EOD;
    }
    $records = $application['db']->fetchAll($query, array($category_id));
    if ($records) {
        foreach ($records as $record) {
            $categories[] = array(
                $record['id'],
                sprintf(
                    '%s%s',
                    implode(' > ', array_merge($prefixes, array(''))),
                    $record['title']
                ),
            );
            $categories = array_merge($categories, get_categories(
                $application, $record['id'],
                array_merge($prefixes, array($record['title']))
            ));
        }
    }

    return $categories;
}

function get_count_and_keywords($keywords) {
    $count = -1;
    $keywords = explode("\n", $keywords);
    if (!empty($keywords)) {
        foreach ($keywords as $key => $value) {
            $value = trim($value);
            if (!empty($value)) {
                $keywords[$key] = $value;
            } else {
                unset($keywords[$key]);
            }
        }
    }
    $keywords = array_unique($keywords);

    return array($count, $keywords);
}

function get_countries() {
    // do not sort
    return array(
        'com' => 'US',
        'co.uk' => 'UK',
        'es' => 'Spain',
        'fr' => 'France',
        'it' => 'Italy',
        'com.br' => 'Brazil',
        'ca' => 'Canada',
        'de' => 'Germany',
        'co.jp' => 'Japan',
    );
};

function get_contents($application, $user, $logo) {
    $file_path = sprintf(
        '%s/%s', get_path($application, $user, 'logos'), $logo
    );
    if (is_file($file_path)) {
        return sprintf(
            'data:%s;base64,%s',
            mime_content_type($file_path),
            base64_encode(file_get_contents($file_path))
        );
    }

    return '';
}

function get_csv($application, $user, $id) {
    list($request, $keywords) = get_request_and_keywords(
        $application, $user, $id
    );

    $stream = fopen('data://text/plain,', 'w+');
    fputcsv($stream, array(
        'Keyword',
        'Buyer Behavior',
        'Competition',
        'Optimization',
        'Popularity',
        sprintf('Spend (%s)', get_currency($request['country'])),
        sprintf('Avg. Price (%s)', get_currency($request['country'])),
        'Avg. Length',
        'Score',
    ));
    if ($keywords) {
        foreach ($keywords as $keyword) {
            fputcsv($stream, array(
                $keyword['string'],
                $keyword['contents']['buyer_behavior'][1],
                $keyword['contents']['competition'][1],
                $keyword['contents']['optimization'][1],
                $keyword['contents']['popularity'][1],
                $keyword['contents']['spend'][0][1],
                $keyword['contents']['average_price'][1],
                $keyword['contents']['average_length'][1],
                $keyword['contents']['score'][1],
            ));
        }
    }
    rewind($stream);
    $contents = stream_get_contents($stream);
    fclose($stream);

    return $contents;
}

function get_currency($country) {
    if ($country == 'co.jp') {
        return '¥';
    }
    if ($country == 'co.uk') {
        return '£';
    }
    if ($country == 'de') {
        return '€';
    }

    return '$';
}

function get_logos($application, $user) {
    $array = array();
    $path = get_path($application, $user, 'logos');
    $resource = dir($path);
    while (false !== ($file_name = $resource->read())) {
        if ($file_name == '.') {
            continue;
        }
        if ($file_name == '..') {
            continue;
        }
        $getimagesize = getimagesize(sprintf('%s/%s', $path, $file_name));
        $array[] = array(
            'dimensions' => sprintf(
                '%dx%d', $getimagesize[0], $getimagesize[1]
            ),
            'file_name' => $file_name,
        );
    }
    $resource->close();
    usort($array, 'usort_logos');

    return $array;
}

function get_part($subject, $body) {
    return str_replace(
        array('{{ subject }}', '{{ body }}'),
        array($subject, nl2br($body)),
        file_get_contents(sprintf('%s/templates/email.twig', __DIR__))
    );
}

function get_path($application, $user, $directory) {
    $path = sprintf('%s/files/%d/%s', __DIR__, $user['id'], $directory);
    if (!is_dir($path)) {
        mkdir($path, 0755, true);
    }

    return $path;
}

function get_pdf($application, $user, $logo, $id, $variables) {
    list($request, $keywords) = get_request_and_keywords(
        $application, $user, $id
    );
    usort($keywords, 'usort_keywords_1');
    if ($keywords) {
        $keywords = array_slice($keywords, 0, 100);
        foreach ($keywords as $key => $value) {
            if (is_array($keywords[$key]['contents']['items'])) {
                $keywords[$key]['contents']['items'] = array_slice(
                    $keywords[$key]['contents']['items'], 0, 25
                );
            }
        }
    }
    if (is_development()) {
        $contents = 'PDF';
    } else {
        $file_path = tempnam(sprintf('%s/tmp', __DIR__), 'weasyprint-');
        file_put_contents(
            $file_path,
            $application['twig']->render(
                'views/keyword_analyzer_multiple_detailed.twig',
                array(
                    'currency' => get_currency($request['country']),
                    'is_pdf' => false,
                    'keywords' => $keywords,
                    'logo' => get_contents($application, $user, $logo),
                )
            )
        );
        $contents = shell_exec(sprintf(
            '%s/weasyprint --format pdf %s - 2>/dev/null',
            $variables['virtualenv'],
            escapeshellarg($file_path)
        ));
        unlink($file_path);
    }

    return $contents;
}

function get_popular_searches($application) {
    $query = <<<EOD
SELECT *
FROM `tools_ps_books`
INNER JOIN
    `tools_ps_trends` ON `tools_ps_books`.`id` = `tools_ps_trends`.`book_id`
WHERE `tools_ps_trends`.`date_and_time` IN (
    SELECT MAX(`date_and_time`)
    FROM `tools_ps_trends`
)
ORDER BY `tools_ps_books`.`title` ASC
EOD;
    $popular_searches = $application['db']->fetchAll($query);
    foreach ($popular_searches as $key => $value) {
        $popular_searches[$key]['amazon_best_sellers_rank'] = json_decode(
            $popular_searches[$key]['amazon_best_sellers_rank'], true
        );
        asort(
            $popular_searches[$key]['amazon_best_sellers_rank'], SORT_NUMERIC
        );
        $popular_searches[$key]['keywords'] = json_decode(
            $popular_searches[$key]['keywords'], true
        );
        arsort($popular_searches[$key]['keywords'], SORT_NUMERIC);
        $query = <<<EOD
SELECT COUNT(DISTINCT DATE(`date_and_time`)) AS `count`
FROM `tools_ps_trends`
WHERE `book_id` = ? AND `date_and_time` >= NOW() - INTERVAL 7 DAY
EOD;
        $record_1 = $application['db']->fetchAssoc($query, array(
            $popular_searches[$key]['book_id'],
        ));
        $query = <<<EOD
SELECT COUNT(DISTINCT DATE(`date_and_time`)) AS `count`
FROM `tools_ps_trends`
WHERE `book_id` = ? AND `date_and_time` >= NOW() - INTERVAL 30 DAY
EOD;
        $record_2 = $application['db']->fetchAssoc($query, array(
            $popular_searches[$key]['book_id'],
        ));
        $popular_searches[$key]['appearances'] = array(
            'last 7 days' => $record_1['count'],
            'last 30 days' => $record_2['count'],
        );
        $popular_searches[$key]['url_'] = urlencode(
            $popular_searches[$key]['url']
        );
    }

    usort($popular_searches, 'usort_popular_searches');

    return $popular_searches;
}

function get_requests($application, $user) {
    $query = <<<EOD
SELECT *
FROM `tools_kns_requests`
WHERE `user_id` = ?
ORDER BY `timestamp` DESC
EOD;
    $requests = $application['db']->fetchAll($query, array($user['id']));
    if ($requests) {
        $query_preview = <<<EOD
SELECT `string`
FROM `tools_kns_keywords`
WHERE `request_id` = ?
ORDER BY `id` ASC
LIMIT 5
OFFSET 0
EOD;
        $query_keywords_1 = <<<EOD
SELECT COUNT(`id`) AS `count`
FROM `tools_kns_keywords`
WHERE `request_id` = ?
EOD;
        $query_keywords_2 = <<<EOD
SELECT COUNT(`tools_kns_keywords`.`id`) AS `count`
FROM `tools_kns_keywords`
LEFT JOIN `tools_kns_requests` ON (
    `tools_kns_requests`.`id` = `tools_kns_keywords`.`request_id`
)
WHERE (
    `tools_kns_keywords`.`request_id` = ?
    AND
    `tools_kns_keywords`.`contents` IS NULL
    AND
    `tools_kns_requests`.`timestamp` < (NOW() - INTERVAL 5 HOUR)
)
EOD;
        $query_total = <<<EOD
SELECT COUNT(`id`) AS `count`
FROM `tools_kns_keywords`
WHERE `request_id` = ?
EOD;
        $query_completed = <<<EOD
SELECT COUNT(`id`) AS `count`
FROM `tools_kns_keywords`
WHERE `request_id` = ? AND `contents` IS NOT NULL
EOD;
        foreach ($requests as $key => $value) {
            $requests[$key]['preview'] = array();
            $records = $application['db']->fetchAll(
                $query_preview, array($value['id'])
            );
            if ($records) {
                foreach ($records as $record) {
                    $requests[$key]['preview'][] = get_truncated_text(
                        $record['string'], 10
                    );
                }
            }
            $requests[$key]['preview'] = implode(
                ', ', $requests[$key]['preview']
            );
            $record_1 = $application['db']->fetchAssoc(
                $query_keywords_1, array($value['id'])
            );
            $record_2 = $application['db']->fetchAssoc(
                $query_keywords_2, array($value['id'])
            );
            $requests[$key]['keywords'] = array(
                $record_1['count'],
                number_format($record_1['count'], 0, '.', ','),
                $record_2['count'],
                number_format($record_2['count'], 0, '.', ','),
            );
            $old = new DateTime(date('Y-m-d H:i:s'));
            $new = new DateTime($requests[$key]['timestamp']);
            $new->add(new DateInterval('P30D'));
            $interval = $old->diff($new);
            $requests[$key]['expires_in'] = $interval->format('%R%a days');
            $total = $application['db']->fetchAssoc(
                $query_total, array($value['id'])
            );
            $completed = $application['db']->fetchAssoc(
                $query_completed, array($value['id'])
            );
            $requests[$key]['progress'] = (
                $completed['count'] / $total['count']
            ) * 100.00;
            if ($requests[$key]['progress'] == 100.00) {
                $requests[$key]['status'] = 'Completed';
            }
            if ($requests[$key]['progress'] == 0.00) {
                $requests[$key]['status'] = 'Waiting';
            }
            if (
                $requests[$key]['progress'] > 0.00
                AND
                $requests[$key]['progress'] < 100.00
            ) {
                $requests[$key]['status'] = 'In Progress';
            }
        }
    }

    return $requests;
}

function get_request_and_keywords($application, $user, $id) {
    $query = <<<EOD
SELECT *
FROM `tools_kns_requests`
WHERE `id` = ? AND `user_id` = ?
EOD;
    $request = $application['db']->fetchAssoc(
        $query, array($id, $user['id'])
    );
    $keywords = array();
    if ($request) {
        $query = <<<EOD
SELECT *
FROM `tools_kns_keywords`
WHERE `request_id` = ?
EOD;
        $keywords = $application['db']->fetchAll($query, array($id));
        if ($keywords) {
            foreach ($keywords as $key => $value) {
                $keywords[$key]['contents'] = json_decode(
                    $keywords[$key]['contents'], true
                );
                if ($keywords[$key]['contents']) {
                    if (empty($keywords[$key]['contents']['popularity'])) {
                        $keywords[$key]['contents']['popularity'] = array(
                            0, 'Very Low',
                        );
                    }
                }
            }
        }
    }

    return array($request, $keywords);
}

function get_sections($application) {
    $sections = array();
    $query = <<<EOD
SELECT *
FROM `tools_ce_sections`
ORDER BY `id` ASC
EOD;
    $records = $application['db']->fetchAll($query);
    if ($records) {
        foreach ($records as $record) {
            $sections[] = array($record['id'], $record['title']);
        }
    }

    return $sections;
}

function get_truncated_text($string, $length) {
    if (strlen($string) > $length) {
        return rtrim(substr($string, 0, $length)) . '...';
    }

    return $string;
}

function get_user($application) {
    if (is_development()) {
        return array(
            'email' => 'administrator@administrator.com',
            'id' => 1,
            'name' => 'Administrator',
        );
    }
    $user = $application['session']->get('user_');
    if ($user) {
        return $user;
    }
    $user = $application['session']->get('user');
    if ($user) {
        return $user;
    }

    return array(
        'email' => '',
        'id' => 0,
        'name' => '',
    );
}

function get_words_from_title($title) {
    $words = array();
    $items = preg_split('/[^A-Za-z0-9]/', $title);
    if ($items) {
        foreach ($items as $item) {
            if (strlen($item) > 3) {
                $words[] = $item;
            }
        }
    }

    return $words;
}

function get_words_from_words($words_) {
    $words = array();
    $words_ = array_count_values($words_);
    arsort($words_);
    $words_ = array_slice($words_, 0, 10);
    if ($words_) {
        foreach ($words_ as $key => $value) {
            $words[] = array($key, $value);
        }
    }
    return $words;
}

function has_statistics($user) {
    return in_array($user['id'], array(1, 2, 3));
}

function is_development() {
    return $_SERVER['SERVER_PORT'] == '5000';
}

function is_paying_customer($application, $user) {
    if (is_development()) {
        return true;
    }

    if (has_statistics($user)) {
        return true;
    }

    $query = <<<EOD
SELECT COUNT(`umeta_id`) AS count
FROM `wp_usermeta`
WHERE `user_id` = ? AND `meta_key` = ? AND `meta_value` = ?
EOD;
    $record = $application['db']->fetchAssoc(
        $query, array($user['id'], 'paying_customer', '1')
    );
    if (!empty($record) AND $record['count'] == 1) {
        return true;
    }

    return false;
}

if (php_sapi_name() === 'cli-server') {
    if (is_file(sprintf(
        '%s/%s',
        __DIR__,
        preg_replace('#(\?.*)$#', '', $_SERVER['REQUEST_URI'])
    ))) {
        return false;
    }
}

require_once sprintf('%s/vendor/autoload.php', __DIR__);

use Doctrine\DBAL\Logging\DebugStack;
use Silex\Application;
use Silex\Provider\DoctrineServiceProvider;
use Silex\Provider\MonologServiceProvider;
use Silex\Provider\SessionServiceProvider;
use Silex\Provider\SwiftmailerServiceProvider;
use Silex\Provider\TwigServiceProvider;
use Silex\Provider\UrlGeneratorServiceProvider;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\ResponseHeaderBag;

$variables = json_decode(file_get_contents(sprintf(
    '%s/variables.json', __DIR__
)), true);

$application = new Application();

$application['debug'] = $variables['application']['debug'];

$application->register(new DoctrineServiceProvider(), array(
    'db.options' => array(
        'charset' => 'utf8',
        'dbname' => $variables['mysql']['database'],
        'driver' => 'pdo_mysql',
        'host' => $variables['mysql']['host'],
        'password' => $variables['mysql']['password'],
        'user' => $variables['mysql']['user'],
    ),
));
$application->register(new SessionServiceProvider(array(
    'session.storage.save_path' => sprintf('%s/tmp', __DIR__),
)));
$application->register(new SwiftmailerServiceProvider(), array(
    'swiftmailer.options' => array(
        'auth_mode' => $variables['smtp']['auth_mode'],
        'encryption' => $variables['smtp']['encryption'],
        'host' => $variables['smtp']['host'],
        'password' => $variables['smtp']['password'],
        'port' => $variables['smtp']['port'],
        'username' => $variables['smtp']['username'],
    ),
));
$application->register(new TwigServiceProvider(), array(
    'twig.path' => sprintf('%s/templates', __DIR__),
));
$application->register(new UrlGeneratorServiceProvider());

$application['mailer'] = $application->share(function ($application) {
    return new \Swift_Mailer($application['swiftmailer.transport']);
});

if ($application['debug']) {
    $application->register(new MonologServiceProvider(), array(
        'monolog.logfile' => sprintf('%s/development.log', __DIR__),
    ));
    $logger = new DebugStack();
    $application->extend(
        'db.config',
        function($configuration) use ($logger) {
            $configuration->setSQLLogger($logger);

            return $configuration;
        }
    );
    $application->finish(function () use ($application, $logger) {
        foreach ($logger->queries as $query) {
            $application['monolog']->debug(
                $query['sql'],
                array(
                    'params' => $query['params'],
                    'types' => $query['types'],
                )
            );
        }
    });
}

$application->before(function (Request $request) use ($application) {
    $user = get_user($application);
    if (!$user['id']) {
        if ($request->get('_route') != 'sign_in') {
            return $application->redirect(
                $application['url_generator']->generate('sign_in')
            );
        }
    }
    if ($request->get('_route') != 'sign_in') {
        $is_paying_customer = is_paying_customer($application, $user);
        if ($is_paying_customer) {
            if ($request->get('_route') == '403') {
                return $application->redirect(
                    $application['url_generator']->generate('dashboard')
                );
            }
        } else {
            if ($request->get('_route') != '403') {
                return $application->redirect(
                    $application['url_generator']->generate('403')
                );
            }
        }
    }
    $application['session']->set('user', $user);
    $application['twig']->addGlobal('has_statistics', has_statistics($user));
    $application['twig']->addGlobal('is_paying_customer', $is_paying_customer);
    $application['twig']->addGlobal('user', $user);
});

$before_statistics = function () use ($application) {
    if (!has_statistics($application['session']->get('user'))) {
        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
};

$application
->match(
    '/',
    function () use ($application) {
        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
)
->method('GET');

$application
->match(
    '/403',
    function () use ($application) {
        return $application['twig']->render('views/403.twig');
    }
)
->bind('403')
->method('GET');

$application
->match(
    '/author-analyzer',
    function (Request $request) use ($application) {
        return $application['twig']->render(
            'views/author_analyzer.twig',
            array(
                'url' => $request->get('url'),
            )
        );
    }
)
->bind('author_analyzer')
->method('GET');

$application
->match(
    '/author-analyzer/author',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/author_analyzer.py get_author %s '.
            '2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('url'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('author_analyzer_author')
->method('POST');

$application
->match(
    '/author-analyzer/authors',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/author_analyzer.py get_authors %s '.
            '2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('keyword'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('author_analyzer_authors')
->method('POST');

$application
->match(
    '/book-analyzer',
    function (Request $request) use ($application) {
        return $application['twig']->render('views/book_analyzer.twig', array(
            'url' => $request->get('url'),
        ));
    }
)
->bind('book_analyzer')
->method('GET');

$application
->match(
    '/book-analyzer/book',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/book_analyzer.py get_book %s 2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('url'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('book_analyzer_book')
->method('POST');

$application
->match(
    '/book-analyzer/books',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/book_analyzer.py get_books %s 2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('keyword'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('book_analyzer_books')
->method('POST');

$application
->match(
    '/book-analyzer/items',
    function (Request $request) use ($application, $variables) {
        $keywords = $request->get('keywords');
        $keywords = strtolower($keywords);
        $keywords = explode("\n", $keywords);
        if (!empty($keywords)) {
            foreach ($keywords as $key => $value) {
                $value = trim($value);
                if (!empty($value)) {
                    $keywords[$key] = $value;
                } else {
                    unset($keywords[$key]);
                }
            }
        }
        $keywords = array_unique($keywords);
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/book_analyzer.py get_items %s %s '.
            '2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('url')),
            escapeshellarg(json_encode($keywords))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('book_analyzer_items')
->method('POST');

$application
->match(
    '/dashboard',
    function () use ($application) {
        return $application['twig']->render('views/dashboard.twig', array(
            'popular_searches' => array_slice(
                get_popular_searches($application), 0, 3
            ),
        ));
    }
)
->bind('dashboard')
->method('GET');

$application
->match(
    '/feedback',
    function (Request $request) use ($application) {
        $error = '';
        if ($request->isMethod('POST')) {
            $body = $request->get('body');
            if (!empty($body)) {
                if (!is_development()) {
                    $user = $application['session']->get('user');
                    $subject = sprintf(
                        'ZonSidekick Feedback from %s', $user['email']
                    );
                    try {
                        $message = \Swift_Message::newInstance()
                            ->setBody(trim($request->get('body')))
                            ->setFrom(array(
                                $user['email'],
                            ))
                            ->setSubject($subject)
                            ->setTo(array(
                                'support@perfectsidekick.com',
                            ));
                        $application['mailer']->send($message);
                    } catch (Exception $exception ) {
                    }
                }
                $application['session']->getFlashBag()->add(
                    'success',
                    array('Your feedback has been sent successfully.')
                );
                return $application->redirect(
                    $application['url_generator']->generate('feedback')
                );
            } else {
                $error = 'Invalid Message';
            }
        }

        return $application['twig']->render('views/feedback.twig', array(
            'error' => $error,
        ));
    }
)
->bind('feedback')
->method('GET|POST');

$application
->match(
    '/keyword-analyzer/multiple',
    function () use ($application) {
        $user = $application['session']->get('user');
        $requests = get_requests($application, $user);

        return $application['twig']->render(
            'views/keyword_analyzer_multiple.twig',
            array(
                'requests' => $requests,
            )
        );
    }
)
->bind('keyword_analyzer_multiple')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/add',
    function () use ($application) {
    $user = $application['session']->get('user');
    list($count, $_) = get_count_and_keywords('');

    return $application['twig']->render(
        'views/keyword_analyzer_multiple_add.twig',
        array(
            'count' => $count,
            'countries' => get_countries(),
        )
    );
})
->bind('keyword_analyzer_multiple_add')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/{id}/csv',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        $csv = get_csv($application, $user, $id);
        $stream = function () use ($csv) {
            echo $csv;
        };

        return $application->stream($stream, 200, array(
            'Content-Disposition' => sprintf(
                'attachment; filename="simple_report_%s.csv"', date('m_d_Y')
            ),
            'Content-Length' => strlen($csv),
            'Content-Type' => 'text/csv',
            'Expires' => '0',
            'Pragma' => 'no-cache',
        ));
    }
)
->bind('keyword_analyzer_multiple_csv')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/{id}/delete',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request_, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request_ OR !$keywords) {
            return $application->redirect(
                $application['url_generator']
                    ->generate('keyword_analyzer_multiple')
            );
        }
        if ($request->isMethod('POST')) {
            $application['db']->executeUpdate(
                'DELETE FROM `tools_kns_requests` WHERE `ID` = ?',
                array($id)
            );
            $application['session']->getFlashBag()->add(
                'success', array('The report was deleted successfully.')
            );
            return $application->redirect(
                $application['url_generator']
                    ->generate('keyword_analyzer_multiple')
            );
        }
        return $application['twig']->render(
            'views/keyword_analyzer_multiple_delete.twig',
            array(
                'id' => $id,
            )
        );
    }
)
->bind('keyword_analyzer_multiple_delete')
->method('GET|POST');

$application
->match(
    '/keyword-analyzer/multiple/{id}/detailed',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request OR !$keywords) {
            return $application->redirect(
                $application['url_generator']
                    ->generate('keyword_analyzer_multiple')
            );
        }
        usort($keywords, 'usort_keywords_1');

        return $application['twig']->render(
            'views/keyword_analyzer_multiple_detailed.twig',
            array(
                'currency' => get_currency($request['country']),
                'is_pdf' => true,
                'keywords' => $keywords,
                'logo' => '',
            )
        );
    }
)
->bind('keyword_analyzer_multiple_detailed')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/{id}/email',
    function (Request $request, $id) use ($application, $variables) {
        $user = $application['session']->get('user');
        $subject = 'Your Keyword Analyzer report is ready!';
        $body = <<<EOD
We have attached your report in simple and detailed formats. The detailed
report includes our recommendations along with important information about each
keyword.

If you have any questions at all please don't hesitate to contact
support@perfectsidekick.com
EOD;
        try {
            $message = \Swift_Message::newInstance()
                ->addPart(get_part($subject, $body), 'text/html')
                ->attach(\Swift_Attachment::newInstance(
                    get_csv($application, $user, $id),
                    sprintf('simple_report_%s.csv', date('m_d_Y')),
                    'text/csv'
                ))
                ->attach(\Swift_Attachment::newInstance(
                    get_pdf(
                        $application,
                        $user,
                        $request->get('logo'),
                        $id,
                        $variables
                    ),
                    sprintf('detailed_report_%s.pdf', date('m_d_Y')),
                    'application/pdf'
                ))
                ->setBody(trim($body))
                ->setFrom(array(
                    'reports@perfectsidekick.com' => 'Zon Sidekick',
                ))
                ->setSubject($subject)
                ->setTo(array($request->get('email')));
            $application['mailer']->send($message);
        } catch (Exception $exception ) {
        }

        return new Response();
    }
)
->bind('keyword_analyzer_multiple_email')
->method('POST');

$application
->match(
    '/keyword-analyzer/multiple/{id}/pdf',
    function (Request $request, $id) use ($application, $variables) {
        $user = $application['session']->get('user');
        $pdf = get_pdf(
            $application, $user, $request->get('logo'), $id, $variables
        );
        $stream = function () use ($pdf) {
            echo $pdf;
        };

        return $application->stream($stream, 200, array(
            'Content-Disposition' => sprintf(
                'attachment; filename="detailed_report_%s.pdf"', date('m_d_Y')
            ),
            'Content-Length' => strlen($pdf),
            'Content-Type' => 'application/pdf',
            'Expires' => '0',
            'Pragma' => 'no-cache',
        ));
    }
)
->bind('keyword_analyzer_multiple_pdf')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/process',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');
        list($count, $keywords) = get_count_and_keywords(
            $request->get('keywords')
        );
        if (!$count OR !$keywords) {
            return $application->redirect(
                $application['url_generator']
                    ->generate('keyword_analyzer_multiple_add')
            );
        }
        $application['db']->insert('tools_kns_requests', array(
            'country' => $request->get('country'),
            'timestamp' => date('Y-m-d H:i:s'),
            'user_id' => $user['id'],
        ));
        $id = $application['db']->lastInsertId();
        if ($keywords) {
            foreach ($keywords as $keyword) {
                $application['db']->insert('tools_kns_keywords', array(
                    'request_id' => $id,
                    'string' => $keyword,
                ));
            }
        }

        return $application->redirect(
            $application['url_generator']->generate(
                'keyword_analyzer_multiple_simple',
                array(
                    'id' => $id,
                )
            )
        );
    }
)
->bind('keyword_analyzer_multiple_process')
->method('POST');

$application
->match(
    '/keyword-analyzer/multiple/{id}/simple',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request OR !$keywords) {
            return $application->redirect(
                $application['url_generator']
                    ->generate('keyword_analyzer_multiple')
            );
        }

        return $application['twig']->render(
            'views/keyword_analyzer_multiple_simple.twig',
            array(
                'currency' => get_currency($request['country']),
                'email' => $user['email'],
                'keywords' => $keywords,
                'logos' => get_logos($application, $user),
                'request' => $request,
            )
        );
    }
)
->bind('keyword_analyzer_multiple_simple')
->method('GET');

$application
->match(
    '/keyword-analyzer/multiple/{id}/xhr',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );

        if ($keywords) {
            foreach ($keywords as $key => $value) {
                if ($keywords[$key]['contents']) {
                    if ($keywords[$key]['contents']['score'][1] !== 'N/A') {
                        $keywords[$key]['position'] = 1;
                    } else {
                        $keywords[$key]['position'] = 2;
                    }
                } else {
                    $keywords[$key]['position'] = 3;
                }
            }
        }

        usort($keywords, 'usort_keywords_2');

        return new Response(json_encode($keywords));
    }
)
->bind('keyword_analyzer_multiple_xhr')
->method('POST');

$application
->match(
    '/keyword-analyzer/single',
    function () use ($application) {
        $countries = array();
        $c = get_countries();
        if ($c) {
            foreach ($c as $key => $value) {
                $countries[] = array($key, $value);
            }
        }
        return $application['twig']->render(
            'views/keyword_analyzer_single.twig',
            array(
                'countries' => $countries,
            )
        );
    }
)
->bind('keyword_analyzer_single')
->method('GET');

$application
->match(
    '/keyword-analyzer/single/xhr',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/keyword_analyzer.py %s %s 2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('keyword')),
            escapeshellarg($request->get('country'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('keyword_analyzer_single_xhr')
->method('POST');

$application
->match(
    '/keyword-suggester',
    function (Request $request) use ($application) {
        return $application['twig']->render(
            'views/keyword_suggester.twig',
            array(
                'countries' => array(
                    'com' => 'US',
                    'co.uk' => 'UK',
                    'es' => 'Spain',
                    'fr' => 'France',
                    'it' => 'Italy',
                    'com.br' => 'Brazil',
                    'ca' => 'Canada',
                    'de' => 'Germany',
                    'co.jp' => 'Japan',
                ),
                'keywords' => $request->get('keywords', ''),
                'mode' => $request->get('mode', 'Suggest'),
                'search_aliases' => array(
                    'aps' => 'All Departments',
                    'digital-text' => 'Kindle Store',
                    'instant-video' => 'Amazon Instant Video',
                    'appliances' => 'Appliances',
                    'mobile-apps' => 'Apps for Android',
                    'arts-crafts' => 'Arts, Crafts &amp; Sewing',
                    'automotive' => 'Automotive',
                    'baby-products' => 'Baby',
                    'beauty' => 'Beauty',
                    'stripbooks' => 'Books',
                    'mobile' => 'Cell Phones &amp; Accessories',
                    'apparel' => 'Clothing &amp; Accessories',
                    'collectibles' => 'Collectibles',
                    'computers' => 'Computers',
                    'financial' => 'Credit Cards',
                    'electronics' => 'Electronics',
                    'gift-cards' => 'Gift Cards Store',
                    'grocery' => 'Grocery &amp; Gourmet Food',
                    'hpc' => 'Health &amp; Personal Care',
                    'garden' => 'Home &amp; Kitchen',
                    'industrial' => 'Industrial &amp; Scientific',
                    'jewelry' => 'Jewelry',
                    'magazines' => 'Magazine Subscriptions',
                    'movies-tv' => 'Movies &amp; TV',
                    'digital-music' => 'MP3 Music',
                    'popular' => 'Music',
                    'mi' => 'Musical Instruments',
                    'office-products' => 'Office Products',
                    'lawngarden' => 'Patio, Lawn &amp; Garden',
                    'pets' => 'Pet Supplies',
                    'shoes' => 'Shoes',
                    'software' => 'Software',
                    'sporting' => 'Sports &amp; Outdoors',
                    'tools' => 'Tools &amp; Home Improvement',
                    'toys-and-games' => 'Toys &amp; Games',
                    'videogames' => 'Video Games',
                    'watches' => 'Watches',
                ),
            )
        );
    }
)
->bind('keyword_suggester')
->method('GET|POST');

$application
->match(
    '/keyword-suggester/download',
    function (Request $request) use ($application) {
        $json = json_decode($request->get('json'), true);
        $json['suggestions'] = implode("\n", $json['suggestions']);
        $stream = function () use ($json) {
            echo $json['suggestions'];
        };
        return $application->stream($stream, 200, array(
            'Content-Disposition' => sprintf(
                'attachment; filename="keyword_suggester.csv"'
            ),
            'Content-Length' => strlen($json['suggestions']),
            'Content-Type' => 'text/csv',
            'Expires' => '0',
            'Pragma' => 'no-cache',
        ));
    }
)
->bind('keyword_suggester_download')
->method('POST');

$application
->match(
    '/keyword-suggester/xhr',
    function (Request $request) use ($application, $variables) {
        if (is_development()) {
            $output = array('["1", "2", "3"]');
        } else {
            ignore_user_abort(true);
            set_time_limit(0);
            exec(sprintf(
                '%s/python %s/scripts/keyword_suggester.py %s %s %s '.
                '2>/dev/null',
                $variables['virtualenv'],
                __DIR__,
                escapeshellarg($request->get('keyword')),
                escapeshellarg($request->get('country')),
                escapeshellarg($request->get('search_alias'))
            ), $output, $return_var);
        }
        return new Response(implode('', $output));
    }
)
->bind('keyword_suggester_xhr')
->method('POST');

$application
->match(
    '/logos',
    function () use ($application) {
        $user = $application['session']->get('user');

        return $application['twig']->render('views/logos.twig', array(
            'logos' => get_logos($application, $user),
        ));
    }
)
->bind('logos')
->method('GET');

$application
->match(
    '/logos/add',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');

        $error = null;
        if ($request->isMethod('POST')) {
            $logo = $request->files->get('logo');
            if (
                $logo
                and
                in_array(
                    $logo->guessExtension(), array('png')
                )
            ) {
                $path = get_path($application, $user, 'logos');
                $logo->move($path, $logo->getClientOriginalName());
                $file_path = sprintf(
                    '%s/%s', $path, $logo->getClientOriginalName()
                );
                exec(sprintf(
                    'convert %s -resize x150 %s',
                    escapeshellarg($file_path),
                    escapeshellarg($file_path)
                ), $output, $return_var);
                $application['session']->getFlashBag()->add(
                    'success', array('The logo was uploaded successfully.')
                );

                return $application->redirect(
                    $application['url_generator']->generate('logos')
                );
            } else {
                $error = 'Invalid Logo';
            }
        }

        return $application['twig']->render('views/logos_add.twig', array(
            'error' => $error,
        ));
    }
)
->bind('logos_add')
->method('GET|POST');

$application
->match(
    '/logos/delete',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');
        if ($request->isMethod('POST')) {
            unlink(sprintf(
                '%s/%s',
                get_path($application, $user, 'logos'),
                $request->get('file_name')
            ));
            $application['session']->getFlashBag()->add(
                'success', array('The logo was deleted successfully.')
            );

            return $application->redirect(
                $application['url_generator']->generate('logos')
            );
        }

        return $application['twig']->render(
            'views/logos_delete.twig', array(
                'file_name' => $request->get('file_name'),
            )
        );
    }
)
->bind('logos_delete')
->method('GET|POST');

$application
->match(
    '/logos/download',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');
        $file_path = sprintf(
            '%s/%s',
            get_path($application, $user, 'logos'),
            $request->get('file_name')
        );
        $stream = function () use ($file_path) {
            readfile($file_path);
        };

        return $application->stream($stream, 200, array(
            'Content-Disposition' => sprintf(
                'attachment; filename="%s"', $request->get('file_name')
            ),
            'Content-length' => filesize($file_path),
            'Content-Type' => 'image/png',
        ));
    }
)
->bind('logos_download')
->method('GET');

$application
->match(
    '/logos/preview',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');
        $stream = function () use ($application, $request, $user) {
            readfile(sprintf(
                '%s/%s',
                get_path($application, $user, 'logos'),
                $request->get('file_name')
            ));
        };

        return $application->stream($stream, 200, array(
            'Content-Type' => 'image/png',
        ));
    }
)
->bind('logos_preview')
->method('GET');

$application
->match(
    '/popular-searches',
    function (Request $request) use ($application) {
        return $application['twig']->render(
            'views/popular_searches.twig',
            array(
                'popular_searches' => get_popular_searches($application),
            )
        );
    }
)
->bind('popular_searches')
->method('GET');

$application
->match(
    '/profile',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');

        $error = null;
        $email = $user['email'];

        if ($request->isMethod('POST')) {
            $email = $request->get('email');
            if (!empty($email)) {
                $application['db']->executeUpdate(
                    'UPDATE `wp_users` SET `user_email` = ? WHERE `ID` = ?',
                    array($email, $user['id'])
                );
                $application['session']->getFlashBag()->add(
                    'success', array('Your profile was updated successfully.')
                );
                return $application->redirect(
                    $application['url_generator']->generate('profile')
                );
            } else {
                $error = 'Invalid Email';
            }
        }

        return $application['twig']->render('views/profile.twig', array(
            'email' => $email,
            'error' => $error,
        ));
    }
)
->bind('profile')
->method('GET|POST');

$application
->match(
    '/sign-in',
    function (Request $request) use ($application) {
        $error = null;
        if ($request->isMethod('POST')) {
            $username = $request->get('username');
            $password = $request->get('password');
            if (!empty($username) AND !empty($password)) {
                $query = <<<EOD
SELECT `id` , `user_email` , `display_name`
FROM `wp_users`
WHERE `user_login` = ? AND `user_pass` = ?
EOD;
                $record = $application['db']->fetchAssoc($query, array(
                    $username,
                    md5($password),
                ));
                if ($record) {
                    $application['session']->set('user', array(
                        'email' => $record['user_email'],
                        'id' => $record['id'],
                        'name' => $record['display_name'],
                    ));
                    $application['session']->getFlashBag()->add(
                        'success',
                        array('You have been signed in successfully.')
                    );

                    return $application->redirect(
                        $application['url_generator']->generate('dashboard')
                    );
                }
            }
            $error = 'Invalid Username/Password';
        }

        return $application['twig']->render('views/sign_in.twig', array(
            'error' => $error,
        ));
    }
)
->bind('sign_in')
->method('GET|POST');

$application
->match(
    '/sign-out',
    function () use ($application) {
        $application['session']->set('user_', array(
            'email' => '',
            'id' => '',
            'name' => '',
        ));

        $application['session']->set('user', array(
            'email' => '',
            'id' => '',
            'name' => '',
        ));

        return $application->redirect(
            $application['url_generator']->generate('sign_in')
        );
    }
)
->bind('sign_out')
->method('GET');

$application
->match(
    '/statistics',
    function (Request $request) use ($application) {
        $items = array();
        $total = array(
            'keywords_1' => 0,
            'keywords_2' => 0,
            'requests' => 0,
        );
        $query = <<<EOD
SELECT `ID` AS `id`, `display_name`
FROM `wp_users`
ORDER BY `ID` ASC
EOD;
        $records = $application['db']->fetchAll($query);
        if (!empty($records)) {
            foreach ($records as $record) {
                $requests = get_requests($application, $record);
                $r = count($requests);
                $k_1 = 0;
                $k_2 = 0;
                if ($requests) {
                    foreach ($requests as $request) {
                        $k_1 += $request['keywords'][0];
                        $k_2 += $request['keywords'][2];
                    }
                }
                $items[] = array(
                    'id' => $record['id'],
                    'display_name' => $record['display_name'],
                    'keywords_1' => number_format($k_1, 0, '.', ','),
                    'keywords_2' => number_format($k_2, 0, '.', ','),
                    'requests' => number_format($r, 0, '.', ','),
                );
                $total['keywords_1'] += $k_1;
                $total['keywords_2'] += $k_2;
                $total['requests'] += $r;
            }
        }

        return $application['twig']->render('views/statistics.twig', array(
            'items' => $items,
            'keywords_1' => number_format($total['keywords_1'], 0, '.', ','),
            'keywords_2' => number_format($total['keywords_2'], 0, '.', ','),
            'requests' => number_format($total['requests'], 0, '.', ','),
        ));
    }
)
->before($before_statistics)
->bind('statistics')
->method('GET');

$application
->match(
    '/suggested_keywords',
    function (Request $request) use ($application, $variables) {
        ignore_user_abort(true);
        set_time_limit(0);
        exec(sprintf(
            '%s/python %s/scripts/suggested_keywords.py %s 2>/dev/null',
            $variables['virtualenv'],
            __DIR__,
            escapeshellarg($request->get('keywords'))
        ), $output, $return_var);
        return new Response(implode('', $output));
    }
)
->bind('suggested_keywords')
->method('POST');

$application
->match(
    '/top-100-explorer',
    function (Request $request) use ($application) {
        return $application['twig']->render(
            'views/top_100_explorer.twig',
            array(
                'categories' => array_merge(
                    array(array(-1, 'All')),
                    get_categories($application, 0, array())
                ),
                'filters' => array(
                    'amazon_best_sellers_rank_1'
                        => $request->get('amazon_best_sellers_rank_1', ''),
                    'amazon_best_sellers_rank_2'
                        => $request->get('amazon_best_sellers_rank_2', ''),
                    'amazon_best_sellers_rank_3'
                        => $request->get('amazon_best_sellers_rank_3', ''),
                    'amazon_best_sellers_rank_4'
                        => $request->get('amazon_best_sellers_rank_4', ''),
                    'appearance_1' => $request->get('appearance_1', ''),
                    'appearance_2' => $request->get('appearance_2', ''),
                    'appearance_3' => $request->get('appearance_3', ''),
                    'appearance_4' => $request->get('appearance_4', ''),
                    'category_id' => $request->get('category_id', ''),
                    'count' => $request->get('count', ''),
                    'price_1' => $request->get('price_1', ''),
                    'price_2' => $request->get('price_2', ''),
                    'price_3' => $request->get('price_3', ''),
                    'price_4' => $request->get('price_4', ''),
                    'print_length_1' => $request->get('print_length_1', ''),
                    'print_length_2' => $request->get('print_length_2', ''),
                    'print_length_3' => $request->get('print_length_3', ''),
                    'print_length_4' => $request->get('print_length_4', ''),
                    'publication_date_1'
                        => $request->get('publication_date_1', ''),
                    'publication_date_2'
                        => $request->get('publication_date_2', ''),
                    'publication_date_3'
                        => $request->get('publication_date_3', ''),
                    'publication_date_4'
                        => $request->get('publication_date_4', ''),
                    'review_average_1'
                        => $request->get('review_average_1', ''),
                    'review_average_2'
                        => $request->get('review_average_2', ''),
                    'review_average_3'
                        => $request->get('review_average_3', ''),
                    'review_average_4'
                        => $request->get('review_average_4', ''),
                    'section_id' => $request->get('section_id', ''),
                ),
                'sections' => get_sections($application),
            )
        );
    }
)
->bind('top_100_explorer')
->method('GET|POST');

$application
->match(
    '/top-100-explorer/xhr',
    function (Request $request) use ($application) {
        $contents = array(
            'books' => array(),
            'categories' => array(),
            'glance' => array(
                'absr' => 0,
                'estimated_sales_per_day' => 0,
                'price' => 0.00,
                'print_length' => 0,
                'review_average' => 0.00,
                'total_number_of_reviews' => 0,
                'words' => array(),
            ),
            'date' => 'N/A',
        );

        $category_id = intval($request->get('category_id'));
        $section_id = intval($request->get('section_id'));
        $print_length_1 = $request->get('print_length_1');
        $print_length_2 = intval($request->get('print_length_2'));
        $print_length_3 = intval($request->get('print_length_3'));
        $print_length_4 = intval($request->get('print_length_4'));
        $price_1 = $request->get('price_1');
        $price_2 = floatval($request->get('price_2'));
        $price_3 = floatval($request->get('price_3'));
        $price_4 = floatval($request->get('price_4'));
        $publication_date_1 = $request->get('publication_date_1');
        $publication_date_2 = $request->get('publication_date_2');
        $publication_date_3 = $request->get('publication_date_3');
        $publication_date_4 = $request->get('publication_date_4');
        $amazon_best_sellers_rank_1 = $request
            ->get('amazon_best_sellers_rank_1');
        $amazon_best_sellers_rank_2 = intval(
            $request->get('amazon_best_sellers_rank_2')
        );
        $amazon_best_sellers_rank_3 = intval(
            $request->get('amazon_best_sellers_rank_3')
        );
        $amazon_best_sellers_rank_4 = intval(
            $request->get('amazon_best_sellers_rank_4')
        );
        $review_average_1 = $request->get('review_average_1');
        $review_average_2 = floatval($request->get('review_average_2'));
        $review_average_3 = floatval($request->get('review_average_3'));
        $review_average_4 = floatval($request->get('review_average_4'));
        $appearance_1 = $request->get('appearance_1');
        $appearance_2 = floatval($request->get('appearance_2'));
        $appearance_3 = floatval($request->get('appearance_3'));
        $appearance_4 = floatval($request->get('appearance_4'));
        $count = intval($request->get('count'));

        if ($category_id == -1) {
            $query = <<<EOD
SELECT MAX(`date`) AS `date`
FROM `tools_ce_trends`
WHERE
    `tools_ce_trends`.`category_id` > ?
    AND
    `tools_ce_trends`.`section_id` = ?
EOD;
        } else {
            $query = <<<EOD
SELECT MAX(`date`) AS `date`
FROM `tools_ce_trends`
WHERE
    `tools_ce_trends`.`category_id` = ?
    AND
    `tools_ce_trends`.`section_id` = ?
EOD;
        }
        $record = $application['db']->fetchAssoc($query, array(
            $category_id,
            $section_id,
        ));
        $contents['date'] = $record['date'];

        $query = <<<EOD
SELECT *
FROM `tools_ce_books`
INNER JOIN
    `tools_ce_trends` ON `tools_ce_books`.`id` = `tools_ce_trends`.`book_id`
WHERE %s
ORDER BY `tools_ce_trends`.`rank` ASC, `tools_ce_trends`.`category_id` ASC
LIMIT %d OFFSET 0
EOD;
        $conditions = array();
        $parameters = array();
        switch ($print_length_1) {
            case 'More Than':
                $conditions[] = '`tools_ce_books`.`print_length` > ?';
                $parameters[] = $print_length_2;
                break;
            case 'Less Than':
                $conditions[] = '`tools_ce_books`.`print_length` < ?';
                $parameters[] = $print_length_2;
                break;
            case 'Between':
                $conditions[] = <<<EOD
`tools_ce_books`.`print_length` >= ? AND `tools_ce_books`.`print_length` <= ?
EOD;
                $parameters[] = $print_length_3;
                $parameters[] = $print_length_4;
                break;
        }
        switch ($price_1) {
            case 'More Than':
                $conditions[] = '`tools_ce_books`.`price` > ?';
                $parameters[] = $price_2;
                break;
            case 'Less Than':
                $conditions[] = '`tools_ce_books`.`price` < ?';
                $parameters[] = $price_2;
                break;
            case 'Between':
                $conditions[] = <<<EOD
`tools_ce_books`.`price` >= ? AND `tools_ce_books`.`price` <= ?
EOD;
                $parameters[] = $price_3;
                $parameters[] = $price_4;
                break;
        }
        switch ($publication_date_1) {
            case 'More Than':
                $conditions[] = '`tools_ce_books`.`publication_date` > ?';
                $parameters[] = $publication_date_2;
                break;
            case 'Less Than':
                $conditions[] = '`tools_ce_books`.`publication_date` < ?';
                $parameters[] = $publication_date_2;
                break;
            case 'Between':
                $conditions[] = <<<EOD
`tools_ce_books`.`publication_date` >= ?
AND
`tools_ce_books`.`publication_date` <= ?
EOD;
                $parameters[] = $publication_date_3;
                $parameters[] = $publication_date_4;
                break;
        }
        switch ($review_average_1) {
            case 'More Than':
                $conditions[] = '`tools_ce_books`.`review_average` > ?';
                $parameters[] = $review_average_2;
                break;
            case 'Less Than':
                $conditions[] = '`tools_ce_books`.`review_average` < ?';
                $parameters[] = $review_average_2;
                break;
            case 'Between':
                $conditions[] = <<<EOD
`tools_ce_books`.`review_average` >= ?
AND
`tools_ce_books`.`review_average` <= ?
EOD;
                $parameters[] = $review_average_3;
                $parameters[] = $review_average_4;
                break;
        }
        if ($category_id !== -1) {
            $conditions[] = '`tools_ce_trends`.`category_id` = ?';
            $parameters[] = $category_id;
        }
        $conditions[] = '`tools_ce_trends`.`section_id` = ?';
        $parameters[] = $section_id;
        $conditions[] = '`tools_ce_trends`.`date` = ?';
        $parameters[] = $contents['date'];
        $conditions = implode(' AND ', $conditions);
        $query = sprintf($query, $conditions, $count);
        $books = $application['db']->fetchAll($query, $parameters);
        if ($books) {
            foreach ($books as $book) {
                if ($category_id == -1) {
                    $query = <<<EOD
SELECT COUNT(DISTINCT `date`) AS `count`
FROM `tools_ce_trends`
WHERE
    `category_id` > ?
    AND
    `section_id` = ?
    AND
    `book_id` = ?
    AND
    `date` >= CURDATE() - INTERVAL 7 DAY
EOD;
                } else {
                    $query = <<<EOD
SELECT COUNT(DISTINCT `date`) AS `count`
FROM `tools_ce_trends`
WHERE
    `category_id` = ?
    AND
    `section_id` = ?
    AND
    `book_id` = ?
    AND
    `date` >= CURDATE() - INTERVAL 7 DAY
EOD;
                }
                $record_1 = $application['db']->fetchAssoc($query, array(
                    $category_id,
                    $section_id,
                    $book['book_id'],
                ));
                if ($category_id == -1) {
                    $query = <<<EOD
SELECT COUNT(DISTINCT `date`) AS `count`
FROM `tools_ce_trends`
WHERE
    `category_id` > ?
    AND
    `section_id` = ?
    AND
    `book_id` = ?
    AND
    `date` >= CURDATE() - INTERVAL 30 DAY
EOD;
                } else {
                    $query = <<<EOD
SELECT COUNT(DISTINCT `date`) AS `count`
FROM `tools_ce_trends`
WHERE
    `category_id` = ?
    AND
    `section_id` = ?
    AND
    `book_id` = ?
    AND
    `date` >= CURDATE() - INTERVAL 30 DAY
EOD;
                }
                $record_2 = $application['db']->fetchAssoc($query, array(
                    $category_id,
                    $section_id,
                    $book['book_id'],
                ));
                $book['appearances'] = array(
                    'last 7 days' => $record_1['count'],
                    'last 30 days' => $record_2['count'],
                );
                $book['amazon_best_sellers_rank'] = json_decode(
                    $book['amazon_best_sellers_rank'], true
                );
                asort($book['amazon_best_sellers_rank'], SORT_NUMERIC);
                if ($amazon_best_sellers_rank_1 == 'More Than') {
                    if (empty(
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                    )) {
                        continue;
                    }
                    if (
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                        <=
                        $amazon_best_sellers_rank_2
                    ) {
                        continue;
                    }
                }
                if ($amazon_best_sellers_rank_1 == 'Less Than') {
                    if (empty(
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                    )) {
                        continue;
                    }
                    if (
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                        >=
                        $amazon_best_sellers_rank_2
                    ) {
                        continue;
                    }
                }
                if ($amazon_best_sellers_rank_1 == 'Between') {
                    if (empty(
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                    )) {
                        continue;
                    }
                    if (!(
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                        >=
                        $amazon_best_sellers_rank_3
                        AND
                        $book[
                            'amazon_best_sellers_rank'
                        ]['Paid in Kindle Store']
                        <=
                        $amazon_best_sellers_rank_4
                    )) {
                        continue;
                    }
                }
                if ($appearance_1 == 'More Than') {
                    if ($book['appearances']['last 7 days'] <= $appearance_2) {
                        continue;
                    }
                }
                if ($appearance_1 == 'Less Than') {
                    if ($book['appearances']['last 7 days'] >= $appearance_2) {
                        continue;
                    }
                }
                if ($appearance_1 == 'Between') {
                    if (!(
                        $book['appearances']['last 7 days'] >= $appearance_3
                        AND
                        $book['appearances']['last 7 days'] <= $appearance_4
                    )) {
                        continue;
                    }
                }
                $book['amazon_best_sellers_rank_'] = 0;
                if (!empty(
                    $book['amazon_best_sellers_rank']['Paid in Kindle Store']
                )) {
                    $book[
                        'amazon_best_sellers_rank_'
                    ] = $book[
                        'amazon_best_sellers_rank'
                    ]['Paid in Kindle Store'];
                    if ($book['amazon_best_sellers_rank_'] <= 25000) {
                        $contents['glance']['absr'] += 1;
                    }
                }
                $book['category'] = get_category(
                    $application, $book['category_id']
                );
                $contents['books'][] = $book;
                $contents['glance']['price'] += $book['price'];
                $contents[
                    'glance'
                ][
                    'estimated_sales_per_day'
                ] += $book['estimated_sales_per_day'];
                $contents[
                    'glance'
                ][
                    'total_number_of_reviews'
                ] += $book['total_number_of_reviews'];
                $contents[
                    'glance'
                ]['review_average'] += $book['review_average'];
                $contents[
                    'glance'
                ]['print_length'] += $book['print_length'];
                $contents['glance']['words'] = array_merge(
                    $contents['glance']['words'],
                    get_words_from_title($book['title'])
                );
                if ($book['amazon_best_sellers_rank']) {
                    foreach (
                        $book['amazon_best_sellers_rank'] as $key => $value
                    ) {
                        if (
                            !preg_match('/^Paid in Kindle Store/', $key)
                            AND
                            !preg_match(
                                '/^Kindle Store > Kindle eBooks/', $key
                            )
                        ) {
                            continue;
                        }
                        $key = str_replace('Kindle Store > ', '', $key);
                        if (empty($contents['categories'][$key])) {
                            $contents['categories'][$key] = 0;
                        }
                        $contents['categories'][$key] += 1;
                    }
                }
            }
        }
        $cs = array();
        if ($contents['categories']) {
            foreach ($contents['categories'] as $key => $value) {
                if ($value > 1) {
                    $cs[] = array(
                        'frequency' => $value,
                        'title' => $key,
                    );
                }
            }
        }
        $contents['categories'] = $cs;
        usort($contents['categories'], 'usort_categories');

        $count = count($contents['books']);
        if ($count) {
            $contents['glance']['price'] /= $count;
            $contents['glance']['estimated_sales_per_day'] /= $count;
            $contents['glance']['total_number_of_reviews']  /= $count;
            $contents['glance']['review_average'] /= $count;
            $contents['glance']['print_length'] /= $count;
            $contents['glance']['words'] = get_words_from_words(
                $contents['glance']['words']
            );
        }

        return new Response(json_encode($contents, JSON_NUMERIC_CHECK));
    }
)
->bind('top_100_explorer_xhr')
->method('POST');

$application
->match(
    '/transfer/{id}',
    function ($id) use ($application) {
        if (!has_statistics($application['session']->get('user'))) {
            return $application->redirect(
                $application['url_generator']->generate('403')
            );
        }
        $query = 'SELECT `user_email` FROM `wp_users` WHERE `ID` = ?';
        $record = $application['db']->fetchAssoc($query, array(
            $id,
        ));
        if (!$record) {
            return $application->redirect(
                $application['url_generator']->generate('403')
            );
        }
        $application['session']->set('user_', array(
            'email' => $record['user_email'],
            'id' => $record['id'],
            'name' => $record['name'],
        ));

        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
)
->before($before_statistics)
->bind('transfer')
->method('GET');

$application->run();
