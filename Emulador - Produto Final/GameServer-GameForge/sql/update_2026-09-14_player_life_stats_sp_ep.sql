-- SP do Revenant e EP (Ki) do Brawler guardados entre logins.
-- 5.0 oficial: o Brawler voltou de outro personagem com Ki 30, sem nenhum 0x175 no login.
-- Sem estas colunas o servidor funciona, mas SP e Ki voltam a 0 a cada login (o PlayerLifeStatsDAO avisa no log).
ALTER TABLE `player_life_stats`
  ADD COLUMN `sp` int NOT NULL DEFAULT '0' AFTER `fp`,
  ADD COLUMN `ep` int NOT NULL DEFAULT '0' AFTER `sp`;
