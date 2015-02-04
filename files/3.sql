DROP TABLE IF EXISTS `apps_hot_keywords_step_1_suggested_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_keywords_step_1_suggested_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `category_id` INT(11) DEFAULT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `popularity` DECIMAL(9,2) DEFAULT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `apps_hot_keywords_suggested_keywords_category_id`
        FOREIGN KEY (`category_id`)
        REFERENCES `apps_top_100_explorer_categories` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE KEY `category_id_string` (`category_id`, `string`),
    KEY `category_id` (`category_id`),
    KEY `string` (`string`),
    KEY `popularity` (`popularity`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

DROP TABLE IF EXISTS `apps_hot_keywords_step_2_keywords`;
CREATE TABLE IF NOT EXISTS `apps_hot_keywords_step_2_keywords` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `count` BIGINT(20) UNSIGNED DEFAULT NULL,
    `buyer_behavior` VARCHAR(255) DEFAULT NULL,
    `competition` VARCHAR(255) DEFAULT NULL,
    `optimization`  VARCHAR(255) DEFAULT NULL,
    `popularity`  VARCHAR(255) DEFAULT NULL,
    `spend` DECIMAL(9,2) DEFAULT NULL,
    `average_price` DECIMAL(9,2) DEFAULT NULL,
    `average_print_length` DECIMAL(9,2) DEFAULT NULL,
    `score` DECIMAL(9,2) DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `string` (`string`),
    KEY `score` (`score`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
