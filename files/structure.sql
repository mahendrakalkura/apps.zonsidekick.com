SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `tools_keywords` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `request_id` int(11) NOT NULL,
    `string` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `contents` longtext COLLATE utf8_unicode_ci,
    PRIMARY KEY (`id`),
    KEY `request_id` (`request_id`),
    KEY `string` (`string`),
    CONSTRAINT `tools_keywords_request_id` FOREIGN KEY (`request_id`) REFERENCES `tools_requests` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `tools_requests` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) NOT NULL,
    `timestamp` datetime NOT NULL,
    `country` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `user_id` (`user_id`),
    KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE TABLE `wp_groups_group` (
    `group_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `parent_id` bigint(20) DEFAULT NULL,
    `creator_id` bigint(20) DEFAULT NULL,
    `datetime` datetime DEFAULT NULL,
    `name` varchar(100) NOT NULL,
    `description` longtext,
    PRIMARY KEY (`group_id`),
    UNIQUE KEY `group_n` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE `wp_groups_user_group` (
    `user_id` bigint(20) unsigned NOT NULL,
    `group_id` bigint(20) unsigned NOT NULL,
    PRIMARY KEY (`user_id`,`group_id`),
    KEY `user_group_gu` (`group_id`,`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `wp_users` (
    `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `user_login` varchar(60) NOT NULL DEFAULT '',
    `user_pass` varchar(64) NOT NULL DEFAULT '',
    `user_nicename` varchar(50) NOT NULL DEFAULT '',
    `user_email` varchar(100) NOT NULL DEFAULT '',
    `user_url` varchar(100) NOT NULL DEFAULT '',
    `user_registered` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `user_activation_key` varchar(60) NOT NULL DEFAULT '',
    `user_status` int(11) NOT NULL DEFAULT '0',
    `display_name` varchar(250) NOT NULL DEFAULT '',
    PRIMARY KEY (`ID`),
    KEY `user_login_key` (`user_login`),
    KEY `user_nicename` (`user_nicename`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
