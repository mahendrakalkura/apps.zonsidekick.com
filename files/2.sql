SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `tools_ce_books`;
CREATE TABLE IF NOT EXISTS `tools_ce_books` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `url` varchar(2048) COLLATE utf8_unicode_ci NOT NULL,
    `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `author` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `price` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `publication_date` date NOT NULL,
    `print_length` int(11) NOT NULL,
    `amazon_best_sellers_rank` text COLLATE utf8_unicode_ci NOT NULL,
    `estimated_sales_per_day` int(11) NOT NULL,
    `earnings_per_day` decimal(9,2) NOT NULL,
    `total_number_of_reviews` int(11) NOT NULL,
    `review_average` decimal(9,2) NOT NULL,
    `section` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    KEY `url` (`url`),
    KEY `title` (`title`),
    KEY `author` (`author`),
    KEY `section` (`section`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `tools_ce_reviews`;
CREATE TABLE IF NOT EXISTS `tools_ce_reviews` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `book_id` int(11) NOT NULL,
    `author` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `date` date NOT NULL,
    `subject` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `body` text COLLATE utf8_unicode_ci NOT NULL,
    `stars` decimal(9,2) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `author` (`author`),
    CONSTRAINT `tools_ce_reviews_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `tools_ce_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `tools_ce_referrals`;
CREATE TABLE IF NOT EXISTS `tools_ce_referrals` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `book_id` int(11) NOT NULL,
    `url` varchar(2048) COLLATE utf8_unicode_ci NOT NULL,
    `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `author` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
    `price` decimal(9,2) NOT NULL,
    `total_number_of_reviews` int(11) NOT NULL,
    `review_average` decimal(9,2) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `url` (`url`),
    CONSTRAINT `tools_ce_referrals_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `tools_ce_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;

DROP TABLE IF EXISTS `tools_ce_trends`;
CREATE TABLE IF NOT EXISTS `tools_ce_trends` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `book_id` int(11) NOT NULL,
    `date_and_time` datetime NOT NULL,
    `rank` int(11) NOT NULL,
    KEY `date_and_time` (`date_and_time`),
    PRIMARY KEY (`id`),
    CONSTRAINT `tools_ce_trends_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `tools_ce_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci AUTO_INCREMENT=1;
