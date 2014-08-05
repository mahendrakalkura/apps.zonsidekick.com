<?php

date_default_timezone_set('UTC');

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

function get_count_and_keywords($application, $user, $keywords) {
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
    $count = -1;
    if (
        $user['id'] != 2
        &&
        !in_array(3, $application['session']->get('groups'))
        &&
        !in_array(4, $application['session']->get('groups'))
        &&
        in_array(5, $application['session']->get('groups'))
    ) {
        $query = <<<EOD
SELECT COUNT(`id`) AS `count`
FROM `tools_keywords`
INNER JOIN `tools_requests` ON `keywords`.`request_id` = `requests`.`id`
WHERE
    `tools_requests`.`user_id` = ?
    AND
    DATE(`tools_requests`.`timestamp`) = ?
EOD;
        $record = $application['db']->fetchAssoc(
            $query, array($user['id'], date('Y-m-d'))
        );
        $limit = 10;
        if ($record['count'] >= $limit) {
            $count = 0;
            $keywords = array();
        } else {
            $keywords = array_slice($keywords, 0, $limit - $record['count']);
            $count = $limit - $record['count'];
        }
    }

    return array($count, $keywords);
}

function get_contents($application, $user, $logo) {
    $file_path = sprintf(
        '%s/%s', get_path($application, $user, 'logos'), $logo
    );
    if (is_file($file_path)) {
        return sprintf(
            'data:%s;base64,%s',
            mime_content_type($image),
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

function get_groups($application) {
    $array = array();
    $user = $application['session']->get('user');
    $records = $application['db']->fetchAll(
        'SELECT `group_id` FROM `wp_groups_user_group` WHERE `user_id` = ?',
        array($user['id'])
    );
    if (!empty($records)) {
        foreach ($records as $record) {
            $array[] = $record['group_id'];
        }
    }

    return $array;
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

function get_pdf($application, $user, $logo, $id) {
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
            $application['twig']->render('views/kns_detailed.twig', array(
                'currency' => get_currency($request['country']),
                'is_pdf' => false,
                'keywords' => $keywords,
                'logo' => get_contents($application, $user, $logo),
            ))
        );
        $contents = shell_exec(sprintf(
            'weasyprint --format pdf %s -', escapeshellarg($file_path)
        ));
        unlink($file_path);
    }

    return $contents;
}

function get_requests($application, $user) {
    $query = <<<EOD
SELECT *
FROM `tools_requests`
WHERE `user_id` = ?
ORDER BY `timestamp` DESC
EOD;
    $requests = $application['db']->fetchAll($query, array($user['id']));
    if ($requests) {
        $query_preview = <<<EOD
SELECT `string`
FROM `tools_keywords`
WHERE `request_id` = ?
ORDER BY `id` ASC
LIMIT 5
OFFSET 0
EOD;
        $query_keywords_1 = <<<EOD
SELECT COUNT(`id`) AS `count`
FROM `tools_keywords`
WHERE `request_id` = ?
EOD;
        $query_keywords_2 = <<<EOD
SELECT COUNT(`tools_keywords`.`id`) AS `count`
FROM `tools_keywords`
LEFT JOIN `tools_requests` ON (
    `tools_requests`.`id` = `tools_keywords`.`request_id`
)
WHERE (
    `tools_keywords`.`request_id` = ?
    AND
    `tools_keywords`.`contents` IS NULL
    AND
    `tools_requests`.`timestamp` < (NOW() - INTERVAL 5 HOUR)
)
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
        }
    }

    return $requests;
}

function get_request_and_keywords($application, $user, $id) {
    $query = <<<EOD
SELECT *
FROM `tools_requests`
WHERE `id` = ? AND `user_id` = ?
EOD;
    $request = $application['db']->fetchAssoc(
        $query, array($id, $user['id'])
    );
    $keywords = array();
    if ($request) {
        $query = <<<EOD
SELECT *
FROM `tools_keywords`
WHERE `request_id` = ?
EOD;
        $keywords = $application['db']->fetchAll($query, array($id));
        if ($keywords) {
            foreach ($keywords as $key => $value) {
                $keywords[$key]['contents'] = json_decode(
                    $keywords[$key]['contents'], true
                );
            }
        }
    }

    return array($request, $keywords);
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
        );
    }
    if ($application['session']->get('transfer')) {
        return array(
            'email' => 'administrator@administrator.com',
            'id' => $application['session']->get('transfer'),
        );
    }
    if (!empty($_COOKIE)) {
        foreach ($_COOKIE as $key => $value) {
            $value = explode('|', $value);
            if (strpos($key, 'wordpress_logged_in_') !== false) {
                $query = <<<EOD
SELECT `ID`, `user_email` FROM `wp_users` WHERE `user_login` = ?
EOD;
                $record = $application['db']->fetchAssoc(
                    $query, array($value[0])
                );
                if (!empty($record)) {
                    return array(
                        'email' => $record['user_email'],
                        'id' => $record['ID'],
                    );
                }
            }
        }
    }

    return array(
        'email' => '',
        'id' => 0,
    );
}

function has_aks($groups) {
    return has_groups($groups, array(2, 5));
}

function has_kns($groups) {
    return has_groups($groups, array(3, 4, 5));
}

function has_groups($one, $two) {
    if (!empty($one)) {
        foreach ($one as $key => $value) {
            if (in_array($value, $two)) {
                return true;
            }
        }
    }

    return false;
}

function has_statistics($user) {
    return in_array($user['id'], array(1, 2, 3));
}

function is_development() {
    return $_SERVER['SERVER_PORT'] == '5000';
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
        'dbname' => $variables['mysql']['database'],
        'driver' => $variables['mysql']['driver'],
        'host' => $variables['mysql']['host'],
        'password' => $variables['mysql']['password'],
        'user' => $variables['mysql']['user'],
    ),
));
$application->register(new SessionServiceProvider());
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
    $application['session']->set('user', get_user($application));
    $application['session']->set('groups', get_groups($application));
    $application['twig']->addGlobal(
        'user', $application['session']->get('user')
    );
    $application['twig']->addGlobal(
        'groups', $application['session']->get('groups')
    );
    $application['twig']->addFunction(
        'has_aks', new \Twig_Function_Function('has_aks')
    );
    $application['twig']->addFunction(
        'has_kns', new \Twig_Function_Function('has_kns')
    );
    $application['twig']->addFunction(
        'has_statistics', new \Twig_Function_Function('has_statistics')
    );
});

$before_aks = function () use ($application) {
    if (!has_aks($application['session']->get('groups'))) {
        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
};

$before_kns = function () use ($application) {
    if (!has_kns($application['session']->get('groups'))) {
        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
};

$before_statistics = function () use ($application) {
    if (!has_statistics($application['session']->get('user'))) {
        return $application->redirect(
            $application['url_generator']->generate('dashboard')
        );
    }
};

$application->match('/', function () use ($application) {
    return $application->redirect(
        $application['url_generator']->generate('dashboard')
    );
})
->method('GET');

$application->match('/transfer/{id}', function ($id) use ($application) {
    $application['session']->set('transfer', intval($id));
    return $application->redirect(
        $application['url_generator']->generate('dashboard')
    );
})
->bind('transfer')
->method('GET');

$application->match('/dashboard', function () use ($application) {
    return $application['twig']->render('views/dashboard.twig');
})
->bind('dashboard')
->method('GET');

$application->match('/kns/overview', function () use ($application) {
    $user = $application['session']->get('user');
    $requests = get_requests($application, $user);

    return $application['twig']->render('views/kns_overview.twig', array(
        'requests' => $requests,
    ));
})
->before($before_kns)
->bind('kns_overview')
->method('GET');

$application->match('/kns/add', function () use ($application) {
    $user = $application['session']->get('user');
    list($count, $_) = get_count_and_keywords($application, $user, '');

    return $application['twig']->render('views/kns_add.twig', array(
        'count' => $count,
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
    ));
})
->before($before_kns)
->bind('kns_add')
->method('GET');

$application->match(
    '/kns/process',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');
        list($count, $keywords) = get_count_and_keywords(
            $application, $user, $request->get('keywords')
        );
        if (!$count OR !$keywords) {
            return $application->redirect(
                $application['url_generator']->generate('kns_add')
            );
        }
        $application['db']->insert('tools_requests', array(
            'country' => $request->get('country'),
            'timestamp' => date('Y-m-d H:i:s'),
            'user_id' => $user['id'],
        ));
        $id = $application['db']->lastInsertId();
        if ($keywords) {
            foreach ($keywords as $keyword) {
                $application['db']->insert('tools_keywords', array(
                    'request_id' => $id,
                    'string' => $keyword,
                ));
            }
        }

        return $application->redirect(
            $application['url_generator']->generate('kns_simple', array(
                'id' => $id,
            ))
        );
    }
)
->before($before_kns)
->bind('kns_process')
->method('POST');

$application->match(
    '/kns/{id}/simple',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request OR !$keywords) {
            return $application->redirect(
                $application['url_generator']->generate('kns_overview')
            );
        }

        return $application['twig']->render('views/kns_simple.twig', array(
            'currency' => get_currency($request['country']),
            'email' => $user['email'],
            'keywords' => $keywords,
            'logos' => get_logos($application, $user),
            'request' => $request,
        ));
    }
)
->before($before_kns)
->bind('kns_simple')
->method('GET');

$application->match(
    '/kns/{id}/detailed',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request OR !$keywords) {
            return $application->redirect(
                $application['url_generator']->generate('kns_overview')
            );
        }
        usort($keywords, 'usort_keywords_1');

        return $application['twig']->render('views/kns_detailed.twig', array(
            'currency' => get_currency($request['country']),
            'is_pdf' => true,
            'keywords' => $keywords,
            'logo' => '',
        ));
    }
)
->before($before_kns)
->bind('kns_detailed')
->method('GET');

$application->match(
    '/kns/{id}/csv',
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
->before($before_kns)
->bind('kns_csv')
->method('GET');

$application->match(
    '/kns/{id}/pdf',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        $pdf = get_pdf($application, $user, $request->get('logo'), $id);
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
->before($before_kns)
->bind('kns_pdf')
->method('GET');

$application->match(
    '/kns/{id}/xhr',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );

        if ($keywords) {
            foreach ($keywords as $key => $value) {
                if ($keywords[$key]['contents']) {
                    unset($keywords[$key]['contents']['items']);
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
->before($before_kns)
->bind('kns_xhr')
->method('POST');

$application->match(
    '/kns/{id}/email',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        $subject = 'Your Kindle Niche Sidekick report is ready!';
        $body = <<<EOD
We have attached your report in simple and detailed formats. The detailed
report includes our recommendations along with important information about each
keyword.

If you have any questions at all please don't hesitate to contact
support@zonsidekick.com
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
                    get_pdf($application, $user, $request->get('logo'), $id),
                    sprintf('detailed_report_%s.pdf', date('m_d_Y')),
                    'application/pdf'
                ))
                ->setBody(trim($body))
                ->setFrom(array(
                    'reports@zonsidekick.com',
                ))
                ->setSubject($subject)
                ->setTo(array($request->get('email')));
            $application['mailer']->send($message);
        } catch (Exception $exception ) {
        }

        return new Response();
    }
)
->before($before_kns)
->bind('kns_email')
->method('POST');

$application->match(
    '/kns/{id}/delete',
    function (Request $request, $id) use ($application) {
        $user = $application['session']->get('user');
        list($request_, $keywords) = get_request_and_keywords(
            $application, $user, $id
        );
        if (!$request_ OR !$keywords) {
            return $application->redirect(
                $application['url_generator']->generate('kns_overview')
            );
        }
        if ($request->isMethod('POST')) {
            $application['db']->executeUpdate(
                'DELETE FROM `tools_requests` WHERE `ID` = ?',
                array($id)
            );
            $application['session']->getFlashBag()->add(
                'success', array('The report was deleted successfully.')
            );
            return $application->redirect(
                $application['url_generator']->generate('kns_overview')
            );
        }
        return $application['twig']->render('views/kns_delete.twig', array(
            'id' => $id,
        ));
    }
)
->before($before_kns)
->bind('kns_delete')
->method('GET|POST');

$application->match('/logos/overview', function () use ($application) {
    $user = $application['session']->get('user');

    return $application['twig']->render('views/logos_overview.twig', array(
        'logos' => get_logos($application, $user),
    ));
})
->before($before_kns)
->bind('logos_overview')
->method('GET');

$application->match(
    '/logos/view',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');

        return $application->sendFile(sprintf(
            '%s/%s',
            get_path($application, $user, 'logos'),
            $request->get('file_name')
        ));
    }
)
->before($before_kns)
->bind('logos_view')
->method('GET');

$application->match(
    '/logos/download',
    function (Request $request) use ($application) {
        $user = $application['session']->get('user');

        return $application
            ->sendFile(sprintf(
                '%s/%s',
                get_path($application, $user, 'logos'),
                $request->get('file_name')
            ))
            ->setContentDisposition(
                ResponseHeaderBag::DISPOSITION_ATTACHMENT,
                $request->get('file_name')
            );
    }
)
->before($before_kns)
->bind('logos_download')
->method('GET');

$application->match(
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
                    $application['url_generator']->generate('logos_overview')
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
->before($before_kns)
->bind('logos_add')
->method('GET|POST');

$application->match(
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
                $application['url_generator']->generate('logos_overview')
            );
        }

        return $application['twig']->render(
            'views/logos_delete.twig', array(
                'file_name' => $request->get('file_name'),
            )
        );
    }
)
->before($before_kns)
->bind('logos_delete')
->method('GET|POST');

$application->match('/aks', function () use ($application) {;
    return $application['twig']->render('views/aks.twig', array(
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
    ));
})
->before($before_aks)
->bind('aks')
->method('GET');

$application->match(
    '/aks/xhr',
    function (Request $request) use ($application, $variables) {
        if (is_development()) {
            $output = array('["1", "2", "3"]');
        } else {
            ignore_user_abort(true);
            set_time_limit(0);
            exec(sprintf(
                'workon %s && python %s/scripts/aks.py %s %s %s %s %s',
                $variables['python']['workon'],
                __DIR__,
                escapeshellarg($request->get('country')),
                escapeshellarg($request->get('level')),
                escapeshellarg($request->get('mode')),
                escapeshellarg($request->get('keyword')),
                escapeshellarg($request->get('search_alias'))
            ), $output, $return_var);
        }
        return new Response(implode('', $output));
    }
)
->before($before_aks)
->bind('aks_xhr')
->method('POST');

$application->match(
    '/aks/download',
    function (Request $request) use ($application) {
        $json = json_decode($request->get('json'), true);
        $stream = function () use ($json) {
            echo implode("\n", $json['suggestions']);
        };
        return $application->stream($stream, 200, array(
            'Content-Disposition' => sprintf(
                'attachment; filename="%s.csv"', $json['keyword']
            ),
            'Content-Length' => strlen($json['suggestions']),
            'Content-Type' => 'text/csv',
            'Expires' => '0',
            'Pragma' => 'no-cache',
        ));
    }
)
->before($before_aks)
->bind('aks_download')
->method('POST');

$application->match(
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
                                $application[
                                    'swiftmailer.options'
                                ]['username'],
                            ))
                            ->setSubject($subject)
                            ->setTo(array(
                                'ncroan@gmail.com',
                                'mahendrakalkura@gmail.com',
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

$application->match(
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

$application->match(
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

$application->run();
