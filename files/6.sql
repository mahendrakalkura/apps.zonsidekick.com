SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `tools_ce_books`
    CHANGE `author` `author_name`
    VARCHAR(255)
    CHARACTER SET utf8
    COLLATE utf8_unicode_ci
    NOT NULL;

ALTER TABLE `tools_ce_books`
    ADD `author_url`
    VARCHAR(255)
    CHARACTER SET utf8
    COLLATE utf8_unicode_ci
    NOT NULL
    AFTER `author_name`;
