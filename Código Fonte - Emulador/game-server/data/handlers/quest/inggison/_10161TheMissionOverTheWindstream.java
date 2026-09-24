package quest.inggison;

import static com.aionemu.gameserver.model.DialogAction.SETPRO7;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10161 The Mission over the Windstream. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10161.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10161TheMissionOverTheWindstream extends CampaignQuestHandler {

	public _10161TheMissionOverTheWindstream() {
		super(10161, 10160);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798927); // Versetti
		talk(1, 2, 2, 798938); // Aglaus
		talk(2, 3, 3, 799025); // Laokoon: SETPRO3 = fazer as correntes de vento...
		branch(SETPRO7, 7); // ...ou SETPRO7 = pular direto para o obelisco (select3_1_1_1)
		sensory(3, 4, 206168); // CSV Progress(3) LF4_SensoryArea_Q11076A
		sensory(4, 5, 206169); // CSV Progress(4) LF4_SensoryArea_Q11076B
		sensory(5, 6, 206170); // CSV Progress(5) LF4_SensoryArea_Q11076C
		talk(6, 7, 7, 799084); // Harami
		talk(7, 8, 8, 730225); // obelisco LF4_FOBJ_Q10020C (objeto com página select8)
		talk(8, 9, 9, 798951); // Ambrosini
		check(9, 10, REWARD, 798951); // Ambrosini confere o dínamo (quest_monster drop@9); check_ok -> SELECT_QUEST_REWARD
		reward(798951); // Ambrosini
	}
}
