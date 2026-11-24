-- Expressão da tela de aparência do 5.0: é o byte logo depois do `expression` no C_CREATE/C_EDIT_CHARACTER e no S_CHARACTER_LIST/S_PUT_USER.
-- O emulador descartava esse byte na leitura e escrevia 5 (masculino) ou 6 (feminino) na escrita, por isso a expressão escolhida nunca ficava salva.
-- Os personagens que já existem ficam com o valor que sempre mostraram.
ALTER TABLE `player_appearance` ADD COLUMN `face_expression` INT NOT NULL DEFAULT 0 AFTER `expression`;
UPDATE `player_appearance` pa JOIN `players` p ON p.id = pa.player_id SET pa.face_expression = IF(p.gender = 'FEMALE', 6, 5);
