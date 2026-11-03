package quest.custom;

import static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT;
import static com.aionemu.gameserver.model.DialogAction.SETPRO10;
import static com.aionemu.gameserver.model.DialogAction.SETPRO6;

import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * Campanha 20153 The Moment of Light and Shadow. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20153.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20153TheMomentOfLightAndShadow extends CampaignQuestHandler {

	private static final int GUARD = 730649, STIGMA_MASTER = 204061, LAND_OF_SHADOWS = 390000000;

	public _20153TheMomentOfLightAndShadow() {
		super(20153);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 730649); // guarda de Pandaemonium (DC1a_DGuard_GUIDE_01): subida-1-60, 1011..1013 e 10000 -> var 1 + teletransporte
		enterWorld(1, 2, 390000000); // subida-1-60, 1219.11 s: var 2 ao chegar à Land of Shadows
		enterWorld(2, 3, 120010000); // subida-1-60, 2669.86 s: var 3 ao chegar a Pandaemonium (ação 104 da Inggril 804135)
		talk(3, 4, 4, 204075); // Balder (select4)
		talk(4, 5, 5, 204053); // Kvasir: SETPRO5 = ir ao Mimir...
		branch(SETPRO6, 6); // ...ou SETPRO6 = pular o Mimir
		talk(5, 6, 6, 204206); // Mimir
		talk(6, 7, 7, 204061); // Aud, mestre de estigma (select7)
		talk(7, 8, 8, 204061); // Aud com estigma equipado (select8; sem estigma, select8_2 no onDialogEvent)
		talk(8, 9, REWARD, 204053); // Kvasir, select9 SET_SUCCEED
		reward(204052); // Vidar
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (fromVar == 0 && next == 1) { // subida-1-60, 1216.65 s: S_QUEST var 1 e S_REQ_TELEPORT no mesmo instante
			WorldMapInstance trial = InstanceService.getNextAvailableInstance(LAND_OF_SHADOWS, env.getPlayer());
			TeleportService.teleportTo(env.getPlayer(), trial, 730.58f, 513.26f, 338.25f, (byte) 60, TeleportAnimation.FADE_OUT_BEAM);
		}
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.START) {
			int var = qs.getQuestVarById(0);
			int action = env.getDialogActionId();
			// select10: o guarda, depois do teste, só manda falar com o sumo sacerdote (SETPRO10 não muda a etapa)
			if (env.getTargetId() == GUARD && var >= 3) {
				if (action == QUEST_SELECT)
					return sendQuestDialog(env, 4080);
				if (action == SETPRO10)
					return closeDialogWindow(env);
			}
			// select8 só com estigma equipado; sem ele, select8_2 (FINISH_DIALOG)
			if (env.getTargetId() == STIGMA_MASTER && var == 7 && action == QUEST_SELECT
				&& env.getPlayer().getEquipment().getEquippedItemsAllStigma().isEmpty())
				return sendQuestDialog(env, 3400);
		}
		return super.onDialogEvent(env);
	}
}
