-- Black Cloud Mail (NPShop 5.0): mercadorias por conta, listadas pelo S 0x10C e resgatadas pelo C 0x9E.
-- A loja web entrega inserindo (account_id, name, item_id, item_count); o GameServer também cria a tabela no boot.
CREATE TABLE IF NOT EXISTS account_blackcloud_goods (
  id BIGINT NOT NULL AUTO_INCREMENT,
  account_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  item_id INT NOT NULL,
  item_count BIGINT NOT NULL,
  register_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  received_player_id INT NULL DEFAULT NULL,
  received_time TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  KEY account_pending (account_id, received_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
