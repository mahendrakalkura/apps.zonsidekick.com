SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO `wp_groups_group` (`group_id`,`parent_id`,`creator_id`,`datetime`,`name`,`description`) VALUES
(1,NULL,1,'2001-01-01 00:00:00','Registered',NULL),
(2,NULL,1,'2001-01-01 00:00:00','Keyword Suggester','Access to the Keyword Suggester tool.'),
(3,NULL,1,'2001-01-01 00:00:00','KNS - Commercial','Commercial license. This grants access to the KNS tool with brand-able PDF reports'),
(4,NULL,1,'2001-01-01 00:00:00','KNS - Personal','Personal License. This grants access to the KNS tool.'),
(5,NULL,1,'2001-01-01 00:00:00','Trial','7 day trial. Unlimited use of keyword suggester. 10 keyword per day limit in analyzer.'),
(6,NULL,1,'2001-01-01 00:00:00','Member Resources','Access to our members only resources.'),
(7,NULL,1,'2001-01-01 00:00:00','Standard Access','Standard level access for ZonSidekick subscriptions.');

INSERT INTO `wp_groups_user_group` (`user_id`,`group_id`) VALUES
(1,1),
(1,2),
(1,3),
(1,4),
(1,5),
(1,6),
(1,7);

INSERT INTO `wp_users` (`ID`,`user_login`,`user_pass`,`user_nicename`,`user_email`,`user_url`,`user_registered`,`user_activation_key`,`user_status`,`display_name`) VALUES
(1,'administrator',MD5('administrator'),'Administrator','administrator@administrator.com','http://www.administrator.com','2001-01-01 00:00:00','',0,'Administrator');
