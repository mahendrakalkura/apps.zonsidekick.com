ALTER TABLE `apps_hot_keywords_step_1_suggested_keywords` ADD `date` DATE NOT NULL AFTER `id` , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_keywords_step_2_keywords` ADD `date` DATE NOT NULL AFTER `id` , ADD INDEX (`date`) ;
