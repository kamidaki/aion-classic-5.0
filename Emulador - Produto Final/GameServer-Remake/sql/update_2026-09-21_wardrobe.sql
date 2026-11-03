-- Wardrobe 5.0 (C 0xEE-0xFB / S 0x122-0x124). O GameServer também faz isto no boot (DatabaseSchemaService).
-- Marca de visual aplicado pelo guarda-roupa (C 0xFA): o blob 0x0B do item leva essa marca, e só esse visual sai pelo Wardrobe.
ALTER TABLE `inventory` ADD COLUMN `wardrobe_skin` boolean NOT NULL DEFAULT '0' AFTER `item_skin`;

-- Entradas do guarda-roupa; a cor fica como 0x01RRGGBB (0 = sem tinta, porque existe tinta preta 000000).
CREATE TABLE IF NOT EXISTS `player_wardrobe` (
  `object_id` int NOT NULL,
  `player_id` int NOT NULL,
  `item_id` int NOT NULL,
  `color` int NOT NULL DEFAULT '0',
  `like` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`object_id`),
  KEY `player_id` (`player_id`),
  CONSTRAINT `player_wardrobe_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
