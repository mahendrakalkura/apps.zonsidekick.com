SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `tools_ps_trends` ADD `keywords` TEXT NOT NULL AFTER `book_id`;

UPDATE `tools_ps_trends` SET `keywords` = '[]';
