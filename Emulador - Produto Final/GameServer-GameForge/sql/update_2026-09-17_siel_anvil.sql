-- Progresso persistente de fabricação garantida na Bigorna de Siel.
CREATE TABLE IF NOT EXISTS player_siel_anvil (
  player_id INT NOT NULL,
  recipe_id INT NOT NULL,
  points SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, recipe_id),
  CONSTRAINT player_siel_anvil_player_fk FOREIGN KEY (player_id)
    REFERENCES players (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
