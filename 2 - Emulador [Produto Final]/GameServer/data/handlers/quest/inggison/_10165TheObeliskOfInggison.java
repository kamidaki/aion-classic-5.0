package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10165 The Obelisk of Inggison. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10165.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10165TheObeliskOfInggison extends CampaignQuestHandler {

	public _10165TheObeliskOfInggison() {
		super(10165, 10164);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798928); // Yulia
		talk(1, 2, 2, 798955); // Marica
		useObject(2, 3, 700628); // instalar o obelisco em LF4_FOBJ_Q10020D
		useObject(3, 4, 700629); // LF4_FOBJ_Q10020E
		useObject(4, 5, 700630); // LF4_FOBJ_Q10020F
		check(5, 6, 6, 798955); // peça roubada pelas lupyllini (quest_monster drop@5); check_ok -> SELECT7
		talk(6, 7, REWARD, 798955); // Marica, select7 SET_SUCCEED
		reward(799058); // Facundus
	}
}
