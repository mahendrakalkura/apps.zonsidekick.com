ALTER TABLE `apps_hot_category_step_1_words` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_2_keywords` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_3_suggested_keywords` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_4_words` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_5_keywords` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_6_suggested_keywords` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_7_groups` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;

ALTER TABLE `apps_hot_category_step_7_groups_suggested_keywords` ADD `date` DATE NOT NULL , ADD INDEX (`date`) ;
