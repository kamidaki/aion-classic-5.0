package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20170 Poison to Poison. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20170.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20170PoisonToPoison extends CampaignQuestHandler {

	public _20170PoisonToPoison() {
		super(20170, 20169);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799308); // Ankea
		talk(1, 2, 2, 799298); // Geeze
		check(2, 3, 3, 799298); // glândula (quest_monster drop@2); check_ok -> SELECT4
		talkGive(3, 4, 4, 182215619, 1, 799298); // Geeze (select4) entrega o sachê de néctar de newt (quest_20170b)
		itemUseArea(4, 5, 182215619, "DF4_ITEMUSEAREA_Q20024_220070000"); // CSV Progress(4) itemUseArea
		useObject(5, 6, 700707); // destruir DF4_Facilities_Q20024
		talk(6, 7, 7, 799298); // Geeze (select7)
		talk(7, 8, REWARD, 799226); // Barretta, select8 SET_SUCCEED
		reward(799225); // Hler
	}
}
