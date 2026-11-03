CREATE TABLE IF NOT EXISTS `player_alter_stats` (
  `player_id` int NOT NULL,
  `alter_kills` int NOT NULL DEFAULT '0',
  `alter_points` int NOT NULL DEFAULT '0',
  `daily_kills` int NOT NULL DEFAULT '0',
  `weekly_kills` int NOT NULL DEFAULT '0',
  `last_kill_time` timestamp NULL DEFAULT NULL,
  `last_reset_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_combat_power` (
  `player_id` int NOT NULL,
  `combat_power` int NOT NULL DEFAULT '0',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`),
  CONSTRAINT `player_combat_power_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_hairstyle` (
  `object_id` int NOT NULL,
  `player_id` int NOT NULL,
  `item_id` int NOT NULL,
  `like` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`object_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `player_hairstyle_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_hits` (
  `account_id` int NOT NULL,
  `player_id` int NOT NULL,
  `cumulative_reward` int NOT NULL DEFAULT '0',
  `better_amount_hits` int NOT NULL DEFAULT '0',
  `daily_hits` int NOT NULL DEFAULT '0',
  `weekly_hits` int NOT NULL DEFAULT '0',
  `monthly_hits` int NOT NULL DEFAULT '0',
  `year_hits` int NOT NULL DEFAULT '0',
  `total_hits` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`account_id`,`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_moros` (
  `player_id` int NOT NULL,
  `level` smallint unsigned NOT NULL DEFAULT '1',
  `points` int unsigned NOT NULL DEFAULT '0',
  `restore_times` varchar(512) NOT NULL DEFAULT '',
  PRIMARY KEY (`player_id`),
  CONSTRAINT `player_moros_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_participation_points` (
  `account_id` int NOT NULL,
  `points` bigint NOT NULL DEFAULT '0',
  `last_update` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_secure_area_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `player_id` int NOT NULL,
  `account_id` int NOT NULL,
  `player_name` varchar(50) NOT NULL,
  `action` varchar(20) NOT NULL,
  `world_id` int NOT NULL,
  `x` float NOT NULL,
  `y` float NOT NULL,
  `z` float NOT NULL,
  `points_spent` int NOT NULL DEFAULT '0',
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_player` (`player_id`),
  KEY `idx_account` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_storybook_finished` (
  `player_id` int NOT NULL,
  `storybook_id` int NOT NULL,
  `finish_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`,`storybook_id`),
  CONSTRAINT `player_storybook_finished_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `player_storybook_items` (
  `player_id` int NOT NULL,
  `storybook_id` int NOT NULL,
  `item_id` int NOT NULL,
  `item_count` int unsigned NOT NULL,
  `register_order` bigint NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`player_id`,`storybook_id`,`item_id`),
  KEY `register_order` (`register_order`),
  CONSTRAINT `player_storybook_items_player_fk` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;