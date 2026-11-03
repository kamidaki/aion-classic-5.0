package quest.cloister_of_kaisinel;

import static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT;
import static com.aionemu.gameserver.model.DialogAction.SETPRO10;

import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.teleport.TeleportService;

/**
 * Campanha 10156 Bound for Inggison. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10156.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10156BoundForInggison extends CampaignQuestHandler {

	private static final int SIBYLLE = 798408;

	public _10156BoundForInggison() {
		super(10156, 10155);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798600); // Eremitia
		talk(1, 2, 2, 798513); // Calimachos
		talk(2, 3, 3, 203760); // Bellia
		talkGive(3, 4, 4, 182215556, 1, 203782); // Bacchus entrega a pedra de onda de éter (quest_10156a, select4)
		talk(4, 5, 5, 798408); // Sibylle
		talkGive(5, 6, 6, 182215557, 1, 203709); // Clymene entrega a chave do navio (quest_10156b, select6_1)
		talk(6, 7, 7, 798408); // Sibylle recebe a chave (select7)
		talk(7, 8, REWARD, 798408); // Sibylle, select8 SET_SUCCEED: embarca para Inggison (onAdvance)
		reward(798926); // Cainus, em Inggison
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (next == REWARD)
			toInggison(env);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// select8_1 (SETPRO10): quem voltou sem falar com o Cainus embarca de novo
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.REWARD && env.getTargetId() == SIBYLLE) {
			if (env.getDialogActionId() == QUEST_SELECT)
				return sendQuestDialog(env, 3399);
			if (env.getDialogActionId() == SETPRO10) {
				toInggison(env);
				return closeDialogWindow(env);
			}
		}
		return super.onDialogEvent(env);
	}

	private static void toInggison(QuestEnv env) {
		// destino do handler 4.8 da 10031 (sem captura 5.0 desta viagem)
		TeleportService.teleportTo(env.getPlayer(), 210050000, 1440, 408, 553, (byte) 77, TeleportAnimation.FADE_OUT_BEAM);
	}
}
