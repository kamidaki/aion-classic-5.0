package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10170 Defeat Inggison's Balaur. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10170.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10170DefeatInggisonSBalaur extends CampaignQuestHandler {

	public _10170DefeatInggisonSBalaur() {
		super(10170, 10169);
	}

	@Override
	protected void defineSteps() {
		talkGive(0, 1, 1, 182215590, 1, 798941); // Pilomenes entrega o mapa (doc_quest_10170a)
		itemUse(1, 2, 182215590); // conferir o mapa no cubo
		talk(2, 3, 3, 799017); // Sulinia
		check(3, 4, 4, 799017); // símbolos dos quatro pontos (quest_monster drop@3); check_ok -> SELECT5
		talkGive(4, 5, 5, 182215595, 1, 799017); // Sulinia (select5) entrega o disfarce (quest_10170f)
		sensory(5, 6, 701568); // CSV Progress(5) LF4_SensoryArea_Q10170a
		itemUseAt(6, 7, 182215595, 210050000, 2143f, 2344f, 82.6875f, 15f); // CSV Progress(6); zona Q10170A ausente -> marcador oficial
		talkGive(7, 8, 8, 182215596, 1, 216498); // carcereiro LF4_C5_DrakanAs_vil_NamedQ_55_Ae (select8) entrega o relatório (quest_10170g)
		talk(8, 9, REWARD, 799017); // Sulinia, select9 SET_SUCCEED
		reward(798926); // Cainus
	}
}
