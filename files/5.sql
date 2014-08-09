SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `tools_ps_books`;
CREATE TABLE IF NOT EXISTS `tools_ps_books` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `url` varchar(1083) COLLATE utf8_unicode_ci NOT NULL,
    `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `book_cover_image` text COLLATE utf8_unicode_ci DEFAULT NULL,
    `amazon_best_sellers_rank` text COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `tools_ps_trends`;
CREATE TABLE IF NOT EXISTS `tools_ps_trends` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `book_id` int(11) NOT NULL,
    `date_and_time` datetime NOT NULL,
    PRIMARY KEY (`id`),
    KEY `date_and_time` (`date_and_time`),
    CONSTRAINT `tools_ps_trends_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `tools_ps_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;
