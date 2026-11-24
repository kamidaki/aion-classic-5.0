-- Classic 5.0: arquiva títulos 1..300 antes de retirar suas referências ativas.
-- Executar somente após backup completo. A operação é reversível pelo script rollback correspondente.
START TRANSACTION;

CREATE TABLE IF NOT EXISTS `player_titles_legacy_archive` (
  `player_id` int NOT NULL,
  `title_id` int NOT NULL,
  `remaining` int NOT NULL DEFAULT '0',
  `archived_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`, `title_id`),
  KEY `title_id` (`title_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `player_title_selections_legacy_archive` (
  `player_id` int NOT NULL,
  `title_id` int NOT NULL DEFAULT '-1',
  `bonus_title_id` int NOT NULL DEFAULT '-1',
  `archived_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `player_titles_legacy_archive` (`player_id`, `title_id`, `remaining`)
SELECT `player_id`, `title_id`, `remaining`
FROM `player_titles`
WHERE `title_id` NOT BETWEEN 408 AND 481
ON DUPLICATE KEY UPDATE `remaining` = VALUES(`remaining`);

INSERT INTO `player_title_selections_legacy_archive` (`player_id`, `title_id`, `bonus_title_id`)
SELECT `id`, `title_id`, `bonus_title_id`
FROM `players`
WHERE (`title_id` NOT BETWEEN 408 AND 481 AND `title_id` <> -1)
   OR (`bonus_title_id` NOT BETWEEN 408 AND 481 AND `bonus_title_id` <> -1)
ON DUPLICATE KEY UPDATE
  `title_id` = VALUES(`title_id`),
  `bonus_title_id` = VALUES(`bonus_title_id`);

UPDATE `players`
SET `title_id` = -1
WHERE `title_id` NOT BETWEEN 408 AND 481 AND `title_id` <> -1;

UPDATE `players`
SET `bonus_title_id` = -1
WHERE `bonus_title_id` NOT BETWEEN 408 AND 481 AND `bonus_title_id` <> -1;

DELETE FROM `player_titles`
WHERE `title_id` NOT BETWEEN 408 AND 481;

COMMIT;
