package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20169 The Secret of the Naduka Biolab. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20169.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20169TheSecretOfTheNadukaBiolab extends CampaignQuestHandler {

	public _20169TheSecretOfTheNadukaBiolab() {
		super(20169, 20168);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799320); // Helen
		talk(1, 2, 2, 799417); // Javis
		talk(2, 3, 3, 799416); // Tonistar
		check(3, 4, 4, 799416); // arma e armadura (quest_monster drop@3); check_ok -> SELECT5
		talk(4, 5, 5, 799416); // Tonistar (select5)
		talk(5, 6, 6, 799529); // Tonistar disfarçado no Biolab de Naduka
		talk(6, 7, REWARD, 799417); // Javis, select7 SET_SUCCEED
		reward(799308); // Ankea
	}
}
