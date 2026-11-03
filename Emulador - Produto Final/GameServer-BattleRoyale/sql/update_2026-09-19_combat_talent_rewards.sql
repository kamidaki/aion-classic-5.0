-- Recompensas únicas por personagem dos marcos de Combat Talent (S 0x0148/0x0149).
CREATE TABLE IF NOT EXISTS player_combat_talent_rewards (
  player_id INT NOT NULL,
  claimed_mask INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id),
  CONSTRAINT player_combat_talent_rewards_player_fk FOREIGN KEY (player_id)
    REFERENCES players (id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
