SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `tools_ps_trends` DROP `popularity`;

DELETE FROM `tools_ps_trends`;
