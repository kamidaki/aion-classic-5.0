package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20164 War Remnants of the Antagor Battlefield. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20164.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20164WarRemnantsOfTheAntagorBattlefield extends CampaignQuestHandler {

	public _20164WarRemnantsOfTheAntagorBattlefield() {
		super(20164, 20163);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799226); // Barretta
		talk(1, 2, 2, 799245); // Vyuin
		check(2, 3, 3, 799245); // restos do Drakan (quest_monster drop@2); check_ok -> SELECT4
		talkGive(3, 4, 4, 182215609, 1, 799245); // Vyuin (select4) entrega o item de uso (quest_20164b)
		itemUseArea(4, 5, 182215609, "DF4_ITEMUSEAREA_Q20020_220070000"); // CSV Progress(4) itemUseArea
		sensory(5, 6, 206128); // CSV Progress(5) DF4_SensoryArea_Q20020
		kill(6, 1, 218987, 216545); // CSV Progress(6) DF4_Drakan_Runner01_Q_55_An ou DF4_DrakanFi_NmdQ_52_An
		talk(7, 8, REWARD, 799245); // Vyuin, select8 SET_SUCCEED
		reward(799226); // Barretta
	}
}
