SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `apps_hot_category_step_1_words`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_1_words` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_2_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_2_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_3_suggested_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_3_suggested_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `count` BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    `buyer_behavior` VARCHAR(255) NOT NULL DEFAULT '',
    `competition` VARCHAR(255) NOT NULL DEFAULT '',
    `optimization`  VARCHAR(255) NOT NULL DEFAULT '',
    `popularity`  VARCHAR(255) NOT NULL DEFAULT '',
    `spend` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `average_price` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `average_print_length` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `score` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `words` LONGTEXT COLLATE utf8_unicode_ci,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`),
    KEY `score` (`score`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_4_words`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_4_words` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_5_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_5_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_6_suggested_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_6_suggested_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `count` BIGINT(20) UNSIGNED NOT NULL DEFAULT 0,
    `buyer_behavior` VARCHAR(255) NOT NULL DEFAULT '',
    `competition` VARCHAR(255) NOT NULL DEFAULT '',
    `optimization`  VARCHAR(255) NOT NULL DEFAULT '',
    `popularity`  VARCHAR(255) NOT NULL DEFAULT '',
    `spend` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `average_price` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `average_print_length` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `score` DECIMAL(9,2) NOT NULL DEFAULT 0.00,
    `words` LONGTEXT COLLATE utf8_unicode_ci,
    PRIMARY KEY (`id`),
    UNIQUE KEY `category_id_print_length_string` (`category_id`, `print_length`, `string`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`),
    KEY `string` (`string`),
    KEY `score` (`score`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_7_groups`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_7_groups` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `print_length` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    PRIMARY KEY (`id`),
    KEY `category_id` (`category_id`),
    KEY `print_length` (`print_length`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_7_groups_suggested_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_7_groups_suggested_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `group_id` BIGINT(20) UNSIGNED NOT NULL,
    `suggested_keyword_id` BIGINT(20) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_hot_category_step_7_groups_keywords_group_id` FOREIGN KEY (`group_id`) REFERENCES `apps_hot_category_step_7_groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `apps_hot_category_step_7_groups_keywords_suggested_keyword_id` FOREIGN KEY (`suggested_keyword_id`) REFERENCES `apps_hot_category_step_6_suggested_keywords` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `group_id_suggested_keyword_id` (`group_id`, `suggested_keyword_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_category_step_7_groups_books`;
CREATE TABLE IF NOT EXISTS `apps_hot_category_step_7_groups_books` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `group_id` BIGINT(20) UNSIGNED NOT NULL,
    `book_id` INT(11) NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_hot_category_step_7_groups_books_group_id` FOREIGN KEY (`group_id`) REFERENCES `apps_hot_category_step_7_groups` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `apps_hot_category_step_7_groups_books_book_id` FOREIGN KEY (`book_id`) REFERENCES `apps_top_100_explorer_books` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `group_id_book_id` (`group_id`, `book_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
