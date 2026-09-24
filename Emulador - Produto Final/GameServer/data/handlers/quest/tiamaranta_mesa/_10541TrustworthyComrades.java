package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10541 Trustworthy Comrades. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10541.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10541TrustworthyComrades extends CampaignQuestHandler {

	public _10541TrustworthyComrades() {
		super(10541, 10540);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 205769); // Ancanus
		talk(1, 2, 2, 205765); // Celesia
		talk(2, 3, 3, 205821); // Erasmus
		talk(3, 4, 4, 802388); // Retinoa
		talk(4, 5, 5, 205769); // Ancanus
		talk(5, 6, 6, 802386); // Adela
		killSection(6, 1, 10, 7, 220625, 220626, 220628, 220629, 220630, 220631, 220632, 220633, 220634, 220635); // CSV SECTION_0==6; SECTION_1<10
		useObject(7, 8, 701475); // lápide A (barra de 12 s; mesma mecânica da C na captura outros2)
		talk(8, 9, REWARD, 802386); // Adela, select9 SET_SUCCEED
		reward(205769); // Ancanus
	}
}
