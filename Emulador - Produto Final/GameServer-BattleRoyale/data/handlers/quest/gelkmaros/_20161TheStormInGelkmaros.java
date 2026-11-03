package quest.gelkmaros;

import static com.aionemu.gameserver.model.DialogAction.SETPRO7;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20161 The Storm in Gelkmaros. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20161.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20161TheStormInGelkmaros extends CampaignQuestHandler {

	public _20161TheStormInGelkmaros() {
		super(20161, 20160);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799227); // Gelastra
		talk(1, 2, 2, 799322); // Herka: SETPRO2 = correntes de vento...
		branch(SETPRO7, 7); // ...ou SETPRO7 = pular para a Vesvola (select2)
		talk(2, 3, 3, 799340); // Vedrfonir
		sensory(3, 4, 206171); // CSV Progress(3) DF4_SensoryArea_Q21080A
		sensory(4, 5, 206172); // CSV Progress(4) DF4_SensoryArea_Q21080B
		sensory(5, 6, 206173); // CSV Progress(5) DF4_SensoryArea_Q21080C
		talk(6, 7, 7, 799427); // Vafuth
		talk(7, 8, 8, 799248); // Vesvola
		check(8, 9, REWARD, 799248); // esporo (quest_monster drop@8); check_ok -> SET_SUCCEED
		reward(799248); // Vesvola
	}
}
