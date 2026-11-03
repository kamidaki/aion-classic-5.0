package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10164 Shulack Refugees in Inggison. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10164.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10164ShulackRefugeesInInggison extends CampaignQuestHandler {

	public _10164ShulackRefugeesInInggison() {
		super(10164, 10163);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798975); // Sulla
		talk(1, 2, 2, 798986); // Setsukiki (Shulack_LF4_2)
		check(2, 3, 3, 798986); // conserva e doce (quest_monster drop@2); check_ok -> FINISH_DIALOG
		talk(3, 4, 4, 798985); // irmão (Shulack_LF4_1)
		talkGive(4, 5, 5, 182215567, 1, 798984); // shugo Shugo_LF4_5 entrega o elixir (quest_10164c, select5_1)
		talk(5, 6, 6, 798985); // irmão recebe o elixir
		talkGive(6, 7, 7, 182215568, 1, 798963); // Cinisca entrega o frasco de vaga-lumes (quest_10164d, select7_1)
		talk(7, 8, 8, 798985); // irmão: usar o frasco perto da Setsukiki
		itemUseArea(8, 9, 182215568, "LF4_ITEMUSEAREA_Q11118A_210050000"); // CSV Progress(8) itemUseArea
		talk(9, 10, 10, 798986); // Setsukiki (select10)
		talk(10, 11, REWARD, 798985); // irmão, select11 SET_SUCCEED
		reward(798928); // Yulia
	}
}
