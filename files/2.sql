ALTER TABLE `apps_keyword_analyzer_keywords` ADD COLUMN `timestamp` DATETIME ;

UPDATE `apps_keyword_analyzer_keywords` SET `timestamp` = NOW() WHERE `contents` IS NOT NULL ;
