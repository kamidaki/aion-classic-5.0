-- Global Auction House (Classic 5.0): anúncios. O item anunciado fica no inventory com item_location 125 e o vendedor como dono.
-- O GameServer também cria a tabela no boot (DatabaseSchemaService).
CREATE TABLE IF NOT EXISTS global_trade_listings (
  id BIGINT NOT NULL AUTO_INCREMENT,
  seller_id INT NOT NULL,
  item_unique_id INT NOT NULL,
  item_id INT NOT NULL,
  item_count BIGINT NOT NULL,
  price BIGINT NOT NULL,
  currency TINYINT NOT NULL,
  category INT NOT NULL,
  register_fee BIGINT NOT NULL DEFAULT 0,
  register_time DATETIME NOT NULL,
  expire_time DATETIME NOT NULL,
  state VARCHAR(16) NOT NULL,
  buyer_id INT NULL DEFAULT NULL,
  sold_time DATETIME NULL DEFAULT NULL,
  sale_fee BIGINT NOT NULL DEFAULT 0,
  collected_time DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (id),
  KEY state_seller (state, seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
