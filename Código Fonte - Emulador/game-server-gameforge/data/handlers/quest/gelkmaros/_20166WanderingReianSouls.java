package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20166 Wandering Reian Souls. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20166.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20166WanderingReianSouls extends CampaignQuestHandler {

	public _20166WanderingReianSouls() {
		super(20166, 20165);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799371); // Vetus
		talk(1, 2, 2, 799289); // Mamalia
		talk(2, 3, 3, 799292); // Belik
		talk(3, 4, 4, 799293); // Stephano
		check(4, 5, 5, 799293); // lembrança (quest_monster drop@4); check_ok -> SELECT6
		talk(5, 6, 6, 799293); // Stephano (select6)
		talk(6, 7, REWARD, 799292); // Belik, select7 SET_SUCCEED
		reward(799289); // Mamalia
	}
}
