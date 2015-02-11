DROP TABLE IF EXISTS `apps_keyword_suggester`;
CREATE TABLE IF NOT EXISTS `apps_keyword_suggester` (
    `id` BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `country` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `search_alias` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `strings` longtext COLLATE utf8_unicode_ci,
    `timestamp` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `email` (`email`),
    KEY `string` (`string`),
    KEY `country` (`country`),
    KEY `search_alias` (`search_alias`),
    KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
