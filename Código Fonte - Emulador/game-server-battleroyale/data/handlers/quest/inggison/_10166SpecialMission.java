package quest.inggison;

import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

/**
 * Campanha 10166 Special Mission. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10166.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10166SpecialMission extends CampaignQuestHandler {

	public _10166SpecialMission() {
		super(10166, 10165);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799058); // Facundus
		talk(1, 2, 2, 798996); // Iaetia
		talkGive(2, 3, 3, 182215572, 1, 798997); // Rollia entrega o puçá (quest_10166a) e faz a larva surgir (onAdvance)
		talkGive(3, 4, 4, 182215573, 1, 799081); // larva (select4): puçá com a larva (quest_10166b)
		talk(4, 5, 5, 798997); // Rollia (select5)
		itemUseAt(5, 6, 182215573, 210050000, 1096.5378f, 1129.3385f, 446f, 15f); // CSV Progress(5); zona Q11147A ausente -> marcador oficial
		talk(6, 7, REWARD, 798997); // Rollia, select7 SET_SUCCEED
		reward(798996); // Iaetia
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// handler 4.8 da 11147 (a quest de origem): a Rollia faz a larva surgir na frente do jogador por 5 minutos
		if (fromVar == 2)
			spawnForFiveMinutesInFrontOf(799081, env.getPlayer(), 1);
		else if (fromVar == 3 && env.getVisibleObject() instanceof Npc larva && larva.getNpcId() == 799081)
			larva.getController().delete();
	}
}
