SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `tools_ps`;
CREATE TABLE IF NOT EXISTS `tools_ps` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `book_cover_image` varchar(1083) COLLATE utf8_unicode_ci DEFAULT NULL,
    `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `amazon_best_sellers_rank` text COLLATE utf8_unicode_ci NOT NULL,
    `url` varchar(1083) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    KEY `url` (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;
