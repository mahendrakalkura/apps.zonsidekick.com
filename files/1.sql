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

DROP TABLE IF EXISTS `wp_usermeta`;
CREATE TABLE IF NOT EXISTS `wp_usermeta` (
  `umeta_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) unsigned NOT NULL DEFAULT '0',
  `meta_key` varchar(255) DEFAULT NULL,
  `meta_value` longtext,
  PRIMARY KEY (`umeta_id`),
  KEY `user_id` (`user_id`),
  KEY `meta_key` (`meta_key`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

INSERT INTO `wp_usermeta` VALUES (1,1,'paying_customer','1');
