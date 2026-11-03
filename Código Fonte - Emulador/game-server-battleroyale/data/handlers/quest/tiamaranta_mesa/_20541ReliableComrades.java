package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20541 Reliable Comrades. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20541.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20541ReliableComrades extends CampaignQuestHandler {

	public _20541ReliableComrades() {
		super(20541, 20540);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 205778); // Udvi
		talk(1, 2, 2, 205774); // Motogut
		talk(2, 3, 3, 205780); // Asraphis
		talk(3, 4, 4, 802389); // Thiamin
		talk(4, 5, 5, 205778); // Udvi
		talk(5, 6, 6, 802387); // Adela
		killSection(6, 1, 10, 7, 220684, 220685, 220690, 220691, 220695, 220696, 220697, 220698, 220699, 220700); // CSV SECTION_0==6; SECTION_1<10
		useObject(7, 8, 701477); // lápide C: captura outros2, barra de 12000 ms e S_QUEST var 8
		talk(8, 9, REWARD, 802387); // Adela: captura, 3739..3742 e 10255 -> st=4
		reward(205778); // Udvi: captura, 10002 -> 1009 -> 5 -> 23 -> st=5 e 20542 LOCKED -> START
	}
}
