package quest.convent_of_marchutan;

import static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT;
import static com.aionemu.gameserver.model.DialogAction.SETPRO10;

import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.teleport.TeleportService;

/**
 * Campanha 20156 Traveling to Gelkmaros. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20156.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20156TravelingToGelkmaros extends CampaignQuestHandler {

	private static final int TIGRINA = 798409;

	public _20156TravelingToGelkmaros() {
		super(20156, 20155);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798800); // Agehia
		talk(1, 2, 2, 798409); // Tigrina
		talk(2, 3, 3, 204202); // Nekai
		talk(3, 4, 4, 204073); // Grer
		talk(4, 5, 5, 204283); // Shugo_DC1_19
		talk(5, 6, 6, 798409); // Tigrina, select6_1 SETPRO6: embarca para Gelkmaros (onAdvance)
		rewardAt(6, 799225); // Hler, em Gelkmaros: só select_success
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (next == 6)
			toGelkmaros(env);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// select6_2 (SETPRO10): quem voltou sem falar com o Hler embarca de novo
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.START && qs.getQuestVarById(0) == 6 && env.getTargetId() == TIGRINA) {
			if (env.getDialogActionId() == QUEST_SELECT)
				return sendQuestDialog(env, 2718);
			if (env.getDialogActionId() == SETPRO10) {
				toGelkmaros(env);
				return closeDialogWindow(env);
			}
		}
		return super.onDialogEvent(env);
	}

	private static void toGelkmaros(QuestEnv env) {
		// destino do handler 4.8 da 20031 (sem captura 5.0 desta viagem)
		TeleportService.teleportTo(env.getPlayer(), 220070000, 1868, 2746, 531, (byte) 20, TeleportAnimation.FADE_OUT_BEAM);
	}
}
