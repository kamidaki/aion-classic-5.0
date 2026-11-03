-- Quna 5.0: saldo por conta (QUNA e FREE_QUNA juntos), mostrado pelo S 0x11B. O GameServer também cria a tabela no boot.
-- A loja web credita com: INSERT INTO account_quna (account_id, quna) VALUES (?, ?) ON DUPLICATE KEY UPDATE quna = quna + VALUES(quna);
CREATE TABLE IF NOT EXISTS `account_quna` (
  `account_id` INT NOT NULL,
  `quna` BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
