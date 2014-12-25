RENAME TABLE `tools_ce_books` TO `apps_top_100_explorer_books`;
RENAME TABLE `tools_ce_categories` TO `apps_top_100_explorer_categories`;
RENAME TABLE `tools_ce_sections` TO `apps_top_100_explorer_sections`;
RENAME TABLE `tools_ce_trends` TO `apps_top_100_explorer_trends`;
RENAME TABLE `tools_kns_keywords` TO `apps_keyword_analyzer_keywords`;
RENAME TABLE `tools_kns_requests` TO `apps_keyword_analyzer_reports`;
RENAME TABLE `tools_ps_books` TO `apps_popular_searches_books`;
RENAME TABLE `tools_ps_trends` TO `apps_popular_searches_trends`;

ALTER TABLE `apps_keyword_analyzer_keywords` CHANGE `request_id` `report_id` INT(11) NOT NULL;
