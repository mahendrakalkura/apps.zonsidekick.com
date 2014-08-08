SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `tools_keywords`;
CREATE TABLE IF NOT EXISTS `tools_keywords` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `request_id` int(11) NOT NULL,
    `string` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    `contents` longtext COLLATE utf8_unicode_ci,
    PRIMARY KEY (`id`),
    KEY `request_id` (`request_id`),
    KEY `string` (`string`),
    CONSTRAINT `tools_keywords_request_id`
    FOREIGN KEY (`request_id`)
    REFERENCES `tools_requests` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `tools_requests`;
CREATE TABLE IF NOT EXISTS `tools_requests` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) NOT NULL,
    `timestamp` datetime NOT NULL,
    `country` varchar(255) COLLATE utf8_unicode_ci NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `user_id` (`user_id`),
    KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
