DROP TABLE IF EXISTS `apps_book_tracker_books`;
CREATE TABLE IF NOT EXISTS `apps_book_tracker_books`
(
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL,
    `url` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `url` (`url`),
    KEY `user_id` (`user_id`)
)
ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `apps_book_tracker_keywords`;
CREATE TABLE IF NOT EXISTS `apps_book_tracker_keywords`
(
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `book_id` BIGINT(20) UNSIGNED NOT NULL,
    `string` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_book_tracker_keywords_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `apps_book_tracker_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    UNIQUE KEY `book_id_string` (`book_id`, `string`)
)
ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `apps_book_tracker_books_ranks`;
CREATE TABLE IF NOT EXISTS `apps_book_tracker_books_ranks`
(
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `book_id` BIGINT(20) UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `number` BIGINT(20) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_book_tracker_books_ranks_book_id`
    FOREIGN KEY (`book_id`)
    REFERENCES `apps_book_tracker_books` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    UNIQUE KEY `book_id_date` (`book_id`, `date`)
)
ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `apps_book_tracker_keywords_ranks`;
CREATE TABLE IF NOT EXISTS `apps_book_tracker_keywords_ranks`
(
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `keyword_id` BIGINT(20) UNSIGNED NOT NULL,
    `date` DATE NOT NULL,
    `number` BIGINT(20) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_book_tracker_keywords_ranks_keyword_id`
    FOREIGN KEY (`keyword_id`)
    REFERENCES `apps_book_tracker_keywords` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
    UNIQUE KEY `keyword_id_date` (`keyword_id`, `date`)
)
ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
