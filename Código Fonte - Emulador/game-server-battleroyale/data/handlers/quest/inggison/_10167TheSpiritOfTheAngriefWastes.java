package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10167 The Spirit of the Angrief Wastes. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10167.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10167TheSpiritOfTheAngriefWastes extends CampaignQuestHandler {

	public _10167TheSpiritOfTheAngriefWastes() {
		super(10167, 10166);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798996); // Iaetia
		talk(1, 2, 2, 799008); // Totus
		check(2, 3, 3, 799008); // enxofre das crateras (quest_monster drop@2); check_ok -> SELECT4
		talkGive(3, 4, 4, 182215578, 1, 799008); // Totus (select4) entrega a tocha (quest_10167e)
		kill(4, 5, 215737, 216786, 215738, 216787); // CSV Progress(4~!9) LF4_C2_DrakanWorkerFi/Pr(_Farm)_55_An
		useObjects(9, 5, 700601); // queimar LF4_FOBJ_Q10022A ([%17]/5); INFERÊNCIA: vars 9..13, o CSV não lista
		talk(14, 7, REWARD, 799008); // Totus, select7 SET_SUCCEED
		reward(799005); // Ingnie
	}
}
