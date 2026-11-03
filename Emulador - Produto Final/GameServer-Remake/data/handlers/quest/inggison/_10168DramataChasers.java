package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

/**
 * Campanha 10168 Dramata Chasers. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10168.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10168DramataChasers extends CampaignQuestHandler {

	public _10168DramataChasers() {
		super(10168, 10167);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799005); // Ingnie
		talk(1, 2, 2, 799010); // Wivius
		check(2, 3, 3, 730645); // Mia confere os pertences (quest_monster drop@2); check_ok -> SELECT4
		talk(3, 4, 4, 730645); // Mia (select4)
		kill(4, 1, 216619); // CSV Progress(4~!5) LF4_DayQ_DrakanPr_55_An; entrega o cristal (onAdvance)
		itemUse(5, 6, 182215583); // usar o cristal de memória ([%17]/1)
		talk(6, 7, REWARD, 799010); // Wivius, select7 SET_SUCCEED
		reward(798941); // Pilomenes
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// INFERÊNCIA: o resumo manda usar o cristal do cubo logo depois do abate; nenhuma fonte diz quem entrega o doc_quest_10168e
		if (fromVar == 4)
			giveQuestItem(env, 182215583, 1);
	}
}
