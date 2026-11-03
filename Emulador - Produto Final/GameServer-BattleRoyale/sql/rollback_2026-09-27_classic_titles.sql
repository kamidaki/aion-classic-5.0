-- Reverte update_2026-09-27_classic_titles.sql sem apagar os arquivos de auditoria.
START TRANSACTION;

INSERT INTO `player_titles` (`player_id`, `title_id`, `remaining`)
SELECT archive.`player_id`, archive.`title_id`, archive.`remaining`
FROM `player_titles_legacy_archive` archive
INNER JOIN `players` player ON player.`id` = archive.`player_id`
ON DUPLICATE KEY UPDATE `remaining` = VALUES(`remaining`);

UPDATE `players` player
INNER JOIN `player_title_selections_legacy_archive` archive ON archive.`player_id` = player.`id`
SET player.`title_id` = archive.`title_id`,
    player.`bonus_title_id` = archive.`bonus_title_id`;

COMMIT;
