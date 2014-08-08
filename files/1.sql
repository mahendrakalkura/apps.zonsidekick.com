SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `wp_users`;
CREATE TABLE IF NOT EXISTS `wp_users` (
    `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `user_login` varchar(60) NOT NULL DEFAULT '',
    `user_pass` varchar(64) NOT NULL DEFAULT '',
    `user_nicename` varchar(50) NOT NULL DEFAULT '',
    `user_email` varchar(100) NOT NULL DEFAULT '',
    `user_url` varchar(100) NOT NULL DEFAULT '',
    `user_registered` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `user_activation_key` varchar(60) NOT NULL DEFAULT '',
    `user_status` int(11) NOT NULL DEFAULT '0',
    `display_name` varchar(250) NOT NULL DEFAULT '',
    PRIMARY KEY (`ID`),
    KEY `user_login_key` (`user_login`),
    KEY `user_nicename` (`user_nicename`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

INSERT INTO `wp_users` (`ID`,`user_login`,`user_pass`,`user_nicename`,`user_email`,`user_url`,`user_registered`,`user_activation_key`,`user_status`,`display_name`) VALUES
(1,'administrator',MD5('administrator'),'Administrator','administrator@administrator.com','http://www.administrator.com','2001-01-01 00:00:00','',0,'Administrator');

DROP TABLE IF EXISTS `wp_groups_group`;
CREATE TABLE IF NOT EXISTS `wp_groups_group` (
    `group_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
    `parent_id` bigint(20) DEFAULT NULL,
    `creator_id` bigint(20) DEFAULT NULL,
    `datetime` datetime DEFAULT NULL,
    `name` varchar(100) NOT NULL,
    `description` longtext,
    PRIMARY KEY (`group_id`),
    UNIQUE KEY `group_n` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

INSERT INTO `wp_groups_group` (`group_id`,`parent_id`,`creator_id`,`datetime`,`name`,`description`) VALUES
(1,NULL,1,'2001-01-01 00:00:00','Registered',NULL),
(2,NULL,1,'2001-01-01 00:00:00','Keyword Suggester','Access to the Keyword Suggester tool.'),
(3,NULL,1,'2001-01-01 00:00:00','KNS - Commercial','Commercial license. This grants access to the KNS tool with brand-able PDF reports'),
(4,NULL,1,'2001-01-01 00:00:00','KNS - Personal','Personal License. This grants access to the KNS tool.'),
(5,NULL,1,'2001-01-01 00:00:00','Trial','7 day trial. Unlimited use of keyword suggester. 10 keyword per day limit in analyzer.'),
(6,NULL,1,'2001-01-01 00:00:00','Member Resources','Access to our members only resources.'),
(7,NULL,1,'2001-01-01 00:00:00','Standard Access','Standard level access for ZonSidekick subscriptions.');

DROP TABLE IF EXISTS `wp_groups_user_group`;
CREATE TABLE IF NOT EXISTS `wp_groups_user_group` (
    `user_id` bigint(20) unsigned NOT NULL,
    `group_id` bigint(20) unsigned NOT NULL,
    PRIMARY KEY (`user_id`,`group_id`),
    KEY `user_group_gu` (`group_id`,`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `wp_groups_user_group` (`user_id`,`group_id`) VALUES
(1,1),
(1,2),
(1,3),
(1,4),
(1,5),
(1,6),
(1,7);
